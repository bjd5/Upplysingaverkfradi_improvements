-- 007_central_perk.sql
-- Phoebe syngur í Central Perk — frosnar niðurstöður greiningarinnar (#10, #24).
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).
--
-- HVAÐAN GÖGNIN KOMA (regla 5)
--   Handritasafn: delvinso/friends-tv-show-analysis
--                 @ a4641fed3d95bb9d9c7ba23681604c692f9b392a — sama safn og
--                 Phoebe-tölurnar í 006 (þar skráð „delvinso/friends“).
--   Greining:     src/phoebe_central_perk.py í upprunaverkefninu
--                 Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe @ 2865ed6.
--                 Klofin í vinnsla/central_perk_*.py (P2.6, PR #58), sem
--                 endurskapar summary.json bæti fyrir bæti.
--   Aðfang hér:   data/processed/central-perk-frosid/ — bætaeins afrit
--                 þriggja frosinna skráa úr viðmiðinu docs/vidmid/generated/:
--                   phoebe-central-perk-summary.json  hópar, miðgildi, söngur
--                   phoebe-central-perk.svg           einn punktur á handrit
--                   phoebe-central-perk-regex.md      segðirnar sem keyrðu
--                 SHA-256 hverrar er í docs/vidmid/provenance.json (safnið
--                 „generated“) og er staðfest áður en hleðsla hefst
--                 (vinnsla.central_perk_adfang). Handritin sjálf eru hvorki
--                 lesin né geymd.
--
-- LEYFI (issue #3, valkostur A)
--   Handritin eru afrit aðdáenda á höfundarréttarvörðu efni; MIT-leyfi
--   delvinso nær yfir kóðann, ekki endilega textann. Hér eru AÐEINS tölur
--   um textann, þáttakóðar og segðirnar sem greiningin notaði — enginn
--   handritstexti, ekki eitt tilsvar.
--
-- SKILGREININGAR (óbreyttar úr greiningunni; sjá PR #58 um frávik frá 006)
--   Eining   = ein handritsskrá (227), EKKI sýndur þáttur: tvíþáttaskrá
--              telst einu sinni.
--   Orð      = [A-Za-z]+(?:['’][A-Za-z]+)? eftir að svigainnskot voru klippt.
--              Annað orðamynstur en í 006, og „Phoebe Sr.“ telst hér sem
--              Phoebe — orðatölurnar eru því ekki sambærilegar við 006.
--   Hlutdeild Phoebe = orð Phoebe / orð aðalpersónanna sex í skránni (0–1).
--   Hópur    = í forgangsröð:
--                phoebe_sings     Phoebe syngur í Central Perk-senu, merkt
--                                 skýrt ((singing), (sings), „Phoebe is
--                                 singing“ …). Óljós söngur er látinn eiga sig.
--                central_perk     Central Perk-sena en enginn slíkur söngur.
--                no_central_perk  Engin sviðsfyrirsögn nefnir Central Perk.
--   Miðgildi = statistics.median yfir skrár hópsins, óafrúnnað.
--   Hlutfallið „hinir fimm á móti Phoebe“ = orð hinna / orð Phoebe, miðgildi
--              yfir skrár þar sem Phoebe segir eitthvað.
--
-- NÁKVÆMNI — HANDRITASTIG ÚR MYNDINNI
--   Hlutdeild Phoebe í hverju handriti er aðeins til frosin í SVG-myndinni,
--   námunduð að 0,1 %. Hún er geymd sem heiltala í prómillum (174 = 17,4 %),
--   nákvæmlega það sem myndin segir. Miðgildi og meðaltöl hópanna eru EKKI
--   reiknuð úr þeim heldur geymd óafrúnnuð úr summary.json. Hleðslan
--   staðfestir að punktarnir og samantektin segi sömu sögu.

-- Uppruni hleðslunnar: ein lína.
CREATE TABLE IF NOT EXISTS central_perk_sources (
    id                    INTEGER PRIMARY KEY CHECK (id = 1),
    transcript_repository TEXT    NOT NULL,  -- delvinso/friends-tv-show-analysis
    transcript_commit     TEXT    NOT NULL,  -- full commit-SHA safnsins
    analysis_repository   TEXT    NOT NULL,  -- upprunaverkefnið
    analysis_commit       TEXT    NOT NULL,  -- commit greiningarskriftunnar
    analysis_script       TEXT    NOT NULL,  -- src/phoebe_central_perk.py
    input_directory       TEXT    NOT NULL,  -- data/processed/central-perk-frosid
    provenance_file       TEXT    NOT NULL,  -- skráin sem geymir SHA-256 summurnar
    licence               TEXT    NOT NULL,  -- leyfisstaðan í stuttu máli
    loaded_at             TEXT    NOT NULL,  -- ISO 8601, UTC — klukkan við hleðslu
    CHECK (length(transcript_commit) = 40
           AND transcript_commit NOT GLOB '*[^0-9a-f]*'),
    CHECK (analysis_commit <> '' AND analysis_commit NOT GLOB '*[^0-9a-f]*')
);

-- Frosnu skrárnar sem voru lesnar, hver með summunni sem hún var staðfest gegn.
CREATE TABLE IF NOT EXISTS central_perk_source_files (
    file_name  TEXT    PRIMARY KEY CHECK (file_name GLOB 'phoebe-central-perk*'),
    sha256     TEXT    NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    CHECK (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*')
);

-- Samanburðarhóparnir þrír (summary.json → groups). Fjöldi handrita er EKKI
-- geymdur hér: hann er COUNT() úr central_perk_transcript_files, og hleðslan
-- staðfestir að hann sé `n` samantektarinnar.
CREATE TABLE IF NOT EXISTS central_perk_groups (
    group_key                      TEXT    PRIMARY KEY CHECK (group_key IN (
                                       'no_central_perk', 'central_perk', 'phoebe_sings')),
    display_order                  INTEGER NOT NULL UNIQUE CHECK (display_order BETWEEN 1 AND 3),
    median_phoebe_share            REAL    NOT NULL CHECK (median_phoebe_share BETWEEN 0 AND 1),
    mean_phoebe_share              REAL    NOT NULL CHECK (mean_phoebe_share BETWEEN 0 AND 1),
    median_friends_to_phoebe_ratio REAL    NOT NULL CHECK (median_friends_to_phoebe_ratio > 0),
    CHECK (typeof(median_phoebe_share) = 'real' AND typeof(mean_phoebe_share) = 'real')
);

-- Handritsskrárnar 227 (punktar SVG-myndarinnar): hópur og hlutdeild Phoebe.
-- Þáttakóðinn er skráarheitið án .html: SSTT eða SSTT-SSTT. Enginn framandi
-- lykill á friends_transcript_files (006): söfnin hlaðast óháð hvort öðru
-- (keyrsla/hledsla.py); prófin sanna að kóðarnir séu þeir sömu.
CREATE TABLE IF NOT EXISTS central_perk_transcript_files (
    episode_code          TEXT    PRIMARY KEY,
    group_key             TEXT    NOT NULL REFERENCES central_perk_groups (group_key),
    phoebe_share_permille INTEGER NOT NULL CHECK (typeof(phoebe_share_permille) = 'integer'
                                                  AND phoebe_share_permille BETWEEN 0 AND 1000),
    CHECK (episode_code GLOB '[0-9][0-9][0-9][0-9]'
           OR episode_code GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'),
    CHECK (CAST(substr(episode_code, 1, 2) AS INTEGER) BETWEEN 1 AND 10)
);

-- Söngsenurnar alls (summary.json → singing_scenes). Eina talan sem er ekki
-- til á handritastigi: myndin sýnir hvaða handrit hafa söng, ekki hve marga.
CREATE TABLE IF NOT EXISTS central_perk_singing (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    singing_scenes INTEGER NOT NULL CHECK (typeof(singing_scenes) = 'integer'
                                           AND singing_scenes >= 0)
);

-- Segðirnar sem greiningin keyrði, orðréttar, með skýringum (regex.md).
CREATE TABLE IF NOT EXISTS central_perk_patterns (
    pattern_name  TEXT    PRIMARY KEY CHECK (pattern_name GLOB '[A-Z]*_RE'),
    display_order INTEGER NOT NULL UNIQUE CHECK (display_order >= 1),
    pattern       TEXT    NOT NULL CHECK (pattern <> ''),
    catches       TEXT    NOT NULL CHECK (catches <> ''),   -- „Grípur“
    misses        TEXT    NOT NULL CHECK (misses <> '')     -- „Sleppur“
);

-- Hóparnir með fjölda handrita, í birtingarröð.
CREATE VIEW IF NOT EXISTS central_perk_group_summary AS
SELECT g.group_key,
       g.display_order,
       COUNT(f.episode_code)            AS transcript_files,
       g.median_phoebe_share,
       g.mean_phoebe_share,
       g.median_friends_to_phoebe_ratio
FROM central_perk_groups AS g
LEFT JOIN central_perk_transcript_files AS f USING (group_key)
GROUP BY g.group_key;

-- Niðurstaðan í einni línu. Munurinn er í prósentustigum og óafrúnnaður,
-- reiknaður eins og greiningin gerði: 100 * (söngur − Central Perk).
CREATE VIEW IF NOT EXISTS central_perk_findings AS
SELECT
    (SELECT COUNT(*) FROM central_perk_transcript_files)             AS transcript_files,
    (SELECT COUNT(*) FROM central_perk_transcript_files
      WHERE group_key = 'phoebe_sings')                              AS singing_files,
    (SELECT singing_scenes FROM central_perk_singing WHERE id = 1)   AS singing_scenes,
    100 * ((SELECT median_phoebe_share FROM central_perk_groups
             WHERE group_key = 'phoebe_sings')
         - (SELECT median_phoebe_share FROM central_perk_groups
             WHERE group_key = 'central_perk'))                      AS median_difference_pp;
