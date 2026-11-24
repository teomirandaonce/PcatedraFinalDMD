import pandas as pd

df = pd.read_excel("data/raw/SAC Retailer Dataset.xlsx")

print("=== RESUMEN DE TODAS LAS COLUMNAS (29) ===")
filas = []
for col in df.columns:
  serie = df[col]
  nulos = int(serie.isna().sum())
  unicos = int(serie.nunique(dropna=True))

  if pd.api.types.is_numeric_dtype(serie):
    min_val = serie.min()
    max_val = serie.max()
    vacios_texto = 0
  else:
    min_val = (
        serie.astype(str).str.strip().replace("", pd.NA).dropna().min()
    )
    max_val = (
        serie.astype(str).str.strip().replace("", pd.NA).dropna().max()
    )
    vacios_texto = int(
        serie.dropna()
        .astype(str)
        .apply(lambda x: len(x.strip()) == 0)
        .sum()
    )

  filas.append({
      "columna": col,
      "dtype": str(serie.dtype),
      "nulos": nulos,
      "vacios_o_espacios": vacios_texto,
      "unicos": unicos,
      "min": min_val,
      "max": max_val,
  })

df_resumen = pd.DataFrame(filas)
print(df_resumen.to_string(index=False))

order_dt = pd.to_datetime(df["Order Date"], errors="coerce")
ship_dt = pd.to_datetime(df["Ship Date"], errors="coerce")

print("\n=== CHEQUEOS ADICIONALES ===")
print("Filas duplicadas exactas:", int(df.duplicated().sum()))
print("Primary ID duplicados:", int(df["Primary ID"].duplicated().sum()))
print(
    "Envío antes de pedido (Ship Date < Order Date):",
    int((ship_dt < order_dt).sum()),
)

nombres_por_cliente = df.groupby("Customer ID")["Customer Name"].nunique()
print(
    "Customer ID con más de un nombre:", int((nombres_por_cliente > 1).sum())
)