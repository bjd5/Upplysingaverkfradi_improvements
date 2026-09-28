-- friends-nafntilvik-eftir-thattarod.sql
-- Spurning: Hversu oft er Phoebe nefnd í hverri þáttaröð — í tali, í
--           sviðsleiðbeiningum, með formlega nafninu og gælunafni — og hve oft
--           á hvern sýndan þátt?
-- Síða: web/sidur/phoebe-tolfraedi.html (NÆRVERA)
-- Breytur: engar
--
-- dialogue_mentions_per_episode er ÓAFRÚNNAÐ. Í þáttaröð 1 er það
-- 99 / 24 = 4,125 nákvæmlega. SQLite ROUND(…, 2) gefur 4,13 (helmingur frá
-- núlli) en greiningin og gamla síðan sýndu 4,12 (Python námundar helming að
-- sléttri tölu). Þess vegna námundar birtingin, ekki SQL — sjá
-- gagnagrunnur/fyrirspurnir.py og docs/adferdafraedi.md 4.1. Prófið festir
-- tilvikið.

SELECT m.season,
       s.aired_episodes                                 AS episodes,
       m.in_dialogue_by_others,
       m.in_own_dialogue,
       m.in_dialogue_by_others + m.in_own_dialogue      AS in_dialogue,
       m.in_stage_directions,
       m.in_dialogue_by_others + m.in_own_dialogue
           + m.in_stage_directions                      AS mentions_total,
       m.formal_phoebe,
       m.nickname_pheebs,
       1.0 * (m.in_dialogue_by_others + m.in_own_dialogue)
           / s.aired_episodes                           AS dialogue_mentions_per_episode,
       m.top_mentioner,
       m.top_mentioner_count
FROM phoebe_mentions_by_season AS m
JOIN friends_seasons AS s USING (season)
ORDER BY m.season;
