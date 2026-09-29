-- central-perk-hopar.sql
-- Spurning: Hve mörg handrit eru í hverjum samanburðarhópi, og hvert er
--           miðgildi og meðaltal hlutdeildar Phoebe og miðgildi hlutfallsins
--           „hinir fimm á móti Phoebe“ í hverjum?
-- Síða: web/sidur/phoebe-central-perk.html (samanburðartaflan)
-- Breytur: engar
--
-- Les sýnina central_perk_group_summary (007), í birtingarröð: engin Central
-- Perk-sena, Central Perk án söngs, Phoebe syngur. Hlutdeild er 0–1 og
-- óafrúnnuð; transcript_files er COUNT() úr handritstöflunni.

SELECT group_key,
       transcript_files,
       median_phoebe_share,
       mean_phoebe_share,
       median_friends_to_phoebe_ratio
FROM central_perk_group_summary
ORDER BY display_order;
