import os
import pandas as pd
import numpy as np

RAW = "data/raw"
CLEAN = "data/clean"
MART = "data/mart"

os.makedirs(CLEAN, exist_ok=True)
os.makedirs(MART, exist_ok=True)


# ----------------------------
# Helper functions
# ----------------------------
def standardize_status(value):
    # Normalize common status labels
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().lower()

    mapping = {
        "active": "Active",
        "churned": "Churned",
        "cancelled": "Cancelled",
        "paused": "Paused",
        "open": "Open",
        "paid": "Paid",
        "overdue": "Overdue"
    }
    return mapping.get(value, value.title())


# ----------------------------
# 1) Customers
# ----------------------------
customers = pd.read_csv(f"{RAW}/raw_customers.csv")
customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")

# Remove duplicates by customer_id
customers = customers.drop_duplicates(subset=["customer_id"]).copy()

# Clean text columns
text_cols = [
    "customer_name",
    "industry",
    "region",
    "country",
    "acquisition_channel",
    "plan_name",
    "billing_frequency"
]
for col in text_cols:
    customers[col] = customers[col].astype(str).str.strip()

# Fix missing industry
customers["industry"] = customers["industry"].replace({"None": np.nan, "nan": np.nan}).fillna("Unknown")

# Standardize status
customers["account_status"] = customers["account_status"].apply(standardize_status)

customers.to_csv(f"{CLEAN}/customers_clean.csv", index=False)


# ----------------------------
# 2) Subscriptions
# ----------------------------
subs = pd.read_csv(f"{RAW}/raw_subscriptions.csv")
subs["start_date"] = pd.to_datetime(subs["start_date"], errors="coerce")
subs["end_date"] = pd.to_datetime(subs["end_date"], errors="coerce")

# Standardize fields
subs["currency"] = subs["currency"].astype(str).str.upper().str.strip()
subs["subscription_status"] = subs["subscription_status"].apply(standardize_status)

# Rebuild ARR from MRR
subs["arr"] = (subs["mrr"] * 12).round(2)

# Keep only valid date ranges
subs = subs[(subs["end_date"].isna()) | (subs["end_date"] >= subs["start_date"])].copy()

subs.to_csv(f"{CLEAN}/subscriptions_clean.csv", index=False)


# ----------------------------
# 3) Invoices
# ----------------------------
invoices = pd.read_csv(f"{RAW}/raw_invoices.csv")
invoices["invoice_date"] = pd.to_datetime(invoices["invoice_date"], errors="coerce")
invoices["due_date"] = pd.to_datetime(invoices["due_date"], errors="coerce")

# Remove duplicate invoice IDs
invoices = invoices.drop_duplicates(subset=["invoice_id"]).copy()

# Standardize status
invoices["invoice_status"] = invoices["invoice_status"].apply(standardize_status)

# Recalculate total
invoices["total_amount"] = (invoices["amount"] + invoices["tax"]).round(2)

invoices.to_csv(f"{CLEAN}/invoices_clean.csv", index=False)


# ----------------------------
# 4) GL
# ----------------------------
gl = pd.read_csv(f"{RAW}/raw_gl_transactions.csv")
gl["txn_date"] = pd.to_datetime(gl["txn_date"], errors="coerce")

# Standardize account names
gl["account_name"] = gl["account_name"].astype(str).str.strip().str.lower()

account_map = {
    "cost of service": "COGS",
    "sales and marketing": "Sales & Marketing",
    "sales & marketing": "Sales & Marketing",
    "research and development": "R&D",
    "general and administrative": "G&A",
    "cash": "Cash"
}

gl["account_category"] = gl["account_name"].map(account_map).fillna("Other")

gl.to_csv(f"{CLEAN}/gl_clean.csv", index=False)


# ----------------------------
# 5) Sales & Marketing
# ----------------------------
sm = pd.read_csv(f"{RAW}/raw_sales_marketing.csv")
sm["period"] = pd.to_datetime(sm["period"], errors="coerce").values.astype("datetime64[M]")

# CAC = spend / won customers
sm["cac"] = np.where(sm["won_customers"] > 0, sm["spend"] / sm["won_customers"], np.nan)
sm["cac"] = sm["cac"].round(2)

sm.to_csv(f"{CLEAN}/sales_marketing_clean.csv", index=False)


# ----------------------------
# 6) Cash
# ----------------------------
cash = pd.read_csv(f"{RAW}/raw_cash_balance.csv")
cash["period"] = pd.to_datetime(cash["period"], errors="coerce").values.astype("datetime64[M]")

# One row per entity-period
cash = cash.drop_duplicates(subset=["period", "entity"]).copy()

cash.to_csv(f"{CLEAN}/cash_balance_clean.csv", index=False)


# ----------------------------
# 7) Monthly KPI base table
# ----------------------------
invoices["period"] = invoices["invoice_date"].values.astype("datetime64[M]")
gl["period"] = gl["txn_date"].values.astype("datetime64[M]")
subs["period"] = subs["start_date"].values.astype("datetime64[M]")
customers["signup_month"] = customers["signup_date"].values.astype("datetime64[M]")

