"""
Scraper da Netshoes.

Netshoes renderiza boa parte do conteúdo via HTML estático — BeautifulSoup
é suficiente para a maioria dos casos sem precisar de Selenium.
"""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, ProductData

logger = logging.getLogger(__name__)

BASE_URL = "https://www.netshoes.com.br"
SEARCH_URL = f"{BASE_URL}/busca"


class NetshoeScraper(BaseScraper):

    store_name = "netshoes"

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def search_team(self, team_name: str) -> list[ProductData]:
        """
        Busca camisas de um time.

        Args:
            team_name: nome do time, ex: 'Flamengo', 'Corinthians'

        Returns:
            Lista de ProductData encontrados.

        Example:
            >>> scraper = NetshoeScraper()
            >>> products = scraper.search_team("Flamengo")
            >>> print(products[0].price)
        """
        query = f"camisa {team_name}"
        params = {"ntt": query, "D": "camisa"}
        url = f"{SEARCH_URL}?{urlencode(params)}"

        logger.info(f"[netshoes] buscando: {query!r} → {url}")

        try:
            response = self._get(url)
        except Exception as e:
            logger.error(f"[netshoes] falha na busca de {team_name!r}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        product_cards = self._parse_search_results(soup)

        logger.info(f"[netshoes] {len(product_cards)} produtos encontrados para {team_name!r}")

        results = []
        for card in product_cards:
            if not card.get("url"):
                continue
            product = self.scrape_product(card["url"])
            if product:
                product.team = team_name
                results.append(product)

        return results

    def scrape_product(self, url: str) -> Optional[ProductData]:
        """
        Coleta dados completos de uma URL de produto

        Args:
            url: URL do produto

        Returns:
            ProductData ou None
        """
        full_url = url if url.startswith("http") else urljoin(BASE_URL, url)

        try:
            response = self._get(full_url)
        except Exception as e:
            logger.error(f"[netshoes] erro ao acessar produto {full_url}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        return self._parse_product_page(soup, full_url)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_search_results(self, soup: BeautifulSoup) -> list[dict]:
        """
        Extrai links e preços básicos da página de resultados.

        A Netshoes usa classes como 'showcase-item' ou 'product-card'?
        """
        cards = []

        # Seletor principal (atualizar se o HTML da loja mudar)
        items = soup.select("li.showcase-item, div[class*='product-card'], div[class*='showcase']")

        if not items:
            # Fallback, tenta qualquer link de produto
            logger.warning("[netshoes] seletor principal não encontrou itens, usando fallback")
            items = soup.select("a[href*='/produto/']")

        for item in items:
            card = self._extract_card_data(item)
            if card:
                cards.append(card)

        return cards

    def _extract_card_data(self, element) -> Optional[dict]:
        """Extrai dados básicos de um card de produto na listagem."""
        try:
            # URL do produto
            link = element.select_one("a[href]") or element
            href = link.get("href", "")
            if not href:
                return None

            # Preço na listagem (pode não ter desconto ainda)
            price_el = element.select_one(
                "[class*='price-current'], [class*='sale-price'], "
                "span[class*='price']:not([class*='original'])"
            )
            price_raw = price_el.get_text(strip=True) if price_el else ""

            # Preço original (riscado)
            old_price_el = element.select_one(
                "[class*='price-original'], [class*='list-price'], "
                "span[class*='old'], del"
            )
            old_price_raw = old_price_el.get_text(strip=True) if old_price_el else ""

            # Nome do produto
            name_el = element.select_one(
                "[class*='product-name'], [class*='title'], h2, h3"
            )
            name = name_el.get_text(strip=True) if name_el else ""

            return {
                "url": href,
                "name": name,
                "price_raw": price_raw,
                "old_price_raw": old_price_raw,
            }
        except Exception as e:
            logger.debug(f"[netshoes] erro ao extrair card: {e}")
            return None

    # ------------------------------------------------------------------
    # Parsing detalhado da página de produto
    # ------------------------------------------------------------------

    def _parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extrai dados completos da página de um produto."""
        try:
            name = self._extract_name(soup)
            price = self._extract_price(soup)
            old_price = self._extract_old_price(soup)
            image_url = self._extract_image(soup)
            available = self._extract_availability(soup)
            discount = self._calc_discount(price, old_price)

            if not name or price is None:
                logger.warning(f"[netshoes] dados incompletos em {url}")
                return None

            return ProductData(
                name=name,
                url=url,
                store=self.store_name,
                price=price,
                old_price=old_price,
                discount=discount,
                available=available,
                image_url=image_url,
            )

        except Exception as e:
            logger.error(f"[netshoes] erro ao parsear produto {url}: {e}", exc_info=True)
            return None

    def _extract_name(self, soup: BeautifulSoup) -> str:
        selectors = [
            "h1.product-title",
            "h1[class*='title']",
            "h1[class*='name']",
            "h1",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        selectors = [
            "[class*='sale-price']",
            "[class*='price-current']",
            "[class*='price-sale']",
            "span[class*='price']:not([class*='original']):not([class*='list'])",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = self._parse_price(el.get_text(strip=True))
                if price and price > 0:
                    return price
        return None

    def _extract_old_price(self, soup: BeautifulSoup) -> Optional[float]:
        selectors = [
            "[class*='price-original']",
            "[class*='list-price']",
            "[class*='price-before']",
            "del[class*='price']",
            "span.old-price",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = self._parse_price(el.get_text(strip=True))
                if price and price > 0:
                    return price
        return None

    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            "img.product-image",
            "img[class*='product']",
            "img[id*='product']",
            ".product-gallery img",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                src = el.get("data-src") or el.get("data-lazy") or el.get("src", "")
                if src and src.startswith("http"):
                    return src
        return None

    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        # Esgotado aparece tipicamente como um badge ou botão desabilitado
        out_of_stock_signals = soup.select(
            "[class*='out-of-stock'], [class*='esgotado'], "
            "button[disabled][class*='buy'], [class*='sold-out']"
        )
        return len(out_of_stock_signals) == 0

    @staticmethod
    def _calc_discount(price: Optional[float], old_price: Optional[float]) -> Optional[float]:
        if price and old_price and old_price > price:
            return round((1 - price / old_price) * 100, 1)
        return None
