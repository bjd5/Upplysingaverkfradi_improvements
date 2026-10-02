-- central-perk-frosnar-skrar.sql
-- Spurning: Hvaða frosnu skrár voru hlaðnar í Central Perk-töflurnar, og með
--           hvaða SHA-256 summu voru þær staðfestar?
-- Síða: web/sidur/phoebe-central-perk.html (rekjanleiki)
-- Breytur: engar
--
-- Summan er lykillinn að provenance-skránni (central-perk-uppruni.sql): þar
-- stendur hvenær greiningin skrifaði hverja skrá (breytt_utc). Það er
-- gagnastimpillinn sem verður `uppfaert` — ekki klukkan við hleðslu.

SELECT file_name,
       sha256,
       size_bytes
FROM central_perk_source_files
ORDER BY file_name;
