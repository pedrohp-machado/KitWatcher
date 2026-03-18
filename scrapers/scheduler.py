"""
Agendador de scraping: roda os scrapers em intervalos personalizados usando APScheduler e Redis para persistencia de jobs
"""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from .netshoes import NetshoeScraper
from database.connection import save_products

logger = logging.getLogger(__name__)

# Times monitorados 
TEAMS_TO_MONITOR = [
    "Flamengo",
    "Corinthians",
    "São Paulo",
    "Palmeiras",
    "Santos",
    "Grêmio",
    "Internacional",
    "Atlético Mineiro",
]

jobstores = {
    "default": RedisJobStore(host="localhost", port=6379, db=1),
}

executors = {
    "default": ThreadPoolExecutor(max_workers=3),
}


def run_netshoes_scraper() -> None:
    """Job executado pelo scheduler: coleta preços da Netshoes."""
    logger.info(f"[scheduler] iniciando coleta Netshoes — {datetime.utcnow().isoformat()}")
    scraper = NetshoeScraper()

    for team in TEAMS_TO_MONITOR:
        try:
            products = scraper.search_team(team)
            if products:
                save_products(products)
                logger.info(f"[scheduler] {team}: {len(products)} produtos salvos")
        except Exception as e:
            logger.error(f"[scheduler] erro ao coletar {team}: {e}", exc_info=True)

    logger.info("[scheduler] coleta finalizada")


def start_scheduler() -> None:
    """Inicia o scheduler bloqueante (roda como processo separado)"""
    scheduler = BlockingScheduler(
        jobstores=jobstores,
        executors=executors,
        timezone="America/Sao_Paulo",
    )

    # Coleta a cada 4 horas
    scheduler.add_job(
        run_netshoes_scraper,
        trigger="interval",
        hours=4,
        id="netshoes_scraper",
        name="Netshoes — coleta de camisas",
        replace_existing=True,
    )

    logger.info("[scheduler] iniciando — coleta a cada 4 horas")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[scheduler] encerrado")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_scheduler()
