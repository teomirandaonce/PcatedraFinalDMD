# Guía del PBIX

**Archivo:** `powerbi/GlobalElectronicRetail_Fase2.pbix`

## 1. Abrir el archivo

1. Abra Power BI Desktop.
2. **Archivo → Abrir** y seleccionar `powerbi/GlobalElectronicRetail_Fase2.pbix`.

## 2. Contenido del modelo

- 5 tablas: `dim_cliente`, `dim_producto`, `dim_ubicacion`, `dim_tiempo` y
  `fact_ventas_finanzas`.
- 5 relaciones N:1 con dirección única:
  - `cliente`, `producto`, `ubicación` y `fecha de pedido` activas;
  - `ship_date_id` → `dim_tiempo[date_id]` **inactiva**.
- `dim_tiempo` marcada como tabla de fechas con la columna `fecha`.
- Columnas calculadas `Periodo` y `Cliente`.
- Medidas de `powerbi/medidas_DAX.txt` + `Total pedidos` + `Clientes activos`.

## 3. Páginas

### Ventas
- Encabezado Global Electronic Retail con botón de navegación Ventas/Finanzas.
- Segmentadores: `anio`, `Periodo`, `region`, `segment`, `category`.
- Tarjetas: Ventas totales, Crecimiento de ventas, Valor promedio por pedido.
- Columnas: ventas por región.
- Dona: participación por categoría.
- Matriz: Top 10 clientes con ventas, pedidos, ticket y margen.
- **Vista por defecto:** 2020 seleccionado
  

### Finanzas
- Tarjetas: Ganancia total, Margen de beneficio, Costos totales registrados.
- Línea temporal: costos y margen por `Periodo`.
- Combinado: ganancia y margen por categoría.
- Matriz: ventas, costos, ganancia y margen por región.
- **Vista por defecto:** 2020

