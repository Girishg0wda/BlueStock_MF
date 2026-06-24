"""
day2_pipeline.py
Bluestock MF Analytics — Day 2
Cleans all datasets, loads into SQLite star schema.
"""

import pandas as pd
import numpy as np
import warnings
import os
from sqlalchemy import create_engine, text

warnings.filterwarnings('ignore')

RAW  = 'data/raw'
PROC = 'data/processed'
DB   = 'bluestock_mf.db'

os.makedirs(PROC, exist_ok=True)

print("=" * 60)
print("  BLUESTOCK MF — DAY 2 PIPELINE")
print("=" * 60)

# ── 1. nav_history ────────────────────────────────────────────
print("\n[1/10] Cleaning nav_history...")
nav = pd.read_csv(f'{RAW}/nav_history.csv')
nav['date'] = pd.to_datetime(nav['date'])
nav = nav.sort_values(['amfi_code', 'date']).reset_index(drop=True)
nav['nav'] = nav.groupby('amfi_code')['nav'].transform(lambda x: x.ffill())
nav = nav.drop_duplicates(subset=['amfi_code', 'date'])
nav = nav[nav['nav'] > 0].dropna(subset=['nav'])
nav.to_csv(f'{PROC}/nav_history_clean.csv', index=False)
print(f"  ✅ nav_history_clean.csv → {nav.shape}")

# ── 2. investor_transactions ──────────────────────────────────
print("\n[2/10] Cleaning investor_transactions...")
txn = pd.read_csv(f'{RAW}/investor_transactions.csv')

def parse_date(d):
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return pd.to_datetime(d, format=fmt)
        except:
            pass
    return pd.NaT

txn['transaction_date'] = txn['transaction_date'].apply(parse_date)
txn['transaction_type'] = txn['transaction_type'].str.strip().str.title()
txn['transaction_type'] = txn['transaction_type'].replace({
    'Sip': 'SIP', 'Lumpsum': 'Lumpsum',
    'Redemption': 'Redemption', 'Switch': 'Switch', 'Dividend': 'Dividend'
})
txn = txn[txn['amount'] > 0]
valid_kyc = {'KYC_VERIFIED', 'KYC_PENDING', 'NOT_KYC', 'KYC_REJECTED'}
txn['kyc_status'] = txn['kyc_status'].str.upper()
txn = txn[txn['kyc_status'].isin(valid_kyc)]
txn.to_csv(f'{PROC}/investor_transactions_clean.csv', index=False)
print(f"  ✅ investor_transactions_clean.csv → {txn.shape}")

# ── 3. scheme_performance ─────────────────────────────────────
print("\n[3/10] Cleaning scheme_performance...")
perf = pd.read_csv(f'{RAW}/scheme_performance.csv')
ret_cols = ['return_1m', 'return_3m', 'return_6m', 'return_1y', 'return_3y', 'return_5y']
for c in ret_cols:
    perf[c] = pd.to_numeric(perf[c], errors='coerce')
perf['expense_ratio_flag'] = perf['expense_ratio'].apply(
    lambda x: 'ANOMALY' if x > 2.5 else 'OK'
)
anomalies = perf[perf['expense_ratio_flag'] == 'ANOMALY']
print(f"  ⚠  Expense ratio anomalies (>2.5%): {len(anomalies)}")
perf.to_csv(f'{PROC}/scheme_performance_clean.csv', index=False)
print(f"  ✅ scheme_performance_clean.csv → {perf.shape}")

# ── 4–10. Remaining datasets ──────────────────────────────────
simple_datasets = [
    'fund_master',
    'aum_history',
    'investor_portfolio',
    'sip_register',
    'investor_master',
    'benchmark_index',
    'dividend_history',
]

for i, name in enumerate(simple_datasets, start=4):
    print(f"\n[{i}/10] Cleaning {name}...")
    df = pd.read_csv(f'{RAW}/{name}.csv')

    # Parse any date-like columns
    date_cols = [c for c in df.columns if 'date' in c.lower() or 'month' in c.lower()]
    for dc in date_cols:
        try:
            df[dc] = pd.to_datetime(df[dc])
        except:
            pass

    # Standardise kyc_status in investor_master
    if name == 'investor_master':
        df['kyc_status'] = df['kyc_status'].str.upper()

    df.to_csv(f'{PROC}/{name}_clean.csv', index=False)
    print(f"  ✅ {name}_clean.csv → {df.shape}")

# ── Load into SQLite ──────────────────────────────────────────
print("\n" + "=" * 60)
print("  LOADING INTO SQLITE: bluestock_mf.db")
print("=" * 60)

engine = create_engine(f'sqlite:///{DB}')

# Apply schema DDL
with engine.connect() as conn:
    with open('sql/schema.sql') as f:
        for stmt in f.read().split(';'):
            s = stmt.strip()
            if s:
                try:
                    conn.execute(text(s))
                except Exception as e:
                    pass  # table may already exist
    conn.commit()

def load_table(table_name, csv_file):
    df = pd.read_csv(f'{PROC}/{csv_file}')
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"  ✅ {table_name:<25} {len(df):>6,} rows")
    return len(df)

load_table('dim_fund',          'fund_master_clean.csv')
load_table('dim_investor',      'investor_master_clean.csv')
load_table('fact_nav',          'nav_history_clean.csv')
load_table('fact_transactions', 'investor_transactions_clean.csv')
load_table('fact_performance',  'scheme_performance_clean.csv')
load_table('fact_aum',          'aum_history_clean.csv')

# Verify row counts
print("\n  Verification:")
with engine.connect() as conn:
    for t in ['dim_fund', 'dim_investor', 'fact_nav', 'fact_transactions', 'fact_performance', 'fact_aum']:
        n = conn.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar()
        print(f"  ✅ {t:<25} {n:>6,} rows in DB")

print("\n" + "=" * 60)
print("  Day 2 complete!")
print(f"  DB saved → {DB}")
print(f"  Cleaned CSVs → {PROC}/")
print("=" * 60)