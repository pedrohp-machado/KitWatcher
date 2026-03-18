"""
Conexão com PostgreSQL via psycopg2.
Funções de acesso ao banco usadas pelos scrapers.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extras import RealDictCursor

from scrapers.base import ProductData

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
)


@contextmanager
def get_conn() -> Generator:
    """Context manager que abre e fecha conexão automaticamente."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_products(products: list[ProductData]) -> None:
    """
    Persiste lista de produtos e registra histórico de preços.

    Upsert em `products` + insert em `price_history`.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            for p in products:
                # Upsert no cadastro do produto
                cur.execute(
                    """
                    INSERT INTO products (name, url, store, image_url)
                    VALUES (%(name)s, %(url)s, %(store)s, %(image_url)s)
                    ON CONFLICT (url)
                    DO UPDATE SET
                        name      = EXCLUDED.name,
                        image_url = EXCLUDED.image_url
                    RETURNING id
                    """,
                    {"name": p.name, "url": p.url, "store": p.store, "image_url": p.image_url},
                )
                product_id = cur.fetchone()["id"]

                # Registra snapshot de preço
                cur.execute(
                    """
                    INSERT INTO price_history
                        (product_id, price, old_price, discount, available, collected_at)
                    VALUES
                        (%(product_id)s, %(price)s, %(old_price)s,
                         %(discount)s, %(available)s, %(collected_at)s)
                    """,
                    {
                        "product_id": product_id,
                        "price": p.price,
                        "old_price": p.old_price,
                        "discount": p.discount,
                        "available": p.available,
                        "collected_at": p.collected_at,
                    },
                )

    logger.info(f"[db] {len(products)} produtos salvos")
