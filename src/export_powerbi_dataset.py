import duckdb
import os

DB = "saas_fpna.duckdb"
OUT = "data/mart"

os.makedirs(OUT, exist_ok=True)

con = duckdb.connect(DB)

tables = [
    "dim_date",
    "dim_customer",
    "dim_plan",
    "dim_account",
    "fact_revenue",
    "fact_subscription",
    "fact_gl",
    "fact_sales_marketing",
    "fact_cash",
]

for t in tables:
    df = con.execute(f"SELECT * FROM {t}").df()
    df.to_csv(f"{OUT}/{t}.csv", index=False)
    print(f"exported {t}")

# also export KPI view for convenience
df = con.execute("SELECT * FROM vw_saas_monthly_kpis").df()
df.to_csv(f"{OUT}/vw_saas_monthly_kpis.csv", index=False)

print("All Power BI tables exported")