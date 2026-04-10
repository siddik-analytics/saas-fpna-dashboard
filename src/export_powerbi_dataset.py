import duckdb
import os

DB = "saas_fpna.duckdb"
OUT = "data/mart"

os.makedirs(OUT, exist_ok=True)

con = duckdb.connect(DB)

tables = [
    "dim_date",
    "dim_month",
    "dim_customer",
    "dim_plan",
    "dim_account",
    "fact_revenue",
    "fact_subscription",
    "fact_gl",
    "fact_sales_marketing",
    "fact_cash",
]

for table_name in tables:
    df = con.execute(f"SELECT * FROM {table_name}").df()
    output_path = f"{OUT}/{table_name}.csv"
    df.to_csv(output_path, index=False)
    print(f"Exported {table_name} -> {output_path}")

# Optional convenience export for quick flat reporting
kpi_df = con.execute("""
SELECT *
FROM vw_saas_monthly_kpis
ORDER BY period
""").df()

kpi_output_path = f"{OUT}/vw_saas_monthly_kpis.csv"
kpi_df.to_csv(kpi_output_path, index=False)
print(f"Exported vw_saas_monthly_kpis -> {kpi_output_path}")

con.close()

print("\nAll Power BI tables exported successfully.")