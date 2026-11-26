"""Configuración de conexión al Datawarehouse (lee variables desde .env)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


def url_dwh() -> URL:
    return URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DWH_USER", "dwh_admin"),
        password=os.getenv("DWH_PASSWORD", "dwh_admin_2026"),
        host=os.getenv("DWH_HOST", "localhost"),
        port=int(os.getenv("DWH_PORT", "5432")),
        database=os.getenv("DWH_DB", "global_retail_dwh"),
    )


def crear_engine() -> Engine:
    return create_engine(url_dwh(), future=True)
