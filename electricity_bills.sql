-- Electricity Consumption Charges and Collection Details
-- Source: Household electricity bills (March 2022 - January 2026)
-- Purpose: Solar + Storage investment analysis (NPV / IRR)

DROP TABLE IF EXISTS electricity_bills;

CREATE TABLE electricity_bills (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_date           DATE NOT NULL,
    entry_date          DATE NOT NULL,
    status              TEXT NOT NULL DEFAULT 'NORMAL',
    kwh_reading         INTEGER,          -- Cumulative meter reading (kWh)
    kvah_reading        INTEGER,          -- Cumulative KVAH reading
    recorded_demand     REAL,             -- Recorded demand (kW/kVA)
    power_factor        REAL,             -- Power factor
    consumption_units   INTEGER NOT NULL, -- Units consumed in billing period
    cc_charges          REAL NOT NULL,    -- Consumption / CC charges (INR)
    electricity_tax     REAL DEFAULT 0,
    welding_charge      REAL DEFAULT 0,
    excess_demand       REAL DEFAULT 0,
    pf_penalty          REAL DEFAULT 0,
    fixed_charges       REAL DEFAULT 0,
    total_charges       REAL NOT NULL,    -- Sum of charges (cols 9-14)
    advance_amount_paid REAL DEFAULT 0,
    adjustment          REAL DEFAULT 0,
    amount_to_be_paid   REAL NOT NULL,
    due_date            DATE,
    amount_paid         REAL,
    receipt_no          TEXT,
    collection_date     DATE
);

-- Insert all billing records (newest to oldest)
INSERT INTO electricity_bills
    (bill_date, entry_date, status, kwh_reading, kvah_reading, recorded_demand, power_factor,
     consumption_units, cc_charges, electricity_tax, welding_charge, excess_demand,
     pf_penalty, fixed_charges, total_charges, advance_amount_paid, adjustment,
     amount_to_be_paid, due_date, amount_paid, receipt_no, collection_date)
