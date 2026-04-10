import os
import numpy as np
import pandas as pd
from faker import Faker
from datetime import timedelta

fake = Faker()
np.random.seed(42)

BASE_PATH = "data/raw"
os.makedirs(BASE_PATH, exist_ok=True)

months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
n_customers = 320

regions = ["North America", "north america", "NA", "EMEA", "emea", "APAC", "apac"]
countries = {
    "North America": ["Canada", "USA"],
    "north america": ["Canada", "USA"],
    "NA": ["Canada", "USA"],
    "EMEA": ["UK", "Germany", "Netherlands"],
    "emea": ["UK", "Germany", "Netherlands"],
    "APAC": ["Australia", "Singapore", "India"],
    "apac": ["Australia", "Singapore", "India"]
}
industries = ["SaaS", "Retail", "Fintech", "Healthcare", "Education", "Manufacturing", None]
channels = ["Organic", "Paid Search", "Partner", "Outbound", "Referral", "paid search", "REFERRAL"]
plans = {
    "Basic": 250,
    "Growth": 700,
    "Pro": 1500,
    "Enterprise": 4000,
    "enterprise ": 4000
}
billing_freqs = ["Monthly", "Annual", "monthly", "annual"]

# ----------------------------
# 1) Customer master
# ----------------------------
customers = []
for i in range(1, n_customers + 1):
    region = np.random.choice(regions)
    country = np.random.choice(countries[region])
    plan = np.random.choice(list(plans.keys()), p=[0.28, 0.34, 0.23, 0.10, 0.05])
    billing_frequency = np.random.choice(billing_freqs, p=[0.45, 0.20, 0.25, 0.10])

    signup_date = fake.date_between(start_date="-2y", end_date="-2m")
    status = np.random.choice(
        ["Active", "Churned", "active", "ACTIVE", "Paused", " paused ", None],
        p=[0.38, 0.12, 0.18, 0.14, 0.08, 0.05, 0.05]
    )

    customer_name = fake.company()
    if np.random.rand() < 0.15:
        customer_name = customer_name + "  "
    if np.random.rand() < 0.08:
        customer_name = customer_name.lower()

    customer_id = f"CUST{i:04d}"
    if np.random.rand() < 0.08:
        customer_id = customer_id + " "

    row = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "industry": np.random.choice(industries),
        "region": region,
        "country": country if np.random.rand() > 0.04 else None,
        "signup_date": signup_date if np.random.rand() > 0.03 else None,
        "acquisition_channel": np.random.choice(channels),
        "account_status": status,
        "plan_name": plan if np.random.rand() > 0.03 else None,
        "billing_frequency": billing_frequency
    }
    customers.append(row)

df_customers = pd.DataFrame(customers)

# Exact duplicate
df_customers = pd.concat([df_customers, df_customers.iloc[[5]]], ignore_index=True)

# Near-duplicate same customer with changed name/casing
dupe_row = df_customers.iloc[12].copy()
dupe_row["customer_name"] = str(dupe_row["customer_name"]).strip().upper()
df_customers = pd.concat([df_customers, pd.DataFrame([dupe_row])], ignore_index=True)

# Force some obvious nulls
df_customers.loc[10, "industry"] = None
df_customers.loc[25, "country"] = None
df_customers.loc[30, "account_status"] = "ACTIVE "

df_customers.to_csv(f"{BASE_PATH}/raw_customers.csv", index=False)

# ----------------------------
# 2) Subscriptions
# ----------------------------
subscriptions = []
sub_id = 1

base_customers = df_customers.drop_duplicates(subset=["customer_id"]).copy()

for _, row in base_customers.iterrows():
    raw_plan = str(row["plan_name"]).strip() if pd.notna(row["plan_name"]) else None

    if raw_plan in plans:
        base_mrr = plans[raw_plan]
    else:
        base_mrr = np.random.choice([250, 700, 1500, 4000])

    start_date = pd.to_datetime(row["signup_date"], errors="coerce")
    if pd.isna(start_date):
        start_date = pd.Timestamp("2023-06-01") + pd.Timedelta(days=int(np.random.randint(0, 180)))

    mrr = round(base_mrr * np.random.uniform(0.85, 1.25), 2)

    if np.random.rand() < 0.03:
        mrr = -abs(mrr)  # bad ERP-style row

    arr = round(mrr * 12 * np.random.uniform(0.95, 1.05), 2)

    status = np.random.choice(
        ["active", "cancelled", "Active", "Paused", "paused ", "CANCELLED", None],
        p=[0.42, 0.14, 0.18, 0.10, 0.06, 0.06, 0.04]
    )

    end_date = None
    if str(status).strip().lower() in ["cancelled", "cancelled", "cancelled"]:
        end_date = start_date + timedelta(days=int(np.random.uniform(120, 540)))

    # Introduce some invalid end dates
    if np.random.rand() < 0.03:
        end_date = start_date - timedelta(days=int(np.random.uniform(10, 90)))

    subscription_id = f"SUB{sub_id:05d}"
    if np.random.rand() < 0.03:
        subscription_id = subscription_id + " "

    subscriptions.append({
        "subscription_id": subscription_id,
        "customer_id": row["customer_id"],
        "start_date": start_date,
        "end_date": end_date,
        "plan_name": row["plan_name"],
        "mrr": mrr,
        "arr": arr,
        "subscription_status": status,
        "discount_pct": np.random.choice([0, 0, 5, 10, 15, 20, None]),
        "currency": np.random.choice(
            ["USD", "usd", "Usd", "US$", "CAD", "cad", None],
            p=[0.36, 0.10, 0.08, 0.06, 0.28, 0.08, 0.04]
        )
    })
    sub_id += 1

