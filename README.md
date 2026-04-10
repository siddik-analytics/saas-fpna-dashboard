
# SaaS FP&A Dashboard — End‑to‑End Finance Analytics Pipeline

An end‑to‑end FP&A analytics project that simulates messy ERP, CRM, billing, and marketing data, cleans and validates it, builds a SQL star schema using DuckDB, and produces SaaS KPI views ready for Power BI dashboards.

This project demonstrates **real-world FP&A data engineering + analytics modeling**.

---

# Project Architecture

Raw → Clean → Mart → SQL Star Schema → KPI Views → Power BI

```
Messy ERP / CRM exports
        ↓
data/raw
        ↓
Data Cleaning + Standardization
        ↓
data/clean
        ↓
KPI Mart Table
        ↓
data/mart
        ↓
DuckDB Star Schema
        ↓
vw_saas_monthly_kpis
        ↓
Power BI Dashboard
```

---

# Metrics Modeled

The pipeline produces:

- ARR
- ARR Growth
- Revenue
- Active Customers
- New Customers
- Churn %
- CAC
- LTV
- LTV/CAC
- Gross Margin
- Burn Rate
- Runway (months)
- ARPU
- Marketing spend
- Leads
- Cash balance

---

# Project Structure

```
saas-fpna-dashboard/
│
├── data/
│   ├── raw/
│   ├── clean/
│   └── mart/
│
├── sql/
│   ├── build_star_schema.sql
│   ├── views_kpis.sql
│   └── checks.sql
│
├── src/
│   ├── generate_data.py
│   ├── audit_raw_data.py
│   ├── transform_data.py
│   ├── validate_data.py
│   └── build_duckdb.py
│
├── run_pipeline.py
├── requirements.txt
└── README.md
```

---

# Run Entire Pipeline

```
pip install -r requirements.txt
python run_pipeline.py
```

---

# Individual Steps

Generate messy ERP data

```
python src/generate_data.py
```

Audit raw data

```
python src/audit_raw_data.py
```

Transform clean + mart

```
python src/transform_data.py
```

Validate data

```
python src/validate_data.py
```

Build SQL star schema

```
python src/build_duckdb.py
```

---

# SQL Model

Dimensions
- dim_date
- dim_customer
- dim_plan
- dim_account

Facts
- fact_revenue
- fact_subscription
- fact_gl
- fact_sales_marketing
- fact_cash

Views
- vw_saas_monthly_kpis
- vw_saas_exec_summary

---

# Example SQL Queries

Monthly SaaS KPIs

```
SELECT *
FROM vw_saas_monthly_kpis
ORDER BY period;
```

Executive Summary

```
SELECT *
FROM vw_saas_exec_summary;
```

ARR Growth

```
SELECT
period,
new_arr_booked,
arr_growth_pct
FROM vw_saas_monthly_kpis;
```

---

# Power BI Dashboard

Connect Power BI to:

```
saas_fpna.duckdb
```

Import:

```
vw_saas_monthly_kpis
```

Recommended pages:

Executive Overview
- ARR growth
- Gross margin
- Burn rate
- runway

Unit Economics
- LTV
- CAC
- LTV/CAC
- churn

Revenue
- ARR
- revenue
- customers

---

# Tech Stack

Python  
Pandas  
DuckDB  
SQL  
Power BI  

---

# Purpose

This project demonstrates:

- SaaS FP&A modeling
- messy ERP data handling
- data cleaning pipelines
- SQL star schema
- KPI modeling
- finance analytics engineering
- dashboard-ready outputs