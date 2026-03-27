"""
Scraper da FutFanatics.

Utiliza a estrutura base para buscar camisas de times diretamente na URL
de categoria da loja, parseando os cards de produto via BeautifulSoup.
"""
from __future__ import annotations

import logging
import unicodedata
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductData
from database.connection import save_products

logger = logging.getLogger(__name__)

BASE_URL = "https://www.futfanatics.com.br"

class FutFanaticsScraper(BaseScraper):

    store_name = "futfanatics"

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def _parse_search_results(self, html: str) -> list[ProductData]:
        """Parseia o HTML da página de resultados de busca e retorna lista de ProductData."""
        soup = BeautifulSoup(html, "html.parser")
        products = []
        
        print(f"Buscando produtos na futfanatics")
        for item in soup.select("li[itemtype='https://schema.org/SomeProducts']"):
            try:
                # Nome
                name_el = item.select_one("div.product-name")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)

                print(f"Parseando produto: {name}")
                
                # Link
                link_el = item.select_one("a")
                if not link_el or not link_el.has_attr("href"):
                    continue
                url = link_el["href"]
                
                # Garante que a URL é absoluta
                if not url.startswith("http"):
                    url = urljoin(BASE_URL, url)
                
                # Preço
                price_el = item.select_one("div.price span")
                if price_el is None:
                    continue  # Ignora produtos sem preço válido
                price = self._parse_price(price_el.get_text(strip=True))
                
                # Tentativa de pegar o preço antigo (geralmente fica em um <del> ou classe 'old-price' na FutFanatics)
                old_price_str = item.select_one("del") or item.select_one(".old-price")
                old_price = self._parse_price(old_price_str.get_text(strip=True)) if old_price_str else None
                
                # Desconto
                discount = round((old_price - price) / old_price * 100, 2) if isinstance(old_price, float) and isinstance(price, float) and old_price > price else None

                # Imagem
                img_el = item.select_one("div.product-image img")
                # Lida com lazy loading se a FutFanatics usar (data-src, data-lazy, etc)
                image_url = None
                if img_el:
                    image_url = img_el.get("data-original") or img_el.get("src")
                
                products.append(ProductData(
                    name=name,
                    url=url,
                    store=self.store_name,
                    price=price,
                    old_price=old_price,
                    discount=discount,
                    available=True,  # Se está na vitrine, assumimos disponível num primeiro momento
                    image_url=image_url,
                ))

            except Exception as e:
                logger.error(f"Erro ao parsear produto na busca da FutFanatics: {e}", exc_info=True)
                
        return products

    def format_team_url(self, team_name: str) -> str:
        """Remove acentos, espaços e deixa em minúsculo (ex: São Paulo -> sao-paulo)"""
        # Remove acentos
        nfkd_form = unicodedata.normalize('NFKD', team_name)
        text = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
       
        # Deixa minúsculo
        return text.lower()

    def search_team(self, team_name: str) -> list[ProductData]:
        """
        Busca camisas de um time na FutFanatics.

        Args:
            team_name: nome do time, ex: 'Flamengo', 'São Paulo'

        Returns:
            Lista de ProductData encontrados.
        """
        formatted_team = self.format_team_url(team_name)
        print(f"Time formatado para URL: {formatted_team}")
        url = f"{BASE_URL}/{formatted_team}"

        logger.info(f"[futfanatics] Acessando URL: {url}")
        
        # Assumindo que o método vem do BaseScraper
        html = self._get_with_selenium(url)
        products = self._parse_search_results(html)

        for p in products:
            p.team = team_name
        
        if products:
            save_products(products) 

        logger.info(f"[futfanatics] encontrado {len(products)} produtos para time '{team_name}'")
        return products 

    def scrape_product(self, url: str) -> Optional[ProductData]:
        """
        Coleta dados completos de uma URL de produto.
        """
        full_url = url if url.startswith("http") else urljoin(BASE_URL, url)

        try:
            # Aqui você pode usar self._get ou self._get_with_selenium dependendo da necessidade
            html = self._get_with_selenium(full_url) 
        except Exception as e:
            logger.error(f"[futfanatics] erro ao acessar produto {full_url}: {e}")
            return None

        soup = BeautifulSoup(html, "html.parser")
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
                logger.warning(f"[futfanatics] dados incompletos em {url}")
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
            logger.error(f"[futfanatics] erro ao parsear produto {url}: {e}", exc_info=True)
            return None

    def _extract_name(self, soup: BeautifulSoup) -> str:
        # Tenta pegar pelo H1 padrão de produto
        el = soup.select_one("h1.product-name, h1[itemprop='name']")
        return el.get_text(strip=True) if el else ""

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        el = soup.select_one(".preco-por, [itemprop='price']")
        if el:
            return self._parse_price(el.get_text(strip=True))
        return None

    def _extract_old_price(self, soup: BeautifulSoup) -> Optional[float]:
        el = soup.select_one(".preco-de, del")
        if el:
            return self._parse_price(el.get_text(strip=True))
        return None

    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one(".qd-product-image img, #image-main")
        if el:
            return el.get("data-src") or el.get("src")
        return None

    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        # Botões de "Avise-me" ou classes de "Indisponível"
        unavailable_signals = soup.select(".indisponivel, .avise-me")
        return len(unavailable_signals) == 0

    @staticmethod
    def _calc_discount(price: Optional[float], old_price: Optional[float]) -> Optional[float]:
        if price and old_price and old_price > price:
            return round((1 - price / old_price) * 100, 1)
        return None