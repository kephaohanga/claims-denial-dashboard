-- ClaimsDenialDashboard: table definition for claims_dataset.csv
-- Run this in SSMS with ClaimsDenialDashboard set as the target database.

USE ClaimsDenialDashboard;
GO

IF OBJECT_ID('dbo.Claims', 'U') IS NOT NULL
    DROP TABLE dbo.Claims;
GO

CREATE TABLE dbo.Claims (
    claim_id            VARCHAR(20)     NOT NULL PRIMARY KEY,
    patient_id          VARCHAR(20)     NOT NULL,
    payer               VARCHAR(50)     NOT NULL,
    provider            VARCHAR(100)    NOT NULL,
    icd10_code          VARCHAR(15)     NOT NULL,
    cpt_code            VARCHAR(20)     NOT NULL,
    billed_amount       DECIMAL(10, 2)  NOT NULL,
    paid_amount         DECIMAL(10, 2)  NOT NULL,
    status              VARCHAR(10)     NOT NULL,
    denial_reason_code  VARCHAR(10)     NULL,
    denial_reason_desc  VARCHAR(100)    NULL,
    submission_date     DATE            NOT NULL
);
GO
