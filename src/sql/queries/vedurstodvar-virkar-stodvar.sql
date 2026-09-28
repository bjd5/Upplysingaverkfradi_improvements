-- vedurstodvar-virkar-stodvar.sql
-- Spurning: Hvaða stöðvar mæla enn? Sama og `active=true` í beiðninni.
-- Síða: web/sidur/vedurstodvar.html
-- Breytur: engar
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.
--
-- `end_year IS NULL` er skilyrðið — tómstrengur kemst ekki í dálkinn (CHECK í 004).

SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE end_year IS NULL
ORDER BY station_id;
