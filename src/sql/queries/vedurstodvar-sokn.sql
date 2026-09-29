-- vedurstodvar-sokn.sql
-- Spurning: Hvaða eintak stöðvaskrárinnar er í grunninum, af hvaða slóð og
--           hvenær var það sótt?
-- Síða: web/sidur/vedurstodvar.html (sóknardagsetningin, áberandi — #22)
-- Breytur:
--   ?1 heiti safnsins í fetch_log (service, t.d. vedurstofa-stodvar)
--
-- fetched_at verður `uppfaert` í web/gogn/vedurstodvar.json (#15): frosið
-- eintak, ekki lifandi staða. record_count er borið við fjölda í töflunni svo
-- hálf hleðsla fari ekki á vefinn.

SELECT endpoint, params, fetched_at, record_count, raw_file
FROM fetch_log
WHERE service = ?
ORDER BY id;
