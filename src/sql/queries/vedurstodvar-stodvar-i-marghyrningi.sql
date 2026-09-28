-- vedurstodvar-stodvar-i-marghyrningi.sql
-- Spurning: Hvaða stöðvar eru innan kassans um VR-II? Sama og `polygon=<WKT>`.
-- Síða: web/sidur/vedurstodvar.html
-- Breytur:
--   ?1 lágmarks breidd
--   ?2 hámarks breidd
--   ?3 lágmarks lengd
--   ?4 hámarks lengd
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.
--
-- Marghyrningurinn sem æfingin sendir er áshliðraður rétthyrningur (kassi um
-- VR-II), svo tvö BETWEEN-skilyrði lýsa honum nákvæmlega; jaðrar meðtaldir.

SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE lat BETWEEN ? AND ?
  AND lon BETWEEN ? AND ?
ORDER BY station_id;
