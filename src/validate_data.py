import pandas as pd
import numpy as np
import os

CLEAN = "data/clean"
MART = "data/mart"


def check_file_exists(path):
    # Simple file existence check
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    print(f"[OK] Found: {path}")


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# ----------------------------
# 1) Check output files exist
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
print(f"customers: {len(customers):,}")
print(f"subscriptions: {len(subs):,}")
print(f"invoices: {len(invoices):,}")
print(f"gl: {len(gl):,}")
print(f"sales_marketing: {len(sm):,}")
print(f"cash: {len(cash):,}")
print(f"kpi_base_monthly: {len(kpi):,}")


# ----------------------------
# 3) Duplicate checks
# ----------------------------
print_section("DUPLICATE CHECKS")

customer_dupes = customers["customer_id"].duplicated().sum()
sub_dupes = subs["subscription_id"].duplicated().sum()
invoice_dupes = invoices["invoice_id"].duplicated().sum()
gl_dupes = gl["gl_txn_id"].duplicated().sum()
cash_dupes = cash.duplicated(subset=["period", "entity"]).sum()

print(f"Duplicate customer_id: {customer_dupes}")
print(f"Duplicate subscription_id: {sub_dupes}")
print(f"Duplicate invoice_id: {invoice_dupes}")
print(f"Duplicate gl_txn_id: {gl_dupes}")
print(f"Duplicate cash period/entity rows: {cash_dupes}")


# ----------------------------
# 4) Null checks
# ----------------------------
print_section("NULL CHECKS")

critical_nulls = {
    "customers.customer_id": customers["customer_id"].isna().sum(),
    "customers.signup_date": customers["signup_date"].isna().sum(),
    "subs.subscription_id": subs["subscription_id"].isna().sum(),
    "subs.customer_id": subs["customer_id"].isna().sum(),
    "subs.start_date": subs["start_date"].isna().sum(),
    "invoices.invoice_id": invoices["invoice_id"].isna().sum(),
    "invoices.customer_id": invoices["customer_id"].isna().sum(),
    "invoices.invoice_date": invoices["invoice_date"].isna().sum(),
    "gl.gl_txn_id": gl["gl_txn_id"].isna().sum(),
    "gl.txn_date": gl["txn_date"].isna().sum(),
    "cash.period": cash["period"].isna().sum(),
    "kpi.period": kpi["period"].isna().sum(),
}

for key, value in critical_nulls.items():
    print(f"{key}: {value}")


# ----------------------------
# 5) Status standardization checks
# ----------------------------
print_section("STATUS STANDARDIZATION CHECKS")

print("Customer account_status values:")
print(sorted(customers["account_status"].dropna().unique()))

print("\nSubscription status values:")
print(sorted(subs["subscription_status"].dropna().unique()))

print("\nInvoice status values:")
print(sorted(invoices["invoice_status"].dropna().unique()))


# ----------------------------
# 6) Currency checks
# ----------------------------
print_section("CURRENCY CHECKS")

if "currency" in subs.columns:
    print("Subscription currency values:")
    print(sorted(subs["currency"].dropna().unique()))


# ----------------------------
# 7) Date logic checks
# ----------------------------
print_section("DATE LOGIC CHECKS")

subs["start_date"] = pd.to_datetime(subs["start_date"], errors="coerce")
subs["end_date"] = pd.to_datetime(subs["end_date"], errors="coerce")
invoices["invoice_date"] = pd.to_datetime(invoices["invoice_date"], errors="coerce")
invoices["due_date"] = pd.to_datetime(invoices["due_date"], errors="coerce")

bad_sub_dates = subs[
    subs["end_date"].notna() & (subs["end_date"] < subs["start_date"])
]

bad_invoice_dates = invoices[
    invoices["due_date"] < invoices["invoice_date"]
]

print(f"Subscriptions with end_date < start_date: {len(bad_sub_dates)}")
print(f"Invoices with due_date < invoice_date: {len(bad_invoice_dates)}")


# ----------------------------
# 8) Math checks
# ----------------------------
print_section("MATH CHECKS")

# Invoice total check
invoice_total_diff = (invoices["amount"] + invoices["tax"] - invoices["total_amount"]).round(2)
bad_invoice_math = (invoice_total_diff != 0).sum()
print(f"Invoices where amount + tax != total_amount: {bad_invoice_math}")

# CAC check
if {"spend", "won_customers", "cac"}.issubset(sm.columns):
    sm["expected_cac"] = np.where(sm["won_customers"] > 0, sm["spend"] / sm["won_customers"], np.nan)
    sm["expected_cac"] = sm["expected_cac"].round(2)
    bad_cac = ((sm["cac"].fillna(-9999) - sm["expected_cac"].fillna(-9999)).round(2) != 0).sum()
    print(f"Sales/marketing rows with incorrect CAC: {bad_cac}")


# ----------------------------
# 9) KPI sanity checks
# ----------------------------
print_section("KPI SANITY CHECKS")

kpi["period"] = pd.to_datetime(kpi["period"], errors="coerce")

numeric_cols = [
    "revenue",
    "new_customers",
    "new_arr_booked",
    "ending_cash",
    "active_customers",
    "churned_customers",
    "churn_pct",
    "gross_margin",
    "burn_rate",
    "runway_months",
    "cac",
    "ltv",
    "ltv_cac",
]

for col in numeric_cols:
    if col in kpi.columns:
        print(f"\nSummary for {col}:")
        print(kpi[col].describe())

# Flag suspicious cases
if "gross_margin" in kpi.columns:
    bad_gm = kpi[(kpi["gross_margin"] < -5) | (kpi["gross_margin"] > 5)]
    print(f"\nRows with suspicious gross margin: {len(bad_gm)}")

if "churn_pct" in kpi.columns:
    bad_churn = kpi[(kpi["churn_pct"] < 0) | (kpi["churn_pct"] > 1.5)]
    print(f"Rows with suspicious churn_pct: {len(bad_churn)}")

if "runway_months" in kpi.columns:
    negative_runway = kpi[kpi["runway_months"] < 0]
    print(f"Rows with negative runway_months: {len(negative_runway)}")


# ----------------------------
# 10) Preview final mart
# ----------------------------
print_section("FINAL MART PREVIEW")
print(kpi.head(12))


# ----------------------------
# 11) Overall summary
# ----------------------------
print_section("VALIDATION SUMMARY")

issues = {
    "duplicate_customer_id": customer_dupes,
    "duplicate_subscription_id": sub_dupes,
    "duplicate_invoice_id": invoice_dupes,
    "duplicate_gl_txn_id": gl_dupes,
    "duplicate_cash_rows": cash_dupes,
    "bad_subscription_dates": len(bad_sub_dates),
    "bad_invoice_dates": len(bad_invoice_dates),
    "bad_invoice_math": bad_invoice_math,
}

total_issues = sum(issues.values())

for issue, count in issues.items():
    print(f"{issue}: {count}")

print(f"\nTotal flagged issues: {total_issues}")

if total_issues == 0:
    print("\n[PASS] Validation completed with no critical issues.")
else:
    print("\n[WARNING] Validation completed with flagged issues. Review the counts above.")