VALUES
    -- 2026
    ('2026-01-20', '2026-01-20', 'NORMAL', 75987, NULL,  16,    NULL, 773,  4514.85,  0, 0, 0, 0, 0,     4515,  0, 0, 4515,  '2026-02-09', 4515,  'PGIINB83031392',   '2026-02-03'),

    -- 2025
    ('2025-11-19', '2025-11-19', 'NORMAL', 75214, NULL,  16,    NULL, 1019, 7089.45,  0, 0, 0, 0, 0,     7089,  0, 0, 7089,  '2025-12-09', 7277,  'PGIINB816009150',  '2025-12-17'),
    ('2025-09-19', '2025-09-19', 'NORMAL', 74195, NULL,  16.86, NULL, 1128, 8348.40,  0, 0, 0, 0, 0,     8348,  0, 0, 8348,  '2025-10-09', 8348,  'PGIINB789500422',  '2025-10-01'),
    ('2025-07-22', '2025-07-22', 'NORMAL', 73067, NULL,  16.86, NULL, 1303, 10369.66, 0, 0, 0, 0, 0,     10370, 0, 0, 10370, '2025-08-11', 10370, 'PGIINB769984428',  '2025-08-02'),
    ('2025-05-21', '2025-05-21', 'NORMAL', 71764, NULL,  15.66, NULL, 1533, 13026.15, 0, 0, 0, 0, 0,     13026, 0, 0, 13026, '2025-06-10', 13026, 'PGIINB749806101',  '2025-06-02'),
    ('2025-03-19', '2025-03-19', 'NORMAL', 70231, NULL,  15.66, NULL, 719,  4004.55,  0, 0, 0, 0, 0,     4005,  0, 0, 4005,  '2025-04-08', 4005,  'PGIINB731410466',  '2025-04-03'),
    ('2025-01-21', '2025-01-21', 'NORMAL', 69512, NULL,  8.14,  NULL, 692,  3749.40,  0, 0, 0, 0, 0,     3749,  0, 0, 3749,  '2025-02-10', 3749,  'PGCCAN713614674',  '2025-02-05'),

    -- 2024
    ('2024-11-19', '2024-11-19', 'NORMAL', 68820, NULL,  8.14,  NULL, 881,  5620.50,  0, 0, 0, 0, 0,     5621,  0, 0, 5621,  '2024-12-10', 5621,  'PGIINB694053570',  '2024-12-02'),
    ('2024-09-20', '2024-09-20', 'NORMAL', 67939, NULL,  8.14,  NULL, 1108, 8117.40,  0, 0, 0, 0, 0,     8117,  0, 0, 8117,  '2024-10-10', 8117,  'PGIINB675920937',  '2024-10-03'),
    ('2024-07-19', '2024-07-19', 'NORMAL', 66831, NULL,  8.14,  NULL, 938,  6070.56,  0, 0, 0, 0, 0,     6071,  0, 0, 6071,  '2024-08-08', 6071,  'PGCINB657632737',  '2024-08-05'),
    ('2024-05-20', '2024-05-20', 'NORMAL', 65893, NULL,  8.14,  NULL, 1320, 10070.00, 0, 0, 0, 0, 0,     10070, 0, 0, 10070, '2024-06-10', 10070, 'PGIINB639168160',  '2024-06-03'),
    ('2024-03-19', '2024-03-19', 'NORMAL', 64573, NULL,  8.14,  0.02, 699,  3641.00,  0, 0, 0, 0, 0,     3641,  0, 0, 3641,  '2024-04-08', 3641,  'PGIINB622879324',  '2024-04-05'),
    ('2024-01-22', '2024-01-22', 'NORMAL', 63874, 65675, 1,     NULL, 531,  2198.00,  0, 0, 0, 0, 0,     2198,  0, 0, 2198,  '2024-02-12', 2198,  'PGIINB602995738',  '2024-01-29'),

    -- 2023
    ('2023-11-21', '2023-11-21', 'NORMAL', 63343, 65151, NULL,  0.97, 856,  5110.00,  0, 0, 0, 0, 0,     5110,  0, 0, 5110,  '2023-12-11', 5110,  'PGIBP1109662812',  '2023-11-30'),
    ('2023-09-20', '2023-09-20', 'NORMAL', 62487, 64272, NULL,  0.97, 1219, 8959.00,  0, 0, 0, 0, 0,     8959,  0, 0, 8959,  '2023-10-10', 8959,  'PGCICI569006088',  '2023-10-04'),
    ('2023-07-19', '2023-07-19', 'NORMAL', 61268, 63013, NULL,  0.97, 1648, 13678.00, 0, 0, 0, 0, 0,     13678, 0, 0, 13678, '2023-08-08', 13678, 'PGCCAN549223429',  '2023-07-29'),
    ('2023-05-19', '2023-05-20', 'NORMAL', 59620, 61320, NULL,  0.96, 1180, 8530.00,  0, 0, 0, 0, 0,     8530,  0, 0, 8530,  '2023-06-08', 8530,  'PGCCAN530798048',  '2023-05-28'),
    ('2023-03-20', '2023-03-20', 'NORMAL', 58440, 60090, NULL,  0.95, 700,  3650.00,  0, 0, 0, 0, 0,     3650,  0, 0, 3650,  '2023-04-10', 3650,  'PGCCAN515085849',  '2023-04-02'),
    ('2023-01-21', '2023-01-21', 'NORMAL', 57740, 59350, NULL,  0.96, 680,  3470.00,  0, 0, 0, 0, 0,     3470,  0, 0, 3470,  '2023-02-10', 3470,  'PGCCAN499568247',  '2023-02-03'),

    -- 2022
    ('2022-11-19', '2022-11-19', 'NORMAL', 57060, 58640, 25,    0.94, 760,  4190.00,  0, 0, 0, 0, 0,     4190,  0, 0, 4190,  '2022-12-09', 4190,  'PGCCAN482702948',  '2022-12-01'),
    ('2022-09-20', '2022-09-20', 'NORMAL', 56300, 57830, 2,     0.97, 1360, 8448.80,  0, 0, 0, 0, 43.33, 8492,  0, 0, 8492,  '2022-10-10', 8492,  'PGCCAN467345213',  '2022-10-03'),
    ('2022-07-19', '2022-07-19', 'NORMAL', 54940, 56430, 8,     0.97, 1740, 9914.00,  0, 0, 0, 0, 50,    9964,  0, 0, 9964,  '2022-08-08', 9964,  'PGCCAN451411937',  '2022-08-01'),
    ('2022-05-19', '2022-05-19', 'NORMAL', 53200, 54640, 2,     0.98, 1540, 8594.00,  0, 0, 0, 0, 50,    8644,  0, 0, 8644,  '2022-06-08', 8644,  'PGCCAN436237231',  '2022-06-02'),
    ('2022-03-18', '2022-03-18', 'NORMAL', 51660, 53067, 8,     0.97, 820,  3842.00,  0, 0, 0, 0, 50,    3892,  0, 0, 3892,  '2022-04-07', 3892,  'PGIBP160914046',   '2022-04-05');

