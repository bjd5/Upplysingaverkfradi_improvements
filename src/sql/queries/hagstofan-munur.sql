-- hagstofan-munur.sql
-- Spurning: Hversu mörgum prósentustigum munar á tveimur hópum í sömu stöðu?
--           (t.d. brautskráðir í verkfræði á móti öllum sviðum, eða konur á
--           móti körlum)
-- Síða: web/sidur/hagstofan.html („Svör við æfingaspurningunum“)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id)
--   ?2 stöðukóði (student_status_code, t.d. 5 = brautskráð)
--   ?3 námssvið hóps A (field_code, t.d. 07 eða Alls)
--   ?4 kyn hóps A (sex_code: Alls, 1 = karlar, 2 = konur)
--   ?5 námssvið hóps B
--   ?6 kyn hóps B
--
-- Munurinn er dreginn saman í SQL, A − B, í prósentustigum og óafrúnnaður.
-- Sjálftenging (self-join) í stað tveggja undirfyrirspurna: hvor hópur er
-- nefndur einu sinni og stöðukóðinn aðeins einu sinni, svo hóparnir geta
-- ekki lent í sitt hvorri stöðu. Engin lína ef annar hópurinn finnst ekki.

SELECT a.value - b.value AS difference_pp
FROM hagstofan_labelled_observations AS a
JOIN hagstofan_labelled_observations AS b
  ON b.dataset_id = a.dataset_id
 AND b.student_status_code = a.student_status_code
WHERE a.dataset_id = ?
  AND a.student_status_code = ?
  AND a.field_code = ? AND a.sex_code = ?
  AND b.field_code = ? AND b.sex_code = ?;
