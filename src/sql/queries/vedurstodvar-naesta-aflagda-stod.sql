-- vedurstodvar-naesta-aflagda-stod.sql
-- Spurning: Hver er næsta stöð sem er hætt mælingum? Sýnir hvað munar litlu —
--           röðun eftir fjarlægð einni saman getur skilað ónothæfri stöð.
-- Síða: web/sidur/vedurstodvar.html
-- Breytur:
--   ?1 breidd viðmiðunarpunkts
--   ?2 lengd viðmiðunarpunkts
--
-- Upphaflega ein af tíu nefndum fyrirspurnum í vedurstodvar-siur.sql (#8);
-- klofin í eina skrá á fyrirspurn í #11.
--
-- Fjarlægðin er óafrúnnuð: röðað er á henni og birtingin námundar í heila
-- metra (sjá gagnagrunnur/fyrirspurnir.py). Fallið fjarlaegd_metrar er skráð
-- á tenginguna í vinnsla/vedurstodvar_fyrirspurnir.py (haversine).

SELECT station_id, name, start_year, end_year,
       fjarlaegd_metrar(lat, lon, ?, ?) AS distance_m
FROM weather_stations
WHERE end_year IS NOT NULL
ORDER BY distance_m, station_id
LIMIT 1;
