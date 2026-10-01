-- skjalftar-syni.sql
-- Spurning: Hvernig líta fyrstu atburðirnir út eins og þeir koma úr hrágögnunum?
-- Síða: web/sidur/skjalftavaktin.html („Hrátt sýni“)
-- Breytur: engar
--
-- Fyrstu átta atburðirnir í tímaröð, frumgildin óbreytt. Átta er nóg til að
-- sýna alla reiti án þess að skráin og síðan fyllist af línum.

SELECT event_id, occurred_at, magnitude, magnitude_type, depth_km,
       latitude, longitude
FROM earthquakes
ORDER BY occurred_at, event_id
LIMIT 8;
