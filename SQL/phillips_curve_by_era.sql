-- phillips_curve_by_era.sql
-- Purpose: Tag each state-month with an economic era and report the
-- average unemployment and inflation rates by (era, state).
--
-- This directly sets up the central empirical question of the project:
-- has the Phillips-Curve relationship between unemployment and inflation
-- been stable over time, or did it change between the pre-crisis years,
-- the Great Recession, the long expansion, and the COVID era?
--
-- Demonstrates: CASE-based bucketing on a date column, GROUP BY across
-- two dimensions, and a custom ORDER BY that respects chronological era.

WITH era_panel AS (
    SELECT
        u.date,
        u.state,
        u.unemployment_rate,
        i.inflation_rate_yoy,
        CASE
            WHEN CAST(SUBSTR(u.date, 1, 4) AS INTEGER) BETWEEN 2000 AND 2007
                THEN 'Pre-Crisis (2000-2007)'
            WHEN CAST(SUBSTR(u.date, 1, 4) AS INTEGER) BETWEEN 2008 AND 2009
                THEN 'Great Recession (2008-2009)'
            WHEN CAST(SUBSTR(u.date, 1, 4) AS INTEGER) BETWEEN 2010 AND 2019
                THEN 'Long Expansion (2010-2019)'
            WHEN CAST(SUBSTR(u.date, 1, 4) AS INTEGER) >= 2020
                THEN 'COVID and Aftermath (2020-)'
        END AS era
    FROM state_unemployment AS u
    INNER JOIN state_inflation AS i
        ON u.date = i.date
       AND u.state = i.state
)
SELECT
    era,
    state,
    COUNT(*)                            AS n_months,
    ROUND(AVG(unemployment_rate), 2)    AS avg_unemployment_rate,
    ROUND(AVG(inflation_rate_yoy), 2)   AS avg_inflation_rate
FROM era_panel
GROUP BY era, state
ORDER BY
    CASE era
        WHEN 'Pre-Crisis (2000-2007)'      THEN 1
        WHEN 'Great Recession (2008-2009)' THEN 2
        WHEN 'Long Expansion (2010-2019)'  THEN 3
        WHEN 'COVID and Aftermath (2020-)' THEN 4
    END,
    state;
