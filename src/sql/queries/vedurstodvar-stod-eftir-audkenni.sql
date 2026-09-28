-- vedurstodvar-stod-eftir-audkenni.sql
-- Spurning: Hvaða stöð hefur þetta auðkenni? Sama og `station_id=<n>` í beiðninni.
-- Síða: web/sidur/vedurstodvar.html
-- Breytur:
--   ?1 auðkenni stöðvar (station_id)
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.

SELECT station_id, name, abbr, station_type, lat, lon,
       elevation_m, wigos_id, owner, start_year, end_year
FROM weather_stations
WHERE station_id = ?;
