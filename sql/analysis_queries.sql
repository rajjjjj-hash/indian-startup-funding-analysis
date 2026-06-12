-- ============================================================
-- Indian Startup Funding Analysis (2015-2017)
-- Business questions answered in SQL against data/funding.db
-- Table: funding_deals
-- ============================================================

-- Q1. How big is the dataset and how much capital does it cover?
SELECT COUNT(*)                          AS total_deals,
       COUNT(amount_usd)                 AS disclosed_deals,
       ROUND(SUM(amount_usd) / 1e9, 2)   AS total_disclosed_usd_bn
FROM funding_deals;

-- Q2. Funding trend by year: is the ecosystem heating up or cooling down?
SELECT year,
       COUNT(*)                          AS deals,
       ROUND(SUM(amount_usd) / 1e9, 2)   AS amount_usd_bn,
       ROUND(AVG(amount_usd) / 1e6, 2)   AS avg_deal_usd_mn
FROM funding_deals
GROUP BY year
ORDER BY year;

-- Q3. Which cities attract the most deals AND the most capital?
-- (Deal count and capital tell different stories.)
SELECT city,
       COUNT(*)                                    AS deals,
       ROUND(SUM(amount_usd) / 1e9, 2)             AS amount_usd_bn,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM funding_deals), 1)
                                                   AS pct_of_all_deals
FROM funding_deals
WHERE city IS NOT NULL AND city != 'nan'
GROUP BY city
ORDER BY deals DESC
LIMIT 10;

-- Q4. Top industries by deal volume.
SELECT industry,
       COUNT(*)                        AS deals,
       ROUND(SUM(amount_usd) / 1e6, 1) AS amount_usd_mn
FROM funding_deals
WHERE industry IS NOT NULL AND industry != 'nan'
GROUP BY industry
ORDER BY deals DESC
LIMIT 10;

-- Q5. Seed vs Private Equity: how does the funding mix shift over time?
-- A falling seed share signals a maturing (or tightening) early-stage market.
SELECT year,
       investment_type,
       COUNT(*) AS deals,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY year), 1)
                AS pct_of_year
FROM funding_deals
WHERE investment_type IN ('Seed Funding', 'Private Equity')
GROUP BY year, investment_type
ORDER BY year, investment_type;

-- Q6. Median deal size by investment type (more honest than the mean,
-- which mega-rounds distort). SQLite has no MEDIAN(), so use a window trick.
WITH ranked AS (
    SELECT investment_type,
           amount_usd,
           ROW_NUMBER() OVER (PARTITION BY investment_type ORDER BY amount_usd) AS rn,
           COUNT(*)    OVER (PARTITION BY investment_type)                      AS cnt
    FROM funding_deals
    WHERE amount_usd IS NOT NULL
)
SELECT investment_type,
       cnt                                   AS disclosed_deals,
       ROUND(AVG(amount_usd) / 1e6, 2)       AS median_usd_mn
FROM ranked
WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
GROUP BY investment_type
ORDER BY median_usd_mn DESC;

-- Q7. The mega-round concentration problem:
-- what share of all disclosed capital went to the top 10 deals?
WITH top10 AS (
    SELECT amount_usd
    FROM funding_deals
    WHERE amount_usd IS NOT NULL
    ORDER BY amount_usd DESC
    LIMIT 10
)
SELECT ROUND((SELECT SUM(amount_usd) FROM top10) / 1e9, 2)        AS top10_usd_bn,
       ROUND(100.0 * (SELECT SUM(amount_usd) FROM top10)
                   / (SELECT SUM(amount_usd) FROM funding_deals), 1)
                                                                  AS top10_pct_of_total;

-- Q8. Which startups raised the most rounds in the period? (repeat fundraisers)
SELECT startup_name,
       COUNT(*)                        AS rounds,
       ROUND(SUM(amount_usd) / 1e6, 1) AS total_usd_mn
FROM funding_deals
GROUP BY startup_name
HAVING COUNT(*) >= 3
ORDER BY rounds DESC, total_usd_mn DESC
LIMIT 10;

-- Q9. Monthly deal momentum: find the peak and trough months.
SELECT year_month,
       COUNT(*) AS deals
FROM funding_deals
GROUP BY year_month
ORDER BY deals DESC
LIMIT 5;

-- Q10. Data quality check: what share of deals have undisclosed amounts,
-- and does it vary by investment type? (Affects how much we trust amount-based metrics.)
SELECT investment_type,
       COUNT(*)                                          AS deals,
       SUM(CASE WHEN amount_usd IS NULL THEN 1 ELSE 0 END) AS undisclosed,
       ROUND(100.0 * SUM(CASE WHEN amount_usd IS NULL THEN 1 ELSE 0 END)
                   / COUNT(*), 1)                        AS pct_undisclosed
FROM funding_deals
GROUP BY investment_type
HAVING COUNT(*) > 5
ORDER BY deals DESC;

-- Q11. Bangalore vs Mumbai vs NCR (New Delhi + Gurgaon + Noida):
-- which hub leads on early-stage (seed) activity specifically?
SELECT CASE
           WHEN city IN ('New Delhi', 'Gurgaon', 'Noida') THEN 'NCR'
           ELSE city
       END                              AS hub,
       COUNT(*)                         AS seed_deals,
       ROUND(SUM(amount_usd) / 1e6, 1)  AS seed_usd_mn
FROM funding_deals
WHERE investment_type = 'Seed Funding'
  AND city IN ('Bangalore', 'Mumbai', 'New Delhi', 'Gurgaon', 'Noida')
GROUP BY hub
ORDER BY seed_deals DESC;

-- Q12. Year-over-year growth rate of deal count, using LAG().
WITH yearly AS (
    SELECT year, COUNT(*) AS deals
    FROM funding_deals
    GROUP BY year
)
SELECT year,
       deals,
       LAG(deals) OVER (ORDER BY year)  AS prev_year_deals,
       ROUND(100.0 * (deals - LAG(deals) OVER (ORDER BY year))
                   / LAG(deals) OVER (ORDER BY year), 1) AS yoy_growth_pct
FROM yearly;
