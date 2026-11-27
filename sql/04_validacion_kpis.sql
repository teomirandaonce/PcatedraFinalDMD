-- PostgreSQL: ejecutar después de cargar el DWH. Solo lectura.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
-- 1. Totales de referencia (crecimiento global no aplica)
SELECT COUNT(*) AS filas, COUNT(DISTINCT f.order_id) AS pedidos,
SUM(f.sales) AS ventas, SUM(f.profit) AS ganancias, SUM(f.total_costs) AS costos,
ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales),0), 2) AS margen_pct,
ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS promedio_pedido FROM dwh.fact_ventas_finanzas f;
-- 2. KPIs anuales y crecimiento interanual
WITH a AS (SELECT t.anio, COUNT(*) AS filas, COUNT(DISTINCT f.order_id) AS pedidos,
SUM(f.sales) AS ventas, SUM(f.profit) AS ganancias, SUM(f.total_costs) AS costos,
ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales),0), 2) AS margen_pct,
ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS promedio_pedido FROM dwh.fact_ventas_finanzas f JOIN dwh.dim_tiempo t ON t.date_id=f.date_id GROUP BY t.anio),
b AS (SELECT a.*, LAG(ventas) OVER (ORDER BY anio) AS anterior, LAG(anio) OVER (ORDER BY anio) AS anio_anterior FROM a)
SELECT *, CASE WHEN anio_anterior=anio-1 THEN ROUND(100.0*(ventas-anterior)/NULLIF(anterior,0),2) END AS crecimiento_pct FROM b ORDER BY anio;
-- 3. KPIs mensuales y crecimiento intermensual
WITH a AS (SELECT DATE_TRUNC('month',t.fecha)::date AS periodo, COUNT(*) AS filas, COUNT(DISTINCT f.order_id) AS pedidos,
SUM(f.sales) AS ventas, SUM(f.profit) AS ganancias, SUM(f.total_costs) AS costos,
ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales),0), 2) AS margen_pct,
ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS promedio_pedido FROM dwh.fact_ventas_finanzas f JOIN dwh.dim_tiempo t ON t.date_id=f.date_id GROUP BY 1),
b AS (SELECT a.*, LAG(ventas) OVER (ORDER BY periodo) AS anterior, LAG(periodo) OVER (ORDER BY periodo) AS periodo_anterior FROM a)
SELECT *, CASE WHEN periodo_anterior=(periodo-INTERVAL '1 month')::date THEN ROUND(100.0*(ventas-anterior)/NULLIF(anterior,0),2) END AS crecimiento_pct FROM b ORDER BY periodo;
-- 4. Rentabilidad por categoría
SELECT p.category, COUNT(*) AS filas, COUNT(DISTINCT f.order_id) AS pedidos,
SUM(f.sales) AS ventas, SUM(f.profit) AS ganancias, SUM(f.total_costs) AS costos,
ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales),0), 2) AS margen_pct,
ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS promedio_pedido FROM dwh.fact_ventas_finanzas f JOIN dwh.dim_producto p ON p.product_id=f.product_id GROUP BY p.category ORDER BY p.category;
-- 5. Márgenes por región
SELECT u.region, COUNT(*) AS filas, COUNT(DISTINCT f.order_id) AS pedidos,
SUM(f.sales) AS ventas, SUM(f.profit) AS ganancias, SUM(f.total_costs) AS costos,
ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales),0), 2) AS margen_pct,
ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id),0), 2) AS promedio_pedido FROM dwh.fact_ventas_finanzas f JOIN dwh.dim_ubicacion u ON u.location_id=f.location_id GROUP BY u.region ORDER BY u.region;
-- 6. Conciliación de los valores de referencia
SELECT SUM(sales)-24636778.30 AS diferencia_ventas, SUM(profit)-2205192.25 AS diferencia_ganancias, SUM(total_costs)-22431586.05 AS diferencia_costos, COUNT(*)-20281 AS diferencia_filas, COUNT(DISTINCT order_id)-9257 AS diferencia_pedidos FROM dwh.fact_ventas_finanzas;
COMMIT;
