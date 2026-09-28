-- vedurstodvar-virkar-stodvar-i-marghyrningi.sql
-- Spurning: Hvaða virkar stöðvar eru innan kassans? Sama og `polygon=<WKT>&active=true`.
-- Síða: web/sidur/vedurstodvar.html
-- Breytur:
--   ?1 lágmarks breidd
--   ?2 hámarks breidd
--   ?3 lágmarks lengd
--   ?4 hámarks lengd
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.

SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE lat BETWEEN ? AND ?
  AND lon BETWEEN ? AND ?
  AND end_year IS NULL
ORDER BY station_id;
