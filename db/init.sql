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

-- Carga inicial de produtos
INSERT INTO estoque (item, quantidade_disponivel, valor, ativo)
SELECT seed.item, seed.quantidade_disponivel, seed.valor, seed.ativo
FROM (
    VALUES
        ('Coxinha de Frango', 40, 7.50, TRUE),
        ('Coxinha de Carne', 30, 8.00, TRUE),
        ('Empada de Frango', 25, 6.50, TRUE),
        ('Empada de Palmito', 20, 7.00, TRUE),
        ('Pastel de Queijo', 35, 6.00, TRUE),
        ('Pastel de Carne', 35, 6.50, TRUE),
        ('Kibe', 28, 5.50, TRUE),
        ('Enroladinho de Salsicha', 32, 5.00, TRUE),
        ('Suco de Laranja 300ml', 18, 4.50, TRUE),
        ('Refrigerante Lata', 24, 5.00, TRUE)
) AS seed(item, quantidade_disponivel, valor, ativo)
LEFT JOIN estoque existente
    ON LOWER(existente.item) = LOWER(seed.item)
WHERE existente.id IS NULL;

-- ------------------------------------------------------------
--  Usuários (autenticação)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id         SERIAL       PRIMARY KEY,
    nome       VARCHAR(255) NOT NULL,
    email      VARCHAR(255) NOT NULL UNIQUE,
    senha      VARCHAR(255) NOT NULL,
    numero     VARCHAR(20)  NOT NULL,
    role       VARCHAR(20)  NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    cliente_id INT          NULL REFERENCES clientes(id),
    ativo      BOOLEAN      NOT NULL DEFAULT TRUE
);

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS cliente_id INT NULL REFERENCES clientes(id);

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS numero VARCHAR(20) NOT NULL DEFAULT '';

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS senha VARCHAR(255) NOT NULL DEFAULT '';

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS nome VARCHAR(255) NOT NULL DEFAULT '';

ALTER TABLE IF EXISTS usuarios
    ADD COLUMN IF NOT EXISTS email VARCHAR(255) NOT NULL DEFAULT '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email_unique ON usuarios(email);

-- Carga inicial de clientes para demonstração do fluxo do usuário
INSERT INTO clientes (nome, numero, ativo)
SELECT seed.nome, seed.numero, seed.ativo
FROM (
    VALUES
        ('Maria Silva', '11999990001', TRUE),
        ('João Souza', '11999990002', TRUE),
        ('Ana Costa', '11999990003', TRUE)
) AS seed(nome, numero, ativo)
LEFT JOIN clientes existente
    ON existente.numero = seed.numero
   AND LOWER(existente.nome) = LOWER(seed.nome)
WHERE existente.id IS NULL;

INSERT INTO usuarios (nome, email, senha, numero, role, cliente_id, ativo)
VALUES ('YAO Admin', 'yao@lanches.com', 'admin', '00000000000', 'admin', NULL, TRUE)
ON CONFLICT (email) DO NOTHING;

-- Carga inicial de usuários comuns vinculados aos clientes de demonstração
INSERT INTO usuarios (nome, email, senha, numero, role, cliente_id, ativo)
SELECT seed.nome, seed.email, seed.senha, seed.numero, 'user', cliente.id, TRUE
FROM (
    VALUES
        ('Maria Silva', 'maria@yao.com', '123456', '11999990001'),
        ('João Souza', 'joao@yao.com', '123456', '11999990002'),
        ('Ana Costa', 'ana@yao.com', '123456', '11999990003')
) AS seed(nome, email, senha, numero)
JOIN clientes cliente
    ON cliente.numero = seed.numero
   AND LOWER(cliente.nome) = LOWER(seed.nome)
LEFT JOIN usuarios existente
    ON LOWER(existente.email) = LOWER(seed.email)
WHERE existente.id IS NULL;

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

    -- Backfill: preenche linhas antigas com um valor consistente do estoque
    UPDATE pedido_itens pi
    SET valor_unitario = e.valor
    FROM estoque e
    WHERE pi.item_id = e.id
      AND pi.valor_unitario IS NULL;

    -- Após o backfill, reforça NOT NULL na coluna
    ALTER TABLE pedido_itens ALTER COLUMN valor_unitario SET NOT NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    -- Recalcula o valor dos pedidos com base nos itens preenchidos
    UPDATE pedidos p
    SET valor = COALESCE(src.total, 0)
    FROM (
        SELECT
            pi.pedido_id AS id,
            SUM(pi.quantidade * pi.valor_unitario) AS total
        FROM pedido_itens pi
        GROUP BY pi.pedido_id
    ) src
    WHERE p.id = src.id;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE pedidos ADD CONSTRAINT pedidos_valor_check CHECK (valor >= 0);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    -- Garante constraint de valor positivo para valor_unitario em bancos criados antes desta migração
    ALTER TABLE pedido_itens ADD CONSTRAINT pedido_itens_valor_unitario_check CHECK (valor_unitario > 0);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
