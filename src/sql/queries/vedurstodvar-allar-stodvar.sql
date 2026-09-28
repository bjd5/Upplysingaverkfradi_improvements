-- vedurstodvar-allar-stodvar.sql
-- Spurning: Hvaða stöðvar þekkir þjónustan — ósíað, virkar sem aflagðar?
-- Síða: web/sidur/vedurstodvar.html
-- Breytur: engar
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.

SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
ORDER BY station_id;
