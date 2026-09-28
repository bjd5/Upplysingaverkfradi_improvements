-- central-perk-handrit.sql
-- Spurning: Hver er hlutdeild Phoebe af orðum aðalpersónanna sex í hverri
--           handritsskrá, og í hvaða samanburðarhópi er skráin?
-- Síða: web/sidur/phoebe-central-perk.html (punktaritið og taflan undir því)
-- Breytur: engar
--
-- Handritastigið er aðeins til frosið með einum aukastaf (SVG-myndin), geymt
-- sem prómill. Deilt með 10,0 gefur prósentuna nákvæmlega eins og myndin
-- sýndi hana — engin frekari námundun.

SELECT f.episode_code,
       f.group_key,
       f.phoebe_share_permille / 10.0 AS phoebe_share_pct
FROM central_perk_transcript_files AS f
JOIN central_perk_groups AS g USING (group_key)
ORDER BY g.display_order, f.episode_code;
