-- ============================================================
--  Marmitaria Yao — Schema inicial
--  Executado automaticamente na primeira criação do banco.
-- ============================================================

-- Tipos enumerados
DO $$ BEGIN
    CREATE TYPE estado_pedido AS ENUM ('EM_ANDAMENTO', 'PRONTO', 'ENTREGUE', 'CANCELADO');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Garante que CANCELADO existe em bancos criados antes desta migração
DO $$ BEGIN
    ALTER TYPE estado_pedido ADD VALUE IF NOT EXISTS 'CANCELADO';
END $$;

-- ------------------------------------------------------------
--  Clientes
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id     SERIAL       PRIMARY KEY,
    nome   VARCHAR(255) NOT NULL,
    numero VARCHAR(20)  NOT NULL,
    ativo  BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Garante coluna de remoção lógica em bancos criados antes desta migração
ALTER TABLE IF EXISTS clientes
    ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;

-- ------------------------------------------------------------
--  Estoque (cardápio / itens disponíveis)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estoque (
    id                    SERIAL         PRIMARY KEY,
    item                  VARCHAR(255)   NOT NULL,
    quantidade_disponivel INT            NOT NULL DEFAULT 0 CHECK (quantidade_disponivel >= 0),
    valor                 NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    ativo                 BOOLEAN        NOT NULL DEFAULT TRUE
);

-- Garante coluna de remoção lógica em bancos criados antes desta migração
ALTER TABLE IF EXISTS estoque
    ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;

-- ------------------------------------------------------------
--  Pedidos
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedidos (
    id          SERIAL         PRIMARY KEY,
    cliente_id  INT            NOT NULL REFERENCES clientes(id),
    data        DATE           NOT NULL DEFAULT CURRENT_DATE,
    estado      estado_pedido  NOT NULL DEFAULT 'EM_ANDAMENTO',
    valor       NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (valor >= 0),
    pago        BOOLEAN        NOT NULL DEFAULT FALSE
);

-- ------------------------------------------------------------
--  Itens do pedido (relação N:N entre pedidos e estoque)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedido_itens (
    id         SERIAL PRIMARY KEY,
    pedido_id  INT    NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    item_id    INT    NOT NULL REFERENCES estoque(id),
    quantidade INT    NOT NULL DEFAULT 1 CHECK (quantidade > 0),
    valor_unitario NUMERIC(10, 2) NOT NULL CHECK (valor_unitario > 0),
    CONSTRAINT uq_pedido_item UNIQUE (pedido_id, item_id)
);

-- Garante constraints em bancos criados antes desta migração
DO $$ BEGIN
    ALTER TABLE pedido_itens ADD CONSTRAINT uq_pedido_item UNIQUE (pedido_id, item_id);
EXCEPTION WHEN duplicate_table THEN NULL;
END $$;

DO $$ BEGIN
    -- Garante coluna valor_unitario em bancos criados antes desta migração
    ALTER TABLE pedido_itens ADD COLUMN IF NOT EXISTS valor_unitario NUMERIC(10, 2);

    -- Backfill: garante que linhas antigas tenham um valor positivo
    UPDATE pedido_itens
    SET valor_unitario = 1
    WHERE valor_unitario IS NULL;

    -- Após o backfill, reforça NOT NULL na coluna
    ALTER TABLE pedido_itens ALTER COLUMN valor_unitario SET NOT NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE pedidos ADD CONSTRAINT pedidos_valor_check CHECK (valor >= 0);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
--  Índices úteis para as buscas mais comuns
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_clientes_nome        ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_id   ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado       ON pedidos(estado);
CREATE INDEX IF NOT EXISTS idx_pedido_itens_pedido  ON pedido_itens(pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedido_itens_item    ON pedido_itens(item_id);
