"""
Scraper da Centauro.


"""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import  urljoin
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductData
from database.connection import save_products

logger = logging.getLogger(__name__)

BASE_URL = "https://www.centauro.com.br"
SEARCH_URL = f"{BASE_URL}/busca/"

class CentauroScraper(BaseScraper):

    store_name = "centauro"

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def _parse_search_results(self, html: str) -> list[ProductData]:
        """Parseia o HTML da página de resultados de busca e retorna lista de ProductData."""
        soup = BeautifulSoup(html, "html.parser")
        products = []
        print("Parseando item de busca...")
        for item in soup.select("div[data-testid='grid-product-card-enhanced']"):
            try:
                name = item.select_one('[data-testid="product-name"]').get_text(strip=True)
                url = item.select_one('.Linkstyled__Link-sc-111jz8f-0')['href']
                
                price_el = item.select_one('[data-testid="price-current"]')
                if price_el is None:
                    continue  # Ignora produtos sem preço válido
                price = self._parse_price(price_el.get_text(strip=True))
                
                old_price_str = item.select_one('[data-testid="price-promotion"]')
                old_price = self._parse_price(old_price_str.get_text(strip=True)) if old_price_str else None
                
                discount = round((old_price - price) / old_price * 100, 2) if isinstance(old_price, float) and isinstance(price, float) and old_price > price else None

                image_url = item.select_one('[data-testid="product-image"]')['src'] if item.select_one('[data-testid="product-image"]') else None

                products.append(ProductData(
                    name=name,
                    url=url,
                    store=self.store_name,
                    price=price,
                    old_price=old_price,
                    discount=discount,
                    available=True,
                    image_url=image_url,
                ))

            except Exception as e:
                logger.error(f"Erro ao parsear produto na busca: {e}", exc_info=True)
        return products


    def search_team(self, team_name: str) -> list[ProductData]:
        """
        Busca camisas de um time.

        Args:
            team_name: nome do time, ex: 'Flamengo', 'Corinthians'

        Returns:
            Lista de ProductData encontrados.

        """
        
        query = f"camisa {team_name}"

        url = f"{SEARCH_URL}{team_name}"

        print(f"Buscando na url: {url}")

        html = self._get_with_selenium(url)
        products = self._parse_search_results(html)

        for p in products:
            p.team = team_name
        
        if products:
            save_products(products) # URL relativa intencional para evitar problemas de duplicação no banco

        return products 

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
            logger.error(f"[centauro] erro ao acessar produto {full_url}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        return self._parse_product_page(soup, full_url)


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
                logger.warning(f"[centauro] dados incompletos em {url}")
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
            logger.error(f"[centauro] erro ao parsear produto {url}: {e}", exc_info=True)
            return None

    def _extract_name(self, soup: BeautifulSoup) -> str:
        # Para o nome do produto
        selectors = [
            '[data-testid="product-name"]',
            'span[data-testid="product-name"]',
            '.ProductMainInfo-styled__Name-sc-5205fe51-0',
            'span.Typographystyled__Simple-sc-bdxvrr-5.bpucZA',
            'span[class*="Name-sc-"]',
            '[class*="product-name"]',
            '.ProductMainInfo-styled__LinkWrapper-sc-5205fe51-1 span',
            'a[class*="ProductMainInfo"] span',
            'span[class*="Name"]'
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        selectors = [
            '[data-testid="price-current"]',
            'p[data-testid="price-current"]',
            '[class*="CurrentPrice"]',
            '[class*="current-price"]',
            '[class*="price-current"]',
            '.Price-styled__Container-sc-f425a1c-0 p:first-of-type'
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
            # Prioridade 1: data-testid encontrado
            '[data-testid="price-promotion"]',
            'del[data-testid="price-promotion"]',
            'del',
            'del[class*="price"]'
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
            '[data-testid="product-image"]',
            'img.ProductMediaCarousel-styled__Photo-sc-c46bd70b-4',
            '.ProductCardWithMedia-styled__ImageWrapper-sc-fcb2ef60-1 img',
            'img[class*="Photo"]',
            'img[class*="Image"]'
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


