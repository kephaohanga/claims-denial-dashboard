-- ClaimsDenialDashboard: starter analysis queries
-- Run against dbo.Claims after the CSV import is complete.

USE ClaimsDenialDashboard;
GO

-- 1. Overall denial rate
-- Denied claims as a percentage of all claims.
SELECT
    COUNT(*)                                             AS total_claims,
    SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END)   AS denied_claims,
    CAST(
        100.0 * SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*)
        AS DECIMAL(5, 2)
    )                                                     AS denial_rate_pct
FROM dbo.Claims;
GO

-- 1b. Denial rate by month
-- Groups claims by the month they were submitted and computes the same
-- denied/total ratio per month, ordered chronologically.
SELECT
    FORMAT(submission_date, 'yyyy-MM')                   AS submission_month,
    COUNT(*)                                             AS total_claims,
    SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END)   AS denied_claims,
    CAST(
        100.0 * SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*)
        AS DECIMAL(5, 2)
    )                                                     AS denial_rate_pct
FROM dbo.Claims
GROUP BY FORMAT(submission_date, 'yyyy-MM')
ORDER BY submission_month;
GO

-- 2. Denial reasons ranked by total dollar value denied
-- Uses billed_amount (not paid_amount, which is 0 for denied claims) to show
-- which denial reasons cost the most in unpaid billed charges, not just which
-- occur most often.
SELECT
    denial_reason_code,
    denial_reason_desc,
    COUNT(*)                       AS denied_claim_count,
    SUM(billed_amount)             AS total_billed_denied
FROM dbo.Claims
WHERE status = 'Denied'
GROUP BY denial_reason_code, denial_reason_desc
ORDER BY total_billed_denied DESC;
GO

-- 3. Denial rate by payer
SELECT
    payer,
    COUNT(*)                                             AS total_claims,
    SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END)   AS denied_claims,
    CAST(
        100.0 * SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*)
        AS DECIMAL(5, 2)
    )                                                     AS denial_rate_pct
FROM dbo.Claims
GROUP BY payer
ORDER BY denial_rate_pct DESC;
GO

-- 4. Denial rate by CPT code / procedure
SELECT
    cpt_code,
    COUNT(*)                                             AS total_claims,
    SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END)   AS denied_claims,
    CAST(
        100.0 * SUM(CASE WHEN status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*)
        AS DECIMAL(5, 2)
    )                                                     AS denial_rate_pct
FROM dbo.Claims
GROUP BY cpt_code
ORDER BY denial_rate_pct DESC;
GO

-- 5. Single denial reason with the largest total dollar impact
-- Same aggregation as query 2, narrowed to the top row via TOP 1.
SELECT TOP 1
    denial_reason_code,
    denial_reason_desc,
    COUNT(*)                       AS denied_claim_count,
    SUM(billed_amount)             AS total_billed_denied
FROM dbo.Claims
WHERE status = 'Denied'
GROUP BY denial_reason_code, denial_reason_desc
ORDER BY total_billed_denied DESC;
GO
