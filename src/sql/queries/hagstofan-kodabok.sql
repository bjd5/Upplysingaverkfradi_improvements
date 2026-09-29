-- hagstofan-kodabok.sql
-- Spurning: Hvaða kóðar standa til boða í hverri vídd, hvað heita þeir og
--           hverjir voru valdir í fyrirspurninni?
-- Síða: web/sidur/hagstofan.html (afmörkunin og víddalýsingin)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id)
--
-- Valin gildi fyrst, í röð `category.index` (value_index); óvalin á eftir í
-- kóðaröð, því þau eiga sér enga stöðu í svarinu.

SELECT v.dimension_code, v.code, v.label, v.selected, v.value_index
FROM hagstofan_dimension_values AS v
JOIN hagstofan_dimensions AS d
  ON d.dataset_id = v.dataset_id
 AND d.code = v.dimension_code
WHERE v.dataset_id = ?
ORDER BY d.position, v.value_index IS NULL, v.value_index, v.code;
