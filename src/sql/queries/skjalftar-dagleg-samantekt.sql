-- skjalftar-dagleg-samantekt.sql
-- Spurning: Hvernig dreifist daglegur fjöldi skjálfta — fjöldi daga, atburðir
--           alls, dagar án atburðar, lágmark, hámark og miðgildi?
-- Síða: web/sidur/skjalftavaktin.html („Fyrsta yfirlit“)
-- Breytur: engar
--
-- Sama dagatalning og skjalftar-dagleg-talning.sql (LEFT JOIN á dagatalið),
-- svo núll-dagarnir teljast með í miðgildinu. Án þeirra væri miðgildið
-- reiknað af 18 dögum og yrði langt yfir 0.
--
-- Miðgildi: SQLite hefur ekkert MEDIAN. Dagarnir eru tölusettir eftir fjölda
-- og meðaltal miðjugildanna tekið — eitt gildi við oddatölu, tvö við slétta,
-- sama skilgreining og statistics.median í Python. Óafrúnnað (regla um
-- námundun: birtingin námundar, sjá gagnagrunnur/fyrirspurnir.py).

WITH daily AS (
    SELECT d.utc_day, COUNT(e.event_id) AS event_count
    FROM earthquake_days AS d
    LEFT JOIN earthquakes AS e ON e.utc_day = d.utc_day
    GROUP BY d.utc_day
),
ordered AS (
    SELECT event_count,
           ROW_NUMBER() OVER (ORDER BY event_count) AS position,
           COUNT(*)     OVER ()                     AS day_count
    FROM daily
)
SELECT COUNT(*)                                  AS day_count,
       SUM(event_count)                          AS event_count,
       SUM(event_count = 0)                      AS days_without_events,
       MIN(event_count)                          AS min_daily,
       MAX(event_count)                          AS max_daily,
       AVG(CASE WHEN position IN ((day_count + 1) / 2, (day_count + 2) / 2)
                THEN event_count END)            AS median_daily
FROM ordered;
