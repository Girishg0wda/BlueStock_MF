import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random, os

np.random.seed(42)
random.seed(42)
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW = BASE_DIR / "data" / "raw"

RAW.mkdir(parents=True, exist_ok=True)

# ── 1. fund_master.csv ──────────────────────────────────────────────────────
fund_houses = ["HDFC","SBI","ICICI Prudential","Nippon India","Axis","Kotak","Mirae Asset","DSP","Franklin Templeton","Aditya Birla Sun Life"]
categories  = ["Equity","Debt","Hybrid","Solution Oriented","Other"]
sub_cats    = {"Equity":["Large Cap","Mid Cap","Small Cap","Flexi Cap","ELSS","Sectoral"],
               "Debt":["Liquid","Short Duration","Corporate Bond","Gilt","Credit Risk"],
               "Hybrid":["Aggressive Hybrid","Conservative Hybrid","Balanced Advantage"],
               "Solution Oriented":["Retirement","Children"],
               "Other":["Index Fund","ETF","FoF"]}
risk_grades = ["Low","Moderately Low","Moderate","Moderately High","High","Very High"]

amfi_codes = [119551,120503,118632,119092,120841,125497,
              118825,118834,118835,118836,118837,118838,118839,118840,118841,118842,
              118843,118844,118845,118846,118847,118848,118849,118850,118851,118852,
              118853,118854,118855,118856,118857,118858,118859,118860,118861,118862,
              118863,118864,118865,118866,118867,118868,118869,118870,118871,118872,
              118873,118874,118875,118876]

rows = []
for i, code in enumerate(amfi_codes):
    fh  = fund_houses[i % len(fund_houses)]
    cat = categories[i % len(categories)]
    sc  = random.choice(sub_cats[cat])
    rg  = risk_grades[i % len(risk_grades)]
    rows.append({"amfi_code":code,"scheme_name":f"{fh} {sc} Fund - Direct Plan",
                 "fund_house":fh,"category":cat,"sub_category":sc,"risk_grade":rg,
                 "launch_date":(datetime(2010,1,1)+timedelta(days=i*120)).strftime("%Y-%m-%d"),
                 "benchmark":f"Nifty {50+i*10}","exit_load_pct":round(random.uniform(0,1),2),
                 "min_sip_amount":500,"min_lumpsum":5000})
fund_master = pd.DataFrame(rows)
fund_master.to_csv(RAW / "fund_master.csv", index=False)
print("fund_master:", fund_master.shape)

# ── 2. nav_history.csv ──────────────────────────────────────────────────────
dates = pd.date_range("2020-01-01","2024-12-31", freq="B")
nav_rows = []
for code in amfi_codes[:20]:   # 20 funds × ~1300 business days
    nav = round(random.uniform(10, 200), 4)
    for d in dates:
        nav = max(1, nav * (1 + np.random.normal(0.0003, 0.008)))
        if random.random() < 0.02:  # ~2% missing (holidays / data gap)
            nav_rows.append({"amfi_code":code,"date":d.strftime("%Y-%m-%d"),"nav":np.nan})
        else:
            nav_rows.append({"amfi_code":code,"date":d.strftime("%Y-%m-%d"),"nav":round(nav,4)})
nav_history = pd.DataFrame(nav_rows)
nav_history.to_csv(f"{RAW}/nav_history.csv", index=False)
print("nav_history:", nav_history.shape)

# ── 3. investor_transactions.csv ────────────────────────────────────────────
states = ["Maharashtra","Karnataka","Tamil Nadu","Delhi","Gujarat","West Bengal","Rajasthan","UP"]
txn_types = ["SIP","sip","Lumpsum","lumpsum","LUMPSUM","Redemption","redemption","Switch","Dividend"]
txn_rows = []
for i in range(5000):
    code = random.choice(amfi_codes[:20])
    txn_date = datetime(2020,1,1) + timedelta(days=random.randint(0,1826))
    amt = round(random.uniform(500, 500000), 2)
    if random.random() < 0.03: amt = -amt   # intentional anomaly
    txn_rows.append({"transaction_id":f"TXN{i+1:06d}",
                     "investor_id":f"INV{random.randint(1,500):05d}",
                     "amfi_code":code,
                     "transaction_date":txn_date.strftime("%d/%m/%Y") if i%3==0 else txn_date.strftime("%Y-%m-%d"),
                     "transaction_type":random.choice(txn_types),
                     "amount":amt,
                     "units":round(amt/random.uniform(10,200),3),
                     "nav_at_transaction":round(random.uniform(10,300),4),
                     "state":random.choice(states),
                     "kyc_status":random.choice(["KYC_VERIFIED","KYC_PENDING","kyc_verified","NOT_KYC","KYC_REJECTED"])})
investor_txn = pd.DataFrame(txn_rows)
investor_txn.to_csv(f"{RAW}/investor_transactions.csv", index=False)
print("investor_transactions:", investor_txn.shape)

# ── 4. scheme_performance.csv ───────────────────────────────────────────────
perf_rows = []
for code in amfi_codes[:20]:
    perf_rows.append({"amfi_code":code,
                      "return_1m":round(random.uniform(-5,8),2),
                      "return_3m":round(random.uniform(-8,15),2),
                      "return_6m":round(random.uniform(-10,20),2),
                      "return_1y":round(random.uniform(-15,40),2),
                      "return_3y":round(random.uniform(5,25),2),
                      "return_5y":round(random.uniform(8,30),2),
                      "alpha":round(random.uniform(-2,5),2),
                      "beta":round(random.uniform(0.5,1.5),2),
                      "sharpe_ratio":round(random.uniform(0.1,2.5),2),
                      "expense_ratio":round(random.uniform(0.1,2.6),2),  # some >2.5 = anomaly
                      "aum_cr":round(random.uniform(100,50000),2),
                      "as_of_date":"2024-12-31"})
