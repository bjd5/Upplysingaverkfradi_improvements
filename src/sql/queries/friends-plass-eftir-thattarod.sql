-- friends-plass-eftir-thattarod.sql
-- Spurning: Hvert er pláss hvers vinar í hverri þáttaröð — línur, orð,
--           hlutdeild í línum þáttaraðarinnar og sæti innan hennar?
-- Síða: web/sidur/phoebe-tolfraedi.html (PLÁSS eftir þáttaröð)
-- Breytur: engar
--
-- Röðunin er innan þáttaraðar: RANK() OVER (PARTITION BY season …). Sæti yfir
-- allar þáttaraðir í einu segði ekkert um hvort Phoebe færðist upp eða niður.
-- Línur og orð á þáttaröð eru SUM() úr friends_episode_lines — ekki geymd
-- aftur (006) — og hlutdeildin er reiknuð úr sömu summum.
-- line_share_pct er óafrúnnað; birtingin námundar (tveir aukastafir).

WITH season_lines AS (
    SELECT t.season,
           l.character_name,
           SUM(l.lines) AS lines,
           SUM(l.words) AS words
    FROM friends_episode_lines AS l
    JOIN friends_transcript_files AS t USING (episode_code)
    GROUP BY t.season, l.character_name
)
SELECT season,
       character_name,
       lines,
       words,
       100.0 * lines / SUM(lines) OVER (PARTITION BY season)        AS line_share_pct,
       RANK() OVER (PARTITION BY season ORDER BY lines DESC)         AS rank_by_lines
FROM season_lines
ORDER BY season, rank_by_lines, character_name;
