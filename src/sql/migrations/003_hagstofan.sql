-- 003_hagstofan.sql
-- Brautskráning af háskólastigi — Hagstofa Íslands.
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).
--
-- HVAÐAN GÖGNIN KOMA (regla 5)
--   Þjónusta:   Hagstofa Íslands, PxWeb API.
--   Endapunktur: https://px.hagstofa.is/pxis/api/v1/is/Samfelag/skolamal/
--                4_haskolastig/1_hsProf/SKO04208b.px
--   Tafla:      „Brautskráningarhlutfall og árgangsbrotthvarf í þriggja ára
--               bakkalárnámi eftir námssviði 2014-2023".
--   Heimild:    Nemendaskrá og prófaskrá Hagstofu Íslands.
--   Hrágögn:    data/raw/hagstofan/ (response.json, metadata.json, query.json,
--               provenance.json) — fryst 2026-09-10, aldrei handbreytt (regla 4).
--   Svarsnið:   json-stat2, útgáfa 2.0.
--   Afmörkun:   innritunarár 2017 og tímapunktur n+3. Hún er hluti af gögnunum
--               sjálfum og stendur því í hverri einustu línu í observations.
--
-- AF HVERJU LÖNG TAFLA EN EKKI KROSSTAFLA
--   json-stat2 skilar marghliða töflu: sex víddir og einn FLATUR listi gilda.
--   Krosstafla (einn dálkur á hvert námssvið, eða á hvert kyn) væri
--   fyrirspurnarvæn í dag en brotnar um leið og afmörkunin breytist — ný gildi
--   í vídd kalla þá á nýja dálka og þar með nýja migration. Löng tafla — ein
--   lína á hverja samsetningu vídda — er eðlilega formið: nýtt gildi í vídd
--   bætir við LÍNUM, ekki dálkum, og öll samanlagning er venjuleg SQL-samlagning.
--   Dálkarnir sex í observations svara nákvæmlega til víddanna sex í `id`;
--   þeir eru fastir af því að fyrirspurnin sjálf er fryst.
--
-- AF HVERJU KÓÐI OG HEITI ERU BÆÐI GEYMD
--   Kóðar Hagstofunnar („05", „n+3", „1") eru ólæsilegir einir og sér. Væru
--   aðeins þeir geymdir yrði taflan ólesanleg án upprunaskránna og þar með
--   ekki sjálfstæð heimild. Þess vegna geymir hagstofan_dimension_values
--   ALLA leyfða kóða úr metadata.json ásamt íslensku heiti þeirra, og merkir
--   hverjir þeirra rötuðu inn í frystu fyrirspurnina (selected).

-- Eitt json-stat2-gagnasafn = ein lína. Lýsigögnin sem svarið ber með sér.
CREATE TABLE IF NOT EXISTS hagstofan_datasets (
    id               TEXT    PRIMARY KEY,         -- töfluauðkenni, t.d. SKO04208b
    label            TEXT    NOT NULL,            -- heiti töflunnar hjá Hagstofunni
    source           TEXT    NOT NULL,            -- `source` úr svarinu
    endpoint         TEXT    NOT NULL,            -- slóðin sem var sótt (regla 4)
    fetched_at       TEXT    NOT NULL,            -- ISO 8601, UTC — okkar eigin sóknartími
    -- `updated` úr svarinu. Frysta svarið gefur 9999-12-31T23:59:59Z, sem er
    -- ekki nothæf dagsetning. Reiturinn er varðveittur sem lýsigagn en er
    -- ALDREI notaður sem sóknartími — til þess er fetched_at.
    updated          TEXT,
    jsonstat_version TEXT    NOT NULL,            -- `version` úr svarinu
    -- `extension.px.decimals`. Er 0 í frysta svarinu þótt gildin hafi aukastaf;
    -- varðveitt óbreytt, en value geymir raunverulegu tölurnar.
    decimals         INTEGER,
    value_count      INTEGER NOT NULL CHECK (value_count > 0),
    raw_file         TEXT    NOT NULL,            -- slóð frysta svarsins í data/raw/
    loaded_at        TEXT    NOT NULL             -- ISO 8601, UTC — hvenær hlaðið inn
);

-- Víddirnar sex, í þeirri röð sem `id` í svarinu gefur. Röðin ræður því
-- hvernig flati gildalistinn er lesinn og er því efnisleg, ekki skraut.
CREATE TABLE IF NOT EXISTS hagstofan_dimensions (
    dataset_id TEXT    NOT NULL REFERENCES hagstofan_datasets (id),
    code       TEXT    NOT NULL,                  -- kóði víddar, t.d. Námssvið
    label      TEXT    NOT NULL,                  -- heiti víddar úr lýsigögnum
    position   INTEGER NOT NULL CHECK (position >= 0),  -- staða í `id`, 0-grunnuð
    size       INTEGER NOT NULL CHECK (size > 0),        -- `size` — fjöldi VALINNA gilda
    is_time    INTEGER NOT NULL DEFAULT 0 CHECK (is_time IN (0, 1)),  -- `role.time`
    PRIMARY KEY (dataset_id, code),
    UNIQUE (dataset_id, position)
);

-- Kóðabókin: sérhvert leyft gildi hverrar víddar með íslensku heiti sínu.
-- Bæði valin gildi og þau sem stóðu til boða en voru ekki valin — án hinna
-- síðarnefndu sést ekki hvaða sneið af töflunni var tekin.
CREATE TABLE IF NOT EXISTS hagstofan_dimension_values (
    dataset_id     TEXT    NOT NULL,
    dimension_code TEXT    NOT NULL,
    code           TEXT    NOT NULL,              -- `values` úr metadata.json
    label          TEXT    NOT NULL,              -- `valueTexts` úr metadata.json
    selected       INTEGER NOT NULL CHECK (selected IN (0, 1)),  -- 1 = í frystu fyrirspurninni
    -- `category.index` úr svarinu: staða gildisins innan víddarinnar og þar með
    -- lykillinn að því hvar það liggur í flata gildalistanum. NULL fyrir gildi
    -- sem ekki voru valin, því þau eiga sér enga stöðu í svarinu.
    value_index    INTEGER CHECK (value_index IS NULL OR value_index >= 0),
    PRIMARY KEY (dataset_id, dimension_code, code),
    UNIQUE (dataset_id, dimension_code, value_index),
    FOREIGN KEY (dataset_id, dimension_code)
        REFERENCES hagstofan_dimensions (dataset_id, code),
    CHECK ((value_index IS NULL) = (selected = 0))
);

-- LANGA TAFLAN: ein lína á hverja samsetningu víddanna sex, með gildinu sínu.
-- Fjöldi lína verður að vera margfeldi víddastærðanna; hleðslan sannreynir það
-- áður en nokkuð er skrifað (src/python/vinnsla/hagstofan.py).
--
-- Hver vídd á sér TVO dálka: *_dim geymir kóða víddarinnar og er njörvaður
-- niður með CHECK, *_code geymir gildið. Saman mynda þeir samsettan
-- aðfangalykil í kóðabókina. Það er eina leiðin í SQLite til að tryggja að
-- kyn-kóði rati ekki í námssviðs-dálk: án *_dim vísaði lykillinn aðeins á
-- „eitthvert gildi einhverrar víddar". Dálkarnir eru fastir, ekki gögn.
CREATE TABLE IF NOT EXISTS hagstofan_observations (
    dataset_id          TEXT    NOT NULL REFERENCES hagstofan_datasets (id),
    -- Staða gildisins í flata `value`-listanum, 0-grunnuð. Geymd svo lestur á
    -- json-stat2 sé rekjanlegur aftur í hrágögnin, línu fyrir línu.
    flat_index          INTEGER NOT NULL CHECK (flat_index >= 0),
    value               REAL    NOT NULL,

    enrolment_year_dim  TEXT NOT NULL DEFAULT 'Innritunarár'
                        CHECK (enrolment_year_dim = 'Innritunarár'),
    enrolment_year_code TEXT NOT NULL,

    time_point_dim      TEXT NOT NULL DEFAULT 'Tími'
                        CHECK (time_point_dim = 'Tími'),
    time_point_code     TEXT NOT NULL,

    student_status_dim  TEXT NOT NULL DEFAULT 'Nemendur'
                        CHECK (student_status_dim = 'Nemendur'),
    student_status_code TEXT NOT NULL,

    measure_dim         TEXT NOT NULL DEFAULT 'Fjöldi/Hlutfall'
                        CHECK (measure_dim = 'Fjöldi/Hlutfall'),
    measure_code        TEXT NOT NULL,

    field_dim           TEXT NOT NULL DEFAULT 'Námssvið'
                        CHECK (field_dim = 'Námssvið'),
    field_code          TEXT NOT NULL,

    sex_dim             TEXT NOT NULL DEFAULT 'Kyn'
                        CHECK (sex_dim = 'Kyn'),
    sex_code            TEXT NOT NULL,

    PRIMARY KEY (dataset_id, flat_index),
    -- Sama samsetning vídda má aldrei koma tvisvar: þá væri gildið tvírætt.
    UNIQUE (dataset_id, enrolment_year_code, time_point_code,
            student_status_code, measure_code, field_code, sex_code),

    FOREIGN KEY (dataset_id, enrolment_year_dim, enrolment_year_code)
        REFERENCES hagstofan_dimension_values (dataset_id, dimension_code, code),
    FOREIGN KEY (dataset_id, time_point_dim, time_point_code)
        REFERENCES hagstofan_dimension_values (dataset_id, dimension_code, code),
    FOREIGN KEY (dataset_id, student_status_dim, student_status_code)
        REFERENCES hagstofan_dimension_values (dataset_id, dimension_code, code),
    FOREIGN KEY (dataset_id, measure_dim, measure_code)
        REFERENCES hagstofan_dimension_values (dataset_id, dimension_code, code),
    FOREIGN KEY (dataset_id, field_dim, field_code)
        REFERENCES hagstofan_dimension_values (dataset_id, dimension_code, code),
    FOREIGN KEY (dataset_id, sex_dim, sex_code)
        REFERENCES hagstofan_dimension_values (dataset_id, dimension_code, code)
);

-- Sama langa taflan með íslensku heitunum við hliðina á kóðunum. Sýnin er til
-- svo birtingarlagið þurfi hvorki að þekkja kóðabókina né endurtaka sex
-- samtengingar; tölurnar sjálfar koma óbreyttar úr observations.
CREATE VIEW IF NOT EXISTS hagstofan_labelled_observations AS
SELECT
    o.dataset_id,
    o.flat_index,
    o.enrolment_year_code,  ey.label AS enrolment_year_label,
    o.time_point_code,      tp.label AS time_point_label,
    o.student_status_code,  ss.label AS student_status_label,
    o.measure_code,         me.label AS measure_label,
    o.field_code,           fs.label AS field_label,
    o.sex_code,             sx.label AS sex_label,
    o.value
FROM hagstofan_observations AS o
JOIN hagstofan_dimension_values AS ey
    ON ey.dataset_id = o.dataset_id
   AND ey.dimension_code = o.enrolment_year_dim
   AND ey.code = o.enrolment_year_code
JOIN hagstofan_dimension_values AS tp
    ON tp.dataset_id = o.dataset_id
   AND tp.dimension_code = o.time_point_dim
   AND tp.code = o.time_point_code
JOIN hagstofan_dimension_values AS ss
    ON ss.dataset_id = o.dataset_id
   AND ss.dimension_code = o.student_status_dim
   AND ss.code = o.student_status_code
JOIN hagstofan_dimension_values AS me
    ON me.dataset_id = o.dataset_id
   AND me.dimension_code = o.measure_dim
   AND me.code = o.measure_code
JOIN hagstofan_dimension_values AS fs
    ON fs.dataset_id = o.dataset_id
   AND fs.dimension_code = o.field_dim
   AND fs.code = o.field_code
JOIN hagstofan_dimension_values AS sx
    ON sx.dataset_id = o.dataset_id
   AND sx.dimension_code = o.sex_dim
   AND sx.code = o.sex_code;
