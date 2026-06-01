-- texas_oil_relationship.sql
-- Purpose: Examine Texas inflation and unemployment in months when WTI crude
-- oil prices moved by more than 30% YoY (in either direction).
--
-- Why this matters:
-- Texas is heavily exposed to the oil and gas sector. An oil-price shock
-- can move BOTH employment AND inflation in Texas, often in the SAME
-- direction (a price spike boosts drilling employment AND raises local
-- prices). That co-movement is the opposite of the textbook Phillips-Curve
-- trade-off and biases the estimated relationship toward zero — or even
-- the wrong sign — unless oil is explicitly controlled for in the model.

WITH oil_yoy AS (
    -- Derive the 12-month percentage change in WTI from the monthly panel.
    SELECT
        date,
        oil_price_wti,
        100.0 * (oil_price_wti - LAG(oil_price_wti, 12) OVER (ORDER BY date))
              / LAG(oil_price_wti, 12) OVER (ORDER BY date) AS oil_yoy_pct
    FROM national_controls
)
SELECT
    o.date,
    ROUND(o.oil_price_wti, 2)        AS oil_price_wti,
    ROUND(o.oil_yoy_pct, 1)          AS oil_yoy_pct_change,
    ROUND(u.unemployment_rate, 2)    AS tx_unemployment_rate,
    ROUND(i.inflation_rate_yoy, 2)   AS tx_inflation_rate_yoy
FROM oil_yoy AS o
INNER JOIN state_unemployment AS u
    ON o.date = u.date
   AND u.state = 'TX'
INNER JOIN state_inflation AS i
    ON o.date = i.date
   AND i.state = 'TX'
WHERE ABS(o.oil_yoy_pct) > 30
ORDER BY o.date;
