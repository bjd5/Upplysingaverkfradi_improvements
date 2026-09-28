-- hagstofan-summur.sql
-- Spurning: Leggjast stöðuflokkarnir þrír saman í 100 % fyrir hvert námssvið
--           og kyn? (sama hópur, sama viðmiðunartími)
-- Síða: web/sidur/hagstofan.html (skýringin „námundun getur gefið 99,9 eða 100,1“)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id)
--
-- Summa óafrúnnaðra gilda. Hagstofan birtir hvert hlutfall á einum aukastaf,
-- svo summan getur verið 99,9 eða 100,1 — það er námundun í heimildinni,
-- ekki villa í gögnunum.

SELECT field_code, field_label,
       sex_code, sex_label,
       SUM(value) AS percentage_sum
FROM hagstofan_labelled_observations
WHERE dataset_id = ?
GROUP BY field_code, sex_code
ORDER BY field_code, sex_code;