df_subscriptions = pd.DataFrame(subscriptions)

# Exact duplicate
df_subscriptions = pd.concat([df_subscriptions, df_subscriptions.iloc[[7]]], ignore_index=True)

# Duplicate ID with slightly different fields
dup_sub = df_subscriptions.iloc[15].copy()
dup_sub["mrr"] = dup_sub["mrr"] * 1.1 if pd.notna(dup_sub["mrr"]) else dup_sub["mrr"]
df_subscriptions = pd.concat([df_subscriptions, pd.DataFrame([dup_sub])], ignore_index=True)

df_subscriptions.to_csv(f"{BASE_PATH}/raw_subscriptions.csv", index=False)

# ----------------------------
# 3) Invoices
# ----------------------------
invoices = []
invoice_id = 1

for _, sub in df_subscriptions.drop_duplicates(subset=["subscription_id"]).iterrows():
    start = pd.to_datetime(sub["start_date"], errors="coerce")
    if pd.isna(start):
        continue

    end = pd.to_datetime(sub["end_date"], errors="coerce")
    if pd.isna(end):
        end = pd.Timestamp("2024-12-31")

    # protect against invalid ranges
    if end < start:
        active_months = [start]
    else:
        active_months = pd.date_range(start=start, end=end, freq="MS")

    for month in active_months:
        discount = sub["discount_pct"] if pd.notna(sub["discount_pct"]) else 0
        raw_amount = sub["mrr"] if pd.notna(sub["mrr"]) else 0
        amount = round(raw_amount * (1 - discount / 100), 2)

        # Some credit notes / reversals
        if np.random.rand() < 0.04:
            amount = -abs(amount)

        tax = round(amount * 0.05, 2)
        total = round(amount + tax, 2)

        # Introduce math mismatches
        if np.random.rand() < 0.05:
            total = round(total + np.random.uniform(-25, 25), 2)

        due_date = month + pd.Timedelta(days=30)
        if np.random.rand() < 0.03:
            due_date = month - pd.Timedelta(days=int(np.random.randint(1, 15)))

        invoice_status = np.random.choice(
            ["Paid", "paid", "Open", "Overdue", "VOID", "void ", None],
            p=[0.42, 0.14, 0.22, 0.10, 0.05, 0.03, 0.04]
        )

        invoices.append({
            "invoice_id": f"INV{invoice_id:06d}",
            "customer_id": sub["customer_id"],
            "subscription_id": sub["subscription_id"],
            "invoice_date": month,
            "due_date": due_date if np.random.rand() > 0.02 else None,
            "amount": amount,
            "tax": tax,
            "total_amount": total,
            "invoice_status": invoice_status
        })
        invoice_id += 1

df_invoices = pd.DataFrame(invoices)

# Exact duplicate row
df_invoices = pd.concat([df_invoices, df_invoices.iloc[[3]]], ignore_index=True)

# Duplicate invoice_id with different totals
dup_inv = df_invoices.iloc[25].copy()
dup_inv["total_amount"] = dup_inv["total_amount"] + 12.34
df_invoices = pd.concat([df_invoices, pd.DataFrame([dup_inv])], ignore_index=True)

df_invoices.to_csv(f"{BASE_PATH}/raw_invoices.csv", index=False)

# ----------------------------
# 4) GL transactions
# ----------------------------
gl_rows = []
gl_id = 1

expense_accounts = [
    ("5000", "Cost of Service"),
    ("5000", "cost of service"),
    ("6100", "Sales and Marketing"),
    ("6100", "sales & marketing"),
    ("6100", "S&M"),
    ("6200", "Research and Development"),
    ("6200", "R&D"),
    ("6300", "General and Administrative"),
    ("6300", "G&A"),
    ("1010", "Cash"),
    ("9999", "Misc Expense")
]

