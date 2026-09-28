-- skjalftar-staerd-eftir-kvarda.sql
-- Spurning: Hversu margir skjálftar eru skráðir á hverjum stærðarkvarða, og
--           hvert er lágmark, hámark og miðgildi stærðar INNAN hvers kvarða?
-- Síða: web/sidur/skjalftavaktin.html (stærðartaflan)
-- Breytur: engar
--
-- Aldrei eitt meðaltal yfir alla: Mlw og Mw eru ekki sama talan, og miðgildi
-- sem blandar kvörðum er ekki mæling á neinu. Öll samantekt er því innan
-- GROUP BY magnitude_type og miðgildið innan PARTITION BY magnitude_type.
-- Í frosna eintakinu er aðeins einn kvarði (Mlw), en fyrirspurnin gerir ekki
-- ráð fyrir því.
--
-- Þetta er heimild birtingarinnar (athugasemd P2.3 á #14, liður 3). Sama tala
-- reiknuð í vinnsla/jardskjalftar_samantekt.py er eftirlitsgagn vinnsluþrepsins
-- og prófið krefst þess að þær stemmi. Óafrúnnað; birtingin námundar.

WITH ordered AS (
    SELECT magnitude_type,
           magnitude,
           ROW_NUMBER() OVER (PARTITION BY magnitude_type ORDER BY magnitude) AS position,
           COUNT(*)     OVER (PARTITION BY magnitude_type)                    AS type_count
    FROM earthquakes
)
SELECT magnitude_type,
       COUNT(*)       AS event_count,
       MIN(magnitude) AS min_magnitude,
       MAX(magnitude) AS max_magnitude,
       AVG(CASE WHEN position IN ((type_count + 1) / 2, (type_count + 2) / 2)
                THEN magnitude END) AS median_magnitude
FROM ordered
GROUP BY magnitude_type
ORDER BY magnitude_type;
