-- ============================================================
-- schema.sql
-- Bluestock MF Analytics — SQLite Star Schema
-- ============================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────────────────────────
-- DIMENSION TABLES
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code       INTEGER PRIMARY KEY,
    scheme_name     TEXT    NOT NULL,
    fund_house      TEXT    NOT NULL,
    category        TEXT    NOT NULL,
    sub_category    TEXT,
    risk_grade      TEXT,
    launch_date     TEXT,
    benchmark       TEXT,
    exit_load_pct   REAL    DEFAULT 0,
    min_sip_amount  REAL    DEFAULT 500,
    min_lumpsum     REAL    DEFAULT 5000
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER PRIMARY KEY,   -- YYYYMMDD integer key
    full_date       TEXT    NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT    NOT NULL,
    week            INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,
    day_name        TEXT    NOT NULL,
    is_weekend      INTEGER NOT NULL DEFAULT 0,
    is_month_end    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dim_investor (
    investor_id         TEXT    PRIMARY KEY,
    name                TEXT,
    pan                 TEXT    UNIQUE,
    email               TEXT,
    mobile              TEXT,
    state               TEXT,
    city                TEXT,
    dob                 TEXT,
    kyc_status          TEXT    CHECK(kyc_status IN ('KYC_VERIFIED','KYC_PENDING','NOT_KYC','KYC_REJECTED')),
    risk_profile        TEXT    CHECK(risk_profile IN ('Conservative','Moderate','Aggressive')),
    registration_date   TEXT
);

-- ────────────────────────────────────────────────────────────
-- FACT TABLES
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL,
    date        TEXT    NOT NULL,
    nav         REAL    NOT NULL CHECK(nav > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    UNIQUE (amfi_code, date)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id          TEXT    PRIMARY KEY,
    investor_id             TEXT    NOT NULL,
    amfi_code               INTEGER NOT NULL,
    transaction_date        TEXT    NOT NULL,
    transaction_type        TEXT    NOT NULL CHECK(transaction_type IN ('SIP','Lumpsum','Redemption','Switch','Dividend')),
    amount                  REAL    NOT NULL CHECK(amount > 0),
    units                   REAL,
    nav_at_transaction      REAL,
    state                   TEXT,
    kyc_status              TEXT,
    FOREIGN KEY (amfi_code)   REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (investor_id) REFERENCES dim_investor(investor_id)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,
    return_1m       REAL,
    return_3m       REAL,
    return_6m       REAL,
    return_1y       REAL,
    return_3y       REAL,
    return_5y       REAL,
    alpha           REAL,
    beta            REAL,
    sharpe_ratio    REAL,
    expense_ratio   REAL,
    expense_ratio_flag TEXT DEFAULT 'OK',
    aum_cr          REAL,
    as_of_date      TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL,
    month_end   TEXT    NOT NULL,
    aum_cr      REAL    NOT NULL,
    folios      INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    UNIQUE (amfi_code, month_end)
);

-- ────────────────────────────────────────────────────────────
-- INDEXES
-- ────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi     ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date     ON fact_nav(date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi     ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date     ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_inv      ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_fact_aum_amfi     ON fact_aum(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_aum_month    ON fact_aum(month_end);
