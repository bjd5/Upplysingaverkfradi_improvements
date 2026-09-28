-- skjalftar-dagleg-talning.sql
-- Spurning: Hversu margir skjálftar urðu hvern UTC-dag tímabilsins — líka
--           dagarnir þar sem enginn varð?
-- Síða: web/sidur/skjalftavaktin.html (dagatöflurnar og súluritið)
-- Breytur: engar
--
-- Dagatalið (earthquake_days, migration 002) er vinstra megin í LEFT JOIN og
-- atburðirnir hægra megin. Talið er COUNT(e.event_id), ekki COUNT(*): dagur án
-- atburðar fær eina línu með NULL úr earthquakes og á að teljast 0, ekki 1.
--
-- Fyrirspurn sem telur aðeins raðir í earthquakes (GROUP BY utc_day) skilar
-- 18 dögum í stað 61 og sleppir 43 þögulum dögum — tímaröðin sýnist þá þéttari
-- en hún var. Prófið keyrir þá röngu útgáfu og sýnir að hún fellur.

SELECT d.utc_day,
       COUNT(e.event_id) AS event_count
FROM earthquake_days AS d
LEFT JOIN earthquakes AS e ON e.utc_day = d.utc_day
GROUP BY d.utc_day
ORDER BY d.utc_day;
