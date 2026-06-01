-- create_tables.sql
-- Purpose: Define the full schema for phillips_curve.db.
-- All tables use ISO date strings ('YYYY-MM-DD') and two-letter state codes
-- ('TX', 'MA', 'OH') for consistent JOINs.

-- ===========================================================
-- state_unemployment: monthly seasonally adjusted state unemployment rate
-- Source: BLS Local Area Unemployment Statistics, via FRED (TXUR/MAUR/OHUR).
-- ===========================================================
CREATE TABLE IF NOT EXISTS state_unemployment (
    date              TEXT NOT NULL,  -- 'YYYY-MM-DD', month-start
    state             TEXT NOT NULL,  -- 'TX' | 'MA' | 'OH'
    unemployment_rate REAL,           -- percent of state labor force
    PRIMARY KEY (date, state)
);

-- ===========================================================
-- state_inflation: monthly CPI level and YoY inflation rate
-- Source: BLS metro-area CPI with Census-region CPI fill for gaps.
-- ===========================================================
CREATE TABLE IF NOT EXISTS state_inflation (
    date               TEXT NOT NULL,
    state              TEXT NOT NULL,
    cpi_index          REAL,           -- price index level (not a rate)
    inflation_rate_yoy REAL,           -- year-over-year percent change
    PRIMARY KEY (date, state)
);

-- ===========================================================
-- national_controls: monthly nation-wide control variables
-- Source: FRED (CPIAUCSL, DCOILWTICO, MORTGAGE30US, FEDFUNDS).
-- ===========================================================
CREATE TABLE IF NOT EXISTS national_controls (
    date                   TEXT PRIMARY KEY,  -- 'YYYY-MM-DD', one row per month
    national_inflation_yoy REAL,              -- YoY change in national CPI (%)
    oil_price_wti          REAL,              -- WTI crude, $/barrel, monthly avg
    mortgage_rate_30yr     REAL,              -- 30-yr fixed rate, monthly avg (%)
    fed_funds_rate         REAL               -- effective fed funds rate (%)
);

-- ===========================================================
-- state_hpi: quarterly FHFA House Price Index by state
-- Source: FRED (TXSTHPI / MASTHPI / OHSTHPI).
-- ===========================================================
CREATE TABLE IF NOT EXISTS state_hpi (
    date  TEXT NOT NULL,  -- quarter-end date
    state TEXT NOT NULL,
    hpi   REAL,           -- index, 1980 Q1 = 100
    PRIMARY KEY (date, state)
);

-- ===========================================================
-- state_characteristics: time-invariant structural attributes
-- Source: U.S. Census Bureau and BLS (hand-entered).
-- ===========================================================
CREATE TABLE IF NOT EXISTS state_characteristics (
    state                   TEXT PRIMARY KEY,
    manufacturing_share_pct REAL,  -- % of state GDP
    energy_share_pct        REAL,  -- % of state GDP (mining/oil/gas)
    unionization_rate_pct   REAL,  -- % of workers in unions
    median_household_income REAL,  -- USD
    pct_bachelors_degree    REAL,  -- % of adults 25+ with BA+
    population_millions     REAL,
    dominant_industries     TEXT   -- comma-separated description
);
