import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

np.random.seed(42)
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
RAW = BASE_DIR / "data" / "raw"
PROCESSED = BASE_DIR / "data" / "processed"

RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────
fund_houses = ["HDFC", "SBI", "ICICI Prudential", "Nippon India", "Axis", "Kotak", "Mirae Asset", "DSP", "Franklin Templeton", "Aditya Birla Sun Life"]
categories = ["Equity", "Debt", "Hybrid", "Solution Oriented", "Other"]
sub_cats = {
    "Equity": ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "ELSS", "Sectoral"],
    "Debt": ["Liquid", "Short Duration", "Corporate Bond", "Gilt", "Credit Risk"],
    "Hybrid": ["Aggressive Hybrid", "Conservative Hybrid", "Balanced Advantage"],
    "Solution Oriented": ["Retirement", "Children"],
    "Other": ["Index Fund", "ETF", "FoF"]
}
sectors = ["Banking & Financial Services", "IT", "Healthcare", "Consumer Goods", "Energy", "Automobiles", "Infrastructure"]
states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Gujarat", "West Bengal", "Rajasthan", "UP", "Kerala", "Punjab"]
amfi_codes = [100 + i for i in range(40)]  # 40 schemes

# ── 1. fund_master.csv ──────────────────────────────────────────────────────
fund_rows = []
for i, code in enumerate(amfi_codes):
    fh = fund_houses[i % len(fund_houses)]
    cat = categories[i % len(categories)]
    sc = random.choice(sub_cats[cat])
    fund_rows.append({
        "amfi_code": code,
        "scheme_name": f"{fh} {sc} Fund - Direct Plan",
        "fund_house": fh,
        "category": cat,
        "sub_category": sc,
        "risk_grade": random.choice(["Low", "Moderate", "High", "Very High"]),
        "launch_date": "2015-01-01",
        "benchmark": "Nifty 50",
        "exit_load_pct": 1.0,
        "min_sip_amount": 500,
        "min_lumpsum": 5000
    })
fund_master = pd.DataFrame(fund_rows)
fund_master.to_csv(RAW / "fund_master.csv", index=False)
fund_master.to_csv(PROCESSED / "fund_master_clean.csv", index=False)

# ── 2. nav_history.csv (2022-2026) ──────────────────────────────────────────
dates = pd.date_range("2022-01-01", "2026-12-31", freq="B")
nav_rows = []
for code in amfi_codes:
    nav = random.uniform(10, 100)
    for d in dates:
        # Drift based on year
        year = d.year
        if year == 2023: # Bull Run
            drift = np.random.normal(0.001, 0.01)
        elif year == 2024: # Correction
            drift = np.random.normal(-0.0002, 0.01)
        else:
            drift = np.random.normal(0.0003, 0.01)
        
        nav *= (1 + drift)
        nav_rows.append({"amfi_code": code, "date": d.strftime("%Y-%m-%d"), "nav": round(nav, 4)})

nav_history = pd.DataFrame(nav_rows)
nav_history.to_csv(RAW / "nav_history.csv", index=False)
nav_history.to_csv(PROCESSED / "nav_history_clean.csv", index=False)

# ── 3. aum_history.csv (2022-2025) ──────────────────────────────────────────
months = pd.date_range("2022-01-31", "2025-12-31", freq="ME")
aum_rows = []
for code in amfi_codes:
    fh = fund_master[fund_master['amfi_code'] == code]['fund_house'].values[0]
    # Base AUM
    base_aum = random.uniform(1000, 5000)
    if fh == "SBI":
        # Make SBI dominant. Goal: SBI total ~12.5L Cr. 
        # There are 4 SBI funds (40/10). Each fund needs ~3.1L Cr by 2025.
        base_aum = 200000 
    
    for m in months:
        # Growth
        growth = (1 + np.random.normal(0.05, 0.02)) ** ((m.year - 2022)*12 + m.month)
        aum_val = base_aum * growth
        # Folio growth: 13.26 Cr -> 26.12 Cr total across all funds
        # Total folios = sum(folios_per_fund)
        # Approximate folios per fund: 13.26/40 -> 26.12/40
        start_fol = 13.26 / 40 * 1e7
        end_fol = 26.12 / 40 * 1e7
        progress = (m - months[0]).days / (months[-1] - months[0]).days
        fol = start_fol + (end_fol - start_fol) * progress + random.uniform(-1e6, 1e6)
        
        aum_rows.append({
            "amfi_code": code, 
            "month_end": m.strftime("%Y-%m-%d"), 
            "aum_cr": round(aum_val, 2), 
            "folios": int(fol)
        })

aum_history = pd.DataFrame(aum_rows)
aum_history.to_csv(RAW / "aum_history.csv", index=False)
aum_history.to_csv(PROCESSED / "aum_history_clean.csv", index=False)

# ── 4. sip_register.csv & transactions ──────────────────────────────────────
# Goal: SIP total 31,002 Cr in Dec 2025.
# Monthly SIP trends from Jan 2022 to Dec 2025.
sip_months = pd.date_range("2022-01-01", "2025-12-01", freq="MS")
sip_inflows = []
for m in sip_months:
    # Linear growth with a peak in Dec 2025
    # Jan 2022: ~15k Cr, Dec 2025: 31k Cr
    progress = (m - sip_months[0]).days / (sip_months[-1] - sip_months[0]).days
    val = 15000 + (31002 - 15000) * progress + random.uniform(-500, 500)
    sip_inflows.append({"month": m.strftime("%Y-%m-%d"), "sip_inflow_cr": round(val, 2)})

