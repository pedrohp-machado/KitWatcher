"""Scheduler de coleta de dados dos sites monitorados, usando rq e redis para enfileirar os jobs de coleta"""
import os
import time 
import logging
import schedule
from redis import Redis
from rq import Queue
from .jobs import collect_futfanatics, collect_netshoes

logger = logging.getLogger(__name__)

TEAMS = ["São Paulo", "Palmeiras", "Corinthians", "Santos"]

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def enqueue_jobs():
    """Enfileira os jobs de coleta para cada time e cada site"""
    logger.info("Enfileirando os jobs de coleta...")


    redis_conn = Redis(REDIS_HOST, REDIS_PORT)
    queue = Queue(connection=redis_conn)

    for team in TEAMS:
        queue.enqueue(collect_futfanatics, team)
        queue.enqueue(collect_netshoes, team)   

        logger.info(f"Add a fila de coleta p/ o time: {team}")

def start_scheduler():
    """Mantem o scheduler rodando e enfileirando os jobs"""

    enqueue_jobs() # Enfileira assim que iniciar

    schedule.every(6).hours.do(enqueue_jobs) # Agenda para a cada 6 hrs

    logger.info("Scheduler iniciado, rodando a cada 6 horas...")

    while True:
        schedule.run_pending()
        time.sleep(300) # verifica jobs a cada 5 min para evitar uso excessivo da CPU

if __name__ == "__main__":
    start_scheduler()