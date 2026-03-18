-- Schema inicial do Monitor de Camisas
-- Rodar: psql -U monitor -d monitor_camisas -f schema.sql

-- Times
CREATE TABLE IF NOT EXISTS teams (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    country    VARCHAR(50)  DEFAULT 'Brasil',
    league     VARCHAR(100),
    created_at TIMESTAMPTZ  DEFAULT NOW()
);

-- Produtos (camisas)
CREATE TABLE IF NOT EXISTS products (
    id         SERIAL PRIMARY KEY,
    team_id    INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    name       VARCHAR(255) NOT NULL,
    url        TEXT         NOT NULL UNIQUE,   -- chave natural para upsert
    store      VARCHAR(50)  NOT NULL,          -- 'netshoes', 'centauro', etc.
    image_url  TEXT,
    active     BOOLEAN      DEFAULT TRUE,
    created_at TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_store   ON products(store);
CREATE INDEX IF NOT EXISTS idx_products_team_id ON products(team_id);

-- Histórico de preços (append-only — nunca deletar)
CREATE TABLE IF NOT EXISTS price_history (
    id           BIGSERIAL PRIMARY KEY,
    product_id   INTEGER     NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price        NUMERIC(10,2) NOT NULL,
    old_price    NUMERIC(10,2),
    discount     NUMERIC(5,2),               -- percentual, ex: 15.50
    available    BOOLEAN       DEFAULT TRUE,
    collected_at TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_product   ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_collected ON price_history(collected_at DESC);

-- Alertas de usuário
CREATE TABLE IF NOT EXISTS user_alerts (
    id           SERIAL PRIMARY KEY,
    user_email   VARCHAR(255) NOT NULL,
    product_id   INTEGER      NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    target_price NUMERIC(10,2) NOT NULL,
    triggered    BOOLEAN       DEFAULT FALSE,
    triggered_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ   DEFAULT NOW(),

    UNIQUE(user_email, product_id)  -- um alerta por produto por usuário
);

-- View útil: último preço de cada produto
CREATE OR REPLACE VIEW products_latest_price AS
SELECT
    p.id,
    p.name,
    p.url,
    p.store,
    p.image_url,
    ph.price,
    ph.old_price,
    ph.discount,
    ph.available,
    ph.collected_at AS last_checked,
    t.name AS team_name
FROM products p
LEFT JOIN LATERAL (
    SELECT * FROM price_history
    WHERE product_id = p.id
    ORDER BY collected_at DESC
    LIMIT 1
) ph ON TRUE
LEFT JOIN teams t ON t.id = p.team_id
WHERE p.active = TRUE;
