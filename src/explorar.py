import pandas as pd

ruta = "data/raw/SAC Retailer Dataset.xlsx"
df = pd.read_excel(ruta)

print("Filas y columnas:", df.shape)
print("\nNombres de las columnas:")
for i, col in enumerate(df.columns, start=1):
  print(f"{i}. {col}")

print("\nPrimeras 3 filas:")
print(df.head(3))

print("\nValores vacíos o nulos por columna:")
print(df.isna().sum())