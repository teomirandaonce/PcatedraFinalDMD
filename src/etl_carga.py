"""
DMD941 - Proyecto de Cátedra Fase 2
Integrante 2 | Pipeline ETL: limpieza (Integrante 1) -> PostgreSQL (esquema dwh)

Pasos:
  1. Extracción y limpieza: reutiliza limpiar_dataset() de src/limpieza.py.
  2. Transformación: tipos estrictos, redondeo monetario y calendario continuo.
  3. Carga en UNA transacción:
       - Crea el esquema (sql/01_crear_esquema.sql, idempotente).
       - Dimensiones con INSERT ... ON CONFLICT (sin duplicar surrogate keys).
       - Lee los mapas llave natural -> surrogate key y los aplica a los hechos.
       - Hechos con COPY FROM STDIN + INSERT ... ON CONFLICT (carga repetible).
     Ante cualquier error se ejecuta ROLLBACK automático.

Uso (desde la raíz del repositorio):
    python src/etl_carga.py                  # carga normal
    python src/etl_carga.py --simular-error  # demuestra el ROLLBACK
"""
import argparse
import io
import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config import RAIZ, crear_engine
from limpieza import (
    ARCHIVO_EXCEPCIONES,
    ARCHIVO_LIMPIO,
    CARPETA_SALIDA,
    RUTA_EXCEL,
    limpiar_dataset,
)

SQL_ESQUEMA = RAIZ / "sql" / "01_crear_esquema.sql"

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre",
}

COLS_MONETARIAS = [
    "sales", "profit", "shipping_costs", "storage_costs",
    "personnel_costs", "selling_costs", "purchasing_costs",
]


# ---------------------------------------------------------------------------
# 1. EXTRACCIÓN
# ---------------------------------------------------------------------------
def extraer() -> pd.DataFrame:
    """Ejecuta la limpieza del Integrante 1 y guarda sus salidas."""
    df, df_exc = limpiar_dataset(RUTA_EXCEL)
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARCHIVO_LIMPIO, index=False, encoding="utf-8")
    df_exc.to_csv(ARCHIVO_EXCEPCIONES, index=False, encoding="utf-8")
    print(f"[EXTRACCIÓN] {len(df):,} filas limpias | {len(df_exc):,} excepciones registradas")
    return df


# ---------------------------------------------------------------------------
# 2. TRANSFORMACIÓN
# ---------------------------------------------------------------------------
def transformar(df: pd.DataFrame) -> dict:
    df = df.rename(columns={"personnel_cost": "personnel_costs"}).copy()

    # Regla Fase 1: eliminar filas sin identificadores obligatorios
    antes = len(df)
    df = df.dropna(subset=["order_id", "customer_id", "product_id"])
    descartadas = antes - len(df)

    # Tipado estricto
    for col in ["order_id", "primary_id", "customer_id", "product_id"]:
        df[col] = df[col].astype(str).str.strip()
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.normalize()
    df["ship_date"] = pd.to_datetime(df["ship_date"]).dt.normalize()
    df["quantity"] = df["quantity"].astype(int)
    df["discount"] = df["discount"].astype(float).round(2)
    for col in COLS_MONETARIAS:
        df[col] = df[col].astype(float).round(2)

    # --- Dimensiones (una fila por llave natural) ---
    dim_cliente = (
        df[["customer_id", "customer_name", "segment"]]
        .drop_duplicates("customer_id")
        .rename(columns={"customer_id": "customer_code"})
    )
    dim_producto = (
        df[["product_id", "product_name", "category", "sub_category"]]
        .drop_duplicates("product_id")
        .rename(columns={"product_id": "product_code"})
    )
    dim_ubicacion = (
        df[["city", "state", "country", "region", "iso3", "market", "latitude", "longitude"]]
        .drop_duplicates(["city", "state", "country"])
        .rename(columns={"latitude": "latitud", "longitude": "longitud"})
    )

    # Calendario continuo: fecha mínima de pedido -> fecha máxima de envío
    fechas = pd.date_range(df["order_date"].min(), df["ship_date"].max(), freq="D")
    dim_tiempo = pd.DataFrame({
        "date_id": fechas.strftime("%Y%m%d").astype(int),
        "fecha": fechas.date,
        "anio": fechas.year,
        "trimestre": fechas.quarter,
        "mes": fechas.month,
        "nombre_mes": fechas.month.map(MESES_ES),
        "dia": fechas.day,
        "dia_semana": fechas.day_of_week + 1,  # 1 = Lunes ... 7 = Domingo
        "es_fin_semana": fechas.day_of_week >= 5,
    })

    df["date_id"] = df["order_date"].dt.strftime("%Y%m%d").astype(int)
    df["ship_date_id"] = df["ship_date"].dt.strftime("%Y%m%d").astype(int)

    print(
        f"[TRANSFORMACIÓN] descartadas={descartadas} | clientes={len(dim_cliente):,} | "
        f"productos={len(dim_producto):,} | ubicaciones={len(dim_ubicacion):,} | "
        f"días calendario={len(dim_tiempo):,}"
    )
    return {
        "hechos": df,
        "dim_cliente": dim_cliente,
        "dim_producto": dim_producto,
        "dim_ubicacion": dim_ubicacion,
        "dim_tiempo": dim_tiempo,
    }


