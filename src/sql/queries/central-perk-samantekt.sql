-- central-perk-samantekt.sql
-- Spurning: Í hve mörgum handritum syngur Phoebe í Central Perk, í hve mörgum
--           senum, og hve mörgum prósentustigum hærra er miðgildi hlutdeildar
--           hennar í sönghandritunum en í öðrum Central Perk-handritum?
-- Síða: web/sidur/phoebe-central-perk.html (niðurstaðan)
-- Breytur: engar
--
-- Les sýnina central_perk_findings (007). Munurinn er óafrúnnaður
-- (4,203443…); birtingin námundar (docs/adferdafraedi.md 4.1). Notuð líka af
-- vinnsla/central_perk_hledsla.py til að staðfesta hleðsluna.

SELECT transcript_files,
       singing_files,
       singing_scenes,
       median_difference_pp
FROM central_perk_findings;
