-- skjalftar-dypt.sql
-- Spurning: Á hvaða dýpi urðu skjálftarnir — lágmark, hámark og miðgildi í km?
-- Síða: web/sidur/skjalftavaktin.html („Fyrsta yfirlit“)
-- Breytur: engar
--
-- Miðgildið er meðaltal miðjugildanna (eitt við oddatölu, tvö við slétta),
-- sama skilgreining og statistics.median. Óafrúnnað; birtingin námundar.

WITH ordered AS (
    SELECT depth_km,
           ROW_NUMBER() OVER (ORDER BY depth_km) AS position,
           COUNT(*)     OVER ()                  AS event_count
    FROM earthquakes
)
SELECT COUNT(*)      AS event_count,
       MIN(depth_km) AS min_depth_km,
       MAX(depth_km) AS max_depth_km,
       AVG(CASE WHEN position IN ((event_count + 1) / 2, (event_count + 2) / 2)
                THEN depth_km END) AS median_depth_km
FROM ordered;
