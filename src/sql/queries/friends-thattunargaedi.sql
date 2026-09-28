-- friends-thattunargaedi.sql
-- Spurning: Hversu vel tókst að þátta handritin — hve margar textablokkir
--           urðu tilsvör, sviðsfyrirsagnir, sviðsleiðbeiningar og óflokkað?
-- Síða: web/sidur/phoebe-tolfraedi.html („Gögnin“ og takmarkanir)
-- Breytur: engar
--
-- Les sýnina friends_parse_quality (migration 006) í stað þess að endurtaka
-- hana. Notuð líka af vinnsla/friends_hledsla.py, sem stöðvar hleðsluna ef
-- svarið víkur frá _meta.json — hleðslan staðfestir því nákvæmlega þá tölu
-- sem síðan birtir.
--
-- UNDANTEKNING FRÁ NÁMUNDUNARVENJUNNI: unclassified_pct er námundað í sýninni
-- (ROUND(…, 2) í 006, sem er ekki breytt — regla 5). Óafrúnnað gildi er
-- 2,9453…, fjarri helmingi, svo SQLite og Python gefa bæði 2,95; prófið
-- staðfestir það. Birting sem þarf aðra nákvæmni reiknar úr unclassified og
-- total_blocks.

SELECT total_blocks, speaker_lines, scene_headings, stage_directions,
       unclassified, unclassified_pct
FROM friends_parse_quality;