departments = ["Sales", "Marketing", "Engineering", "Finance", "Operations", None, ""]
cost_centers = ["CC100", "CC200", "CC300", "CC400", None, ""]
entities = ["SaaS HoldCo", "SaaS Canada", "SaaS US", "saas us"]

for month in months:
    for _ in range(90):
        acct = expense_accounts[np.random.randint(0, len(expense_accounts))]
        amount = round(np.random.uniform(1000, 25000), 2)

        dr_cr = np.random.choice(["DR", "CR", "dr", "cr", None], p=[0.48, 0.24, 0.12, 0.10, 0.06])

        if str(dr_cr).upper() == "CR":
            signed_amount = -amount
        elif str(dr_cr).upper() == "DR":
            signed_amount = amount
        else:
            signed_amount = amount if np.random.rand() > 0.5 else -amount

        # sign inconsistency on some rows
        if np.random.rand() < 0.03:
            signed_amount = -signed_amount

        gl_rows.append({
            "gl_txn_id": f"GL{gl_id:07d}",
            "txn_date": month + pd.Timedelta(days=int(np.random.randint(0, 27))),
            "account_code": acct[0] if np.random.rand() > 0.03 else None,
            "account_name": acct[1],
            "department": np.random.choice(departments),
            "cost_center": np.random.choice(cost_centers),
            "vendor_customer": fake.company() if np.random.rand() > 0.02 else None,
            "amount": signed_amount,
            "dr_cr": dr_cr,
            "entity": np.random.choice(entities),
            "memo": np.random.choice([
                "AWS hosting",
                "Payroll",
                "Google Ads",
                "Software tools",
                "Contractor costs",
                "Refund",
                "Reclass",
                None
            ])
        })
        gl_id += 1

df_gl = pd.DataFrame(gl_rows)

# Duplicate transaction
df_gl = pd.concat([df_gl, df_gl.iloc[[10]]], ignore_index=True)

df_gl.to_csv(f"{BASE_PATH}/raw_gl_transactions.csv", index=False)

# ----------------------------
# 5) Sales & marketing
# ----------------------------
sm_rows = []
for month in months:
    for channel in ["Paid Search", "LinkedIn", "Partner", "Outbound", "Organic", "paid search", "PARTNER"]:
        spend = np.random.uniform(5000, 30000) if "organic" not in channel.lower() else np.random.uniform(300, 3000)
        won_customers = np.random.randint(5, 40) if "organic" not in channel.lower() else np.random.randint(8, 30)

        if np.random.rand() < 0.05:
            won_customers = 0
        if np.random.rand() < 0.02:
            won_customers = -abs(won_customers)
        if np.random.rand() < 0.04:
            spend = -abs(spend)

        sm_rows.append({
            "period": month if np.random.rand() > 0.02 else None,
            "channel": channel,
            "campaign_name": f"{channel} Campaign {month.strftime('%Y-%m')}" if np.random.rand() > 0.05 else None,
            "spend": round(spend, 2),
            "leads": np.random.randint(50, 500) if np.random.rand() > 0.03 else None,
            "won_customers": won_customers
        })

df_sm = pd.DataFrame(sm_rows)

# Duplicate row
df_sm = pd.concat([df_sm, df_sm.iloc[[5]]], ignore_index=True)

df_sm.to_csv(f"{BASE_PATH}/raw_sales_marketing.csv", index=False)

# ----------------------------
# 6) Cash balances
# ----------------------------
cash_rows = []
cash_bal = 2500000

for month in months:
    beginning = cash_bal
    movement = np.random.uniform(-180000, 120000)
    ending = beginning + movement
    cash_bal = ending

    row = {
        "period": month,
        "entity": np.random.choice(["SaaS HoldCo", "saas holdco", "SaaS HoldCo "], p=[0.7, 0.15, 0.15]),
        "beginning_cash": round(beginning, 2),
        "ending_cash": round(ending, 2) if np.random.rand() > 0.04 else None
    }
    cash_rows.append(row)

df_cash = pd.DataFrame(cash_rows)

# Duplicate period/entity-ish row
cash_dup = df_cash.iloc[4].copy()
cash_dup["ending_cash"] = cash_dup["ending_cash"] + 5000 if pd.notna(cash_dup["ending_cash"]) else cash_dup["ending_cash"]
df_cash = pd.concat([df_cash, pd.DataFrame([cash_dup])], ignore_index=True)

df_cash.to_csv(f"{BASE_PATH}/raw_cash_balance.csv", index=False)

print("Messier raw ERP-style data generated in data/raw/")
print("Files created:")
print("- raw_customers.csv")
print("- raw_subscriptions.csv")
print("- raw_invoices.csv")
print("- raw_gl_transactions.csv")
print("- raw_sales_marketing.csv")
print("- raw_cash_balance.csv")