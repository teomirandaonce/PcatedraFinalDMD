# Proyecto de Cátedra DMD941 — Global Electronic Retail (Fase 2)

Datawarehouse en PostgreSQL (esquema estrella) + ETL en Python + reportes en Power BI.

## Estructura
| Ruta | Contenido | Responsable |
|---|---|---|
| `src/explorar.py`, `src/diagnostico.py`, `src/limpieza.py` | Exploración, diagnóstico y limpieza | Integrante 1 |
| `sql/01_crear_esquema.sql` | Esquema `dwh`: 4 dimensiones + `fact_ventas_finanzas` | Integrante 2 |
| `src/etl_carga.py` | Pipeline ETL (pandas + SQLAlchemy + psycopg2, COPY, una transacción) | Integrante 2 |
| `src/validar_carga.py`, `sql/02_validaciones_carga.sql` | Validaciones V1–V7 de la carga | Integrante 2 |
| `sql/03_vistas_powerbi.sql`, `docs/conexion_powerbi.md` | Usuario de lectura, vista plana y consultas de referencia de KPIs | Integrante 2 |
| `docs/diagrama_estrella.png` | Diagrama del modelo estrella implementado | Integrante 2 |
| `powerbi/medidas_DAX.txt`, `powerbi/variaciones_DAX.txt` | Medidas DAX y variaciones de Finanzas | Integrante 3 |
| `powerbi/Tema_Finanzas.json`, `docs/integrante3_powerbi.txt` | Tema visual y guía de la página Finanzas | Integrante 3 |
| `sql/04_validacion_kpis.sql`, `docs/referencia_*.csv` | Validación SQL de KPIs y valores de referencia | Integrante 3 |
| `powerbi/GlobalElectronicRetail_Fase2.pbix` | PBIX integrado con las páginas Ventas y Finanzas | Integrante 4 |
| `powerbi/medidas_ventas_DAX.txt` | Medidas y columnas calculadas usadas en Ventas | Integrante 4 |
| `sql/05_verificacion_ventas.sql` | Consultas de contraste de la página Ventas | Integrante 4 |
| `Evidencias/Integrante 4/` | Capturas del PBIX: conexión, modelo, Ventas y Finanzas | Integrante 4 |
| `Evidencias/Integrante N/` | Capturas de cada integrante | Todos |

## Ejecución rápida
```bash
docker compose up -d
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/etl_carga.py        # carga (repetible: no duplica datos)
python src/validar_carga.py    # validaciones de calidad
```
Ver `docs/conexion_powerbi.md` para conectar Power BI.

## Reporte en Power BI
El entregable integrado es `powerbi/GlobalElectronicRetail_Fase2.pbix`:
modelo estrella, página **Ventas** y página **Finanzas** con filtros
sincronizados. Guía de apertura y verificación en
`powerbi/guia_pbix.md`; valores de contraste en
`sql/05_verificacion_ventas.sql`.
