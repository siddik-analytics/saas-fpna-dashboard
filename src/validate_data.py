import os
import pandas as pd
import numpy as np

CLEAN = "data/clean"
MART = "data/mart"


def check_file_exists(path):
    # Check whether a required file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    print(f"[OK] Found: {path}")


def print_section(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


# ----------------------------
# 1) Check expected files exist
# ----------------------------
files_to_check = [
    f"{CLEAN}/customers_clean.csv",
    f"{CLEAN}/subscriptions_clean.csv",
    f"{CLEAN}/invoices_clean.csv",
    f"{CLEAN}/gl_clean.csv",
    f"{CLEAN}/sales_marketing_clean.csv",
    f"{CLEAN}/cash_balance_clean.csv",
    f"{MART}/kpi_base_monthly.csv",
]

print_section("CHECKING OUTPUT FILES")
for file in files_to_check:
    check_file_exists(file)


# ----------------------------
# 2) Load files
# ----------------------------
customers = pd.read_csv(f"{CLEAN}/customers_clean.csv")
subs = pd.read_csv(f"{CLEAN}/subscriptions_clean.csv")
invoices = pd.read_csv(f"{CLEAN}/invoices_clean.csv")
gl = pd.read_csv(f"{CLEAN}/gl_clean.csv")
sm = pd.read_csv(f"{CLEAN}/sales_marketing_clean.csv")
cash = pd.read_csv(f"{CLEAN}/cash_balance_clean.csv")
kpi = pd.read_csv(f"{MART}/kpi_base_monthly.csv")

print_section("ROW COUNTS")
print(f"customers_clean: {len(customers):,}")
print(f"subscriptions_clean: {len(subs):,}")
print(f"invoices_clean: {len(invoices):,}")
print(f"gl_clean: {len(gl):,}")
print(f"sales_marketing_clean: {len(sm):,}")
print(f"cash_balance_clean: {len(cash):,}")
print(f"kpi_base_monthly: {len(kpi):,}")


# ----------------------------
# 3) Parse date columns
# ----------------------------
date_columns = {
    "customers": ["signup_date"],
    "subs": ["start_date", "end_date"],
    "invoices": ["invoice_date", "due_date"],
    "gl": ["txn_date"],
    "sm": ["period"],
    "cash": ["period"],
    "kpi": ["period"],
}

for col in date_columns["customers"]:
    if col in customers.columns:
        customers[col] = pd.to_datetime(customers[col], errors="coerce")

for col in date_columns["subs"]:
    if col in subs.columns:
        subs[col] = pd.to_datetime(subs[col], errors="coerce")

for col in date_columns["invoices"]:
    if col in invoices.columns:
        invoices[col] = pd.to_datetime(invoices[col], errors="coerce")

for col in date_columns["gl"]:
    if col in gl.columns:
        gl[col] = pd.to_datetime(gl[col], errors="coerce")

for col in date_columns["sm"]:
    if col in sm.columns:
        sm[col] = pd.to_datetime(sm[col], errors="coerce")

for col in date_columns["cash"]:
    if col in cash.columns:
        cash[col] = pd.to_datetime(cash[col], errors="coerce")

for col in date_columns["kpi"]:
    if col in kpi.columns:
        kpi[col] = pd.to_datetime(kpi[col], errors="coerce")


# ----------------------------
# 4) Duplicate checks
# ----------------------------
print_section("DUPLICATE CHECKS")

customer_dupes = customers["customer_id"].duplicated().sum() if "customer_id" in customers.columns else -1
sub_dupes = subs["subscription_id"].duplicated().sum() if "subscription_id" in subs.columns else -1
invoice_dupes = invoices["invoice_id"].duplicated().sum() if "invoice_id" in invoices.columns else -1
gl_dupes = gl["gl_txn_id"].duplicated().sum() if "gl_txn_id" in gl.columns else -1
cash_dupes = cash.duplicated(subset=["period", "entity"]).sum() if {"period", "entity"}.issubset(cash.columns) else -1

print(f"Duplicate customer_id: {customer_dupes}")
print(f"Duplicate subscription_id: {sub_dupes}")
print(f"Duplicate invoice_id: {invoice_dupes}")
print(f"Duplicate gl_txn_id: {gl_dupes}")
print(f"Duplicate cash period/entity rows: {cash_dupes}")


# ----------------------------
# 5) Critical null checks
# ----------------------------
print_section("CRITICAL NULL CHECKS")

critical_nulls = {
    "customers.customer_id": customers["customer_id"].isna().sum() if "customer_id" in customers.columns else -1,
    "customers.customer_name": customers["customer_name"].isna().sum() if "customer_name" in customers.columns else -1,
    "subs.subscription_id": subs["subscription_id"].isna().sum() if "subscription_id" in subs.columns else -1,
    "subs.customer_id": subs["customer_id"].isna().sum() if "customer_id" in subs.columns else -1,
    "subs.start_date": subs["start_date"].isna().sum() if "start_date" in subs.columns else -1,
    "invoices.invoice_id": invoices["invoice_id"].isna().sum() if "invoice_id" in invoices.columns else -1,
    "invoices.customer_id": invoices["customer_id"].isna().sum() if "customer_id" in invoices.columns else -1,
    "invoices.invoice_date": invoices["invoice_date"].isna().sum() if "invoice_date" in invoices.columns else -1,
    "gl.gl_txn_id": gl["gl_txn_id"].isna().sum() if "gl_txn_id" in gl.columns else -1,
    "gl.txn_date": gl["txn_date"].isna().sum() if "txn_date" in gl.columns else -1,
    "cash.period": cash["period"].isna().sum() if "period" in cash.columns else -1,
    "cash.entity": cash["entity"].isna().sum() if "entity" in cash.columns else -1,
    "kpi.period": kpi["period"].isna().sum() if "period" in kpi.columns else -1,
}

for key, value in critical_nulls.items():
    print(f"{key}: {value}")


# ----------------------------
# 6) Allowed values checks
# ----------------------------
print_section("STANDARDIZATION CHECKS")

if "account_status" in customers.columns:
    allowed_customer_status = {"Active", "Churned", "Paused", "Unknown"}
    actual_customer_status = set(customers["account_status"].dropna().unique())
    unexpected_customer_status = sorted(actual_customer_status - allowed_customer_status)
    print("Customer account_status values:", sorted(actual_customer_status))
    print("Unexpected customer statuses:", unexpected_customer_status)

if "subscription_status" in subs.columns:
    allowed_sub_status = {"Active", "Cancelled", "Paused", "Unknown"}
    actual_sub_status = set(subs["subscription_status"].dropna().unique())
    unexpected_sub_status = sorted(actual_sub_status - allowed_sub_status)
    print("\nSubscription status values:", sorted(actual_sub_status))
    print("Unexpected subscription statuses:", unexpected_sub_status)

if "invoice_status" in invoices.columns:
    allowed_invoice_status = {"Paid", "Open", "Overdue", "Void", "Unknown"}
    actual_invoice_status = set(invoices["invoice_status"].dropna().unique())
    unexpected_invoice_status = sorted(actual_invoice_status - allowed_invoice_status)
    print("\nInvoice status values:", sorted(actual_invoice_status))
    print("Unexpected invoice statuses:", unexpected_invoice_status)

if "currency" in subs.columns:
    allowed_currency = {"USD", "CAD", "Unknown"}
    actual_currency = set(subs["currency"].dropna().unique())
    unexpected_currency = sorted(actual_currency - allowed_currency)
    print("\nSubscription currency values:", sorted(actual_currency))
    print("Unexpected currency values:", unexpected_currency)

if "region" in customers.columns:
    allowed_region = {"North America", "EMEA", "APAC", "Unknown"}
    actual_region = set(customers["region"].dropna().unique())
    unexpected_region = sorted(actual_region - allowed_region)
    print("\nCustomer region values:", sorted(actual_region))
    print("Unexpected region values:", unexpected_region)

if "entity" in cash.columns:
    allowed_entity = {"SaaS HoldCo", "SaaS Canada", "SaaS US", "Unknown"}
    actual_entity = set(cash["entity"].dropna().unique())
    unexpected_entity = sorted(actual_entity - allowed_entity)
    print("\nCash entity values:", sorted(actual_entity))
    print("Unexpected cash entities:", unexpected_entity)


# ----------------------------
# 7) Date logic checks
# ----------------------------
print_section("DATE LOGIC CHECKS")

bad_sub_dates = subs[
    subs["end_date"].notna() & (subs["end_date"] < subs["start_date"])
] if {"start_date", "end_date"}.issubset(subs.columns) else pd.DataFrame()

bad_invoice_dates = invoices[
    invoices["due_date"] < invoices["invoice_date"]
] if {"invoice_date", "due_date"}.issubset(invoices.columns) else pd.DataFrame()

future_signup_dates = customers[
    customers["signup_date"] > pd.Timestamp.today()
] if "signup_date" in customers.columns else pd.DataFrame()

print(f"Subscriptions with end_date < start_date: {len(bad_sub_dates)}")
print(f"Invoices with due_date < invoice_date: {len(bad_invoice_dates)}")
print(f"Customers with future signup_date: {len(future_signup_dates)}")


# ----------------------------
# 8) Business rule checks
# ----------------------------
print_section("BUSINESS RULE CHECKS")

negative_mrr = subs[subs["mrr"] <= 0] if "mrr" in subs.columns else pd.DataFrame()
negative_arr = subs[subs["arr"] <= 0] if "arr" in subs.columns else pd.DataFrame()
negative_spend = sm[sm["spend"] < 0] if "spend" in sm.columns else pd.DataFrame()
negative_won_customers = sm[sm["won_customers"] < 0] if "won_customers" in sm.columns else pd.DataFrame()
negative_leads = sm[sm["leads"] < 0] if "leads" in sm.columns else pd.DataFrame()
null_ending_cash = cash[cash["ending_cash"].isna()] if "ending_cash" in cash.columns else pd.DataFrame()

print(f"Subscriptions with mrr <= 0: {len(negative_mrr)}")
print(f"Subscriptions with arr <= 0: {len(negative_arr)}")
print(f"Sales rows with negative spend: {len(negative_spend)}")
print(f"Sales rows with negative won_customers: {len(negative_won_customers)}")
print(f"Sales rows with negative leads: {len(negative_leads)}")
print(f"Cash rows with null ending_cash: {len(null_ending_cash)}")


# ----------------------------
# 9) Invoice math checks
# ----------------------------
print_section("INVOICE MATH CHECKS")

if {"amount", "tax", "total_amount"}.issubset(invoices.columns):
    expected_total = (invoices["amount"].fillna(0) + invoices["tax"].fillna(0)).round(2)
    diff = (expected_total - invoices["total_amount"].fillna(0)).round(2)
    bad_invoice_math = (diff != 0).sum()
    print(f"Invoices where amount + tax != total_amount: {bad_invoice_math}")
else:
    bad_invoice_math = -1
    print("Invoice math columns not all present.")

if "is_void" in invoices.columns and "invoice_status" in invoices.columns:
    void_mismatch = (invoices["is_void"] != invoices["invoice_status"].eq("Void")).sum()
    print(f"Rows where is_void does not match invoice_status == 'Void': {void_mismatch}")
else:
    void_mismatch = 0


# ----------------------------
# 10) CAC checks
# ----------------------------
print_section("CAC CHECKS")

if {"spend", "won_customers", "cac"}.issubset(sm.columns):
    expected_cac = np.where(sm["won_customers"] > 0, sm["spend"] / sm["won_customers"], np.nan)
    expected_cac = pd.Series(expected_cac).round(2)
    actual_cac = sm["cac"].round(2)

    # Compare NaNs safely
    cac_mismatch = (
        ~(
            (expected_cac.isna() & actual_cac.isna()) |
            (expected_cac.fillna(-999999) == actual_cac.fillna(-999999))
        )
    ).sum()

    zero_win_with_cac = sm[(sm["won_customers"] <= 0) & sm["cac"].notna()]
    print(f"Rows with incorrect CAC: {cac_mismatch}")
    print(f"Rows with won_customers <= 0 but CAC present: {len(zero_win_with_cac)}")
else:
    cac_mismatch = -1
    print("Sales/marketing CAC columns not all present.")


# ----------------------------
# 11) GL category checks
# ----------------------------
print_section("GL CATEGORY CHECKS")

if "account_category" in gl.columns:
    allowed_gl_categories = {"COGS", "Sales & Marketing", "R&D", "G&A", "Cash", "Other"}
    actual_gl_categories = set(gl["account_category"].dropna().unique())
    unexpected_gl_categories = sorted(actual_gl_categories - allowed_gl_categories)

    print("GL account categories:", sorted(actual_gl_categories))
    print("Unexpected GL categories:", unexpected_gl_categories)
else:
    unexpected_gl_categories = ["Missing account_category"]
    print("Missing account_category column.")


# ----------------------------
# 12) KPI sanity checks
# ----------------------------
print_section("KPI SANITY CHECKS")

numeric_cols = [
    "revenue",
    "new_customers",
    "new_arr_booked",
    "customer_signups",
    "total_marketing_spend",
    "marketing_won_customers",
    "leads",
    "ending_cash",
    "active_customers",
    "churned_customers",
    "churn_pct",
    "gross_margin",
    "burn_rate",
    "runway_months",
    "cac",
    "arpu",
    "ltv",
    "ltv_cac",
]

for col in numeric_cols:
    if col in kpi.columns:
        print(f"\nSummary for {col}:")
        print(kpi[col].describe())

kpi_duplicate_periods = kpi["period"].duplicated().sum() if "period" in kpi.columns else -1
negative_revenue = len(kpi[kpi["revenue"] < 0]) if "revenue" in kpi.columns else -1
negative_active_customers = len(kpi[kpi["active_customers"] < 0]) if "active_customers" in kpi.columns else -1
bad_churn = len(kpi[(kpi["churn_pct"] < 0) | (kpi["churn_pct"] > 1.5)]) if "churn_pct" in kpi.columns else -1
bad_gm = len(kpi[(kpi["gross_margin"] < -5) | (kpi["gross_margin"] > 5)]) if "gross_margin" in kpi.columns else -1
negative_runway = len(kpi[kpi["runway_months"] < 0]) if "runway_months" in kpi.columns else -1
negative_cac = len(kpi[kpi["cac"] < 0]) if "cac" in kpi.columns else -1

print(f"\nDuplicate KPI periods: {kpi_duplicate_periods}")
print(f"Rows with negative revenue: {negative_revenue}")
print(f"Rows with negative active_customers: {negative_active_customers}")
print(f"Rows with suspicious churn_pct: {bad_churn}")
print(f"Rows with suspicious gross_margin: {bad_gm}")
print(f"Rows with negative runway_months: {negative_runway}")
print(f"Rows with negative CAC: {negative_cac}")


# ----------------------------
# 13) Preview final mart
# ----------------------------
print_section("FINAL MART PREVIEW")
print(kpi.head(12))


# ----------------------------
# 14) Summary
# ----------------------------
print_section("VALIDATION SUMMARY")

issues = {
    "duplicate_customer_id": customer_dupes,
    "duplicate_subscription_id": sub_dupes,
    "duplicate_invoice_id": invoice_dupes,
    "duplicate_gl_txn_id": gl_dupes,
    "duplicate_cash_rows": cash_dupes,
    "critical_nulls_total": sum(v for v in critical_nulls.values() if isinstance(v, (int, np.integer)) and v > 0),
    "unexpected_customer_statuses": len(unexpected_customer_status),
    "unexpected_subscription_statuses": len(unexpected_sub_status),
    "unexpected_invoice_statuses": len(unexpected_invoice_status),
    "unexpected_currency_values": len(unexpected_currency) if "currency" in subs.columns else 0,
    "unexpected_region_values": len(unexpected_region) if "region" in customers.columns else 0,
    "unexpected_entity_values": len(unexpected_entity) if "entity" in cash.columns else 0,
    "bad_subscription_dates": len(bad_sub_dates),
    "bad_invoice_dates": len(bad_invoice_dates),
    "future_signup_dates": len(future_signup_dates),
    "nonpositive_mrr_rows": len(negative_mrr),
    "nonpositive_arr_rows": len(negative_arr),
    "negative_spend_rows": len(negative_spend),
    "negative_won_customers_rows": len(negative_won_customers),
    "negative_leads_rows": len(negative_leads),
    "null_ending_cash_rows": len(null_ending_cash),
    "bad_invoice_math": bad_invoice_math if isinstance(bad_invoice_math, (int, np.integer)) else 0,
    "void_flag_mismatch": void_mismatch,
    "cac_mismatch_rows": cac_mismatch if isinstance(cac_mismatch, (int, np.integer)) else 0,
    "unexpected_gl_categories": len(unexpected_gl_categories),
    "duplicate_kpi_periods": kpi_duplicate_periods if isinstance(kpi_duplicate_periods, (int, np.integer)) else 0,
    "negative_kpi_revenue_rows": negative_revenue if isinstance(negative_revenue, (int, np.integer)) else 0,
    "negative_active_customer_rows": negative_active_customers if isinstance(negative_active_customers, (int, np.integer)) else 0,
    "suspicious_churn_rows": bad_churn if isinstance(bad_churn, (int, np.integer)) else 0,
    "suspicious_gross_margin_rows": bad_gm if isinstance(bad_gm, (int, np.integer)) else 0,
    "negative_runway_rows": negative_runway if isinstance(negative_runway, (int, np.integer)) else 0,
    "negative_cac_rows": negative_cac if isinstance(negative_cac, (int, np.integer)) else 0,
}

total_issues = sum(v for v in issues.values() if isinstance(v, (int, np.integer)))

for issue, count in issues.items():
    print(f"{issue}: {count}")

print(f"\nTotal flagged issues: {total_issues}")

if total_issues == 0:
    print("\n[PASS] Validation completed with no flagged issues.")
else:
    print("\n[WARNING] Validation completed with flagged issues. Review the counts above.")