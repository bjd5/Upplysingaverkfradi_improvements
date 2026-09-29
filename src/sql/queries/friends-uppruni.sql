-- friends-uppruni.sql
-- Spurning: Úr hvaða handritasafni og hvaða greiningu koma Friends-tölurnar,
--           hvenær voru þær reiknaðar og hvaða leyfi gildir?
-- Síða: web/sidur/phoebe-tolfraedi.html (heimild og takmarkanir)
-- Breytur: engar
--
-- analysis_generated_utc er gagnastimpillinn: hvenær greiningin reiknaði
-- tölurnar. Hann er sá sami í hverri byggingu og er því `uppfaert` í
-- útflutningnum. loaded_at er klukkan við hleðslu og er ekki valið.

SELECT transcript_repository,
       transcript_commit,
       analysis_repository,
       analysis_commit,
       analysis_script,
       analysis_generated_utc,
       licence
FROM friends_sources;
