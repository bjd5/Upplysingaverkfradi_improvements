-- 005_mbl_regex.sql
-- Niðurstöður regex-æfingarinnar á fréttasíðu mbl.is (issue #9).
--
-- Hvaðan gögnin koma (regla 5):
--   Þjónusta : mbl.is — https://www.mbl.is/frettir/
--   Eintak   : data/raw/mbl/mbl-20260916T120851Z.html, sótt 2026-09-16T12:08:51Z,
--              HTTP 200, 367.351 bæti, MD5 c2c83bddb8ed41357b7b1b8ab51a6457.
--              Lýsigögnin liggja í samnefndri .json-skrá (regla 4).
--   Aðferð   : reglulegar segðir á VISTUÐU svari — engin vefbeiðni er send
--              við hleðslu (src/python/vinnsla/mbl_utdrattur.py).
--
-- Leyfi og afmörkun: fréttatexti mbl.is er höfundarréttarvarinn. Hér er HTML-ið
-- sjálft hvergi geymt, aðeins NIÐURSTÖÐUR útdráttarins, mynstrin sem framkölluðu
-- þær og stutt sýnishorn af því sem mynstrið hitti á. Hráa eintakið er áfram
-- eina frumgagnið og því er aldrei breytt.
--
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).

-- Eitt vistað HTML-svar. Fleiri en eitt eintak mega liggja hér samtímis,
-- aðgreind eftir sóknartíma, svo hægt sé að bera saman tvær sóknir án þess
-- að sú eldri glatist.
CREATE TABLE IF NOT EXISTS mbl_snapshots (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at           TEXT    NOT NULL UNIQUE,  -- ISO 8601 UTC; aðgreinir eintökin
    source_url           TEXT    NOT NULL,         -- slóðin sem var sótt
    raw_file             TEXT    NOT NULL UNIQUE,  -- skráarheitið í data/raw/mbl/
    sha256               TEXT    NOT NULL,         -- reiknað við hleðslu
    md5                  TEXT    NOT NULL,         -- úr lýsigögnunum, sannreynt við hleðslu
    content_length_bytes INTEGER NOT NULL,
    status_code          INTEGER NOT NULL,
    content_type         TEXT,
    loaded_at            TEXT    NOT NULL,         -- hvenær færslan var sett í grunninn

    CHECK (content_length_bytes > 0),
    CHECK (length(sha256) = 64),
    CHECK (length(md5) = 32)
);

-- Ein lína á hvert útdregið atriði: hvaða spurning, hvaða mynstur, hvað fannst.
--
-- Mynstrið sjálft er geymt með niðurstöðunni af ásettu ráði (regla 8): án þess
-- er ekki hægt að sjá hvers vegna talan varð þessi. Talan á sér þá leið alla
-- leið aftur í hráa eintakið — snapshot_id segir hvaða svar var lesið,
-- pattern segir hvernig, og sample_match sýnir dæmi um það sem hitti.
CREATE TABLE IF NOT EXISTS mbl_extractions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id     INTEGER NOT NULL REFERENCES mbl_snapshots (id) ON DELETE CASCADE,

    question_number INTEGER NOT NULL,  -- 1–5, röð spurninganna í æfingunni
    question_key    TEXT    NOT NULL,  -- vélleshæft auðkenni, t.d. 'gengi-usd'
    question_is     TEXT    NOT NULL,  -- spurningin eins og hún birtist lesanda

    pattern_name    TEXT    NOT NULL,  -- heiti fastans í mbl_mynstur.py
    pattern         TEXT    NOT NULL,  -- MYNSTRIÐ SJÁLFT, orðrétt
    pattern_flags   TEXT    NOT NULL,  -- re-flöggin sem það var þýtt með
    scope_name      TEXT,              -- afmörkun leitarsvæðis, ef við á
    scope_pattern   TEXT,              -- mynstrið sem afmarkaði svæðið

    value_number    REAL    NOT NULL,  -- svarið sem tala
    value_text      TEXT    NOT NULL,  -- svarið eins og það birtist á íslensku
    unit            TEXT,              -- eining svarsins, t.d. '°C'

    match_count     INTEGER NOT NULL,  -- fjöldi tilvika sem mynstrið fann
    distinct_count  INTEGER NOT NULL,  -- fjöldi einstakra gilda eftir afritahreinsun
    sample_match    TEXT    NOT NULL,  -- sýnishorn af því sem mynstrið hitti á
    notes           TEXT,              -- þekktar takmarkanir talnanna (regla 8)
    extracted_at    TEXT    NOT NULL,

    -- Sama spurning er aðeins svöruð einu sinni fyrir hvert eintak.
    UNIQUE (snapshot_id, question_key),
    UNIQUE (snapshot_id, question_number),

    CHECK (question_number BETWEEN 1 AND 5),
    -- Lína verður aldrei til án þess að mynstrið hafi hitt á eitthvað.
    -- Finnist mynstur ekki stöðvast hleðslan með villu í stað þess að
    -- skrifa tóma línu (regla 6).
    CHECK (match_count > 0),
    CHECK (distinct_count > 0 AND distinct_count <= match_count),
    CHECK (length(sample_match) > 0),
    CHECK ((scope_name IS NULL) = (scope_pattern IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_mbl_extractions_snapshot
    ON mbl_extractions (snapshot_id, question_number);

CREATE INDEX IF NOT EXISTS idx_mbl_extractions_question
    ON mbl_extractions (question_key);
