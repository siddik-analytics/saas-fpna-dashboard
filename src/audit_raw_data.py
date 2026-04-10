import pandas as pd
import os

RAW = "data/raw"

def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

# Load raw files
customers = pd.read_csv(f"{RAW}/raw_customers.csv")
subs = pd.read_csv(f"{RAW}/raw_subscriptions.csv")
invoices = pd.read_csv(f"{RAW}/raw_invoices.csv")
gl = pd.read_csv(f"{RAW}/raw_gl_transactions.csv")

print_section("RAW CUSTOMERS AUDIT")
print(f"Rows: {len(customers)}")
print(f"Duplicate customer_id: {customers['customer_id'].duplicated().sum()}")
print("account_status values:", sorted(customers["account_status"].dropna().astype(str).unique()))
print("Missing industry:", customers["industry"].isna().sum())

print_section("RAW SUBSCRIPTIONS AUDIT")
print(f"Rows: {len(subs)}")
print("subscription_status values:", sorted(subs["subscription_status"].dropna().astype(str).unique()))
print("currency values:", sorted(subs["currency"].dropna().astype(str).unique()))

print_section("RAW INVOICES AUDIT")
print(f"Rows: {len(invoices)}")
print(f"Duplicate invoice_id: {invoices['invoice_id'].duplicated().sum()}")
print("invoice_status values:", sorted(invoices["invoice_status"].dropna().astype(str).unique()))

print_section("RAW GL AUDIT")
print(f"Rows: {len(gl)}")
print("account_name values sample:", sorted(gl["account_name"].dropna().astype(str).unique())[:15])