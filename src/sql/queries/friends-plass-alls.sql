-- friends-plass-alls.sql
-- Spurning: Hversu margar línur og orð á hver vinanna sex yfir alla þættina,
--           og í hvaða sæti er hver eftir línufjölda?
-- Síða: web/sidur/phoebe-tolfraedi.html (PLÁSS)
-- Breytur: engar
--
-- Les sýnina friends_character_totals (006). Notuð líka af
-- vinnsla/friends_hledsla.py til að staðfesta línur og orð við _meta.json.
-- RANK (ekki ROW_NUMBER): jafnmargar línur gæfu sama sæti.

SELECT character_name,
       lines,
       words,
       RANK() OVER (ORDER BY lines DESC) AS rank_by_lines
FROM friends_character_totals
ORDER BY rank_by_lines, character_name;
