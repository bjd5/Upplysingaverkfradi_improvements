-- vedurstodvar-kassi-eftir-fjarlaegd.sql
-- Spurning: Hvaða stöðvar eru innan kassans um VR-II, raðaðar eftir fjarlægð
--           frá húsinu — og hver þeirra mælir enn? (súluritið á síðunni)
-- Síða: web/sidur/vedurstodvar.html
-- Breytur:
--   ?1 breidd viðmiðunarpunkts
--   ?2 lengd viðmiðunarpunkts
--   ?3 lágmarks breidd
--   ?4 hámarks breidd
--   ?5 lágmarks lengd
--   ?6 hámarks lengd
--
-- Súluritið átti sér enga SQL-fyrirspurn; það var aðeins til í mat.json
-- (athugasemd P2.4 á #14, liður 2). Sama röð og vinnsla/vedurstodvar_mat.py
-- (rada_eftir_fjarlaegd): röðað á ÓAFRÚNNAÐRI fjarlægð, svo tvær stöðvar sem
-- rúnnast í sama metrafjölda halda réttri innbyrðis röð. Jöfn fjarlægð raðast
-- eftir station_id svo röðin sé alltaf sú sama.
--
-- distance_m er óafrúnnuð; birtingin námundar í heila metra. is_active er 1
-- fyrir stöð sem mælir enn (end_year IS NULL) — sama skilyrði og active=true.

WITH in_box AS (
    SELECT station_id, name, start_year, end_year,
           end_year IS NULL                 AS is_active,
           fjarlaegd_metrar(lat, lon, ?, ?) AS distance_m
    FROM weather_stations
    WHERE lat BETWEEN ? AND ?
      AND lon BETWEEN ? AND ?
)
SELECT station_id, name, start_year, end_year, is_active, distance_m,
       ROW_NUMBER() OVER (ORDER BY distance_m, station_id) AS distance_rank
FROM in_box
ORDER BY distance_rank;
