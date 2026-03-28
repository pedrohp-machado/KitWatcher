"""
Testes do FutFanaticsScraper.

Usa `responses` para mockar chamadas HTTP.
Rodar com: pytest tests/test_futfanatics.py -v
"""
import pytest
import responses as resp_mock
from unittest.mock import patch
from scrapers.futfanatics import FutFanaticsScraper, BASE_URL

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def scraper():
    return FutFanaticsScraper(delay_min=0, delay_max=0)  # sem delay nos testes


# HTML baseado nos seletores mapeados da FutFanatics (li.apoio-sh, etc)
FAKE_SEARCH_HTML = """
<html><body>
  <li itemtype="https://schema.org/SomeProducts">
    <a href="/camisa-sao-paulo-2024">
      <div class="product-image"><img src="https://img.futfanatics.com.br/spfc1.jpg"/></div>
      <div class="product-name">Camisa São Paulo 2024</div>
      <div class="price"><span>R$ 299,90</span></div>
      <del>R$ 349,90</del>
    </a>
  </li>
  <li itemtype="https://schema.org/SomeProducts">
    <a href="/camisa-sao-paulo-away">
      <div class="product-image"><img src="https://img.futfanatics.com.br/spfc2.jpg"/></div>
      <div class="product-name">Camisa São Paulo Away 2024</div>
      <div class="price"><span>R$ 269,90</span></div>
    </a>
  </li>
</body></html>
"""

# HTML da página de produto baseada nos seletores da FutFanatics
FAKE_PRODUCT_HTML = """
<html><body>
  <h1 class="product-name">Camisa São Paulo 2024 - New Balance</h1>
  <span class="preco-por">R$ 299,90</span>
  <span class="preco-de">R$ 349,90</span>
  <div class="qd-product-image"><img src="https://img.futfanatics.com.br/camisa-spfc.jpg"/></div>
</body></html>
"""

# HTML de produto esgotado (usando as classes da FutFanatics)
FAKE_UNAVAILABLE_HTML = """
<html><body>
  <h1 class="product-name">Camisa Esgotada</h1>
  <span class="preco-por">R$ 199,90</span>
  <div class="indisponivel">Avise-me quando chegar</div>
</body></html>
"""


# ------------------------------------------------------------------
# Testes de _parse_price (Herdados da base, mas testamos via classe atual)
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
    result = FutFanaticsScraper._parse_price(raw)
    assert result == expected


# ------------------------------------------------------------------
# Testes de _calc_discount
# ------------------------------------------------------------------

def test_calc_discount_with_values():
    discount = FutFanaticsScraper._calc_discount(299.90, 349.90)
    assert discount == pytest.approx(14.3, abs=0.2)

def test_calc_discount_no_old_price():
    assert FutFanaticsScraper._calc_discount(299.90, None) is None

def test_calc_discount_price_higher():
    # preço atual maior que original — sem desconto
    assert FutFanaticsScraper._calc_discount(400.0, 350.0) is None

# ------------------------------------------------------------------
# Testes de scrape_product (HTTP mockado)
# ------------------------------------------------------------------

@resp_mock.activate
def test_scrape_product_success(scraper):
    with patch.object(scraper, '_get_with_selenium', return_value=FAKE_PRODUCT_HTML):
        product = scraper.scrape_product(f"{BASE_URL}/produto/camisa-sao-paulo-2024")
        assert product is not None
        assert "São Paulo" in product.name
        assert product.price == 299.90
        assert product.old_price == 349.90
        assert product.store == "futfanatics"
        assert product.available is True
        assert product.image_url == "https://img.futfanatics.com.br/camisa-spfc.jpg"


@resp_mock.activate
def test_scrape_product_unavailable(scraper):
    url = f"{BASE_URL}/produto/camisa-esgotada"
    resp_mock.add(resp_mock.GET, url, body=FAKE_UNAVAILABLE_HTML, status=200)
    product = scraper.scrape_product(url)
    assert product is None


@resp_mock.activate
def test_scrape_product_http_error(scraper):
    with patch.object(scraper, '_get_with_selenium', side_effect=Exception("erro")):
        product = scraper.scrape_product(f"{BASE_URL}/produto/nao-existe")
        assert product is None



# ------------------------------------------------------------------
# Testes de search_team (Selenium mockado)
# ------------------------------------------------------------------

def test_search_team_returns_products(scraper):
    with patch.object(scraper, '_get_with_selenium', return_value=FAKE_SEARCH_HTML):
        products = scraper.search_team("São Paulo")
        assert len(products) == 2
        # Verifica se preencheu o campo team corretamente
        assert products[0].team == "São Paulo"

def test_search_team_empty_results(scraper):
    with patch.object(scraper, '_get_with_selenium', return_value="<html><body><p>Nenhum resultado</p></body></html>"):
        products = scraper.search_team("TimeInexistente")
        assert products == []