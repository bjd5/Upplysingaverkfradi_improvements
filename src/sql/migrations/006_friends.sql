-- 006_friends.sql
-- Friends-handritin og Phoebe Buffay — afleiddar tölur (issue #10).
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).
--
-- HVAÐAN GÖGNIN KOMA (regla 5)
--   Handritasafn: delvinso/friends @ a4641fed3d95bb9d9c7ba23681604c692f9b392a
--                 (afleiða af fangj/friends; HTML-handrit, season/*.html).
--   Greining:     src/phoebe_analysis.py í upprunaverkefninu
--                 Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe @ 2865ed6,
--                 keyrð 2026-09-17T09:47:09Z.
--   Aðfang hér:   data/processed/phoebe-stats/ — 17 skrár, bætaeins viðmiðinu
--                 docs/vidmid/phoebe-stats/; SHA-256 hverrar skrár er í
--                 docs/vidmid/provenance.json (safnið „phoebe-stats“) og er
--                 staðfest áður en hleðsla hefst (vinnsla.friends_skrar).
--   Heimildaskrá: docs/heimildir.md kafli 2.1.
--
-- LEYFI — OG AF HVERJU ENGINN HANDRITSTEXTI ER HÉR (issue #3, valkostur A)
--   fangj/friends hefur ekkert leyfi: það er safn afritaðra handrita aðdáenda
--   á höfundarréttarvörðu sjónvarpsefni. MIT-leyfi delvinso/friends nær yfir
--   kóðann þar, ekki endilega yfir handritatextann. Þess vegna geymir ENGIN
--   tafla hér samfelldan handritstexta — ekki eitt tilsvar. Grunnurinn geymir
--   talningar, hlutföll og ræðuskipti: staðreyndir UM textann. Einu textagildin
--   eru persónunöfn, þáttatitlar, skráarheiti og stök orð/orðtök úr
--   tíðnitöflunum, og hvert þeirra stendur þegar í talnaskránum (prófað í
--   tests/test_friends_sannreyning.py). Afleiðingin: línutaflan sem issue #10
--   gerði ráð fyrir („ein lína á tilsvar“) er ekki til — fínasta kornið er
--   ein persóna í einni handritsskrá (friends_episode_lines).
--
-- SKILGREININGAR SEM TÖLURNAR HVÍLA Á (óbreyttar úr greiningunni)
--   Lína     = ein „Nafn: texti“-blokk. Hóplínur („All:“, „Monica and
--              Phoebe:“) eru ekki eignaðar neinum; Phoebe Sr og Ursula teljast
--              ekki sem Phoebe.
--   Orð      = [a-z][a-z'-]* eftir að svigainnskot voru fjarlægð.
--   Skrá     = ein HTML-handritsskrá. 227 skrár svara til 236 sýndra þátta,
--              því 9 skrár geyma tvo þætti. 0423uncut.html og 07outtakes.html
--              eru undanskildar.
--
-- PERSÓNUR SEM FRAMANDI LYKLAR
--   Tölur sem eiga aðeins við vinina sex bera dálkinn is_friend, njörvaðan við
--   1 með CHECK, og samsettan framandi lykil (nafn, is_friend) í
--   friends_characters. Sama bragð og *_dim í 003: án þess gæti gestapersóna
--   ratað í töflu sem á aðeins við vinina sex.

-- Uppruni hleðslunnar: ein lína. Hleðslan skrifar hana og ekkert annað.
CREATE TABLE IF NOT EXISTS friends_sources (
    id                     INTEGER PRIMARY KEY CHECK (id = 1),
    transcript_repository  TEXT    NOT NULL,  -- delvinso/friends
    transcript_commit      TEXT    NOT NULL,  -- full commit-SHA safnsins sem var greint
    analysis_repository    TEXT    NOT NULL,  -- upprunaverkefnið
    analysis_commit        TEXT    NOT NULL,  -- commit greiningarskriftunnar
    analysis_script        TEXT    NOT NULL,  -- `generator` úr _meta.json
    analysis_generated_utc TEXT    NOT NULL,  -- `generated_utc` úr _meta.json — gagnastimpill
    stats_directory        TEXT    NOT NULL,  -- data/processed/phoebe-stats
    provenance_file        TEXT    NOT NULL,  -- skráin sem geymir SHA-256 summurnar
    licence                TEXT    NOT NULL,  -- leyfisstaðan í stuttu máli
    loaded_at              TEXT    NOT NULL,  -- ISO 8601, UTC — klukkan við hleðslu
    CHECK (length(transcript_commit) = 40
           AND transcript_commit NOT GLOB '*[^0-9a-f]*'),
    CHECK (analysis_commit <> '' AND analysis_commit NOT GLOB '*[^0-9a-f]*')
);

-- Talnaskrárnar sem voru lesnar, hver með summunni sem hún var staðfest gegn.
CREATE TABLE IF NOT EXISTS friends_source_files (
    file_name  TEXT    PRIMARY KEY,           -- heiti í data/processed/phoebe-stats/
    sha256     TEXT    NOT NULL,              -- úr docs/vidmid/provenance.json
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    CHECK (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*')
);

-- Gæðamat þáttunarinnar (`parse_quality` í _meta.json): hver textablokk
-- handritanna lenti í nákvæmlega einum flokki. Óflokkaðar blokkir eru TALDAR
-- en ekki hentar — hlutfall þeirra er gæðamælikvarði sem birtist á síðunni.
CREATE TABLE IF NOT EXISTS friends_parse_blocks (
    block_kind TEXT    PRIMARY KEY CHECK (block_kind IN (
                   'speaker_line', 'scene_heading', 'stage_direction', 'unclassified')),
    blocks     INTEGER NOT NULL CHECK (typeof(blocks) = 'integer' AND blocks >= 0)
);

-- Þáttaraðirnar tíu og fjöldi SÝNDRA þátta í hverri (`episodes_per_season`).
CREATE TABLE IF NOT EXISTS friends_seasons (
    season         INTEGER PRIMARY KEY CHECK (season BETWEEN 1 AND 10),
    aired_episodes INTEGER NOT NULL CHECK (aired_episodes BETWEEN 1 AND 30)
);

-- Handritsskrárnar 227 (phoebe-per-episode.csv). Þáttakóðinn er skráarheitið
-- án .html: SSTT eða SSTT-SSTT, og tveir fyrstu stafirnir eru þáttaröðin.
CREATE TABLE IF NOT EXISTS friends_transcript_files (
    episode_code   TEXT    PRIMARY KEY,
    season         INTEGER NOT NULL REFERENCES friends_seasons (season),
    title          TEXT    NOT NULL CHECK (title <> ''),   -- <title> handritsins
    aired_episodes INTEGER NOT NULL CHECK (aired_episodes IN (1, 2)),
    CHECK (episode_code GLOB '[0-9][0-9][0-9][0-9]'
           OR episode_code GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'),
    CHECK (CAST(substr(episode_code, 1, 2) AS INTEGER) = season)
);

-- Skrárnar tvær sem voru EKKI greindar: 0423uncut.html (óklippt útgáfa þáttar
-- sem er þegar með) og 07outtakes.html (upptökuafgangur, aldrei sýndur).
CREATE TABLE IF NOT EXISTS friends_excluded_files (
    file_name TEXT PRIMARY KEY CHECK (file_name GLOB '*.html')
);

-- Persónur sem tölurnar nefna: vinirnir sex og gestirnir sem tala við Phoebe.
CREATE TABLE IF NOT EXISTS friends_characters (
    character_name TEXT    PRIMARY KEY CHECK (character_name <> ''),
    is_friend      INTEGER NOT NULL CHECK (is_friend IN (0, 1)),
    UNIQUE (character_name, is_friend)
);

-- PLÁSS: línur og orð hvers vinar í hverri handritsskrá (227 × 6).
CREATE TABLE IF NOT EXISTS friends_episode_lines (
    episode_code   TEXT    NOT NULL REFERENCES friends_transcript_files (episode_code),
    character_name TEXT    NOT NULL,
    is_friend      INTEGER NOT NULL DEFAULT 1 CHECK (is_friend = 1),
    lines          INTEGER NOT NULL CHECK (typeof(lines) = 'integer' AND lines >= 0),
    words          INTEGER NOT NULL CHECK (typeof(words) = 'integer' AND words >= 0),
    PRIMARY KEY (episode_code, character_name),
    FOREIGN KEY (character_name, is_friend)
        REFERENCES friends_characters (character_name, is_friend)
);

-- PLÁSS og NÆRVERA eftir þáttaröð: það sem ekki er summa úr skránum hér að
-- ofan (phoebe-screentime-by-season.csv). Línur og orð á þáttaröð eru EKKI
-- geymd aftur; þau eru SUM() úr friends_episode_lines og hleðslan staðfestir
-- að sú summa sé sú sama og skráin segir.
CREATE TABLE IF NOT EXISTS friends_season_characters (
    season           INTEGER NOT NULL REFERENCES friends_seasons (season),
    character_name   TEXT    NOT NULL,
    is_friend        INTEGER NOT NULL DEFAULT 1 CHECK (is_friend = 1),
    characters_typed INTEGER NOT NULL CHECK (characters_typed >= 0),  -- stafafjöldi tilsvara
    speaking_scenes  INTEGER NOT NULL CHECK (speaking_scenes >= 0),   -- senur þar sem hún/hann talar
    PRIMARY KEY (season, character_name),
    FOREIGN KEY (character_name, is_friend)
        REFERENCES friends_characters (character_name, is_friend)
);

-- TENGSL: hver svarar hverjum meðal vinanna (interaction-matrix.csv).
CREATE TABLE IF NOT EXISTS friends_interactions (
    speaker             TEXT    NOT NULL,
    speaker_is_friend   INTEGER NOT NULL DEFAULT 1 CHECK (speaker_is_friend = 1),
    addressee           TEXT    NOT NULL,
    addressee_is_friend INTEGER NOT NULL DEFAULT 1 CHECK (addressee_is_friend = 1),
    lines               INTEGER NOT NULL CHECK (lines >= 0),
    PRIMARY KEY (speaker, addressee),
    CHECK (speaker <> addressee),
    FOREIGN KEY (speaker, speaker_is_friend)
        REFERENCES friends_characters (character_name, is_friend),
    FOREIGN KEY (addressee, addressee_is_friend)
        REFERENCES friends_characters (character_name, is_friend)
);

-- TENGSL: ræðuskipti við Phoebe, allar persónur sem talnaskrárnar nefna
-- (speaks-with-phoebe.csv). adjacent_turns = summa dálkanna tveggja.
CREATE TABLE IF NOT EXISTS phoebe_exchanges (
    character_name    TEXT    PRIMARY KEY REFERENCES friends_characters (character_name),
    replies_to_phoebe INTEGER NOT NULL CHECK (replies_to_phoebe >= 0),  -- talar strax á eftir henni
    phoebe_replies_to INTEGER NOT NULL CHECK (phoebe_replies_to >= 0),  -- hún talar strax á eftir
    shared_scenes     INTEGER NOT NULL CHECK (shared_scenes >= 0),      -- senur þar sem bæði tala
    CHECK (character_name <> 'Phoebe')
);

-- TENGSL: viðbótarmælingar sem eru aðeins til fyrir vinina fimm
-- (phoebe-top-talkers.csv). Afleiddu dálkarnir þar — hlutdeildir,
-- interaction_lift og röð — eru ekki geymdir; sýnin phoebe_interaction_lift
-- reiknar þá og hleðslan stöðvast ef hún fær annað en skráin.
CREATE TABLE IF NOT EXISTS phoebe_friend_interactions (
    character_name              TEXT    PRIMARY KEY,
    is_friend                   INTEGER NOT NULL DEFAULT 1 CHECK (is_friend = 1),
    two_person_scene_lines      INTEGER NOT NULL CHECK (two_person_scene_lines >= 0),
    lines_mentioning_phoebe     INTEGER NOT NULL CHECK (lines_mentioning_phoebe >= 0),
    lines_naming_phoebe_at_edge INTEGER NOT NULL CHECK (lines_naming_phoebe_at_edge >= 0),
    CHECK (character_name <> 'Phoebe'),
    CHECK (lines_naming_phoebe_at_edge <= lines_mentioning_phoebe),
    FOREIGN KEY (character_name, is_friend)
        REFERENCES friends_characters (character_name, is_friend),
    FOREIGN KEY (character_name) REFERENCES phoebe_exchanges (character_name)
);

-- TENGSL eftir þáttaröð (phoebe-top-talkers-by-season.csv).
CREATE TABLE IF NOT EXISTS phoebe_exchanges_by_season (
    season            INTEGER NOT NULL REFERENCES friends_seasons (season),
    character_name    TEXT    NOT NULL,
    is_friend         INTEGER NOT NULL DEFAULT 1 CHECK (is_friend = 1),
    replies_to_phoebe INTEGER NOT NULL CHECK (replies_to_phoebe >= 0),
    phoebe_replies_to INTEGER NOT NULL CHECK (phoebe_replies_to >= 0),
    PRIMARY KEY (season, character_name),
    CHECK (character_name <> 'Phoebe'),
    FOREIGN KEY (character_name, is_friend)
        REFERENCES friends_characters (character_name, is_friend)
);

-- NÆRVERA: nafntilvik Phoebe eftir þáttaröð (phoebe-mentions-by-season.csv).
-- Nafnmyndir: \bph(oe|ee)b\w*\b. Samtölur, tilvik á þátt og breyting milli
-- þáttaraða eru afleiddar og ekki geymdar.
CREATE TABLE IF NOT EXISTS phoebe_mentions_by_season (
    season                  INTEGER PRIMARY KEY REFERENCES friends_seasons (season),
    in_dialogue_by_others   INTEGER NOT NULL CHECK (in_dialogue_by_others >= 0),
    in_own_dialogue         INTEGER NOT NULL CHECK (in_own_dialogue >= 0),
    in_stage_directions     INTEGER NOT NULL CHECK (in_stage_directions >= 0),
    formal_phoebe           INTEGER NOT NULL CHECK (formal_phoebe >= 0),     -- Phoebe, Phoebe's
    nickname_pheebs         INTEGER NOT NULL CHECK (nickname_pheebs >= 0),   -- Pheebs, Phoebs …
    top_mentioner           TEXT    NOT NULL,
    top_mentioner_is_friend INTEGER NOT NULL DEFAULT 1 CHECK (top_mentioner_is_friend = 1),
    top_mentioner_count     INTEGER NOT NULL CHECK (top_mentioner_count >= 0),
    -- Hvert nafntilvik í tali er annaðhvort formlega nafnið eða gælunafn.
    CHECK (formal_phoebe + nickname_pheebs = in_dialogue_by_others + in_own_dialogue),
    CHECK (top_mentioner_count <= in_dialogue_by_others),
    FOREIGN KEY (top_mentioner, top_mentioner_is_friend)
        REFERENCES friends_characters (character_name, is_friend)
);

-- Einkennisorðtök Phoebe (signature-phrases.csv) — 1–3 orð hvert.
CREATE TABLE IF NOT EXISTS phoebe_signature_phrases (
    phrase       TEXT    PRIMARY KEY CHECK (phrase <> ''),
    occurrences  INTEGER NOT NULL CHECK (occurrences >= 0),
    first_season INTEGER NOT NULL REFERENCES friends_seasons (season),
    last_season  INTEGER NOT NULL REFERENCES friends_seasons (season),
    CHECK (first_season <= last_season)
);

-- Orð sem Phoebe notar hlutfallslega oftar en hinir fimm
-- (phoebe-distinctive-words.csv): z-gildi úr log-odds hlutfalli með
-- Dirichlet-prior. Tíðni á 10.000 orð er afleidd og ekki geymd.
CREATE TABLE IF NOT EXISTS phoebe_distinctive_words (
    word         TEXT    PRIMARY KEY CHECK (word <> '' AND word NOT GLOB '* *'),
    z_score      REAL    NOT NULL,
    phoebe_count INTEGER NOT NULL CHECK (phoebe_count > 0),
    others_count INTEGER NOT NULL CHECK (others_count >= 0)
);

-- Gæðamatið í einni línu: samtala blokka og hlutfall óflokkaðra (%).
CREATE VIEW IF NOT EXISTS friends_parse_quality AS
SELECT
    SUM(blocks)                                                   AS total_blocks,
    SUM(CASE block_kind WHEN 'speaker_line'    THEN blocks END)   AS speaker_lines,
    SUM(CASE block_kind WHEN 'scene_heading'   THEN blocks END)   AS scene_headings,
    SUM(CASE block_kind WHEN 'stage_direction' THEN blocks END)   AS stage_directions,
    SUM(CASE block_kind WHEN 'unclassified'    THEN blocks END)   AS unclassified,
    ROUND(100.0 * SUM(CASE block_kind WHEN 'unclassified' THEN blocks END)
          / SUM(blocks), 2)                                       AS unclassified_pct
FROM friends_parse_blocks;

-- PLÁSS yfir alla þættina: línur og orð hvers vinar.
CREATE VIEW IF NOT EXISTS friends_character_totals AS
SELECT character_name, SUM(lines) AS lines, SUM(words) AS words
FROM friends_episode_lines
GROUP BY character_name;

-- TENGSL leiðrétt fyrir málgleði. Hrá talning sýnir alltaf Rachel efsta því
-- hún talar mest allra; lift ber hlutdeild persónu í ræðuskiptum við Phoebe
-- saman við hlutdeild hennar í öllum línum vinanna fimm. Lift > 1: talar
-- oftar við Phoebe en málgleðin ein skýrir.
CREATE VIEW IF NOT EXISTS phoebe_interaction_lift AS
WITH turns AS (
    SELECT x.character_name,
           x.replies_to_phoebe + x.phoebe_replies_to AS adjacent_turns
    FROM phoebe_exchanges AS x
    JOIN friends_characters AS c USING (character_name)
    WHERE c.is_friend = 1
),
turn_shares AS (
    SELECT character_name, adjacent_turns,
           1.0 * adjacent_turns / SUM(adjacent_turns) OVER () AS adjacency_share
    FROM turns
),
line_shares AS (
    SELECT character_name, lines AS total_lines,
           1.0 * lines / SUM(lines) OVER () AS expected_share
    FROM friends_character_totals
    WHERE character_name IN (SELECT character_name FROM turns)
)
SELECT
    t.character_name,
    t.adjacent_turns,
    l.total_lines,
    ROUND(100.0 * t.adjacency_share, 2)          AS adjacency_share_pct,
    ROUND(100.0 * l.expected_share, 2)           AS expected_share_pct,
    ROUND(t.adjacency_share / l.expected_share, 3) AS interaction_lift
FROM turn_shares AS t
JOIN line_shares AS l USING (character_name);