--  Índices úteis para as buscas mais comuns
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_clientes_nome        ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_usuarios_email       ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_id   ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado       ON pedidos(estado);
CREATE INDEX IF NOT EXISTS idx_pedido_itens_pedido  ON pedido_itens(pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedido_itens_item    ON pedido_itens(item_id);

-- ============================================================
--  Part 2 — Schema evolution
-- ============================================================

-- Novos ENUMs
DO $$ BEGIN
    CREATE TYPE forma_pagamento AS ENUM ('CARTAO', 'BOLETO', 'PIX', 'BERRIES');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE status_pagamento AS ENUM ('PENDENTE', 'CONFIRMADO', 'REJEITADO');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
--  Novas colunas em clientes (perfil de desconto)
-- ------------------------------------------------------------
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS torce_flamengo BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS assiste_one_piece BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS eh_de_sousa BOOLEAN NOT NULL DEFAULT FALSE;

-- ------------------------------------------------------------
--  Novas colunas em estoque (categoria + origem)
-- ------------------------------------------------------------
ALTER TABLE estoque ADD COLUMN IF NOT EXISTS categoria VARCHAR(100) NOT NULL DEFAULT 'Geral';
ALTER TABLE estoque ADD COLUMN IF NOT EXISTS fabricado_em_mari BOOLEAN NOT NULL DEFAULT FALSE;

-- ------------------------------------------------------------
--  Novas colunas em pedidos (vendedor, pagamento, desconto)
-- ------------------------------------------------------------
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS vendedor_id INT NULL REFERENCES usuarios(id);
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS forma_pagamento forma_pagamento NULL;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS status_pagamento status_pagamento NOT NULL DEFAULT 'PENDENTE';
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS desconto NUMERIC(10, 2) NOT NULL DEFAULT 0;

DO $$ BEGIN
    ALTER TABLE pedidos ADD CONSTRAINT pedidos_desconto_check CHECK (desconto >= 0);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
--  Novos índices
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_pedidos_vendedor ON pedidos(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_estoque_categoria ON estoque(categoria);
CREATE INDEX IF NOT EXISTS idx_pedidos_data ON pedidos(data);

-- ------------------------------------------------------------
--  FUNCTION: cálculo automático de desconto por perfil do cliente
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION calcular_desconto(p_cliente_id INT)
RETURNS NUMERIC AS $$
DECLARE
    desconto NUMERIC := 0;
    v_torce_flamengo BOOLEAN;
    v_assiste_one_piece BOOLEAN;
    v_eh_de_sousa BOOLEAN;
BEGIN
    SELECT torce_flamengo, assiste_one_piece, eh_de_sousa
    INTO v_torce_flamengo, v_assiste_one_piece, v_eh_de_sousa
    FROM clientes
    WHERE id = p_cliente_id AND ativo = TRUE;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    IF v_torce_flamengo THEN desconto := desconto + 5; END IF;
    IF v_assiste_one_piece THEN desconto := desconto + 5; END IF;
    IF v_eh_de_sousa THEN desconto := desconto + 5; END IF;

    RETURN desconto;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------
--  VIEW: vendas mensais por vendedor
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_vendas_por_vendedor AS
SELECT
    u.id AS vendedor_id,
    u.nome AS vendedor_nome,
    DATE_TRUNC('month', p.data)::DATE AS mes,
    COUNT(*) AS total_pedidos,
    SUM(p.valor) AS valor_total,
    SUM(p.desconto) AS desconto_total,
    SUM(CASE WHEN p.status_pagamento = 'CONFIRMADO' THEN 1 ELSE 0 END) AS pagamentos_confirmados
FROM pedidos p
JOIN usuarios u ON u.id = p.vendedor_id
GROUP BY u.id, u.nome, DATE_TRUNC('month', p.data)
ORDER BY mes DESC, valor_total DESC;

-- ------------------------------------------------------------
--  Seed updates: categorias do estoque e perfis de desconto
-- ------------------------------------------------------------
UPDATE estoque SET categoria = 'Salgados' WHERE item ILIKE '%coxinha%' OR item ILIKE '%empada%' OR item ILIKE '%pastel%' OR item ILIKE '%kibe%' OR item ILIKE '%enroladinho%';
UPDATE estoque SET categoria = 'Bebidas' WHERE item ILIKE '%suco%' OR item ILIKE '%refrigerante%';

UPDATE clientes SET torce_flamengo = TRUE WHERE nome = 'Maria Silva';
UPDATE clientes SET assiste_one_piece = TRUE WHERE nome = 'João Souza';
UPDATE clientes SET eh_de_sousa = TRUE, torce_flamengo = TRUE WHERE nome = 'Ana Costa';
