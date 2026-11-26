-- =====================================================================
-- DMD941 - Fase 2 | Integrante 2
-- Validaciones de la carga del DWH (criterios de la Fase 1, sección 4.3)
-- =====================================================================

-- V1: Conteo de hechos (esperado: 20,281)
SELECT 'V1 Conteo de hechos' AS validacion, COUNT(*) AS resultado
FROM dwh.fact_ventas_finanzas;

-- V2: Control de huérfanos (esperado: 0 en todas las dimensiones)
SELECT 'V2 Huérfanos' AS validacion,
       COUNT(*) FILTER (WHERE c.customer_id IS NULL) AS sin_cliente,
       COUNT(*) FILTER (WHERE p.product_id  IS NULL) AS sin_producto,
       COUNT(*) FILTER (WHERE u.location_id IS NULL) AS sin_ubicacion,
       COUNT(*) FILTER (WHERE t.date_id     IS NULL) AS sin_fecha_pedido,
       COUNT(*) FILTER (WHERE f.ship_date_id IS NOT NULL AND te.date_id IS NULL) AS sin_fecha_envio
FROM dwh.fact_ventas_finanzas f
LEFT JOIN dwh.dim_cliente   c  ON c.customer_id = f.customer_id
LEFT JOIN dwh.dim_producto  p  ON p.product_id  = f.product_id
LEFT JOIN dwh.dim_ubicacion u  ON u.location_id = f.location_id
LEFT JOIN dwh.dim_tiempo    t  ON t.date_id     = f.date_id
LEFT JOIN dwh.dim_tiempo    te ON te.date_id    = f.ship_date_id;

-- V3 / V4: Totales para reconciliar contra el Excel
-- (Excel: Sales = 24,636,778.30 | Profit = 2,205,192.25)
SELECT 'V3/V4 Totales DWH' AS validacion,
       SUM(sales)  AS total_sales,
       SUM(profit) AS total_profit
FROM dwh.fact_ventas_finanzas;

-- V5: Descuentos fuera del rango [0, 1] (esperado: 0)
SELECT 'V5 Descuento fuera de rango' AS validacion, COUNT(*) AS resultado
FROM dwh.fact_ventas_finanzas
WHERE discount NOT BETWEEN 0 AND 1;

-- V6: Duplicados por grano order_id + primary_id (esperado: 0)
SELECT 'V6 Duplicados de grano' AS validacion, COUNT(*) AS resultado
FROM (
    SELECT order_id, primary_id
    FROM dwh.fact_ventas_finanzas
    GROUP BY order_id, primary_id
    HAVING COUNT(*) > 1
) d;

-- Control: filas por tabla
SELECT 'dim_cliente' AS tabla, COUNT(*) FROM dwh.dim_cliente
UNION ALL SELECT 'dim_producto', COUNT(*) FROM dwh.dim_producto
UNION ALL SELECT 'dim_ubicacion', COUNT(*) FROM dwh.dim_ubicacion
UNION ALL SELECT 'dim_tiempo', COUNT(*) FROM dwh.dim_tiempo
UNION ALL SELECT 'fact_ventas_finanzas', COUNT(*) FROM dwh.fact_ventas_finanzas;

-- V7: Columnas calculadas (total_costs = suma de los 5 costos)
SELECT 'V7 total_costs inconsistente' AS validacion, COUNT(*) AS resultado
FROM dwh.fact_ventas_finanzas
WHERE total_costs <> shipping_costs + storage_costs + personnel_costs
                    + selling_costs + purchasing_costs;
