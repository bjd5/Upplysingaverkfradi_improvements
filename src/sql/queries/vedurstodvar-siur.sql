-- vedurstodvar-siur.sql
-- Síurnar og spurningarnar úr veðurstöðvaæfingunni, framkvæmdar á
-- `weather_stations` (migration 004).
--
-- Gamla verkefnið sendi hverja síu sem sérstaka beiðni til
-- https://api.vedur.is/weather/stations og treysti þjónustunni fyrir svarinu.
-- Hér er sama síun gerð á frosna eintakinu í grunninum: sama mengi, sama
-- niðurstaða, en endurtekjanleg og netlaus.
--
-- SNIÐ: hver fyrirspurn hefst á línunni `-- @fyrirspurn: <heiti>`.
-- `src/python/vinnsla/vedurstodvar_fyrirspurnir.py` les skrána eftir þessum
-- merkjum, svo SQL-ið er geymt á einum stað og ekki afritað inn í Python.
--
-- ÖLL GILDI KOMA INN SEM BREYTUR (`?`) — aldrei strengjasamsetning (regla 5).
-- Fallið fjarlaegd_metrar(lat, lon, ?, ?) er skráð á tenginguna í Python
-- (sqlite3.Connection.create_function) og reiknar stórbaugsfjarlægð í metrum.


-- @fyrirspurn: allar_stodvar
-- Ósíað: allar stöðvar sem þjónustan þekkir, virkar sem aflagðar.
SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
ORDER BY station_id;


-- @fyrirspurn: fjoldi_stodva
-- Svar: hversu margar stöðvar eru í eintakinu?
SELECT COUNT(*) AS fjoldi
FROM weather_stations;


-- @fyrirspurn: stod_eftir_audkenni
-- Sama og `station_id=<n>` í beiðninni: ein stöð sótt beint á frumlyklinum.
SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE station_id = ?;


-- @fyrirspurn: virkar_stodvar
-- Sama og `active=true`: stöðin mælir enn og hefur því ekkert lokaár.
-- `end_year IS NULL` er skilyrðið — tómstrengur kemst ekki í dálkinn (CHECK í 004).
SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE end_year IS NULL
ORDER BY station_id;


-- @fyrirspurn: fjoldi_virkra
-- Svar: hversu margar stöðvanna eru virkar?
SELECT COUNT(*) AS fjoldi
FROM weather_stations
WHERE end_year IS NULL;


-- @fyrirspurn: stodvar_i_marghyrningi
-- Sama og `polygon=<WKT>`: marghyrningurinn sem æfingin sendir er áshliðra
-- rétthyrningur (kassi um VR-II), svo tvö BETWEEN-skilyrði lýsa honum nákvæmlega.
-- Breytur: lágmarks breidd, hámarks breidd, lágmarks lengd, hámarks lengd.
SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE lat BETWEEN ? AND ?
  AND lon BETWEEN ? AND ?
ORDER BY station_id;


-- @fyrirspurn: virkar_stodvar_i_marghyrningi
-- Sama og `polygon=<WKT>&active=true` — báðar síur í sömu beiðni.
SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE lat BETWEEN ? AND ?
  AND lon BETWEEN ? AND ?
  AND end_year IS NULL
ORDER BY station_id;


-- @fyrirspurn: naesta_virka_stod
-- Svar: hver er næsta stöð við gefin hnit sem mælir enn?
SELECT station_id, name, start_year, end_year,
       CAST(ROUND(fjarlaegd_metrar(lat, lon, ?, ?)) AS INTEGER) AS metrar
FROM weather_stations
WHERE end_year IS NULL
ORDER BY metrar
LIMIT 1;


-- @fyrirspurn: naesta_aflagda_stod
-- Svar: hver er næsta stöð sem er hætt mælingum? Sýnir hvað munar litlu —
-- röðun eftir fjarlægð einni saman getur skilað ónothæfri stöð.
SELECT station_id, name, start_year, end_year,
       CAST(ROUND(fjarlaegd_metrar(lat, lon, ?, ?)) AS INTEGER) AS metrar
FROM weather_stations
WHERE end_year IS NOT NULL
ORDER BY metrar
LIMIT 1;


-- @fyrirspurn: naesta_virka_langtimastod
-- Svar: dygði næsta stöð til að bera saman við veður fyrir 50 árum?
-- Breytur: viðmiðunarhnitin tvö og elsta árið sem þarf að ná til.
SELECT station_id, name, start_year, end_year,
       CAST(ROUND(fjarlaegd_metrar(lat, lon, ?, ?)) AS INTEGER) AS metrar
FROM weather_stations
WHERE end_year IS NULL
  AND start_year <= ?
ORDER BY metrar
LIMIT 1;
