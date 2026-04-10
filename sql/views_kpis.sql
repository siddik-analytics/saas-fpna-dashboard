-- -----------------------------------
-- SaaS Monthly KPI View
-- -----------------------------------
CREATE VIEW vw_saas_monthly_kpis AS
WITH revenue AS (
    SELECT
        period,
        SUM(CASE WHEN COALESCE(is_void, FALSE) = FALSE THEN amount ELSE 0 END) AS revenue
    FROM fact_revenue
    GROUP BY 1
),
new_customers AS (
    SELECT
        period,
        COUNT(DISTINCT customer_id) AS new_customers
    FROM fact_subscription
    GROUP BY 1
),
new_arr AS (
    SELECT
        period,
        SUM(arr) AS new_arr_booked
    FROM fact_subscription
    GROUP BY 1
),
gl_summary AS (
    SELECT
        period,
        SUM(CASE WHEN account_category = 'COGS' THEN amount ELSE 0 END) AS cogs,
        SUM(CASE WHEN account_category = 'Sales & Marketing' THEN amount ELSE 0 END) AS sales_marketing,
        SUM(CASE WHEN account_category = 'R&D' THEN amount ELSE 0 END) AS rnd,
        SUM(CASE WHEN account_category = 'G&A' THEN amount ELSE 0 END) AS ga
    FROM fact_gl
    GROUP BY 1
),
marketing AS (
    SELECT
        period,
        SUM(spend) AS total_marketing_spend,
        SUM(leads) AS leads,
        SUM(won_customers) AS marketing_won_customers,
        CASE
            WHEN SUM(won_customers) > 0 THEN SUM(spend) / SUM(won_customers)
            ELSE NULL
        END AS cac
    FROM fact_sales_marketing
    GROUP BY 1
),
cash AS (
    SELECT
        period,
        SUM(ending_cash) AS ending_cash
    FROM fact_cash
    GROUP BY 1
),
active_customers AS (
    SELECT
        d.month_start AS period,
        COUNT(DISTINCT s.customer_id) AS active_customers
    FROM (
        SELECT DISTINCT month_start
        FROM dim_date
    ) d
    LEFT JOIN fact_subscription s
        ON s.start_date <= d.month_start
       AND (s.end_date IS NULL OR s.end_date >= d.month_start)
       AND s.subscription_status IN ('Active', 'Paused')
    GROUP BY 1
),
churned_customers AS (
    SELECT
        DATE_TRUNC('month', end_date) AS period,
        COUNT(DISTINCT customer_id) AS churned_customers
    FROM fact_subscription
    WHERE subscription_status = 'Cancelled'
      AND end_date IS NOT NULL
    GROUP BY 1
),
base AS (
    SELECT
        COALESCE(r.period, nc.period, na.period, g.period, m.period, c.period) AS period,
        COALESCE(r.revenue, 0) AS revenue,
        COALESCE(nc.new_customers, 0) AS new_customers,
        COALESCE(na.new_arr_booked, 0) AS new_arr_booked,
        COALESCE(g.cogs, 0) AS cogs,
        COALESCE(g.sales_marketing, 0) AS sales_marketing,
        COALESCE(g.rnd, 0) AS rnd,
        COALESCE(g.ga, 0) AS ga,
        COALESCE(m.total_marketing_spend, 0) AS total_marketing_spend,
        COALESCE(m.leads, 0) AS leads,
        COALESCE(m.marketing_won_customers, 0) AS marketing_won_customers,
        m.cac,
        COALESCE(c.ending_cash, 0) AS ending_cash
    FROM revenue r
    FULL OUTER JOIN new_customers nc ON r.period = nc.period
    FULL OUTER JOIN new_arr na ON COALESCE(r.period, nc.period) = na.period
    FULL OUTER JOIN gl_summary g ON COALESCE(r.period, nc.period, na.period) = g.period
    FULL OUTER JOIN marketing m ON COALESCE(r.period, nc.period, na.period, g.period) = m.period
    FULL OUTER JOIN cash c ON COALESCE(r.period, nc.period, na.period, g.period, m.period) = c.period
)
SELECT
    b.period,
    b.revenue,
    b.new_customers,
    b.new_arr_booked,
    b.cogs,
    b.sales_marketing,
    b.rnd,
    b.ga,
    b.total_marketing_spend,
    b.leads,
    b.marketing_won_customers,
    b.cac,
    b.ending_cash,
    COALESCE(a.active_customers, 0) AS active_customers,
    COALESCE(ch.churned_customers, 0) AS churned_customers,

    CASE
        WHEN COALESCE(a.active_customers, 0) > 0
        THEN COALESCE(ch.churned_customers, 0) * 1.0 / a.active_customers
        ELSE NULL
    END AS churn_pct,

    CASE
        WHEN b.revenue <> 0
        THEN (b.revenue - b.cogs) * 1.0 / b.revenue
        ELSE NULL
    END AS gross_margin,

    (b.sales_marketing + b.rnd + b.ga + b.cogs - b.revenue) AS burn_rate,

    CASE
        WHEN (b.sales_marketing + b.rnd + b.ga + b.cogs - b.revenue) > 0
        THEN b.ending_cash * 1.0 / (b.sales_marketing + b.rnd + b.ga + b.cogs - b.revenue)
        ELSE NULL
    END AS runway_months,

    CASE
        WHEN COALESCE(a.active_customers, 0) > 0
        THEN b.revenue * 1.0 / a.active_customers
        ELSE NULL
    END AS arpu,

    CASE
        WHEN COALESCE(a.active_customers, 0) > 0
         AND b.revenue <> 0
         AND COALESCE(ch.churned_customers, 0) > 0
        THEN
            (
                (b.revenue * 1.0 / a.active_customers) *
                ((b.revenue - b.cogs) * 1.0 / b.revenue)
            )
            /
            (ch.churned_customers * 1.0 / a.active_customers)
        ELSE NULL
    END AS ltv,

    CASE
        WHEN m.cac IS NOT NULL
         AND m.cac > 0
         AND COALESCE(a.active_customers, 0) > 0
         AND b.revenue <> 0
         AND COALESCE(ch.churned_customers, 0) > 0
        THEN
            (
                (
                    (b.revenue * 1.0 / a.active_customers) *
                    ((b.revenue - b.cogs) * 1.0 / b.revenue)
                )
                /
                (ch.churned_customers * 1.0 / a.active_customers)
            ) / m.cac
        ELSE NULL
    END AS ltv_cac,

    LAG(b.new_arr_booked) OVER (ORDER BY b.period) AS prior_month_arr,

    CASE
        WHEN LAG(b.new_arr_booked) OVER (ORDER BY b.period) IS NOT NULL
         AND LAG(b.new_arr_booked) OVER (ORDER BY b.period) <> 0
        THEN
            (b.new_arr_booked - LAG(b.new_arr_booked) OVER (ORDER BY b.period)) * 1.0
            / LAG(b.new_arr_booked) OVER (ORDER BY b.period)
        ELSE NULL
    END AS arr_growth_pct
FROM base b
LEFT JOIN active_customers a
    ON b.period = a.period
LEFT JOIN churned_customers ch
    ON b.period = ch.period
LEFT JOIN marketing m
    ON b.period = m.period
ORDER BY b.period;


-- -----------------------------------
-- Executive summary view
-- -----------------------------------
CREATE VIEW vw_saas_exec_summary AS
SELECT
    MAX(period) AS latest_period,
    SUM(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN revenue ELSE 0 END) AS latest_revenue,
    SUM(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN new_arr_booked ELSE 0 END) AS latest_arr_booked,
    SUM(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN ending_cash ELSE 0 END) AS latest_ending_cash,
    AVG(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN gross_margin END) AS latest_gross_margin,
    AVG(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN churn_pct END) AS latest_churn_pct,
    AVG(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN runway_months END) AS latest_runway_months,
    AVG(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN cac END) AS latest_cac,
    AVG(CASE WHEN period = (SELECT MAX(period) FROM vw_saas_monthly_kpis) THEN ltv_cac END) AS latest_ltv_cac
FROM vw_saas_monthly_kpis;