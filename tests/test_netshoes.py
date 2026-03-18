"""
Testes do NetshoeScraper.

Usa `responses` para mockar chamadas HTTP

pytest tests/test_netshoes.py -v
"""
import pytest
import responses as resp_mock
from scrapers.netshoes import NetshoeScraper, BASE_URL, SEARCH_URL


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def scraper():
    return NetshoeScraper(delay_min=0, delay_max=0)  # sem delay nos testes


FAKE_SEARCH_HTML = """
<html><body>
  <ul>
    <li class="showcase-item">
      <a href="/produto/camisa-flamengo-2024">
        <h3 class="product-title">Camisa Flamengo 2024</h3>
        <span class="price-current">R$ 299,90</span>
        <span class="price-original">R$ 349,90</span>
      </a>
    </li>
    <li class="showcase-item">
      <a href="/produto/camisa-flamengo-away">
        <h3 class="product-title">Camisa Flamengo Away 2024</h3>
        <span class="price-current">R$ 269,90</span>
      </a>
    </li>
  </ul>
</body></html>
"""

FAKE_PRODUCT_HTML = """
<html><body>
  <h1 class="product-title">Camisa Flamengo 2024 - Adidas</h1>
  <span class="sale-price">R$ 299,90</span>
  <span class="price-original">R$ 349,90</span>
  <img class="product-image" src="https://img.netshoes.com.br/camisa-fla.jpg"/>
</body></html>
"""

FAKE_UNAVAILABLE_HTML = """
<html><body>
  <h1 class="product-title">Camisa Esgotada</h1>
  <span class="sale-price">R$ 199,90</span>
  <span class="out-of-stock">Esgotado</span>
</body></html>
"""


# ------------------------------------------------------------------
# Testes de _parse_price
# ------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("R$ 299,90",   299.90),
    ("R$299,90",    299.90),
    ("1.299,90",   1299.90),
    ("299.90",      299.90),
    ("1.299",      1299),
    ("",            None),
    ("1.299.90",    1299.90), 
    ("indisponível", None),
])
def test_parse_price(raw, expected):
    result = NetshoeScraper._parse_price(raw)
    assert result == expected


# ------------------------------------------------------------------
# Testes de _calc_discount
# ------------------------------------------------------------------

def test_calc_discount_with_values():
    discount = NetshoeScraper._calc_discount(299.90, 349.90)
    assert discount == pytest.approx(14.3, abs=0.2)

def test_calc_discount_no_old_price():
    assert NetshoeScraper._calc_discount(299.90, None) is None

def test_calc_discount_price_higher():
    # preço atual maior que original — sem desconto
    assert NetshoeScraper._calc_discount(400.0, 350.0) is None

# ------------------------------------------------------------------
# Testes de scrape_product (HTTP mockado)
# ------------------------------------------------------------------

@resp_mock.activate
def test_scrape_product_success(scraper):
    url = f"{BASE_URL}/produto/camisa-flamengo-2024"
    resp_mock.add(resp_mock.GET, url, body=FAKE_PRODUCT_HTML, status=200)

    product = scraper.scrape_product(url)

    assert product is not None
    assert "Flamengo" in product.name
    assert product.price == 299.90
    assert product.old_price == 349.90
    assert product.store == "netshoes"
    assert product.available is True
    assert product.image_url == "https://img.netshoes.com.br/camisa-fla.jpg"


@resp_mock.activate
def test_scrape_product_unavailable(scraper):
    url = f"{BASE_URL}/produto/camisa-esgotada"
    resp_mock.add(resp_mock.GET, url, body=FAKE_UNAVAILABLE_HTML, status=200)

    product = scraper.scrape_product(url)

    assert product is not None
    assert product.available is False


@resp_mock.activate
def test_scrape_product_http_error(scraper):
    url = f"{BASE_URL}/produto/nao-existe"
    resp_mock.add(resp_mock.GET, url, status=404)

    product = scraper.scrape_product(url)
    assert product is None


# ------------------------------------------------------------------
# Testes de search_team
# ------------------------------------------------------------------

@resp_mock.activate
def test_search_team_returns_products(scraper):
    # Mock da busca
    resp_mock.add(
        resp_mock.GET,
        SEARCH_URL,
        match_querystring=False,
        body=FAKE_SEARCH_HTML,
        status=200,
    )
    # Mock das páginas individuais
    resp_mock.add(
        resp_mock.GET,
        f"{BASE_URL}/produto/camisa-flamengo-2024",
        body=FAKE_PRODUCT_HTML,
        status=200,
    )
    resp_mock.add(
        resp_mock.GET,
        f"{BASE_URL}/produto/camisa-flamengo-away",
        body=FAKE_PRODUCT_HTML,
        status=200,
    )

    products = scraper.search_team("Flamengo")

    assert len(products) == 2
    for p in products:
        assert p.team == "Flamengo"
        assert p.store == "netshoes"
        assert p.price > 0


@resp_mock.activate
def test_search_team_empty_results(scraper):
    resp_mock.add(
        resp_mock.GET,
        SEARCH_URL,
        match_querystring=False,
        body="<html><body><p>Nenhum resultado</p></body></html>",
        status=200,
    )
    products = scraper.search_team("TimeInexistente")
    assert products == []
