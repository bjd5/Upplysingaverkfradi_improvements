-- hagstofan-utflutningur.sql
-- Fyrirspurnirnar sem útflutningurinn í web/gogn/hagstofan.json keyrir á
-- töflur migration 003 (og fetch_log úr 001). Issue #15.
--
-- Útflutningurinn les EINGÖNGU úr grunninum — aldrei úr data/raw/ né
-- data/processed/ beint (kafli 0 í CLAUDE.md). Allar tölur sem síðan birtir
-- eru rúnnaðar HÉR, með ROUND(..., :aukastafir), svo vafrinn þurfi aldrei að
-- reikna né námunda (issue #15).
--
-- SNIÐ: hver fyrirspurn hefst á línunni `-- @fyrirspurn: <heiti>`, sama snið
-- og vedurstodvar-siur.sql. `src/python/utflutningur/sql_safn.py` les skrána.
--
-- ÖLL GILDI KOMA INN SEM NEFNDAR BREYTUR (`:heiti`) — aldrei
-- strengjasamsetning (regla 5).


-- @fyrirspurn: gagnasafn
-- Lýsigögn töflunnar og sóknartíminn. `fetched_at` er okkar eigin sóknartími
-- úr provenance.json og verður `uppfaert` í útfluttu skránni; `updated` úr
-- svarinu (9999-12-31T23:59:59Z) er ekki nothæf dagsetning og er aðeins
-- flutt út sem lýsigagn.
SELECT id, label, source, endpoint, fetched_at, updated,
       jsonstat_version, decimals, value_count, raw_file
FROM hagstofan_datasets
WHERE id = :gagnasafn;


-- @fyrirspurn: fyrirspurn
-- POST-beiðnin (query.json) eins og hún var send. Hleðslan geymir hana
-- óbreytta í fetch_log.params; tengt á hráskrána og endapunktinn svo
-- skráningin sé örugglega sú sem gagnasafnið kom úr.
SELECT f.params, f.record_count
FROM hagstofan_datasets AS d
JOIN fetch_log AS f
  ON f.raw_file = d.raw_file
 AND f.endpoint = d.endpoint
WHERE d.id = :gagnasafn;


-- @fyrirspurn: viddir
-- Víddirnar sex í röð `id` — röðin ræður því hvernig flati listinn er lesinn.
SELECT code, label, position, size, is_time
FROM hagstofan_dimensions
WHERE dataset_id = :gagnasafn
ORDER BY position;


-- @fyrirspurn: viddargildi
-- Kóðabókin: öll leyfð gildi hverrar víddar, valin og óvalin. Valin gildi
-- fyrst, í röð `category.index`; óvalin á eftir í kóðaröð (þau eiga sér
-- enga stöðu í svarinu).
SELECT v.dimension_code, v.code, v.label, v.selected, v.value_index
FROM hagstofan_dimension_values AS v
JOIN hagstofan_dimensions AS d
  ON d.dataset_id = v.dataset_id
 AND d.code = v.dimension_code
WHERE v.dataset_id = :gagnasafn
ORDER BY d.position, v.value_index IS NULL, v.value_index, v.code;


-- @fyrirspurn: nidurstodur
-- Ein lína á hverja samsetningu námssviðs og kyns, stöðuflokkarnir þrír sem
-- dálkar. Kóðar stöðuflokkanna koma inn sem breytur. `fjoldi_maelinga` er
-- með svo útflutningurinn geti staðfest að hver lína byggi á nákvæmlega einni
-- mælingu í hverjum flokki — MAX() myndi annars fela tvítekningu.
-- `samtals` er summa ÓRÚNNAÐRA gilda, rúnnuð í lokin (99,9–100,1).
SELECT o.field_code,
       fs.label AS field_label,
       o.sex_code,
       sx.label AS sex_label,
       ROUND(MAX(CASE WHEN o.student_status_code = :brautskradir THEN o.value END),
             :aukastafir) AS brautskradir,
       ROUND(MAX(CASE WHEN o.student_status_code = :brottfallnir THEN o.value END),
             :aukastafir) AS brottfallnir,
       ROUND(MAX(CASE WHEN o.student_status_code = :enn_i_nami THEN o.value END),
             :aukastafir) AS enn_i_nami,
       ROUND(SUM(o.value), :aukastafir) AS samtals,
       COUNT(*) AS fjoldi_maelinga
FROM hagstofan_observations AS o
JOIN hagstofan_dimension_values AS fs
  ON fs.dataset_id = o.dataset_id
 AND fs.dimension_code = o.field_dim
 AND fs.code = o.field_code
JOIN hagstofan_dimension_values AS sx
  ON sx.dataset_id = o.dataset_id
 AND sx.dimension_code = o.sex_dim
 AND sx.code = o.sex_code
WHERE o.dataset_id = :gagnasafn
GROUP BY o.field_code, o.sex_code
ORDER BY fs.value_index, sx.value_index;


-- @fyrirspurn: munur_brautskradra
-- Mismunur brautskráningarhlutfalls tveggja hópa, í prósentustigum.
-- Reiknaður á órúnnuðum gildum og rúnnaður í lokin — ekki mismunur tveggja
-- rúnnaðra talna.
SELECT ROUND(
    (SELECT value FROM hagstofan_observations
      WHERE dataset_id = :gagnasafn AND student_status_code = :brautskradir
        AND field_code = :svid_a AND sex_code = :kyn_a)
  - (SELECT value FROM hagstofan_observations
      WHERE dataset_id = :gagnasafn AND student_status_code = :brautskradir
        AND field_code = :svid_b AND sex_code = :kyn_b),
    :aukastafir) AS prosentustig;
