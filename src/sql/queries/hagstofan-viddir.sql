-- hagstofan-viddir.sql
-- Spurning: Hverjar eru víddir json-stat2-svarsins, í hvaða röð og hve stórar?
-- Síða: web/sidur/hagstofan.html (hvernig flati gildalistinn er lesinn)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id)
--
-- Röðin (`position`, röð `id` í svarinu) ræður því hvernig flati listinn er
-- lesinn: síðasta víddin breytist hraðast. Margfeldi stærðanna er fjöldi gilda.

SELECT code, label, position, size, is_time
FROM hagstofan_dimensions
WHERE dataset_id = ?
ORDER BY position;