# Monthly revenue from invoices
monthly_revenue = (
    invoices.groupby("period", as_index=False)["amount"]
    .sum()
    .rename(columns={"amount": "revenue"})
)

# New customers from subscription start
monthly_customers = (
    subs.groupby("period", as_index=False)["customer_id"]
    .count()
    .rename(columns={"customer_id": "new_customers"})
)

# New ARR booked from subscription start
monthly_arr = (
    subs.groupby("period", as_index=False)["arr"]
    .sum()
    .rename(columns={"arr": "new_arr_booked"})
)

# Customer signups from customer master
monthly_customer_counts = (
    customers.groupby("signup_month", as_index=False)["customer_id"]
    .count()
)
monthly_customer_counts.columns = ["period", "customer_signups"]

# GL summarized by account category
gl_summary = gl.groupby(["period", "account_category"], as_index=False)["amount"].sum()
gl_pivot = (
    gl_summary
    .pivot(index="period", columns="account_category", values="amount")
    .reset_index()
    .fillna(0)
)

# Monthly avg CAC from marketing table
monthly_cac = (
    sm.groupby("period", as_index=False)
    .agg(
        total_marketing_spend=("spend", "sum"),
        won_customers=("won_customers", "sum")
    )
)
monthly_cac["cac"] = np.where(
    monthly_cac["won_customers"] > 0,
    monthly_cac["total_marketing_spend"] / monthly_cac["won_customers"],
    np.nan
)
monthly_cac["cac"] = monthly_cac["cac"].round(2)

# Build KPI base table
kpi_base = monthly_revenue.merge(monthly_customers, on="period", how="outer")
kpi_base = kpi_base.merge(monthly_arr, on="period", how="outer")
kpi_base = kpi_base.merge(monthly_customer_counts, on="period", how="outer")
kpi_base = kpi_base.merge(gl_pivot, on="period", how="outer")
kpi_base = kpi_base.merge(monthly_cac[["period", "total_marketing_spend", "won_customers", "cac"]], on="period", how="outer")
kpi_base = kpi_base.merge(cash[["period", "ending_cash"]], on="period", how="left")

kpi_base = kpi_base.fillna(0).sort_values("period").reset_index(drop=True)

# Active subscriptions by month
active_subs = []
for period in kpi_base["period"]:
    active_count = subs[
        (subs["start_date"] <= pd.to_datetime(period)) &
        (
            subs["end_date"].isna() |
            (subs["end_date"] >= pd.to_datetime(period))
        ) &
        (subs["subscription_status"].isin(["Active", "Paused", "Cancelled"]))
    ]["customer_id"].nunique()

    active_subs.append(active_count)

kpi_base["active_customers"] = active_subs

# Churned customers by month
cancelled_subs = subs[subs["subscription_status"] == "Cancelled"].copy()
cancelled_subs["churn_month"] = cancelled_subs["end_date"].values.astype("datetime64[M]")

monthly_churned = (
    cancelled_subs.groupby("churn_month", as_index=False)["customer_id"]
    .nunique()
)
monthly_churned.columns = ["period", "churned_customers"]

kpi_base = kpi_base.merge(monthly_churned, on="period", how="left")
kpi_base["churned_customers"] = kpi_base["churned_customers"].fillna(0)

# Churn rate
kpi_base["churn_pct"] = np.where(
    kpi_base["active_customers"] > 0,
    kpi_base["churned_customers"] / kpi_base["active_customers"],
    np.nan
)

# Gross margin
kpi_base["gross_margin"] = np.where(
    kpi_base["revenue"] != 0,
    (kpi_base["revenue"] - kpi_base.get("COGS", 0)) / kpi_base["revenue"],
    np.nan
)

# Burn rate
kpi_base["burn_rate"] = (
    kpi_base.get("Sales & Marketing", 0)
    + kpi_base.get("R&D", 0)
    + kpi_base.get("G&A", 0)
    + kpi_base.get("COGS", 0)
    - kpi_base["revenue"]
)

# Runway
kpi_base["runway_months"] = np.where(
    kpi_base["burn_rate"] > 0,
    kpi_base["ending_cash"] / kpi_base["burn_rate"],
    np.nan
)

# ARR growth %
kpi_base["arr_growth_pct"] = kpi_base["new_arr_booked"].pct_change()

# LTV estimate
# Simple portfolio project formula:
# LTV = ARPU * Gross Margin / Churn Rate
kpi_base["arpu"] = np.where(
    kpi_base["active_customers"] > 0,
    kpi_base["revenue"] / kpi_base["active_customers"],
    np.nan
)

kpi_base["ltv"] = np.where(
    (kpi_base["churn_pct"] > 0) & (kpi_base["gross_margin"].notna()),
    (kpi_base["arpu"] * kpi_base["gross_margin"]) / kpi_base["churn_pct"],
    np.nan
)

# LTV/CAC
kpi_base["ltv_cac"] = np.where(
    kpi_base["cac"] > 0,
    kpi_base["ltv"] / kpi_base["cac"],
    np.nan
)

# Save mart table
kpi_base.to_csv(f"{MART}/kpi_base_monthly.csv", index=False)

print("Clean data saved to data/clean/")
print("Mart-ready base table saved to data/mart/kpi_base_monthly.csv")
print(kpi_base.head())