# ---------------------------------------------------------------------------
# 3. CARGA
# ---------------------------------------------------------------------------
def copiar_a_temporal(cur, df: pd.DataFrame, tabla_tmp: str) -> None:
    """Carga masiva de un DataFrame a una tabla temporal con COPY FROM STDIN."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)
    columnas = ", ".join(df.columns)
    cur.copy_expert(f"COPY {tabla_tmp} ({columnas}) FROM STDIN WITH (FORMAT csv)", buffer)


def upsert_dimension(cur, df, tabla, llave, columnas_tmp_ddl, actualizar):
    tmp = f"tmp_{tabla.split('.')[-1]}"
    cur.execute(f"CREATE TEMP TABLE {tmp} ({columnas_tmp_ddl}) ON COMMIT DROP")
    copiar_a_temporal(cur, df, tmp)
    cols = ", ".join(df.columns)
    set_ = ", ".join(f"{c} = EXCLUDED.{c}" for c in actualizar)
    # Solo actualiza si algún atributo cambió (evita escrituras innecesarias)
    cambio = " OR ".join(f"{tabla}.{c} IS DISTINCT FROM EXCLUDED.{c}" for c in actualizar)
    cur.execute(
        f"INSERT INTO {tabla} ({cols}) SELECT {cols} FROM {tmp} "
        f"ON CONFLICT ({llave}) DO UPDATE SET {set_} WHERE {cambio}"
    )
    return cur.rowcount


def cargar(datos: dict, simular_error: bool = False) -> None:
    engine = crear_engine()
    t0 = time.perf_counter()

    # engine.begin(): COMMIT si todo sale bien, ROLLBACK automático ante cualquier excepción
    with engine.begin() as conn:
        conn.exec_driver_sql(SQL_ESQUEMA.read_text(encoding="utf-8"))
        raw = conn.connection.dbapi_connection  # misma conexión/transacción (psycopg2)
        with raw.cursor() as cur:
            n = upsert_dimension(
                cur, datos["dim_cliente"], "dwh.dim_cliente", "customer_code",
                "customer_code TEXT, customer_name TEXT, segment TEXT",
                ["customer_name", "segment"],
            )
            print(f"[CARGA] dim_cliente   insertadas/actualizadas: {n:,}")
            n = upsert_dimension(
                cur, datos["dim_producto"], "dwh.dim_producto", "product_code",
                "product_code TEXT, product_name TEXT, category TEXT, sub_category TEXT",
                ["product_name", "category", "sub_category"],
            )
            print(f"[CARGA] dim_producto  insertadas/actualizadas: {n:,}")
            n = upsert_dimension(
                cur, datos["dim_ubicacion"], "dwh.dim_ubicacion", "city, state, country",
                "city TEXT, state TEXT, country TEXT, region TEXT, iso3 TEXT, market TEXT, "
                "latitud NUMERIC, longitud NUMERIC",
                ["region", "iso3", "market", "latitud", "longitud"],
            )
            print(f"[CARGA] dim_ubicacion insertadas/actualizadas: {n:,}")
            n = upsert_dimension(
                cur, datos["dim_tiempo"], "dwh.dim_tiempo", "date_id",
                "date_id INT, fecha DATE, anio SMALLINT, trimestre SMALLINT, mes SMALLINT, "
                "nombre_mes TEXT, dia SMALLINT, dia_semana SMALLINT, es_fin_semana BOOLEAN",
                ["fecha", "anio", "trimestre", "mes", "nombre_mes", "dia", "dia_semana", "es_fin_semana"],
            )
            print(f"[CARGA] dim_tiempo    insertadas/actualizadas: {n:,}")

        # Resolver claves: llave natural -> surrogate key
        mapa_cli = dict(conn.execute(text("SELECT customer_code, customer_id FROM dwh.dim_cliente")).all())
        mapa_prod = dict(conn.execute(text("SELECT product_code, product_id FROM dwh.dim_producto")).all())
        mapa_ubi = {
            (c, s, p): i for c, s, p, i in conn.execute(
                text("SELECT city, state, country, location_id FROM dwh.dim_ubicacion")
            ).all()
        }

        h = datos["hechos"]
        hechos = pd.DataFrame({
            "order_id": h["order_id"],
            "primary_id": h["primary_id"],
            "ship_mode": h["ship_mode"],
            "customer_id": h["customer_id"].map(mapa_cli),
            "product_id": h["product_id"].map(mapa_prod),
            "location_id": pd.Series(
                list(zip(h["city"], h["state"], h["country"])), index=h.index
            ).map(mapa_ubi),
            "date_id": h["date_id"],
            "ship_date_id": h["ship_date_id"],
            "quantity": h["quantity"],
            "discount": h["discount"],
            **{c: h[c] for c in COLS_MONETARIAS},
        })

        sin_clave = hechos[["customer_id", "product_id", "location_id"]].isna().any(axis=1)
        if sin_clave.any():
            raise ValueError(f"{int(sin_clave.sum())} hechos sin surrogate key; se aborta la carga")
        for c in ["customer_id", "product_id", "location_id"]:
            hechos[c] = hechos[c].astype(int)

        if simular_error:
            # Clave foránea inexistente: PostgreSQL rechazará la fila y se hará ROLLBACK
            hechos.loc[hechos.index[0], "customer_id"] = 999_999_999
            print("[SIMULACIÓN] Se inyectó customer_id=999999999 en el primer hecho")

        with raw.cursor() as cur:
            cols = list(hechos.columns)
            # Tabla temporal con los mismos tipos que la tabla de hechos (sin datos)
            cur.execute(
                f"CREATE TEMP TABLE tmp_fact ON COMMIT DROP AS "
                f"SELECT {', '.join(cols)} FROM dwh.fact_ventas_finanzas WITH NO DATA"
            )
            copiar_a_temporal(cur, hechos, "tmp_fact")
            medidas = [c for c in cols if c not in ("order_id", "primary_id")]
            cur.execute(
                f"INSERT INTO dwh.fact_ventas_finanzas ({', '.join(cols)}) "
                f"SELECT {', '.join(cols)} FROM tmp_fact "
                f"ON CONFLICT (order_id, primary_id) DO UPDATE SET "
                + ", ".join(f"{c} = EXCLUDED.{c}" for c in medidas)
                + ", loaded_at = now() WHERE "
                # Solo reescribe la fila si algún valor cambió en el origen
                + " OR ".join(f"dwh.fact_ventas_finanzas.{c} IS DISTINCT FROM EXCLUDED.{c}" for c in medidas)
            )
            print(f"[CARGA] fact_ventas_finanzas insertadas/actualizadas: {cur.rowcount:,}")

    print(f"[COMMIT] Transacción confirmada en {time.perf_counter() - t0:.2f} s")


def resumen() -> None:
    engine = crear_engine()
    with engine.connect() as conn:
        print("\n=== FILAS POR TABLA EN EL DWH ===")
        for tabla in ["dim_cliente", "dim_producto", "dim_ubicacion", "dim_tiempo", "fact_ventas_finanzas"]:
            existe = conn.execute(text(f"SELECT to_regclass('dwh.{tabla}')")).scalar_one()
            if existe is None:
                print(f"  dwh.{tabla:<22} {'(no existe)':>12}")
                continue
            n = conn.execute(text(f"SELECT COUNT(*) FROM dwh.{tabla}")).scalar_one()
            print(f"  dwh.{tabla:<22} {n:>12,}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ETL Global Electronic Retail -> PostgreSQL")
    parser.add_argument("--simular-error", action="store_true",
                        help="Inyecta una clave inválida para demostrar el ROLLBACK")
    args = parser.parse_args()

    print("=== ETL GLOBAL ELECTRONIC RETAIL -> DWH (PostgreSQL) ===")
    datos = transformar(extraer())
    try:
        cargar(datos, simular_error=args.simular_error)
    except Exception as e:  # noqa: BLE001 - se reporta y se sale con error
        print(f"[ROLLBACK] La transacción se revirtió completa: {type(e).__name__}: "
              f"{str(e).splitlines()[0]}")
        resumen()
        return 1
    resumen()
    return 0


if __name__ == "__main__":
    sys.exit(main())
