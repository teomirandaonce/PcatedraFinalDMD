

\echo 'V1. Totales globales (tarjetas Ventas)'
SELECT count(*)                                        AS filas,
       count(DISTINCT order_id)                        AS pedidos,
       round(sum(sales)::numeric, 2)                   AS ventas,
       round(sum(profit)::numeric, 2)                  AS ganancia,
       round(sum(total_costs)::numeric, 2)             AS costos,
       round(100 * sum(profit) / nullif(sum(sales), 0), 2) AS margen_pct,
       round(sum(sales) / nullif(count(DISTINCT order_id), 0), 2) AS ticket_promedio
FROM dwh.fact_ventas_finanzas;

\echo 'V2. Ventas y margen por anio'
SELECT t.anio,
       count(*)                                        AS filas,
       count(DISTINCT f.order_id)                      AS pedidos,
       round(sum(f.sales)::numeric, 2)                 AS ventas,
       round(100 * sum(f.profit) / nullif(sum(f.sales), 0), 2) AS margen_pct
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_tiempo t ON t.date_id = f.date_id
GROUP BY t.anio
ORDER BY t.anio;

\echo 'V3. Crecimiento 2020 vs 2019 (tarjeta Crecimiento de ventas)'
WITH anio AS (
    SELECT t.anio, sum(f.sales) AS ventas
    FROM dwh.fact_ventas_finanzas f
    JOIN dwh.dim_tiempo t ON t.date_id = f.date_id
    GROUP BY t.anio
)
SELECT round(100 * (max(CASE WHEN anio = 2020 THEN ventas END)
                  - max(CASE WHEN anio = 2019 THEN ventas END))
             / nullif(max(CASE WHEN anio = 2019 THEN ventas END), 0), 2) AS crecimiento_pct
FROM anio;

\echo 'V4. Ventas por region (grafico de columnas)'
SELECT u.region,
       round(sum(f.sales)::numeric, 2)                 AS ventas,
       round(100 * sum(f.sales) / sum(sum(f.sales)) OVER (), 2) AS participacion_pct,
       round(100 * sum(f.profit) / nullif(sum(f.sales), 0), 2)  AS margen_pct,
       count(DISTINCT f.order_id)                      AS pedidos
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_ubicacion u ON u.location_id = f.location_id
GROUP BY u.region
ORDER BY ventas DESC;

\echo 'V5. Participacion por categoria (dona)'
SELECT p.category,
       round(sum(f.sales)::numeric, 2)                 AS ventas,
       round(100 * sum(f.sales) / sum(sum(f.sales)) OVER (), 2) AS participacion_pct,
       round(100 * sum(f.profit) / nullif(sum(f.sales), 0), 2)  AS margen_pct
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_producto p ON p.product_id = f.product_id
GROUP BY p.category
ORDER BY ventas DESC;

\echo 'V6. Ventas por segmento (filtro Segmento)'
SELECT c.segment,
       round(sum(f.sales)::numeric, 2)                 AS ventas,
       round(100 * sum(f.sales) / sum(sum(f.sales)) OVER (), 2) AS participacion_pct,
       round(100 * sum(f.profit) / nullif(sum(f.sales), 0), 2)  AS margen_pct
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_cliente c ON c.customer_id = f.customer_id
GROUP BY c.segment
ORDER BY ventas DESC;

\echo 'V7. Top 10 clientes por ventas (matriz)'
SELECT c.customer_name || ' (' || c.customer_code || ')' AS cliente,
       round(sum(f.sales)::numeric, 2)                 AS ventas,
       count(DISTINCT f.order_id)                      AS pedidos,
       round(sum(f.sales) / nullif(count(DISTINCT f.order_id), 0), 2) AS ticket_promedio,
       round(100 * sum(f.profit) / nullif(sum(f.sales), 0), 2)        AS margen_pct
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_cliente c ON c.customer_id = f.customer_id
GROUP BY c.customer_name, c.customer_code
ORDER BY ventas DESC
LIMIT 10;

\echo 'V8. Prueba 2020 + categoria TV'
SELECT t.anio,
       p.category,
       count(*)                                        AS filas,
       count(DISTINCT f.order_id)                      AS pedidos,
       round(sum(f.sales)::numeric, 2)                 AS ventas
FROM dwh.fact_ventas_finanzas f
JOIN dwh.dim_tiempo t   ON t.date_id = f.date_id
JOIN dwh.dim_producto p ON p.product_id = f.product_id
WHERE t.anio = 2020
  AND p.category = 'TV'
GROUP BY t.anio, p.category;
