"""
Base scraper — todas as lojas herdam desta classe.
Define a interface comum e utilitários compartilhados.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import logging
import time
import random

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class ProductData:
    """Dados de um produto coletado pelo scraper."""
    name: str
    url: str
    store: str
    price: float
    old_price: Optional[float] = None
    discount: Optional[float] = None   # percentual, ex: 15.0
    available: bool = True
    image_url: Optional[str] = None
    team: Optional[str] = None
    collected_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_discount(self) -> bool:
        return self.old_price is not None and self.old_price > self.price

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "store": self.store,
            "price": self.price,
            "old_price": self.old_price,
            "discount": self.discount,
            "available": self.available,
            "image_url": self.image_url,
            "team": self.team,
            "collected_at": self.collected_at.isoformat(),
        }


class BaseScraper(ABC):
    """
    Classe base para todos os scrapers.

    Subclasses devem implementar:
        - store_name: str
        - search_team(team_name) -> list[ProductData]
        - scrape_product(url) -> ProductData | None
    """

    # Headers que imitam um browser real
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1",
    }

    def __init__(
        self,
        delay_min: float = 1.5,
        delay_max: float = 3.5,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.timeout = timeout
        self.session = self._build_session(max_retries)

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Nome da loja, ex: 'netshoes'"""

    @abstractmethod
    def search_team(self, team_name: str) -> list[ProductData]:
        """Busca camisas de um time e retorna lista de produtos."""

    @abstractmethod
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """Coleta dados de uma URL de produto específica."""

    # ------------------------------------------------------------------
    # Utilitários protegidos
    # ------------------------------------------------------------------

    def _get(self, url: str, **kwargs) -> requests.Response:
        """GET com retry, delay aleatório e headers padrão."""
        self._random_delay()
        headers = {**self.DEFAULT_HEADERS, **kwargs.pop("headers", {})}
        response = self.session.get(
            url, headers=headers, timeout=self.timeout, **kwargs
        )
        response.raise_for_status()
        logger.debug(f"[{self.store_name}] GET {url} → {response.status_code}")
        return response

    def _random_delay(self) -> None:
        """Pausa aleatória para não sobrecarregar o servidor."""
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.debug(f"[{self.store_name}] aguardando {delay:.1f}s")
        time.sleep(delay)

    @staticmethod
    def _parse_price(raw: str) -> Optional[float]:
        """
        Converte string de preço para float.
        Aceita: 'R$ 299,90', '299.90', '1.299,90'
        """
        if not raw:
            return None
        cleaned = (
            raw.strip()
            .replace("R$", "")
            .replace(" ", "")
            .replace(",", ".")
        )
        if cleaned.count(".") > 1:
            # Ex: '1.299,90' → '1299.90' 
            # Deve remover o ponto dos milhares, mantendo a vírgula como separador decimal
            cleaned = cleaned.replace(".", "", cleaned.count(".") - 1)

        elif cleaned.count(".") == 1 and cleaned.find(".") < len(cleaned) - 3:
            # Ex: 1.299 → 1299
            cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Não foi possível converter preço: {raw!r}")
            return None

    @staticmethod
    def _build_session(max_retries: int) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
