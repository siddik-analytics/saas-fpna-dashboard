SELECT 'dim_customer' AS table_name, COUNT(*) AS row_count FROM dim_customer
UNION ALL
SELECT 'dim_plan', COUNT(*) FROM dim_plan
UNION ALL
SELECT 'dim_account', COUNT(*) FROM dim_account
UNION ALL
SELECT 'fact_revenue', COUNT(*) FROM fact_revenue
UNION ALL
SELECT 'fact_subscription', COUNT(*) FROM fact_subscription
UNION ALL
SELECT 'fact_gl', COUNT(*) FROM fact_gl
UNION ALL
SELECT 'fact_sales_marketing', COUNT(*) FROM fact_sales_marketing
UNION ALL
SELECT 'fact_cash', COUNT(*) FROM fact_cash;

SELECT *
FROM vw_saas_monthly_kpis
ORDER BY period
LIMIT 12;

SELECT *
FROM vw_saas_exec_summary;