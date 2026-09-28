-- vedurstodvar-fjoldi-virkra.sql
-- Spurning: Hversu margar stöðvanna eru virkar (`active=true`)?
-- Síða: web/sidur/vedurstodvar.html
-- Breytur: engar
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.

SELECT COUNT(*) AS station_count
FROM weather_stations
WHERE end_year IS NULL;
