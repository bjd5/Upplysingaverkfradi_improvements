-- central-perk-uppruni.sql
-- Spurning: Úr hvaða handritasafni og hvaða greiningu koma Central Perk-tölurnar,
--           hvaða leyfi gildir og hvar er summa frosnu skránna skráð?
-- Síða: web/sidur/phoebe-central-perk.html (heimild og takmarkanir)
-- Breytur: engar
--
-- Les central_perk_sources (007). provenance_file er skráin sem geymir
-- SHA-256 og breytingartíma frosnu skránna; útflutningurinn tekur `uppfaert`
-- þaðan (sjá central-perk-frosnar-skrar.sql). loaded_at er klukkan við
-- hleðslu og er viljandi ekki valið.

SELECT transcript_repository,
       transcript_commit,
       analysis_repository,
       analysis_commit,
       analysis_script,
       input_directory,
       provenance_file,
       licence
FROM central_perk_sources;
