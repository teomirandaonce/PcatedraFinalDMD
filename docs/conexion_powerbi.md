# Acceso al Datawarehouse desde Power BI (Integrantes 3 y 4)

## 1. Levantar el DWH en tu máquina
```bash
docker compose up -d                     # PostgreSQL 16 en localhost:5432
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python src/etl_carga.py                  # carga el DWH (≈1 s)
python src/validar_carga.py              # 7/7 validaciones PASS
docker exec -i dwh_global_retail psql -U dwh_admin -d global_retail_dwh < sql/03_vistas_powerbi.sql
```
> Si el puerto 5432 ya está ocupado, cambia `DWH_PORT` en `.env` (por ejemplo 5434) y vuelve a ejecutar `docker compose up -d`.

## 2. Datos de conexión
| Parámetro | Valor |
|---|---|
| Servidor | `localhost:5432` (o el puerto de tu `.env`) |
| Base de datos | `global_retail_dwh` |
| Usuario (solo lectura) | `powerbi_reader` |
| Contraseña | `powerbi_2026` |
| Esquema | `dwh` |

## 3. Conectar en Power BI Desktop
1. **Obtener datos → Base de datos PostgreSQL**.
2. Servidor: `localhost:5432` · Base de datos: `global_retail_dwh` · Modo: **Importar**.
3. Credenciales: pestaña **Base de datos**, usuario `powerbi_reader`.
4. Seleccionar: `dwh.dim_cliente`, `dwh.dim_producto`, `dwh.dim_ubicacion`, `dwh.dim_tiempo`, `dwh.fact_ventas_finanzas`.

## 4. Relaciones del modelo estrella
| Desde (hechos) | Hacia (dimensión) | Cardinalidad | Estado |
|---|---|---|---|
| fact_ventas_finanzas[customer_id] | dim_cliente[customer_id] | N:1 | Activa |
| fact_ventas_finanzas[product_id] | dim_producto[product_id] | N:1 | Activa |
| fact_ventas_finanzas[location_id] | dim_ubicacion[location_id] | N:1 | Activa |
| fact_ventas_finanzas[date_id] | dim_tiempo[date_id] | N:1 | Activa (fecha de pedido) |
| fact_ventas_finanzas[ship_date_id] | dim_tiempo[date_id] | N:1 | **Inactiva** (usar `USERELATIONSHIP`) |

Marcar `dim_tiempo` como **tabla de fechas** usando la columna `fecha`.

## 5. Valores de referencia para comprobar las medidas DAX
Resultado de `sql/03_vistas_powerbi.sql` sobre la carga completa:

| KPI | Valor SQL |
|---|---|
| Ganancia total | 2,205,192.25 |
| Margen de beneficio | 8.95 % |
| Costos totales | 22,431,586.05 |
| Ventas totales | 24,636,778.30 |
| Valor promedio por pedido | 2,661.42 |
| Crecimiento de ventas 2020 vs 2019 | 24.41 % |
