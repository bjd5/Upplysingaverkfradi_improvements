-- mbl-svor.sql
-- Spurning: Hver eru svörin við spurningunum fimm úr frosna eintakinu af
--           fréttasíðu mbl.is — og með hvaða mynstri og úr hvaða eintaki
--           fékkst hvert þeirra?
-- Síða: web/sidur/mbl-regex.html
-- Breytur:
--   ?1 sóknartími eintaksins (mbl_snapshots.fetched_at, ISO 8601 UTC)
--   ?2 lykill spurningar (question_key), eða NULL fyrir allar fimm
--   ?3 sami lykill aftur (sama gildi og ?2)
--
-- Eitt svar á spurningu, ásamt mynstrinu sem framkallaði það og eintakinu
-- sem það var lesið úr, svo talan sé rekjanleg alla leið í hrágagnið
-- (regla 8). ?2 og ?3 eru sama gildið: „(? IS NULL OR key = ?)“ gerir einni
-- fyrirspurn kleift að svara einni spurningu eða öllum án þess að setja
-- skilyrðið saman úr strengjum (regla 5).
--
-- Áður tvítekin: SVOR_SQL í tests/mbl_grunnur.py og STADFESTA_SQL í
-- vinnsla/mbl_hledsla.py. Báðar lesa nú þessa skrá.

SELECT e.question_number AS nr,
       e.question_key    AS lykill,
       e.question_is     AS spurning,
       e.value_number    AS gildi,
       e.value_text      AS svar,
       e.unit            AS eining,
       e.pattern_name    AS mynsturheiti,
       e.pattern         AS mynstur,
       e.pattern_flags   AS mynsturflogg,
       e.scope_name      AS afmorkun,
       e.scope_pattern   AS afmorkunarmynstur,
       e.match_count     AS tilvik,
       e.distinct_count  AS einstok,
       e.sample_match    AS synishorn,
       e.notes           AS takmarkanir,
       s.raw_file        AS eintak,
       s.fetched_at      AS sott,
       s.source_url      AS upprunaslod
  FROM mbl_extractions e
  JOIN mbl_snapshots   s ON s.id = e.snapshot_id
 WHERE s.fetched_at = ?
   AND (? IS NULL OR e.question_key = ?)
 ORDER BY e.question_number;
