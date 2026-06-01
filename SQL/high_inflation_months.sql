-- high_inflation_months.sql
-- Purpose: List every state-month where YoY inflation exceeded 5%,
-- alongside the corresponding state unemployment rate.
--
-- Directly relevant to the Phillips-Curve question: was unemployment
-- low (consistent with the textbook trade-off) or high (i.e. stagflation)
-- in the months when prices were rising fastest?

SELECT
    i.date,
    i.state,
    ROUND(i.inflation_rate_yoy, 2) AS inflation_rate_yoy,
    ROUND(u.unemployment_rate, 2)  AS unemployment_rate
FROM state_inflation AS i
INNER JOIN state_unemployment AS u
    ON i.date = u.date
   AND i.state = u.state
WHERE i.inflation_rate_yoy > 5.0
ORDER BY i.inflation_rate_yoy DESC;
