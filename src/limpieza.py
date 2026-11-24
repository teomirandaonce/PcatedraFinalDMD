from pathlib import Path
import numpy as np
import pandas as pd

RUTA_EXCEL = Path("data/raw/SAC Retailer Dataset.xlsx")
CARPETA_SALIDA = Path("data/procesado")
ARCHIVO_LIMPIO = CARPETA_SALIDA / "sac_retailer_limpio.csv"
ARCHIVO_EXCEPCIONES = CARPETA_SALIDA / "reporte_excepciones.csv"


def limpiar_dataset(ruta_excel: Path = RUTA_EXCEL):
    df = pd.read_excel(ruta_excel)
    excepciones = []

    def registrar_excepcion(idx, regla, columna, valor, accion):
        excepciones.append({
            "fila_excel": int(idx) + 2,  # +2 por encabezado en fila 1 e índice base 0
            "primary_id": df.loc[idx, "Primary ID"] if "Primary ID" in df.columns else None,
            "order_id": df.loc[idx, "Order ID"] if "Order ID" in df.columns else None,
            "regla": regla,
            "columna": columna,
            "valor_original": valor,
            "accion_tomada": accion,
        })

    # 1. Limpieza de textos e identificadores
    cols_texto = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype) == "str"]
    for col in cols_texto:
        originales = df[col].copy()
        limpios = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        limpios_sin_comilla = limpios.str.lstrip("'").str.strip()
        cambios = originales.astype(str) != limpios_sin_comilla
        for idx in df.index[cambios]:
            registrar_excepcion(
                idx,
                "LIMPIEZA_TEXTO_ESPACIOS_COMILLA",
                col,
                originales.loc[idx],
                "Normalizado en texto",
            )
        df[col] = limpios_sin_comilla

    # Estandarizar mayúsculas en códigos e ISO3
    for col_code in ["Customer ID", "Product ID", "ISO3"]:
        if col_code in df.columns:
            df[col_code] = df[col_code].str.upper()

    # 2. Fechas y validación de secuencia (Ship Date < Order Date)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    fechas_invalidas = df["Order Date"].isna() | df["Ship Date"].isna()
    for idx in df.index[fechas_invalidas]:
        registrar_excepcion(
            idx,
            "FECHA_INVALIDA",
            "Order Date / Ship Date",
            f"{df.loc[idx, 'Order Date']} | {df.loc[idx, 'Ship Date']}",
            "Marcada para revisión",
        )

    envio_antes_pedido = df["Ship Date"] < df["Order Date"]
    for idx in df.index[envio_antes_pedido]:
        registrar_excepcion(
            idx,
            "SHIP_DATE_MENOR_A_ORDER_DATE",
            "Ship Date",
            f"Order: {df.loc[idx, 'Order Date'].date()} | Ship: {df.loc[idx, 'Ship Date'].date()}",
            "Registrada en excepciones (conservar/auditar)",
        )

    # 3. Tipos numéricos y normalización de descuentos
    cols_monetarias = [
        "Sales",
        "Profit",
        "Shipping Costs",
        "Storage Costs",
        "Personnel Cost",
        "Selling Costs",
        "Purchasing Costs",
    ]

    for col in cols_monetarias:
        if col in df.columns and df[col].dtype == "object":
            limpio_num = (
                df[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace("(", "-", regex=False)
                .str.replace(")", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(limpio_num, errors="coerce")

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")

    # Si algún descuento viene > 1 (ej. 15 en vez de 0.15), convertir a fracción
    desc_mayor_1 = df["Discount"] > 1
    for idx in df.index[desc_mayor_1]:
        registrar_excepcion(
            idx,
            "DESCUENTO_PORCENTAJE_ENTERO",
            "Discount",
            df.loc[idx, "Discount"],
            "Convertido a fracción dividiendo entre 100",
        )
    df.loc[desc_mayor_1, "Discount"] = df.loc[desc_mayor_1, "Discount"] / 100.0

    # Validar rango [0, 1] en Discount
    desc_fuera_rango = (df["Discount"] < 0) | (df["Discount"] > 1) | df["Discount"].isna()
    for idx in df.index[desc_fuera_rango]:
        registrar_excepcion(
            idx,
            "DESCUENTO_FUERA_DE_RANGO_0_1",
            "Discount",
            df.loc[idx, "Discount"],
            "Registrada en excepciones",
        )

    # Validar cantidades <= 0
    qty_no_positiva = df["Quantity"] <= 0
    for idx in df.index[qty_no_positiva]:
        registrar_excepcion(
            idx,
            "CANTIDAD_NO_POSITIVA",
            "Quantity",
            df.loc[idx, "Quantity"],
            "Registrada en excepciones",
        )

    # Registrar ganancias negativas como hallazgo financiero
    profit_negativo = df["Profit"] < 0
    for idx in df.index[profit_negativo]:
        registrar_excepcion(
            idx,
            "GANANCIA_NEGATIVA",
            "Profit",
            df.loc[idx, "Profit"],
            "Registrada como hallazgo financiero",
        )

    # 4. Estandarización de nombres de columnas a snake_case para el DWH
    df_limpio = df.copy()
    df_limpio.columns = (
        df_limpio.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    df_exc = pd.DataFrame(excepciones)
    return df_limpio, df_exc


if __name__ == "__main__":
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    df_limpio, df_exc = limpiar_dataset(RUTA_EXCEL)

    # Exportar CSV limpio y CSV de excepciones
    df_limpio.to_csv(ARCHIVO_LIMPIO, index=False, encoding="utf-8")
    df_exc.to_csv(ARCHIVO_EXCEPCIONES, index=False, encoding="utf-8")

    print("=== RESUMEN DE LIMPIEZA ===")
    print(f"Total filas procesadas: {len(df_limpio):,}")
    print(f"Total columnas estandarizadas: {len(df_limpio.columns)}")
    print(f"CSV limpio guardado en: {ARCHIVO_LIMPIO}")
    print(f"CSV de excepciones guardado en: {ARCHIVO_EXCEPCIONES}")
    print(f"Total registros de excepciones: {len(df_exc):,}")

    if not df_exc.empty:
        print("\n=== EXCEPCIONES POR REGLA ===")
        print(df_exc["regla"].value_counts().to_string())

        print("\n=== PRIMERAS 15 EXCEPCIONES ===")
        print(df_exc.head(15).to_string(index=False))