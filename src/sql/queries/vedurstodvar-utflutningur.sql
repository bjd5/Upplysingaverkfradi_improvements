-- vedurstodvar-utflutningur.sql
-- Fyrirspurnirnar sem útflutningurinn í web/gogn/vedurstodvar.json keyrir á
-- `weather_stations` (migration 004) og `fetch_log` (001). Issue #15.
--
-- Síurnar sjálfar (station_id, active, polygon, næsta stöð) eru í
-- vedurstodvar-siur.sql og eru endurnýttar þaðan; hér eru aðeins þær
-- samantektir sem síðan þarf til viðbótar. Tölur eru rúnnaðar HÉR, ekki í
-- vafranum.
--
-- SNIÐ: `-- @fyrirspurn: <heiti>`, lesið af src/python/utflutningur/sql_safn.py.
-- ÖLL GILDI KOMA INN SEM NEFNDAR BREYTUR (`:heiti`) — regla 5.
-- `fjarlaegd_metrar(lat, lon, lat0, lon0)` er skráð á tenginguna í Python
-- (vinnsla.vedurstodvar_fyrirspurnir.skra_fjarlaegdarfall).


-- @fyrirspurn: sokn
-- Hvaða eintak var hlaðið og hvenær það var sótt. `fetched_at` verður
-- `uppfaert` í útfluttu skránni.
SELECT endpoint, params, fetched_at, record_count, raw_file
FROM fetch_log
WHERE service = :thjonusta
ORDER BY id;


-- @fyrirspurn: fjoldatolur
-- Allar stöðvar, virkar stöðvar og hlutfall virkra í heilum prósentum.
SELECT COUNT(*) AS allar,
       SUM(end_year IS NULL) AS virkar,
       SUM(end_year IS NOT NULL) AS aflagdar,
       CAST(ROUND(100.0 * SUM(end_year IS NULL) / COUNT(*)) AS INTEGER)
           AS hlutfall_virkra_prosent
FROM weather_stations;


-- @fyrirspurn: fjoldi_i_kassa
-- Sama og `polygon` og `polygon` + `active=true` gömlu síðunnar, talið í SQL.
SELECT COUNT(*) AS allar,
       COALESCE(SUM(end_year IS NULL), 0) AS virkar
FROM weather_stations
WHERE lat BETWEEN :min_breidd AND :max_breidd
  AND lon BETWEEN :min_lengd AND :max_lengd;


-- @fyrirspurn: fjoldi_med_audkenni
-- Sama og `station_id=<n>`: 1 ef stöðin er til, annars 0.
SELECT COUNT(*) AS fjoldi
FROM weather_stations
WHERE station_id = :stod;


-- @fyrirspurn: stodvar_i_kassa
-- Stöðvarnar innan kassans, raðaðar eftir ÓRÚNNAÐRI fjarlægð (næsta fyrst),
-- eins og gamla skriftan gerði. Hnit rúnnuð á fjóra aukastafi (~10 m), sama
-- nákvæmni og WKT-kassinn sem var sendur þjónustunni.
SELECT station_id, name, station_type,
       ROUND(lat, :hnitaaukastafir) AS lat,
       ROUND(lon, :hnitaaukastafir) AS lon,
       CAST(ROUND(elevation_m) AS INTEGER) AS elevation_m,
       start_year, end_year,
       end_year IS NULL AS virk,
       CAST(ROUND(fjarlaegd_metrar(lat, lon, :breidd, :lengd)) AS INTEGER) AS metrar
FROM weather_stations
WHERE lat BETWEEN :min_breidd AND :max_breidd
  AND lon BETWEEN :min_lengd AND :max_lengd
ORDER BY fjarlaegd_metrar(lat, lon, :breidd, :lengd), station_id;


-- @fyrirspurn: munur_aflagdrar_og_virkrar
-- Hversu miklu nær VR-II næsta aflagða stöðin er en næsta virka, í metrum.
-- Sömu skilyrði og naesta_virka_stod / naesta_aflagda_stod í
-- vedurstodvar-siur.sql. Reiknað á órúnnaðri fjarlægð og rúnnað í lokin, eins
-- og gamla skriftan — ekki mismunur tveggja rúnnaðra talna.
SELECT CAST(ROUND(ABS(
    (SELECT MIN(fjarlaegd_metrar(lat, lon, :breidd, :lengd))
       FROM weather_stations WHERE end_year IS NOT NULL)
  - (SELECT MIN(fjarlaegd_metrar(lat, lon, :breidd, :lengd))
       FROM weather_stations WHERE end_year IS NULL)
)) AS INTEGER) AS munur_metrar;
