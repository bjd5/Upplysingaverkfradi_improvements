-- central-perk-segdir.sql
-- Spurning: Hvaða reglulegu segðir ákváðu senur, ræðumenn, söng og orð, og
--           hvað grípa þær og hvað sleppur?
-- Síða: web/sidur/phoebe-central-perk.html (aðferðin)
-- Breytur: engar

SELECT pattern_name,
       pattern,
       catches,
       misses
FROM central_perk_patterns
ORDER BY display_order;
