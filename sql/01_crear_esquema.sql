-- =====================================================================
-- DMD941 - Proyecto de Cátedra Fase 2
-- Integrante 2 | Creación del esquema estrella del Datawarehouse
-- Motor: PostgreSQL 16
-- Basado en el diccionario de datos de la Fase 1 (sección 3.7)
-- El script es idempotente: puede ejecutarse varias veces sin error.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS dwh;

-- ---------------------------------------------------------------------
-- Dimensión Cliente: quién compra
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.dim_cliente (
    customer_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_code  VARCHAR(50)  NOT NULL,
    customer_name  VARCHAR(100) NOT NULL,
    segment        VARCHAR(50),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uk_dim_cliente_code UNIQUE (customer_code)
);

-- ---------------------------------------------------------------------
-- Dimensión Producto: qué se vende
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.dim_producto (
    product_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_code  VARCHAR(50)  NOT NULL,
    product_name  VARCHAR(150) NOT NULL,
    category      VARCHAR(50),
    sub_category  VARCHAR(50),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uk_dim_producto_code UNIQUE (product_code)
);

-- ---------------------------------------------------------------------
-- Dimensión Ubicación: dónde se vende
-- Llave natural: ciudad + estado + país
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.dim_ubicacion (
    location_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city         VARCHAR(50) NOT NULL,
    state        VARCHAR(50) NOT NULL,
    country      VARCHAR(50) NOT NULL,
    region       VARCHAR(50) NOT NULL,
    iso3         VARCHAR(3),
    market       VARCHAR(50) NOT NULL,
    latitud      NUMERIC(9,6),
    longitud     NUMERIC(9,6),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uk_dim_ubicacion UNIQUE (city, state, country),
    CONSTRAINT ck_dim_ubicacion_lat  CHECK (latitud  BETWEEN -90  AND 90),
    CONSTRAINT ck_dim_ubicacion_long CHECK (longitud BETWEEN -180 AND 180)
);

-- ---------------------------------------------------------------------
-- Dimensión Tiempo: cuándo ocurre el pedido y el envío
-- date_id con formato YYYYMMDD (llave inteligente)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.dim_tiempo (
    date_id        INTEGER     PRIMARY KEY,
    fecha          DATE        NOT NULL,
    anio           SMALLINT    NOT NULL,
    trimestre      SMALLINT    NOT NULL,
    mes            SMALLINT    NOT NULL,
    nombre_mes     VARCHAR(15) NOT NULL,
    dia            SMALLINT    NOT NULL,
    dia_semana     SMALLINT    NOT NULL,
    es_fin_semana  BOOLEAN     NOT NULL,
    CONSTRAINT uk_dim_tiempo_fecha UNIQUE (fecha),
    CONSTRAINT ck_dim_tiempo_trimestre  CHECK (trimestre  BETWEEN 1 AND 4),
    CONSTRAINT ck_dim_tiempo_mes        CHECK (mes        BETWEEN 1 AND 12),
    CONSTRAINT ck_dim_tiempo_dia        CHECK (dia        BETWEEN 1 AND 31),
    CONSTRAINT ck_dim_tiempo_dia_semana CHECK (dia_semana BETWEEN 1 AND 7)
);

-- ---------------------------------------------------------------------
-- Tabla de hechos: una fila por línea de pedido (Order ID + Primary ID)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.fact_ventas_finanzas (
    fact_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- Dimensiones degeneradas
    order_id          VARCHAR(30) NOT NULL,
    primary_id        VARCHAR(50) NOT NULL,
    ship_mode         VARCHAR(30),
    -- Claves foráneas
    customer_id       INTEGER NOT NULL REFERENCES dwh.dim_cliente   (customer_id),
    product_id        INTEGER NOT NULL REFERENCES dwh.dim_producto  (product_id),
    location_id       INTEGER NOT NULL REFERENCES dwh.dim_ubicacion (location_id),
    date_id           INTEGER NOT NULL REFERENCES dwh.dim_tiempo    (date_id),
    ship_date_id      INTEGER          REFERENCES dwh.dim_tiempo    (date_id),
    -- Medidas
    quantity          INTEGER       NOT NULL,
    discount          NUMERIC(4,2)  NOT NULL,
    sales             NUMERIC(12,2) NOT NULL,
    profit            NUMERIC(12,2) NOT NULL,
    shipping_costs    NUMERIC(10,2) NOT NULL,
    storage_costs     NUMERIC(10,2) NOT NULL,
    personnel_costs   NUMERIC(10,2) NOT NULL,
    selling_costs     NUMERIC(10,2) NOT NULL,
    purchasing_costs  NUMERIC(10,2) NOT NULL,
    -- Columnas calculadas persistidas
    total_costs       NUMERIC(12,2) GENERATED ALWAYS AS
                      (shipping_costs + storage_costs + personnel_costs
                       + selling_costs + purchasing_costs) STORED,
    margen_neto       NUMERIC(10,4) GENERATED ALWAYS AS
                      (profit / NULLIF(sales, 0)) STORED,
    loaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uk_fact_linea_pedido UNIQUE (order_id, primary_id),
    CONSTRAINT ck_fact_quantity CHECK (quantity >= 0),
    CONSTRAINT ck_fact_discount CHECK (discount BETWEEN 0 AND 1)
);

-- Índices sobre las claves foráneas para acelerar los JOIN de Power BI
CREATE INDEX IF NOT EXISTS ix_fact_customer  ON dwh.fact_ventas_finanzas (customer_id);
CREATE INDEX IF NOT EXISTS ix_fact_product   ON dwh.fact_ventas_finanzas (product_id);
CREATE INDEX IF NOT EXISTS ix_fact_location  ON dwh.fact_ventas_finanzas (location_id);
CREATE INDEX IF NOT EXISTS ix_fact_date      ON dwh.fact_ventas_finanzas (date_id);
CREATE INDEX IF NOT EXISTS ix_fact_ship_date ON dwh.fact_ventas_finanzas (ship_date_id);

COMMENT ON TABLE dwh.fact_ventas_finanzas IS
    'Hechos de ventas y finanzas. Grano: una línea de pedido (order_id + primary_id).';
