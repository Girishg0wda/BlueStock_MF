-- ============================================================
-- queries.sql
-- Bluestock MF Analytics — 10 Analytical Queries
-- ============================================================

-- ── Q1: Top 5 funds by latest AUM ───────────────────────────────────────────
SELECT
    f.fund_house,
    f.scheme_name,
    f.category,
    a.aum_cr,
    a.folios
FROM fact_aum a
JOIN dim_fund f ON a.amfi_code = f.amfi_code
WHERE a.month_end = (SELECT MAX(month_end) FROM fact_aum)
ORDER BY a.aum_cr DESC
LIMIT 5;

-- ── Q2: Average NAV per month for top 5 schemes ─────────────────────────────
SELECT
    f.scheme_name,
    SUBSTR(n.date, 1, 7) AS year_month,
    ROUND(AVG(n.nav), 2) AS avg_nav,
    ROUND(MIN(n.nav), 2) AS min_nav,
    ROUND(MAX(n.nav), 2) AS max_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE n.amfi_code IN (
    SELECT amfi_code FROM fact_aum
    WHERE month_end = (SELECT MAX(month_end) FROM fact_aum)
    ORDER BY aum_cr DESC LIMIT 5
)
GROUP BY f.scheme_name, year_month
ORDER BY f.scheme_name, year_month;

-- ── Q3: SIP transaction YoY growth ──────────────────────────────────────────
SELECT
    SUBSTR(transaction_date, 1, 4)   AS year,
    COUNT(*)                          AS sip_count,
    ROUND(SUM(amount), 2)             AS total_sip_amount,
    ROUND(AVG(amount), 2)             AS avg_sip_amount
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY year
ORDER BY year;

-- ── Q4: Total transaction volume by state ───────────────────────────────────
SELECT
    state,
    COUNT(*)                    AS txn_count,
    ROUND(SUM(amount), 2)       AS total_amount,
    COUNT(DISTINCT investor_id) AS unique_investors
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- ── Q5: Funds with expense_ratio < 1% ───────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    f.sub_category,
    p.expense_ratio,
    p.return_1y,
    p.sharpe_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0
ORDER BY p.expense_ratio ASC;

-- ── Q6: Fund-wise NAV growth (first vs latest NAV) ──────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    first_nav.nav                                                  AS first_nav,
    last_nav.nav                                                   AS latest_nav,
    ROUND((last_nav.nav - first_nav.nav) / first_nav.nav * 100, 2) AS total_return_pct
FROM dim_fund f
JOIN (
    SELECT amfi_code, nav FROM fact_nav n1
    WHERE date = (SELECT MIN(date) FROM fact_nav n2 WHERE n2.amfi_code = n1.amfi_code)
) first_nav ON f.amfi_code = first_nav.amfi_code
JOIN (
    SELECT amfi_code, nav FROM fact_nav n1
    WHERE date = (SELECT MAX(date) FROM fact_nav n2 WHERE n2.amfi_code = n1.amfi_code)
) last_nav ON f.amfi_code = last_nav.amfi_code
ORDER BY total_return_pct DESC;

-- ── Q7: Monthly AUM trend across all funds ───────────────────────────────────
SELECT
    month_end,
    ROUND(SUM(aum_cr), 2)  AS total_aum_cr,
    SUM(folios)            AS total_folios,
    COUNT(DISTINCT amfi_code) AS num_funds
FROM fact_aum
GROUP BY month_end
ORDER BY month_end;

-- ── Q8: Top performing funds (1-year return) with risk metrics ───────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.risk_grade,
    p.return_1y,
    p.return_3y,
    p.alpha,
    p.beta,
    p.sharpe_ratio,
    p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.return_1y DESC
LIMIT 10;

-- ── Q9: Investor KYC status breakdown with transaction values ────────────────
SELECT
    t.kyc_status,
    COUNT(*)                    AS txn_count,
    COUNT(DISTINCT t.investor_id) AS unique_investors,
    ROUND(SUM(t.amount), 2)     AS total_transacted,
    ROUND(AVG(t.amount), 2)     AS avg_transaction
FROM fact_transactions t
GROUP BY t.kyc_status
ORDER BY total_transacted DESC;

-- ── Q10: Category-wise average returns and risk profile ──────────────────────
SELECT
    f.category,
    f.sub_category,
    COUNT(DISTINCT f.amfi_code)     AS num_schemes,
    ROUND(AVG(p.return_1y), 2)      AS avg_return_1y,
    ROUND(AVG(p.return_3y), 2)      AS avg_return_3y,
    ROUND(AVG(p.expense_ratio), 2)  AS avg_expense_ratio,
    ROUND(AVG(p.sharpe_ratio), 2)   AS avg_sharpe,
    ROUND(AVG(p.beta), 2)           AS avg_beta
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
GROUP BY f.category, f.sub_category
ORDER BY avg_return_1y DESC;
