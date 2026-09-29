-- central-perk-songhandrit.sql
-- Spurning: Í hvaða handritsskrám syngur Phoebe í Central Perk samkvæmt
--           skýrum söngmerkingum?
-- Síða: web/sidur/phoebe-central-perk.html (listinn yfir sönghandritin)
-- Breytur: engar
--
-- Notuð líka af vinnsla/central_perk_hledsla.py: listinn verður að vera
-- singing_episode_ids úr samantektinni, í sömu röð.

SELECT episode_code
FROM central_perk_transcript_files
WHERE group_key = 'phoebe_sings'
ORDER BY episode_code;
