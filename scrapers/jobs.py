from .netshoes import NetshoeScraper
from .futfanatics import FutFanaticsScraper
import logging

logger = logging.getLogger(__name__)

def collect_netshoes(team_name: str) -> int:
    """Coleto os produtos da Netshoes para um time especifico"""
    logger.info(f"Coletando as camisas da Netshoes para o time: {team_name}")

    try:
        scraper = NetshoeScraper()

        products = scraper.search_team(team_name)

        count = len(products)

        logger.info(f"Coleta finalizada, total de produtos: {count}")

        return count
    except Exception as e:
        logger.error(f"Erro ao fazer a coleta da Netshoes para o time {team_name}: {e}")
        return 0


def collect_futfanatics(team_name: str) -> int:
    """Coleto os produtos da FutFanatics para um time especifico"""
    logger.info(f"Coletando as camisas da FutFanatics para o time: {team_name}")

    try:
        scraper = FutFanaticsScraper()

        products = scraper.search_team(team_name)

        count = len(products)

        logger.info(f"Coleta finalizada, total de produtos: {count}")

        return count
    except Exception as e:
        logger.error(f"Erro ao fazer a coleta da FutFanatics para o time {team_name}: {e}")
        return 0
    