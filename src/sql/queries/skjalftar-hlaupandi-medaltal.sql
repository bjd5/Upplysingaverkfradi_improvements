-- skjalftar-hlaupandi-medaltal.sql
-- Spurning: Hver er hlaupandi 7 daga meðalfjöldi skjálfta á dag — sléttuð
--           tímaröð sem sýnir hrinurnar án dagsveiflunnar?
-- Síða: web/sidur/skjalftavaktin.html
-- Breytur: engar
--
-- NÝ AFLEIDD MÆLING. Gamla síðan reiknaði hana ekki og hún á sér ENGA tölu í
-- docs/vidmid/vidmid.json (athugasemd P2.3 á #14, liður 2). Prófin bera hana
-- því ekki við viðmið heldur við sjálfstæðan útreikning úr daglegu talningunni
-- og sýna að sama gluggi yfir röð án núll-daga gefur annað svar.
--
-- Skilgreining:
--   * Gluggi sem ENDAR á deginum (dagurinn og 6 dagar á undan), ekki
--     miðjaður — gildið er seinkað um 3 daga miðað við atburðina.
--   * Núll-dagar eru í glugganum (LEFT JOIN á dagatalið). ROWS en ekki RANGE:
--     dagatalið hefur línu fyrir hvern dag, svo 7 raðir = 7 almanaksdagar.
--   * Fyrstu 6 dagar tímabilsins hafa styttri glugga; days_in_window segir
--     hversu marga daga meðaltalið nær yfir, svo birtingin geti merkt þá eða
--     sleppt þeim. Engir dagar fyrir 1. nóvember 2023 eru í gögnunum.
--   * Óafrúnnað; birtingin námundar.
-- Sléttun, ekki spá — sjá docs/adferdafraedi.md kafla 4.

WITH daily AS (
    SELECT d.utc_day, COUNT(e.event_id) AS event_count
    FROM earthquake_days AS d
    LEFT JOIN earthquakes AS e ON e.utc_day = d.utc_day
    GROUP BY d.utc_day
)
SELECT utc_day,
       event_count,
       AVG(event_count) OVER last_7_days AS rolling_avg_7d,
       COUNT(*)         OVER last_7_days AS days_in_window
FROM daily
WINDOW last_7_days AS (ORDER BY utc_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
ORDER BY utc_day;
