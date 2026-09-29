-- mbl-eintok.sql
-- Spurning: Hvaða eintök af fréttasíðu mbl.is liggja í grunninum — hvenær
--           sótt, af hvaða slóð, í hvaða skrá og með hvaða summu?
-- Síða: web/sidur/mbl-regex.html (sóknartími eintaksins og slóðin)
-- Breytur: engar
--
-- Sóknartíminn (fetched_at) er breytan sem mbl-svor.sql tekur. Nýjasta
-- eintakið er síðast. loaded_at er klukkan við hleðslu og er ekki valið.

SELECT fetched_at,
       source_url,
       raw_file,
       md5,
       content_length_bytes,
       status_code
FROM mbl_snapshots
ORDER BY fetched_at;
