import duckdb

DB_PATH = "saas_fpna.duckdb"

con = duckdb.connect(DB_PATH)

# Drop old objects so the build is fully repeatable
drop_sql = """
DROP VIEW IF EXISTS vw_saas_exec_summary;
DROP VIEW IF EXISTS vw_saas_monthly_kpis;

DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_month;
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

# Read SQL files
with open("sql/build_star_schema.sql", "r", encoding="utf-8") as f:
    build_sql = f.read()

with open("sql/views_kpis.sql", "r", encoding="utf-8") as f:
    views_sql = f.read()

# Build schema and views
con.execute(build_sql)
con.execute(views_sql)

print(f"DuckDB model built successfully: {DB_PATH}")

# Quick previews
print("\nTables created:")
tables = con.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_name
""").fetchall()

for table in tables:
    print(f"- {table[0]}")

print("\nPreview: dim_month")
print(con.execute("""
SELECT *
FROM dim_month
ORDER BY month_start
LIMIT 12
""").df())

print("\nPreview: vw_saas_monthly_kpis")
print(con.execute("""
SELECT *
FROM vw_saas_monthly_kpis
ORDER BY period
LIMIT 12
""").df())

con.close()