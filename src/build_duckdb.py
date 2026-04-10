import duckdb
import os

DB_PATH = "saas_fpna.duckdb"
CLEAN = "data/clean"

con = duckdb.connect(DB_PATH)

# Drop old objects for rebuildability
drop_sql = """
DROP VIEW IF EXISTS vw_saas_exec_summary;
DROP VIEW IF EXISTS vw_saas_monthly_kpis;

DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_plan;
DROP TABLE IF EXISTS dim_account;

DROP TABLE IF EXISTS fact_revenue;
DROP TABLE IF EXISTS fact_subscription;
DROP TABLE IF EXISTS fact_gl;
DROP TABLE IF EXISTS fact_sales_marketing;
DROP TABLE IF EXISTS fact_cash;
"""
con.execute(drop_sql)

# Load SQL files
with open("sql/build_star_schema.sql", "r", encoding="utf-8") as f:
    build_sql = f.read()

with open("sql/views_kpis.sql", "r", encoding="utf-8") as f:
    view_sql = f.read()

con.execute(build_sql)
con.execute(view_sql)

print(f"DuckDB model built successfully: {DB_PATH}")

# Optional quick preview
print("\nPreview: vw_saas_monthly_kpis")
print(con.execute("SELECT * FROM vw_saas_monthly_kpis ORDER BY period LIMIT 12").df())

con.close()