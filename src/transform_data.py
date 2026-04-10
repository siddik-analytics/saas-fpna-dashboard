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
def clean_text(value):
    # Trim whitespace and preserve nulls
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    return value if value != "" else np.nan


def normalize_case(value):
    # Title-case generic text fields
    if pd.isna(value):
        return np.nan
    return str(value).strip().title()


def standardize_status(value):
    # Normalize status labels across files
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
        "overdue": "Overdue",
        "void": "Void"
    }
    return mapping.get(value, value.title())


def standardize_region(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().lower()
    mapping = {
        "north america": "North America",
        "na": "North America",
        "emea": "EMEA",
        "apac": "APAC"
    }
    return mapping.get(value, value.title())


def standardize_channel(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().lower()
    mapping = {
        "paid search": "Paid Search",
        "organic": "Organic",
        "partner": "Partner",
        "outbound": "Outbound",
        "referral": "Referral",
        "linkedin": "LinkedIn"
    }
    return mapping.get(value, value.title())


def standardize_entity(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().lower()
    mapping = {
        "saas holdco": "SaaS HoldCo",
        "saas canada": "SaaS Canada",
        "saas us": "SaaS US"
    }
    return mapping.get(value, value.title())


def standardize_currency(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().upper()
    mapping = {
        "USD": "USD",
        "US$": "USD",
        "CAD": "CAD"
    }
    return mapping.get(value, value)


def standardize_billing_frequency(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().lower()
    mapping = {
        "monthly": "Monthly",
        "annual": "Annual"
    }
    return mapping.get(value, value.title())


def standardize_plan(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().lower()
    mapping = {
        "basic": "Basic",
        "growth": "Growth",
        "pro": "Pro",
        "enterprise": "Enterprise"
    }
    return mapping.get(value, value.title())


# ----------------------------
# 1) Customers
# ----------------------------
customers = pd.read_csv(f"{RAW}/raw_customers.csv")

for col in customers.columns:
    if customers[col].dtype == "object":
        customers[col] = customers[col].apply(clean_text)

customers["customer_id"] = customers["customer_id"].astype(str).str.strip()
customers["customer_name"] = customers["customer_name"].apply(normalize_case)
customers["industry"] = customers["industry"].apply(normalize_case)
customers["region"] = customers["region"].apply(standardize_region)
customers["country"] = customers["country"].apply(normalize_case)
customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")
customers["acquisition_channel"] = customers["acquisition_channel"].apply(standardize_channel)
customers["account_status"] = customers["account_status"].apply(standardize_status)
customers["plan_name"] = customers["plan_name"].apply(standardize_plan)
customers["billing_frequency"] = customers["billing_frequency"].apply(standardize_billing_frequency)

customers["industry"] = customers["industry"].fillna("Unknown")
customers["country"] = customers["country"].fillna("Unknown")
customers["customer_name"] = customers["customer_name"].fillna("Unknown Customer")
customers["plan_name"] = customers["plan_name"].fillna("Unknown")
customers["billing_frequency"] = customers["billing_frequency"].fillna("Unknown")

# Keep earliest signup record per customer_id
customers = customers.sort_values(["customer_id", "signup_date"], na_position="last")
customers = customers.drop_duplicates(subset=["customer_id"], keep="first").copy()

customers.to_csv(f"{CLEAN}/customers_clean.csv", index=False)


# ----------------------------
# 2) Subscriptions
# ----------------------------
subs = pd.read_csv(f"{RAW}/raw_subscriptions.csv")

for col in subs.columns:
    if subs[col].dtype == "object":
        subs[col] = subs[col].apply(clean_text)

subs["subscription_id"] = subs["subscription_id"].astype(str).str.strip()
subs["customer_id"] = subs["customer_id"].astype(str).str.strip()
subs["start_date"] = pd.to_datetime(subs["start_date"], errors="coerce")
subs["end_date"] = pd.to_datetime(subs["end_date"], errors="coerce")
subs["plan_name"] = subs["plan_name"].apply(standardize_plan)
subs["subscription_status"] = subs["subscription_status"].apply(standardize_status)
subs["currency"] = subs["currency"].apply(standardize_currency)
subs["discount_pct"] = pd.to_numeric(subs["discount_pct"], errors="coerce").fillna(0)

subs["mrr"] = pd.to_numeric(subs["mrr"], errors="coerce")
subs["arr"] = pd.to_numeric(subs["arr"], errors="coerce")

# Remove invalid or nonsensical MRR rows
subs = subs[subs["mrr"].notna()].copy()
subs = subs[subs["mrr"] > 0].copy()

# Fix missing plans from customer table where possible
subs = subs.merge(
    customers[["customer_id", "plan_name"]].rename(columns={"plan_name": "customer_plan"}),
    on="customer_id",
    how="left"
)
subs["plan_name"] = np.where(
    subs["plan_name"].isin(["Unknown"]) | subs["plan_name"].isna(),
    subs["customer_plan"],
    subs["plan_name"]
)
subs["plan_name"] = subs["plan_name"].fillna("Unknown")
subs = subs.drop(columns=["customer_plan"])

# Standardize ARR from MRR
subs["arr"] = (subs["mrr"] * 12).round(2)

# Remove impossible date rows
subs = subs[subs["start_date"].notna()].copy()
subs = subs[(subs["end_date"].isna()) | (subs["end_date"] >= subs["start_date"])].copy()

# If duplicate subscription_id exists, keep latest valid row
subs = subs.sort_values(["subscription_id", "start_date", "end_date"], na_position="last")
subs = subs.drop_duplicates(subset=["subscription_id"], keep="last").copy()

subs.to_csv(f"{CLEAN}/subscriptions_clean.csv", index=False)


# ----------------------------
# 3) Invoices
# ----------------------------
invoices = pd.read_csv(f"{RAW}/raw_invoices.csv")

for col in invoices.columns:
    if invoices[col].dtype == "object":
        invoices[col] = invoices[col].apply(clean_text)

invoices["invoice_id"] = invoices["invoice_id"].astype(str).str.strip()
invoices["customer_id"] = invoices["customer_id"].astype(str).str.strip()
invoices["subscription_id"] = invoices["subscription_id"].astype(str).str.strip()
invoices["invoice_date"] = pd.to_datetime(invoices["invoice_date"], errors="coerce")
invoices["due_date"] = pd.to_datetime(invoices["due_date"], errors="coerce")
invoices["invoice_status"] = invoices["invoice_status"].apply(standardize_status)

invoices["amount"] = pd.to_numeric(invoices["amount"], errors="coerce")
invoices["tax"] = pd.to_numeric(invoices["tax"], errors="coerce")
invoices["total_amount"] = pd.to_numeric(invoices["total_amount"], errors="coerce")

# Remove rows missing essential fields
invoices = invoices[
    invoices["invoice_id"].notna() &
    invoices["invoice_date"].notna() &
    invoices["customer_id"].notna()
].copy()

# Drop Void invoices from recognized revenue
# but keep them in clean layer if you want a fuller audit trail
invoices["is_void"] = invoices["invoice_status"].eq("Void")

# Fix due dates where missing or earlier than invoice date
invoices["due_date"] = np.where(
    invoices["due_date"].isna() | (invoices["due_date"] < invoices["invoice_date"]),
    invoices["invoice_date"] + pd.to_timedelta(30, unit="D"),
    invoices["due_date"]
)
invoices["due_date"] = pd.to_datetime(invoices["due_date"])

# Recalculate invoice math
invoices["tax"] = invoices["tax"].fillna(0)
invoices["amount"] = invoices["amount"].fillna(0)
invoices["total_amount"] = (invoices["amount"] + invoices["tax"]).round(2)

# Keep latest row per invoice_id
invoices = invoices.sort_values(["invoice_id", "invoice_date"])
invoices = invoices.drop_duplicates(subset=["invoice_id"], keep="last").copy()

invoices.to_csv(f"{CLEAN}/invoices_clean.csv", index=False)


# ----------------------------
# 4) GL
# ----------------------------
gl = pd.read_csv(f"{RAW}/raw_gl_transactions.csv")

for col in gl.columns:
    if gl[col].dtype == "object":
        gl[col] = gl[col].apply(clean_text)

gl["gl_txn_id"] = gl["gl_txn_id"].astype(str).str.strip()
gl["txn_date"] = pd.to_datetime(gl["txn_date"], errors="coerce")
gl["account_code"] = gl["account_code"].apply(clean_text)
gl["account_name"] = gl["account_name"].apply(clean_text)
gl["department"] = gl["department"].apply(normalize_case)
gl["cost_center"] = gl["cost_center"].apply(clean_text)
gl["vendor_customer"] = gl["vendor_customer"].apply(clean_text)
gl["entity"] = gl["entity"].apply(standardize_entity)
gl["memo"] = gl["memo"].apply(clean_text)

gl["amount"] = pd.to_numeric(gl["amount"], errors="coerce")
gl["dr_cr"] = gl["dr_cr"].apply(lambda x: str(x).strip().upper() if pd.notna(x) else np.nan)

gl["department"] = gl["department"].fillna("Unknown")
gl["cost_center"] = gl["cost_center"].fillna("Unknown")
gl["vendor_customer"] = gl["vendor_customer"].fillna("Unknown")
gl["memo"] = gl["memo"].fillna("Unknown")
gl["account_code"] = gl["account_code"].fillna("Unknown")
gl["account_name"] = gl["account_name"].fillna("Unknown").str.lower()

account_map = {
    "cost of service": "COGS",
    "sales and marketing": "Sales & Marketing",
    "sales & marketing": "Sales & Marketing",
    "s&m": "Sales & Marketing",
    "research and development": "R&D",
    "r&d": "R&D",
    "general and administrative": "G&A",
    "g&a": "G&A",
    "cash": "Cash",
    "misc expense": "Other"
}

gl["account_category"] = gl["account_name"].map(account_map).fillna("Other")

# Remove rows missing essential fields
gl = gl[gl["gl_txn_id"].notna() & gl["txn_date"].notna() & gl["amount"].notna()].copy()

# Keep latest row per transaction ID
gl = gl.sort_values(["gl_txn_id", "txn_date"])
gl = gl.drop_duplicates(subset=["gl_txn_id"], keep="last").copy()

gl.to_csv(f"{CLEAN}/gl_clean.csv", index=False)


# ----------------------------
# 5) Sales & Marketing
# ----------------------------
sm = pd.read_csv(f"{RAW}/raw_sales_marketing.csv")

for col in sm.columns:
    if sm[col].dtype == "object":
        sm[col] = sm[col].apply(clean_text)

sm["period"] = pd.to_datetime(sm["period"], errors="coerce")
sm["channel"] = sm["channel"].apply(standardize_channel)
sm["campaign_name"] = sm["campaign_name"].fillna("Unknown Campaign")
sm["spend"] = pd.to_numeric(sm["spend"], errors="coerce")
sm["leads"] = pd.to_numeric(sm["leads"], errors="coerce")
sm["won_customers"] = pd.to_numeric(sm["won_customers"], errors="coerce")

# Remove rows with no period
sm = sm[sm["period"].notna()].copy()

# Fix negative spend by keeping value as absolute marketing spend
sm["spend"] = sm["spend"].fillna(0).abs()

# Won customers should not be negative
sm["won_customers"] = sm["won_customers"].fillna(0)
sm["won_customers"] = np.where(sm["won_customers"] < 0, 0, sm["won_customers"])

# Leads should not be negative
sm["leads"] = sm["leads"].fillna(0)
sm["leads"] = np.where(sm["leads"] < 0, 0, sm["leads"])

sm["period"] = sm["period"].values.astype("datetime64[M]")

# CAC
sm["cac"] = np.where(sm["won_customers"] > 0, sm["spend"] / sm["won_customers"], np.nan)
sm["cac"] = sm["cac"].round(2)

# Drop exact duplicates
sm = sm.drop_duplicates().copy()

sm.to_csv(f"{CLEAN}/sales_marketing_clean.csv", index=False)


# ----------------------------
# 6) Cash
# ----------------------------
cash = pd.read_csv(f"{RAW}/raw_cash_balance.csv")

for col in cash.columns:
    if cash[col].dtype == "object":
        cash[col] = cash[col].apply(clean_text)

cash["period"] = pd.to_datetime(cash["period"], errors="coerce")
cash["entity"] = cash["entity"].apply(standardize_entity)
cash["beginning_cash"] = pd.to_numeric(cash["beginning_cash"], errors="coerce")
cash["ending_cash"] = pd.to_numeric(cash["ending_cash"], errors="coerce")

cash = cash[cash["period"].notna()].copy()
cash["period"] = cash["period"].values.astype("datetime64[M]")

# Fill missing ending cash with beginning cash
cash["ending_cash"] = np.where(
    cash["ending_cash"].isna(),
    cash["beginning_cash"],
    cash["ending_cash"]
)

# Consolidate duplicate period/entity rows by taking last non-null / max balances
cash = (
    cash.groupby(["period", "entity"], as_index=False)
    .agg(
        beginning_cash=("beginning_cash", "max"),
        ending_cash=("ending_cash", "max")
    )
)

cash.to_csv(f"{CLEAN}/cash_balance_clean.csv", index=False)


# ----------------------------
# 7) KPI base table
# ----------------------------
# Period fields
invoices["period"] = invoices["invoice_date"].values.astype("datetime64[M]")
gl["period"] = gl["txn_date"].values.astype("datetime64[M]")
subs["period"] = subs["start_date"].values.astype("datetime64[M]")
customers["signup_month"] = customers["signup_date"].values.astype("datetime64[M]")

# Revenue from non-void invoices only
recognized_invoices = invoices[~invoices["is_void"]].copy()

monthly_revenue = (
    recognized_invoices.groupby("period", as_index=False)["amount"]
    .sum()
    .rename(columns={"amount": "revenue"})
)

# New customers from subscription starts
monthly_new_customers = (
    subs.groupby("period", as_index=False)["customer_id"]
    .nunique()
    .rename(columns={"customer_id": "new_customers"})
)

# New ARR booked
monthly_arr = (
    subs.groupby("period", as_index=False)["arr"]
    .sum()
    .rename(columns={"arr": "new_arr_booked"})
)

# Customer signups from customer master
monthly_customer_signups = (
    customers[customers["signup_month"].notna()]
    .groupby("signup_month", as_index=False)["customer_id"]
    .nunique()
)
monthly_customer_signups.columns = ["period", "customer_signups"]

# GL by category
gl_summary = (
    gl.groupby(["period", "account_category"], as_index=False)["amount"]
    .sum()
)

gl_pivot = (
    gl_summary
    .pivot(index="period", columns="account_category", values="amount")
    .reset_index()
    .fillna(0)
)

# Marketing aggregation
monthly_cac = (
    sm.groupby("period", as_index=False)
    .agg(
        total_marketing_spend=("spend", "sum"),
        marketing_won_customers=("won_customers", "sum"),
        leads=("leads", "sum")
    )
)

monthly_cac["cac"] = np.where(
    monthly_cac["marketing_won_customers"] > 0,
    monthly_cac["total_marketing_spend"] / monthly_cac["marketing_won_customers"],
    np.nan
)
monthly_cac["cac"] = monthly_cac["cac"].round(2)

# Base table
kpi_base = monthly_revenue.merge(monthly_new_customers, on="period", how="outer")
kpi_base = kpi_base.merge(monthly_arr, on="period", how="outer")
kpi_base = kpi_base.merge(monthly_customer_signups, on="period", how="outer")
kpi_base = kpi_base.merge(gl_pivot, on="period", how="outer")
kpi_base = kpi_base.merge(
    monthly_cac[["period", "total_marketing_spend", "marketing_won_customers", "leads", "cac"]],
    on="period",
    how="outer"
)
kpi_base = kpi_base.merge(cash[["period", "ending_cash"]], on="period", how="left")

kpi_base = kpi_base.fillna(0).sort_values("period").reset_index(drop=True)

# Active customers by period
active_counts = []
for period in kpi_base["period"]:
    period_ts = pd.to_datetime(period)

    active_count = subs[
        (subs["start_date"] <= period_ts) &
        (
            subs["end_date"].isna() |
            (subs["end_date"] >= period_ts)
        ) &
        (subs["subscription_status"].isin(["Active", "Paused"]))
    ]["customer_id"].nunique()

    active_counts.append(active_count)

kpi_base["active_customers"] = active_counts

# Churned customers by month
cancelled_subs = subs[
    (subs["subscription_status"] == "Cancelled") &
    (subs["end_date"].notna())
].copy()

cancelled_subs["churn_month"] = cancelled_subs["end_date"].values.astype("datetime64[M]")

monthly_churned = (
    cancelled_subs.groupby("churn_month", as_index=False)["customer_id"]
    .nunique()
)
monthly_churned.columns = ["period", "churned_customers"]

kpi_base = kpi_base.merge(monthly_churned, on="period", how="left")
kpi_base["churned_customers"] = kpi_base["churned_customers"].fillna(0)

# Churn %
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

# ARR growth based on booked ARR trend
kpi_base["arr_growth_pct"] = kpi_base["new_arr_booked"].pct_change()

# ARPU
kpi_base["arpu"] = np.where(
    kpi_base["active_customers"] > 0,
    kpi_base["revenue"] / kpi_base["active_customers"],
    np.nan
)

# LTV
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

# Sort and save
kpi_base = kpi_base.sort_values("period").reset_index(drop=True)
kpi_base.to_csv(f"{MART}/kpi_base_monthly.csv", index=False)

print("Clean data saved to data/clean/")
print("Mart-ready base table saved to data/mart/kpi_base_monthly.csv")
print("\nPreview:")
print(kpi_base.head(10))