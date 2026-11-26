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
