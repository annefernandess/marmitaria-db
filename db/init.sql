-- ============================================================
--  Marmitaria Yao — Schema inicial
--  Executado automaticamente na primeira criação do banco.
-- ============================================================

-- Tipos enumerados
CREATE TYPE estado_pedido AS ENUM ('EM_ANDAMENTO', 'PRONTO', 'ENTREGUE');

-- ------------------------------------------------------------
--  Clientes
-- ------------------------------------------------------------
CREATE TABLE clientes (
    id     SERIAL       PRIMARY KEY,
    nome   VARCHAR(255) NOT NULL,
    numero VARCHAR(20)  NOT NULL
);

-- ------------------------------------------------------------
--  Estoque (cardápio / itens disponíveis)
-- ------------------------------------------------------------
CREATE TABLE estoque (
    id                    SERIAL         PRIMARY KEY,
    item                  VARCHAR(255)   NOT NULL,
    quantidade_disponivel INT            NOT NULL DEFAULT 0 CHECK (quantidade_disponivel >= 0),
    valor                 NUMERIC(10, 2) NOT NULL CHECK (valor > 0)
);

-- ------------------------------------------------------------
--  Pedidos
-- ------------------------------------------------------------
CREATE TABLE pedidos (
    id          SERIAL         PRIMARY KEY,
    cliente_id  INT            NOT NULL REFERENCES clientes(id),
    data        DATE           NOT NULL DEFAULT CURRENT_DATE,
    estado      estado_pedido  NOT NULL DEFAULT 'EM_ANDAMENTO',
    valor       NUMERIC(10, 2) NOT NULL DEFAULT 0,
    pago        BOOLEAN        NOT NULL DEFAULT FALSE
);

-- ------------------------------------------------------------
--  Itens do pedido (relação N:N entre pedidos e estoque)
-- ------------------------------------------------------------
CREATE TABLE pedido_itens (
    id         SERIAL PRIMARY KEY,
    pedido_id  INT    NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    item_id    INT    NOT NULL REFERENCES estoque(id),
    quantidade INT    NOT NULL DEFAULT 1 CHECK (quantidade > 0)
);

-- ------------------------------------------------------------
--  Índices úteis para as buscas mais comuns
-- ------------------------------------------------------------
CREATE INDEX idx_clientes_nome        ON clientes(nome);
CREATE INDEX idx_pedidos_cliente_id   ON pedidos(cliente_id);
CREATE INDEX idx_pedidos_estado       ON pedidos(estado);
CREATE INDEX idx_pedido_itens_pedido  ON pedido_itens(pedido_id);
CREATE INDEX idx_pedido_itens_item    ON pedido_itens(item_id);
