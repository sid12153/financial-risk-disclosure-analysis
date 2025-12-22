import pandas as pd
from pathlib import Path

clean_path = Path("./transactions_clean.csv")
df = pd.read_csv(clean_path)

# ----------------------------
# Rule enforcement checks
# ----------------------------

# 1) No cancelled invoices
cancelled_count = df["Invoice"].astype(str).str.startswith("C", na=False).sum()

# 2) Quantity strictly positive
bad_qty = (df["Quantity"] <= 0).sum()

# 3) Price strictly positive
bad_price = (df["Price"] <= 0).sum()

# 4) Customer ID missing
missing_cust = df["Customer ID"].isna().sum()

print("Cancelled invoices:", cancelled_count)
print("Quantity <= 0:", bad_qty)
print("Price <= 0:", bad_price)
print("Missing Customer ID:", missing_cust)

# ----------------------------
# Date sanity checks
# ----------------------------

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
print("Unparsed InvoiceDate:", df["InvoiceDate"].isna().sum())
print("Date range:", df["InvoiceDate"].min(), "to", df["InvoiceDate"].max())

# ----------------------------
# Duplicate analysis (DO NOT DROP HERE)
# ----------------------------

# A) Exact full-row duplicates (safe to drop in cleaning if needed)
exact_dup_count = df.duplicated().sum()
print("Exact full-row duplicates:", exact_dup_count)

# B) Business-key duplicates (for awareness only)
business_key_cols = ["Invoice", "StockCode", "InvoiceDate"]
business_key_dup = df.duplicated(subset=business_key_cols).sum()
print("Duplicates by Invoice + StockCode + InvoiceDate:", business_key_dup)
print("Rows after dropping exact duplicates:", len(df))