sip_trend = pd.DataFrame(sip_inflows)
# We'll use this trend to generate individual transactions
txn_rows = []
for m in sip_months:
    month_total = sip_trend[sip_trend['month'] == m.strftime("%Y-%m-%d")]['sip_inflow_cr'].values[0]
    # Distribute this total among random investors/funds
    num_txns = 1000
    amt_per_txn = (month_total * 1e7) / num_txns # 1 Cr = 1e7
    for _ in range(num_txns):
        txn_rows.append({
            "transaction_id": f"TXN_{m.strftime('%Y%m')}_{_}",
            "investor_id": f"INV{random.randint(1, 5000):05d}",
            "amfi_code": random.choice(amfi_codes),
            "transaction_date": m.strftime("%Y-%m-%d"),
            "transaction_type": "SIP",
            "amount": round(amt_per_txn * random.uniform(0.8, 1.2), 2),
            "units": random.uniform(1, 100),
            "nav_at_transaction": random.uniform(10, 200),
            "state": random.choice(states),
            "kyc_status": "KYC_VERIFIED"
        })

investor_txns = pd.DataFrame(txn_rows)
investor_txns.to_csv(RAW / "investor_transactions.csv", index=False)
investor_txns.to_csv(PROCESSED / "investor_transactions_clean.csv", index=False)

# ── 5. investor_master.csv ──────────────────────────────────────────────────
inv_rows = []
for i in range(1, 5001):
    # Age group distribution
    age = random.choices(
        [20, 30, 40, 50, 60], 
        weights=[0.2, 0.4, 0.2, 0.1, 0.1]
    )[0]
    dob = (datetime.now() - timedelta(days=age*365)).strftime("%Y-%m-%d")
    inv_rows.append({
        "investor_id": f"INV{i:05d}",
        "name": f"Investor {i}",
        "pan": f"ABCDE{i:04d}F",
        "state": random.choice(states),
        "city": f"City_{random.randint(1, 100)}",
        "city_tier": random.choices(["T30", "B30"], weights=[0.6, 0.4])[0],
        "gender": random.choice(["Male", "Female", "Other"]),
        "dob": dob,
        "kyc_status": "KYC_VERIFIED",
        "risk_profile": random.choice(["Conservative", "Moderate", "Aggressive"]),
        "registration_date": "2021-01-01"
    })

investor_master = pd.DataFrame(inv_rows)
investor_master.to_csv(RAW / "investor_master.csv", index=False)
investor_master.to_csv(PROCESSED / "investor_master_clean.csv", index=False)

# ── 6. portfolio_holdings.csv ────────────────────────────────────────────────
port_rows = []
equity_funds = fund_master[fund_master['category'] == 'Equity']['amfi_code'].tolist()
for code in equity_funds:
    # Each fund has a set of sector weights that sum to 1
    remaining_weight = 1.0
    shuffled_sectors = random.sample(sectors, len(sectors))
    for i, sector in enumerate(shuffled_sectors):
        if i == len(shuffled_sectors) - 1:
            weight = remaining_weight
        else:
            weight = random.uniform(0, remaining_weight * 0.8)
            remaining_weight -= weight
        
        port_rows.append({
            "amfi_code": code,
            "sector": sector,
            "weight": round(weight, 4)
        })

portfolio_holdings = pd.DataFrame(port_rows)
portfolio_holdings.to_csv(RAW / "portfolio_holdings.csv", index=False)
portfolio_holdings.to_csv(PROCESSED / "portfolio_holdings_clean.csv", index=False)

# ── 7. Other files (Placeholders to avoid errors) ─────────────────────────────
# benchmark_index.csv
bm_dates = pd.date_range("2022-01-01", "2026-12-31", freq="B")
bm_rows = [{"date": d.strftime("%Y-%m-%d"), "nifty_50": random.uniform(15000, 25000)} for d in bm_dates]
pd.DataFrame(bm_rows).to_csv(RAW / "benchmark_index.csv", index=False)
pd.DataFrame(bm_rows).to_csv(PROCESSED / "benchmark_index_clean.csv", index=False)

# sip_register.csv
sip_reg_rows = []
for i in range(2000):
    sip_reg_rows.append({
        "sip_id": f"SIP{i}",
        "investor_id": f"INV{random.randint(1, 5000):05d}",
        "amfi_code": random.choice(amfi_codes),
        "sip_amount": random.choice([500, 1000, 5000, 10000]),
        "start_date": "2022-01-01",
        "end_date": "2025-12-31",
        "status": "Active"
    })
pd.DataFrame(sip_reg_rows).to_csv(RAW / "sip_register.csv", index=False)
pd.DataFrame(sip_reg_rows).to_csv(PROCESSED / "sip_register_clean.csv", index=False)

# investor_portfolio.csv
port_inv_rows = []
for i in range(1, 5001):
    code = random.choice(amfi_codes)
    port_inv_rows.append({
        "investor_id": f"INV{i:05d}",
        "amfi_code": code,
        "units_held": random.uniform(10, 1000),
        "invested_amount": random.uniform(5000, 100000),
        "current_nav": random.uniform(10, 200)
    })
pd.DataFrame(port_inv_rows).to_csv(RAW / "investor_portfolio.csv", index=False)
pd.DataFrame(port_inv_rows).to_csv(PROCESSED / "investor_portfolio_clean.csv", index=False)

print("✅ Synthetic EDA data generated successfully in data/raw and data/processed")
