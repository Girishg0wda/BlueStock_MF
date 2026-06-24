# Data Dictionary — Bluestock Mutual Fund Analytics

**Project:** Bluestock MF Analytics Platform  
**Version:** 1.0  
**Last Updated:** 2024-12-31  
**Database:** `bluestock_mf.db` (SQLite)

---

## Table of Contents

1. [dim_fund](#dim_fund)
2. [dim_investor](#dim_investor)
3. [fact_nav](#fact_nav)
4. [fact_transactions](#fact_transactions)
5. [fact_performance](#fact_performance)
6. [fact_aum](#fact_aum)
7. [Supporting CSVs](#supporting-csvs)
8. [Source References](#source-references)

---

## dim_fund

**Description:** Master dimension table for all mutual fund schemes registered with AMFI.  
**Source:** `data/processed/fund_master_clean.csv`  
**Grain:** One row per AMFI scheme code.

| Column | Data Type | Nullable | Business Definition |
|---|---|---|---|
| `amfi_code` | INTEGER (PK) | No | Unique 6-digit numeric code assigned by AMFI (Association of Mutual Funds in India) to every registered scheme. Codes are sequential and publicly available on amfiindia.com. |
| `scheme_name` | TEXT | No | Full official scheme name as registered with AMFI, including plan type (Direct/Regular). |
| `fund_house` | TEXT | No | Asset Management Company (AMC) that manages the fund. E.g., HDFC, SBI, ICICI Prudential. |
| `category` | TEXT | No | SEBI-mandated broad category: Equity, Debt, Hybrid, Solution Oriented, Other. |
| `sub_category` | TEXT | Yes | SEBI-defined sub-category within the category. E.g., Large Cap, Liquid, ELSS. |
| `risk_grade` | TEXT | Yes | Riskometer grade as mandated by SEBI: Low / Moderately Low / Moderate / Moderately High / High / Very High. |
| `launch_date` | TEXT | Yes | Date the scheme was launched and open for subscription (YYYY-MM-DD). |
| `benchmark` | TEXT | Yes | Index against which the fund's performance is measured. E.g., Nifty 50, BSE Sensex. |
| `exit_load_pct` | REAL | Yes | Percentage charged on redemption before the exit load period. Range: 0.0–2.0. |
| `min_sip_amount` | REAL | Yes | Minimum amount (INR) for a Systematic Investment Plan instalment. Typically ₹500. |
| `min_lumpsum` | REAL | Yes | Minimum one-time investment amount (INR). Typically ₹5,000. |

---

## dim_investor

**Description:** Master dimension for retail investors registered with the platform.  
**Source:** `data/processed/investor_master_clean.csv`  
**Grain:** One row per investor (unique PAN).

| Column | Data Type | Nullable | Business Definition |
|---|---|---|---|
| `investor_id` | TEXT (PK) | No | Internal platform identifier. Format: INV00001–INV99999. |
| `name` | TEXT | Yes | Full name of the investor. |
| `pan` | TEXT | Yes | Permanent Account Number — mandatory for MF investments above ₹50,000. Format: AAAAA9999A. |
| `email` | TEXT | Yes | Registered email for communication and account statements. |
| `mobile` | TEXT | Yes | 10-digit mobile number linked to the investor account. |
| `state` | TEXT | Yes | Indian state of the investor's registered address. |
| `city` | TEXT | Yes | City of the investor's registered address. |
| `dob` | TEXT | Yes | Date of birth (YYYY-MM-DD). Used for minor account checks and age-based eligibility. |
| `kyc_status` | TEXT | Yes | KYC compliance status. Enum: KYC_VERIFIED, KYC_PENDING, NOT_KYC, KYC_REJECTED. Only KYC_VERIFIED investors can transact above ₹50,000. |
| `risk_profile` | TEXT | Yes | Investor's self-declared risk appetite. Enum: Conservative, Moderate, Aggressive. |
| `registration_date` | TEXT | Yes | Date the investor registered on the platform (YYYY-MM-DD). |

---

## fact_nav

**Description:** Daily Net Asset Value (NAV) history for all tracked schemes.  
**Source:** `data/processed/nav_history_clean.csv`  
**Grain:** One row per (amfi_code, date). Business days only (forward-filled for weekends/holidays).

| Column | Data Type | Nullable | Business Definition |
|---|---|---|---|
| `nav_id` | INTEGER (PK) | No | Auto-incremented surrogate key. |
| `amfi_code` | INTEGER (FK) | No | References dim_fund. Identifies the mutual fund scheme. |
| `date` | TEXT | No | NAV declaration date (YYYY-MM-DD). AMFI publishes NAV every business day by 9 PM IST. |
| `nav` | REAL | No | Net Asset Value per unit in INR. Must be > 0. Calculated as (Total Assets − Liabilities) / Total Units. |

**Data Quality Notes:**
- Raw data had ~2% missing NAVs (weekends, public holidays). These were forward-filled with the last available NAV.
- Duplicate (amfi_code, date) pairs were removed (0 found post-cleaning).

---

## fact_transactions

**Description:** All investor buy, sell, and switch transactions across schemes.  
**Source:** `data/processed/investor_transactions_clean.csv`  
**Grain:** One row per transaction.

| Column | Data Type | Nullable | Business Definition |
|---|---|---|---|
| `transaction_id` | TEXT (PK) | No | Unique transaction reference. Format: TXN000001. |
| `investor_id` | TEXT (FK) | No | References dim_investor. |
| `amfi_code` | INTEGER (FK) | No | References dim_fund. The fund involved in the transaction. |
| `transaction_date` | TEXT | No | Date the transaction was processed (YYYY-MM-DD). Raw data had mixed formats (dd/mm/YYYY and YYYY-mm-dd) — standardised during cleaning. |
| `transaction_type` | TEXT | No | Enum: SIP (Systematic Investment Plan instalment), Lumpsum (one-time purchase), Redemption (withdrawal), Switch (move between schemes), Dividend (payout reinvestment). |
| `amount` | REAL | No | Transaction amount in INR. Must be > 0. Negative amounts (~3% in raw) were removed as invalid. |
| `units` | REAL | Yes | Number of units purchased or redeemed. Computed as amount / nav_at_transaction. |
| `nav_at_transaction` | REAL | Yes | The applicable NAV (INR/unit) at the time of transaction. |
| `state` | TEXT | Yes | Investor's state at time of transaction. |
| `kyc_status` | TEXT | Yes | KYC status at time of transaction. |

**Data Quality Notes:**
- Raw `transaction_type` had mixed case (sip, SIP, LUMPSUM). Standardised to Title Case with canonical enum mapping.
- Raw data had ~3% negative `amount` values — removed as invalid entries.
- Date format inconsistency resolved: mixed dd/MM/YYYY and YYYY-MM-DD unified to YYYY-MM-DD.

---

## fact_performance

**Description:** Point-in-time performance metrics for each scheme.  
**Source:** `data/processed/scheme_performance_clean.csv`  
**Grain:** One row per amfi_code (latest snapshot as of `as_of_date`).

| Column | Data Type | Nullable | Business Definition |
|---|---|---|---|
| `perf_id` | INTEGER (PK) | No | Auto-incremented surrogate key. |
| `amfi_code` | INTEGER (FK) | No | References dim_fund. |
| `return_1m` | REAL | Yes | Absolute return over the past 1 month (%). |
| `return_3m` | REAL | Yes | Absolute return over the past 3 months (%). |
| `return_6m` | REAL | Yes | Absolute return over the past 6 months (%). |
| `return_1y` | REAL | Yes | CAGR / absolute return over the past 1 year (%). |
| `return_3y` | REAL | Yes | CAGR over the past 3 years (%). |
| `return_5y` | REAL | Yes | CAGR over the past 5 years (%). |
| `alpha` | REAL | Yes | Jensen's Alpha — excess return over benchmark's expected return. Positive = outperformance. |
| `beta` | REAL | Yes | Sensitivity of fund returns to benchmark movement. Beta = 1 means fund moves in line with market. |
| `sharpe_ratio` | REAL | Yes | Risk-adjusted return = (Fund Return − Risk-free Rate) / Standard Deviation. Higher is better. |
| `expense_ratio` | REAL | Yes | Annual fee charged by the fund as a % of AUM. SEBI cap: 2.25% (equity), 2.0% (debt). |
| `expense_ratio_flag` | TEXT | Yes | 'ANOMALY' if expense_ratio > 2.5%, else 'OK'. Used for data quality monitoring. |
| `aum_cr` | REAL | Yes | Assets Under Management in Crore INR (1 Cr = 10 million INR). |
| `as_of_date` | TEXT | Yes | Snapshot date for this performance record (YYYY-MM-DD). |

**Data Quality Notes:**
- 1 record had expense_ratio > 2.5% (flagged as ANOMALY — possible data entry error or regulatory breach).

---

## fact_aum

**Description:** Monthly AUM and folio count per fund.  
**Source:** `data/processed/aum_history_clean.csv`  
**Grain:** One row per (amfi_code, month_end).

| Column | Data Type | Nullable | Business Definition |
|---|---|---|---|
| `aum_id` | INTEGER (PK) | No | Auto-incremented surrogate key. |
| `amfi_code` | INTEGER (FK) | No | References dim_fund. |
| `month_end` | TEXT | No | Last calendar day of the month (YYYY-MM-DD). AMFI publishes AUM data monthly. |
| `aum_cr` | REAL | No | Total AUM for the scheme in Crore INR at month end. |
| `folios` | INTEGER | Yes | Number of active investor folios (accounts) invested in the scheme. One investor can have multiple folios in the same scheme. |

---

## Supporting CSVs

These tables are loaded as CSVs and used for supplementary analysis but not loaded into the star schema:

### sip_register_clean.csv
Active and historical SIP mandates. Key columns: `sip_id`, `investor_id`, `amfi_code`, `sip_amount`, `frequency`, `sip_date` (day of month), `start_date`, `end_date`, `status` (Active/Paused/Cancelled).

### investor_portfolio_clean.csv
Current holdings per investor per scheme. Key columns: `investor_id`, `amfi_code`, `units_held`, `avg_purchase_nav`, `invested_amount`, `current_nav`. Used to compute unrealised P&L.

### benchmark_index_clean.csv
Daily index levels for Nifty 50, Nifty 100, Sensex, Nifty Midcap, Nifty Smallcap. Used for alpha/beta calculations and relative performance analysis.

### dividend_history_clean.csv
Historical dividend payouts per scheme. Key columns: `amfi_code`, `dividend_date`, `dividend_per_unit`, `record_date`, `dividend_type` (Interim/Final).

### live_nav_data.csv
Real-time NAV data fetched from mfapi.in for 6 key schemes. Refreshed daily via `live_nav_fetch.py`.

---

## Source References

| Source | Description | URL |
|---|---|---|
| AMFI India | Official AMFI NAV and scheme data | https://www.amfiindia.com |
| mfapi.in | Unofficial free API for historical MF NAV | https://api.mfapi.in |
| SEBI | Regulations on expense ratios, categories | https://www.sebi.gov.in |
| NSE India | Benchmark index data (Nifty series) | https://www.nseindia.com |

---

*Generated by Bluestock MF Analytics Pipeline · Day 2*
