-- hagstofan-fyrirspurn.sql
-- Spurning: Hvaða POST-beiðni (query.json) var send til að fá þessa töflu?
-- Síða: web/sidur/hagstofan.html (beiðnin sýnd — rekjanleiki, regla 8)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id)
--
-- Hleðslan (vinnsla/hagstofan.py) geymir query.json óbreytt í fetch_log.params.
-- Tengt á hráskrána og endapunktinn svo skráningin sé örugglega sú sem
-- gagnasafnið kom úr, en ekki önnur sókn sömu þjónustu.

SELECT f.params, f.record_count
FROM hagstofan_datasets AS d
JOIN fetch_log AS f
  ON f.raw_file = d.raw_file
 AND f.endpoint = d.endpoint
WHERE d.id = ?;
