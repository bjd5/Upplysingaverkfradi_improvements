-- hagstofan-gagnasafn.sql
-- Spurning: Hvaða tafla Hagstofunnar liggur í grunninum — auðkenni, heiti,
--           heimild, slóð og hvenær hún var sótt?
-- Síða: web/sidur/hagstofan.html (heimild, sóknardagsetning og slóð þjónustunnar)
-- Breytur: engar
--
-- Auðkennið (id) er breytan sem hinar Hagstofufyrirspurnirnar taka; útflutningurinn
-- les það hér í stað þess að slá töfluheitið inn í kóða.
--
-- `updated` er viljandi ekki valið: frysta svarið gefur 9999-12-31T23:59:59Z,
-- sem er ekki dagsetning (sjá 003). Sóknartíminn er fetched_at. loaded_at er
-- klukkan við hleðslu og á ekkert erindi á síðuna.

SELECT id,
       label,
       source,
       endpoint,
       fetched_at,
       jsonstat_version,
       value_count,
       raw_file
FROM hagstofan_datasets
ORDER BY id;
