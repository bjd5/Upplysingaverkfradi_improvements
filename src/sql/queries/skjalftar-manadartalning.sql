-- skjalftar-manadartalning.sql
-- Spurning: Hversu margir dagar og hversu margir skjálftar eru í hverjum
--           mánuði tímabilsins? (fyrirsagnir mánaðartaflnanna)
-- Síða: web/sidur/skjalftavaktin.html
-- Breytur: engar
--
-- Dagafjöldinn kemur úr dagatalinu, ekki úr atburðunum: desember 2023 hefur
-- 31 dag þótt skjálftar hafi aðeins orðið á fáum þeirra.

WITH daily AS (
    SELECT d.utc_day, COUNT(e.event_id) AS event_count
    FROM earthquake_days AS d
    LEFT JOIN earthquakes AS e ON e.utc_day = d.utc_day
    GROUP BY d.utc_day
)
SELECT substr(utc_day, 1, 7) AS month,
       COUNT(*)              AS day_count,
       SUM(event_count)      AS event_count
FROM daily
GROUP BY month
ORDER BY month;
