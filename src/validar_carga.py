"""
DMD941 - Fase 2 | Integrante 2
Validaciones automáticas de la carga (Fase 1, sección 4.3) contra el Excel original.

Uso (desde la raíz del repositorio):
    python src/validar_carga.py
"""
import sys
from decimal import Decimal

import pandas as pd
from sqlalchemy import text

from config import crear_engine
from limpieza import RUTA_EXCEL


def totales_excel():
    df = pd.read_excel(RUTA_EXCEL)
    redondear = lambda s: Decimal(str(round(float(s.round(2).sum()), 2)))
    return len(df), redondear(df["Sales"]), redondear(df["Profit"])


def main() -> int:
    filas_xlsx, sales_xlsx, profit_xlsx = totales_excel()
    engine = crear_engine()
    with engine.connect() as c:
        q = lambda sql: c.execute(text(sql)).scalar_one()
        filas = q("SELECT COUNT(*) FROM dwh.fact_ventas_finanzas")
        huerfanos = q("""
            SELECT COUNT(*) FROM dwh.fact_ventas_finanzas f
            LEFT JOIN dwh.dim_cliente   c ON c.customer_id = f.customer_id
            LEFT JOIN dwh.dim_producto  p ON p.product_id  = f.product_id
            LEFT JOIN dwh.dim_ubicacion u ON u.location_id = f.location_id
            LEFT JOIN dwh.dim_tiempo    t ON t.date_id     = f.date_id
            LEFT JOIN dwh.dim_tiempo   te ON te.date_id    = f.ship_date_id
            WHERE c.customer_id IS NULL OR p.product_id IS NULL OR u.location_id IS NULL
               OR t.date_id IS NULL OR te.date_id IS NULL""")
        sales = q("SELECT SUM(sales) FROM dwh.fact_ventas_finanzas")
        profit = q("SELECT SUM(profit) FROM dwh.fact_ventas_finanzas")
        desc = q("SELECT COUNT(*) FROM dwh.fact_ventas_finanzas WHERE discount NOT BETWEEN 0 AND 1")
        dups = q("""SELECT COUNT(*) FROM (SELECT 1 FROM dwh.fact_ventas_finanzas
                    GROUP BY order_id, primary_id HAVING COUNT(*) > 1) d""")
        costos = q("""SELECT COUNT(*) FROM dwh.fact_ventas_finanzas WHERE total_costs <>
                    shipping_costs + storage_costs + personnel_costs + selling_costs + purchasing_costs""")

    pruebas = [
        ("V1 Conteo de hechos", f"{filas_xlsx:,}", f"{filas:,}", filas == filas_xlsx),
        ("V2 Huérfanos (LEFT JOIN IS NULL)", "0", f"{huerfanos}", huerfanos == 0),
        ("V3 Reconciliación de ventas", f"${sales_xlsx:,.2f}", f"${sales:,.2f} (dif ${sales - sales_xlsx:,.2f})", sales == sales_xlsx),
        ("V4 Reconciliación de ganancias", f"${profit_xlsx:,.2f}", f"${profit:,.2f} (dif ${profit - profit_xlsx:,.2f})", profit == profit_xlsx),
        ("V5 Descuentos fuera de [0,1]", "0", f"{desc}", desc == 0),
        ("V6 Duplicados order_id+primary_id", "0", f"{dups}", dups == 0),
        ("V7 total_costs inconsistente", "0", f"{costos}", costos == 0),
    ]

    print("=== VALIDACIONES DE CALIDAD DEL DWH ===")
    print(f"{'Validación':<36} {'Esperado':<16} {'Obtenido':<34} Estado")
    print("-" * 96)
    for nombre, esperado, obtenido, ok in pruebas:
        print(f"{nombre:<36} {esperado:<16} {obtenido:<34} {'PASS' if ok else 'FAIL'}")
    total_ok = sum(p[3] for p in pruebas)
    print("-" * 96)
    print(f"Resultado: {total_ok}/{len(pruebas)} validaciones aprobadas")
    return 0 if total_ok == len(pruebas) else 1


if __name__ == "__main__":
    sys.exit(main())
