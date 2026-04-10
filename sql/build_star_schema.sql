-- -----------------------------------
-- Source staging from clean CSV files
-- -----------------------------------
CREATE OR REPLACE TEMP TABLE stg_customers AS
SELECT *
FROM read_csv_auto('data/clean/customers_clean.csv', HEADER=TRUE);

CREATE OR REPLACE TEMP TABLE stg_subscriptions AS
SELECT *
FROM read_csv_auto('data/clean/subscriptions_clean.csv', HEADER=TRUE);

CREATE OR REPLACE TEMP TABLE stg_invoices AS
SELECT *
FROM read_csv_auto('data/clean/invoices_clean.csv', HEADER=TRUE);

CREATE OR REPLACE TEMP TABLE stg_gl AS
SELECT *
FROM read_csv_auto('data/clean/gl_clean.csv', HEADER=TRUE);

CREATE OR REPLACE TEMP TABLE stg_sales_marketing AS
SELECT *
FROM read_csv_auto('data/clean/sales_marketing_clean.csv', HEADER=TRUE);

CREATE OR REPLACE TEMP TABLE stg_cash AS
SELECT *
FROM read_csv_auto('data/clean/cash_balance_clean.csv', HEADER=TRUE);


-- -----------------------------------
-- Dimension: Date
-- Daily-level date dimension
-- -----------------------------------
CREATE TABLE dim_date AS
WITH all_dates AS (
    SELECT DISTINCT CAST(signup_date AS DATE) AS dt FROM stg_customers WHERE signup_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(start_date AS DATE) AS dt FROM stg_subscriptions WHERE start_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(end_date AS DATE) AS dt FROM stg_subscriptions WHERE end_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(invoice_date AS DATE) AS dt FROM stg_invoices WHERE invoice_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(due_date AS DATE) AS dt FROM stg_invoices WHERE due_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(txn_date AS DATE) AS dt FROM stg_gl WHERE txn_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(period AS DATE) AS dt FROM stg_sales_marketing WHERE period IS NOT NULL
    UNION
    SELECT DISTINCT CAST(period AS DATE) AS dt FROM stg_cash WHERE period IS NOT NULL
)
SELECT
    dt AS date_key,
    EXTRACT(YEAR FROM dt) AS year,
    EXTRACT(MONTH FROM dt) AS month_num,
    STRFTIME(dt, '%Y-%m') AS year_month,
    DATE_TRUNC('month', dt) AS month_start,
    EXTRACT(QUARTER FROM dt) AS quarter_num
FROM all_dates;


-- -----------------------------------
-- Dimension: Month
-- One row per month for Power BI relationships
-- -----------------------------------
CREATE TABLE dim_month AS
SELECT DISTINCT
    month_start,
    EXTRACT(YEAR FROM month_start) AS year,
    EXTRACT(MONTH FROM month_start) AS month_num,
    STRFTIME(month_start, '%Y-%m') AS year_month,
    EXTRACT(QUARTER FROM month_start) AS quarter_num
FROM dim_date
ORDER BY month_start;


-- -----------------------------------
-- Dimension: Customer
-- -----------------------------------
CREATE TABLE dim_customer AS
SELECT
    customer_id,
    customer_name,
    industry,
    region,
    country,
    CAST(signup_date AS DATE) AS signup_date,
    acquisition_channel,
    account_status,
    plan_name,
    billing_frequency
FROM stg_customers;


-- -----------------------------------
-- Dimension: Plan
-- One row per plan
-- -----------------------------------
CREATE TABLE dim_plan AS
SELECT DISTINCT
    plan_name
FROM stg_subscriptions
WHERE plan_name IS NOT NULL;


-- -----------------------------------
-- Dimension: Account
-- One row per account code
-- -----------------------------------
CREATE TABLE dim_account AS
SELECT DISTINCT
    account_code,
    account_name,
    account_category
FROM stg_gl
WHERE account_code IS NOT NULL;


-- -----------------------------------
-- Fact: Revenue
-- -----------------------------------
CREATE TABLE fact_revenue AS
SELECT
    invoice_id,
    customer_id,
    subscription_id,
    CAST(invoice_date AS DATE) AS invoice_date,
    DATE_TRUNC('month', CAST(invoice_date AS DATE)) AS period,
    CAST(due_date AS DATE) AS due_date,
    amount,
    tax,
    total_amount,
    invoice_status,
    is_void
FROM stg_invoices;


-- -----------------------------------
-- Fact: Subscription
-- -----------------------------------
CREATE TABLE fact_subscription AS
SELECT
    subscription_id,
    customer_id,
    CAST(start_date AS DATE) AS start_date,
    DATE_TRUNC('month', CAST(start_date AS DATE)) AS period,
    CAST(end_date AS DATE) AS end_date,
    plan_name,
    mrr,
    arr,
    subscription_status,
    discount_pct,
    currency
FROM stg_subscriptions;


-- -----------------------------------
-- Fact: GL
-- -----------------------------------
CREATE TABLE fact_gl AS
SELECT
    gl_txn_id,
    CAST(txn_date AS DATE) AS txn_date,
    DATE_TRUNC('month', CAST(txn_date AS DATE)) AS period,
    account_code,
    account_name,
    account_category,
    department,
    cost_center,
    vendor_customer,
    amount,
    dr_cr,
    entity,
    memo
FROM stg_gl;


-- -----------------------------------
-- Fact: Sales & Marketing
-- -----------------------------------
CREATE TABLE fact_sales_marketing AS
SELECT
    CAST(period AS DATE) AS period,
    channel,
    campaign_name,
    spend,
    leads,
    won_customers,
    cac
FROM stg_sales_marketing;


-- -----------------------------------
-- Fact: Cash
-- -----------------------------------
CREATE TABLE fact_cash AS
SELECT
    CAST(period AS DATE) AS period,
    entity,
    beginning_cash,
    ending_cash
FROM stg_cash;