-- ============================================================
-- Useful views for solar + storage investment analysis
-- ============================================================

-- View: Billing period details with derived metrics
CREATE VIEW IF NOT EXISTS v_billing_analysis AS
SELECT
    id,
    bill_date,
    consumption_units,
    total_charges,
    amount_paid,
    -- Effective rate per unit (INR/kWh)
    ROUND(CAST(total_charges AS REAL) / NULLIF(consumption_units, 0), 2) AS rate_per_unit,
    -- Billing period duration (approx days between consecutive bills)
    CAST(julianday(bill_date) - julianday(
        LAG(bill_date) OVER (ORDER BY bill_date)
    ) AS INTEGER) AS billing_period_days,
    -- Average daily consumption
    ROUND(CAST(consumption_units AS REAL) / NULLIF(
        CAST(julianday(bill_date) - julianday(
            LAG(bill_date) OVER (ORDER BY bill_date)
        ) AS INTEGER), 0
    ), 2) AS avg_daily_units,
    -- Year and month for seasonal analysis
    strftime('%Y', bill_date) AS bill_year,
    strftime('%m', bill_date) AS bill_month
FROM electricity_bills
ORDER BY bill_date;

-- View: Annual summary for year-over-year comparison
CREATE VIEW IF NOT EXISTS v_annual_summary AS
SELECT
    strftime('%Y', bill_date) AS year,
    COUNT(*)                  AS num_bills,
    SUM(consumption_units)    AS total_units,
    SUM(total_charges)        AS total_charges,
    ROUND(AVG(consumption_units), 0) AS avg_units_per_bill,
    ROUND(CAST(SUM(total_charges) AS REAL) / SUM(consumption_units), 2) AS avg_rate_per_unit
FROM electricity_bills
GROUP BY strftime('%Y', bill_date)
ORDER BY year;

-- View: Seasonal pattern (bi-monthly averages across all years)
CREATE VIEW IF NOT EXISTS v_seasonal_pattern AS
SELECT
    CASE CAST(strftime('%m', bill_date) AS INTEGER)
        WHEN 1  THEN 'Jan-Feb'
        WHEN 2  THEN 'Jan-Feb'
        WHEN 3  THEN 'Mar-Apr'
        WHEN 4  THEN 'Mar-Apr'
        WHEN 5  THEN 'May-Jun'
        WHEN 6  THEN 'May-Jun'
        WHEN 7  THEN 'Jul-Aug'
        WHEN 8  THEN 'Jul-Aug'
        WHEN 9  THEN 'Sep-Oct'
        WHEN 10 THEN 'Sep-Oct'
        WHEN 11 THEN 'Nov-Dec'
        WHEN 12 THEN 'Nov-Dec'
    END AS season,
    ROUND(AVG(consumption_units), 0) AS avg_units,
    ROUND(AVG(total_charges), 0)     AS avg_charges,
    MIN(consumption_units)           AS min_units,
    MAX(consumption_units)           AS max_units
FROM electricity_bills
GROUP BY season
ORDER BY MIN(CAST(strftime('%m', bill_date) AS INTEGER));
