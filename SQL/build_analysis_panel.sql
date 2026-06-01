-- build_analysis_panel.sql
-- Purpose: Assemble the analysis-ready monthly panel by joining
-- state_unemployment, state_inflation, and national_controls.
--
-- Join logic:
--   * state_unemployment <-> state_inflation : matched on (date, state)
--   * national_controls is national so it's joined on date alone.
-- Result grain: one row per (date, state).

SELECT
    u.date,
    u.state,
    u.unemployment_rate,
    i.cpi_index,
    i.inflation_rate_yoy,
    n.national_inflation_yoy,
    n.oil_price_wti,
    n.mortgage_rate_30yr,
    n.fed_funds_rate
FROM state_unemployment AS u
INNER JOIN state_inflation AS i
    ON u.date = i.date
   AND u.state = i.state
INNER JOIN national_controls AS n
    ON u.date = n.date
ORDER BY u.state, u.date;