scheme_perf = pd.DataFrame(perf_rows)
scheme_perf.to_csv(f"{RAW}/scheme_performance.csv", index=False)
print("scheme_performance:", scheme_perf.shape)

# ── 5. aum_history.csv ──────────────────────────────────────────────────────
months = pd.date_range("2020-01-31","2024-12-31",freq="ME")
aum_rows = []
for code in amfi_codes[:20]:
    aum = round(random.uniform(500,50000),2)
    for m in months:
        aum = max(100, aum * (1 + np.random.normal(0.01,0.05)))
        aum_rows.append({"amfi_code":code,"month_end":m.strftime("%Y-%m-%d"),"aum_cr":round(aum,2),
                         "folios":random.randint(10000,5000000)})
aum_df = pd.DataFrame(aum_rows)
aum_df.to_csv(f"{RAW}/aum_history.csv", index=False)
print("aum_history:", aum_df.shape)

# ── 6. investor_portfolio.csv ───────────────────────────────────────────────
port_rows = []
for inv in [f"INV{i:05d}" for i in range(1,501)]:
    for code in random.sample(amfi_codes[:20], random.randint(1,5)):
        units = round(random.uniform(10,5000),3)
        avg_nav = round(random.uniform(10,300),4)
        port_rows.append({"investor_id":inv,"amfi_code":code,
                          "units_held":units,"avg_purchase_nav":avg_nav,
                          "invested_amount":round(units*avg_nav,2),
                          "current_nav":round(avg_nav*(1+random.uniform(-0.2,0.8)),4),
                          "as_of_date":"2024-12-31"})
portfolio = pd.DataFrame(port_rows)
portfolio.to_csv(f"{RAW}/investor_portfolio.csv", index=False)
print("investor_portfolio:", portfolio.shape)

# ── 7. sip_register.csv ─────────────────────────────────────────────────────
sip_rows = []
for i in range(2000):
    start = datetime(2020,1,1) + timedelta(days=random.randint(0,1095))
    end   = start + timedelta(days=random.randint(180,1825))
    sip_rows.append({"sip_id":f"SIP{i+1:06d}",
                     "investor_id":f"INV{random.randint(1,500):05d}",
                     "amfi_code":random.choice(amfi_codes[:20]),
                     "sip_amount":random.choice([500,1000,2000,5000,10000]),
                     "frequency":"Monthly","sip_date":random.randint(1,28),
                     "start_date":start.strftime("%Y-%m-%d"),
                     "end_date":end.strftime("%Y-%m-%d"),
                     "status":random.choice(["Active","Active","Active","Paused","Cancelled"])})
sip_df = pd.DataFrame(sip_rows)
sip_df.to_csv(f"{RAW}/sip_register.csv", index=False)
print("sip_register:", sip_df.shape)

# ── 8. investor_master.csv ───────────────────────────────────────────────────
inv_rows = []
for i in range(1,501):
    dob = datetime(1960,1,1) + timedelta(days=random.randint(0,14600))
    inv_rows.append({"investor_id":f"INV{i:05d}",
                     "name":f"Investor {i}","pan":f"ABCDE{i:04d}F",
                     "email":f"investor{i}@email.com","mobile":f"9{random.randint(100000000,999999999)}",
                     "state":random.choice(states),"city":f"City_{i%50}",
                     "dob":dob.strftime("%Y-%m-%d"),
                     "kyc_status":random.choice(["KYC_VERIFIED","KYC_VERIFIED","KYC_PENDING"]),
                     "risk_profile":random.choice(["Conservative","Moderate","Aggressive"]),
                     "registration_date":(datetime(2018,1,1)+timedelta(days=random.randint(0,1826))).strftime("%Y-%m-%d")})
inv_df = pd.DataFrame(inv_rows)
inv_df.to_csv(f"{RAW}/investor_master.csv", index=False)
print("investor_master:", inv_df.shape)

# ── 9. benchmark_index.csv ──────────────────────────────────────────────────
bm_rows = []
for d in dates:
    bm_rows.append({"date":d.strftime("%Y-%m-%d"),
                    "nifty_50":round(random.uniform(10000,24000),2),
                    "nifty_100":round(random.uniform(10000,25000),2),
                    "sensex":round(random.uniform(33000,80000),2),
                    "nifty_midcap":round(random.uniform(15000,55000),2),
                    "nifty_smallcap":round(random.uniform(5000,20000),2)})
bm_df = pd.DataFrame(bm_rows)
bm_df.to_csv(f"{RAW}/benchmark_index.csv", index=False)
print("benchmark_index:", bm_df.shape)

# ── 10. dividend_history.csv ─────────────────────────────────────────────────
div_rows = []
for i in range(300):
    code = random.choice(amfi_codes[:20])
    div_date = datetime(2020,1,1) + timedelta(days=random.randint(0,1826))
    div_rows.append({"amfi_code":code,
                     "dividend_date":div_date.strftime("%Y-%m-%d"),
                     "dividend_per_unit":round(random.uniform(0.1,5.0),2),
                     "record_date":(div_date-timedelta(days=2)).strftime("%Y-%m-%d"),
                     "dividend_type":random.choice(["Interim","Final"])})
div_df = pd.DataFrame(div_rows)
div_df.to_csv(f"{RAW}/dividend_history.csv", index=False)
print("dividend_history:", div_df.shape)

print("\n✅ All 10 CSV files generated in data/raw/")