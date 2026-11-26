-- =====================================================================
-- DMD941 - Fase 2 | Integrante 2
-- Acceso al modelo para Power BI (Integrantes 3 y 4)
-- =====================================================================

-- Usuario de solo lectura para el reporte
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'powerbi_reader') THEN
        CREATE ROLE powerbi_reader LOGIN PASSWORD 'powerbi_2026';
    END IF;
END $$;

GRANT CONNECT ON DATABASE global_retail_dwh TO powerbi_reader;
GRANT USAGE ON SCHEMA dwh TO powerbi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dwh TO powerbi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA dwh GRANT SELECT ON TABLES TO powerbi_reader;

-- Vista plana de apoyo para comprobar medidas DAX contra SQL
CREATE OR REPLACE VIEW dwh.vw_ventas_finanzas AS
SELECT f.fact_id, f.order_id, f.primary_id, f.ship_mode,
       t.fecha AS fecha_pedido, t.anio, t.trimestre, t.mes, t.nombre_mes,
       te.fecha AS fecha_envio,
       c.customer_code, c.customer_name, c.segment,
       p.product_code, p.product_name, p.category, p.sub_category,
       u.city, u.state, u.country, u.region, u.market, u.iso3,
       f.quantity, f.discount, f.sales, f.profit,
       f.shipping_costs, f.storage_costs, f.personnel_costs,
       f.selling_costs, f.purchasing_costs, f.total_costs, f.margen_neto
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_tiempo    t  ON t.date_id     = f.date_id
LEFT JOIN dwh.dim_tiempo te ON te.date_id  = f.ship_date_id
JOIN dwh.dim_cliente   c  ON c.customer_id = f.customer_id
JOIN dwh.dim_producto  p  ON p.product_id  = f.product_id
JOIN dwh.dim_ubicacion u  ON u.location_id = f.location_id;

GRANT SELECT ON dwh.vw_ventas_finanzas TO powerbi_reader;

-- Consultas de referencia de los 6 KPIs (para comprobar las medidas DAX)
-- Ganancia total, margen, costos totales, ventas totales, valor promedio por pedido
SELECT SUM(profit)                                  AS ganancia_total,
       ROUND(SUM(profit) / NULLIF(SUM(sales),0)*100, 2) AS margen_beneficio_pct,
       SUM(total_costs)                             AS costos_totales,
       SUM(sales)                                   AS ventas_totales,
       ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS valor_promedio_pedido
FROM dwh.fact_ventas_finanzas;

-- Crecimiento de ventas anual
SELECT t.anio, SUM(f.sales) AS ventas,
       ROUND((SUM(f.sales) - LAG(SUM(f.sales)) OVER (ORDER BY t.anio))
             / NULLIF(LAG(SUM(f.sales)) OVER (ORDER BY t.anio),0) * 100, 2) AS crecimiento_pct
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_tiempo t ON t.date_id = f.date_id
GROUP BY t.anio ORDER BY t.anio;
