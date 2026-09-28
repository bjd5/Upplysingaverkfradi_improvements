-- gagnasofnun-skraning.sql
-- Spurning: Hvaðan og hvenær var safnið sótt — slóð, breytur, sóknartími,
--           fjöldi færslna og hrágagnaskráin sem hlaðið var úr?
-- Síða: web/sidur/hagstofan.html og web/sidur/vedurstodvar.html (heimild og sóknartími)
-- Breytur:
--   ?1 heiti þjónustunnar eins og hleðslan skráði hana (fetch_log.service)
--
-- Les fetch_log (migration 001). Útflutningurinn tekur `uppfaert` úr
-- fetched_at: sóknartíminn er lesinn úr provenance frosna safnsins við hleðslu
-- og er því sá sami í hverri byggingu — ólíkt klukkunni við útflutning, sem
-- gerði úttakið óákvarðað (#47, athugasemd á #14 liður 8).
--
-- id er viljandi ekki valið: það er röð hleðslunnar, ekki eiginleiki gagnanna.

SELECT service,
       endpoint,
       params,
       fetched_at,
       record_count,
       raw_file
FROM fetch_log
WHERE service = ?
ORDER BY fetched_at, raw_file;
