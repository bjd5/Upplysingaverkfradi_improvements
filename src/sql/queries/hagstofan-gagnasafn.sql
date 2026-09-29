-- hagstofan-gagnasafn.sql
-- Spurning: Hvaða tafla er þetta, hvaðan var hún sótt og hvenær?
-- Síða: web/sidur/hagstofan.html (heimild, slóð þjónustunnar og sóknardagsetning)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id, t.d. SKO04208b)
--
-- fetched_at er okkar eigin sóknartími úr provenance.json og verður `uppfaert`
-- í web/gogn/hagstofan.json (#15). `updated` úr svarinu (9999-12-31T23:59:59Z)
-- er ekki nothæf dagsetning og er aðeins flutt út sem lýsigagn; sama um
-- `decimals` (0 þótt gildin hafi aukastaf).

SELECT id, label, source, endpoint, fetched_at, updated,
       jsonstat_version, decimals, value_count, raw_file
FROM hagstofan_datasets
WHERE id = ?;
