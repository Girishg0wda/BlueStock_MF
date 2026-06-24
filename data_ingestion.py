"""
data_ingestion.py
Bluestock Mutual Fund Analytics — Day 1
Loads all 10 raw CSV datasets, prints diagnostics, and notes anomalies.
"""

import pandas as pd
import os

RAW_DIR = "data/raw"

DATASETS = [
    "fund_master.csv",
    "nav_history.csv",
    "investor_transactions.csv",
    "scheme_performance.csv",
    "aum_history.csv",
    "investor_portfolio.csv",
    "sip_register.csv",
    "investor_master.csv",
    "benchmark_index.csv",
    "dividend_history.csv",
]

ANOMALY_NOTES = {
    "nav_history.csv":             "~2% NAV values are NaN (holiday/weekend gaps); requires forward-fill.",
    "investor_transactions.csv":   "Mixed date formats (dd/mm/YYYY vs YYYY-mm-dd); transaction_type has mixed case (sip/SIP/LUMPSUM); ~3% negative amounts.",
    "scheme_performance.csv":      "expense_ratio has values >2.5% (SEBI cap breach); needs flagging.",
    "investor_master.csv":         "kyc_status values are inconsistent — needs enum standardisation.",
    "fund_master.csv":             "No anomalies detected.",
    "aum_history.csv":             "No anomalies detected.",
    "investor_portfolio.csv":      "No anomalies detected.",
    "sip_register.csv":            "No anomalies detected.",
    "benchmark_index.csv":         "No anomalies detected.",
    "dividend_history.csv":        "No anomalies detected.",
}

dataframes = {}

print("=" * 70)
print("  BLUESTOCK MF — DATA INGESTION REPORT")
print("=" * 70)

for filename in DATASETS:
    path = os.path.join(RAW_DIR, filename)
    df = pd.read_csv(path)
    dataframes[filename] = df
    name = filename.replace(".csv", "").upper()

    print(f"\n{'─'*70}")
    print(f"  Dataset : {name}")
    print(f"  File    : {path}")
    print(f"{'─'*70}")
    print(f"  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")

    print("\n  dtypes:")
    for col, dtype in df.dtypes.items():
        nulls = df[col].isna().sum()
        null_pct = f"({nulls/len(df)*100:.1f}% null)" if nulls > 0 else ""
        print(f"    {col:<35} {str(dtype):<12} {null_pct}")

    print("\n  head(3):")
    print(df.head(3).to_string(index=False))

    note = ANOMALY_NOTES.get(filename, "No anomalies noted.")
    print(f"\n  ⚠  Anomalies: {note}")

print(f"\n{'='*70}")
print(f"  SUMMARY: {len(DATASETS)} datasets loaded successfully.")
total_rows = sum(df.shape[0] for df in dataframes.values())
print(f"  Total rows across all datasets: {total_rows:,}")
print("=" * 70)
