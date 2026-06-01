-- average_conditions_by_state.sql
-- Purpose: Statistical profile of each state's economic experience
-- over the full sample. One row per state.
--
-- Demonstrates: INNER JOIN on composite key, GROUP BY, aggregates
-- (COUNT, AVG, MIN, MAX) over multiple columns.

SELECT
    u.state,
    COUNT(*)                                AS n_months,
    ROUND(AVG(u.unemployment_rate), 2)      AS avg_unemployment_rate,
    ROUND(MIN(u.unemployment_rate), 2)      AS min_unemployment_rate,
    ROUND(MAX(u.unemployment_rate), 2)      AS max_unemployment_rate,
    ROUND(AVG(i.inflation_rate_yoy), 2)     AS avg_inflation_rate,
    ROUND(MIN(i.inflation_rate_yoy), 2)     AS min_inflation_rate,
    ROUND(MAX(i.inflation_rate_yoy), 2)     AS max_inflation_rate
FROM state_unemployment AS u
INNER JOIN state_inflation AS i
    ON u.date = i.date
   AND u.state = i.state
GROUP BY u.state
ORDER BY u.state;
