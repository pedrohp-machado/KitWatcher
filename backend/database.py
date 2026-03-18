import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://monitor:monitor@localhost:5432/monitor_camisas"
)

engine = create_engine(DATABASE_URL)

# Session factory para criar sessões de banco de dados (cada instancia é uma sessão unica)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


