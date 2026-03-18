# Monitor de Camisas de Time ⚽

Sistema para monitorar preços de camisas em e-commerces brasileiros com histórico, alertas e análise de tendências.

## Stack

- **Scraping**: Python + BeautifulSoup4
- **Fila**: Redis + APScheduler
- **Banco**: PostgreSQL
- **API**: FastAPI (próxima fase)
- **Frontend**: React (próxima fase)

## Início rápido

```bash
# 1. Sobe o banco e o Redis
docker-compose up db redis -d

# 2. Instala dependências
pip install -r requirements.txt

# 3. Aplica o schema
psql -U monitor -d monitor_camisas -f database/schema.sql

# 4. Roda o scraper manualmente (teste)
python -c "
from scrapers.netshoes import NetshoeScraper
s = NetshoeScraper()
produtos = s.search_team('Flamengo')
for p in produtos:
    print(p.name, p.price)
"

# 5. Inicia o scheduler (coleta a cada 4h)
python -m scrapers.scheduler
```

## Testes

```bash
pytest tests/ -v
```

## Estrutura

```
monitor-camisas/
├── scrapers/
│   ├── base.py          # Classe abstrata BaseScraper
│   ├── netshoes.py      # Scraper Netshoes
│   └── scheduler.py     # APScheduler com Redis
├── backend/             # FastAPI (fase 2)
├── database/
│   ├── schema.sql       # Criação das tabelas
│   └── connection.py    # Funções de acesso ao banco
├── tests/
│   └── test_netshoes.py
├── docker-compose.yml
└── requirements.txt
```

## Roadmap

- [x] Scraper Netshoes
- [ ] Scraper Centauro
- [ ] Scraper FutFanatics
- [ ] FastAPI com endpoints REST
- [ ] Frontend React + gráficos
- [ ] Alertas email/Telegram
- [ ] Docker completo + CI/CD
