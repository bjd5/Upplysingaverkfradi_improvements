-- friends-umfang.sql
-- Spurning: Hversu stórt er handritasafnið — hve margar handritsskrár voru
--           greindar, hve marga sýnda þætti þær geyma og hve margar skrár
--           voru undanskildar?
-- Síða: web/sidur/phoebe-tolfraedi.html („Gögnin“)
-- Breytur: engar
--
-- 227 skrár svara til 236 sýndra þátta, því 9 skrár geyma tvo þætti (006).
-- Þættirnir eru taldir úr friends_seasons (episodes_per_season), skrárnar úr
-- friends_transcript_files; hleðslan staðfestir að summurnar stemmi.

SELECT (SELECT COUNT(*) FROM friends_transcript_files)          AS transcript_files,
       (SELECT SUM(aired_episodes) FROM friends_seasons)         AS aired_episodes,
       (SELECT COUNT(*) FROM friends_transcript_files
         WHERE aired_episodes = 2)                               AS double_episode_files,
       (SELECT COUNT(*) FROM friends_seasons)                    AS seasons,
       (SELECT COUNT(*) FROM friends_excluded_files)             AS excluded_files;
