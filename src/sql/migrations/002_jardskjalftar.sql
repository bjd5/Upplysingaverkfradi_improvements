-- 002_jardskjalftar.sql
-- Jarðskjálftar á Reykjanesskaga, þemaverkefnið „Skjálftavaktin" (issue #6).
--
-- Heimild:   Veðurstofa Íslands, Quakes API — https://api.vedur.is/quakes/events
-- Hrágögn:   data/raw/vedur-quakes/events.json (GeoJSON FeatureCollection, 334 atburðir)
-- Beiðnin:   data/raw/vedur-quakes/provenance.json geymir allar breytur kallsins.
--            Marghyrningur yfir Reykjanes (lengd -23 til -21,5; breidd 63,7 til 64,1),
--            tímabil 2023-11-01T00:00:00+00:00 (meðtalið) til
--            2024-01-01T00:00:00+00:00 (undanskilið), stærð 3-7, dýpt 0-50 km,
--            type=earthquake, evaluation_mode=manual, system=sil.
-- Leyfi:     CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
-- Hleðsla:   src/python/vinnsla/jardskjalftar_hledsla.py
--
-- CHECK-skilyrðin hér að neðan endurspegla síur beiðninnar. Þau eru seinni
-- varnarlínan: hleðslan hafnar fráviki áður en það kemst hingað, og grunnurinn
-- hafnar því líka kæmi það aðra leið. Tölurnar eiga sér heimild í provenance.json.
--
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).

-- Einn dagur á hverja línu fyrir HVERN UTC-dag tímabilsins, líka daga með núll
-- atburði. Fyrirspurn sem telur aðeins raðir í earthquakes sleppir þögulum
-- dögum og sýnir ranga tímaröð; 43 dagar tímabilsins eru án atburðar.
CREATE TABLE IF NOT EXISTS earthquake_days (
    utc_day     TEXT    PRIMARY KEY,           -- YYYY-MM-DD í UTC
    event_count INTEGER NOT NULL DEFAULT 0,    -- atburðir dagsins sem standast síur beiðninnar

    CHECK (utc_day GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (event_count >= 0)
);

-- Einn atburður á hverja línu. Frumgildin úr svarinu (event_id, occurred_at)
-- standa við hlið afleiddu lyklanna (source_system, event_number, utc_day) svo
-- alltaf sé hægt að rekja töluna aftur í hrágögnin (regla 8).
CREATE TABLE IF NOT EXISTS earthquakes (
    event_id        TEXT PRIMARY KEY,  -- frumgildi: einkvæmt SIL-auðkenni úr properties.event_id
    source_system   TEXT NOT NULL,     -- afleitt úr event_id: kerfisheitið (SIL)
    event_number    TEXT NOT NULL,     -- afleitt úr event_id: atburðanúmerið sem texti
    occurred_at     TEXT NOT NULL,     -- frumgildi: properties.time, ISO 8601 með Z
    utc_day         TEXT NOT NULL,     -- afleitt úr occurred_at: UTC-dagurinn
    magnitude       REAL NOT NULL,     -- properties.magnitude
    magnitude_type  TEXT NOT NULL,     -- properties.magnitude_type; kvarðinn er aldrei óskráður
    depth_km        REAL NOT NULL,     -- properties.depth, kílómetrar
    latitude        REAL NOT NULL,     -- geometry.coordinates[1]
    longitude       REAL NOT NULL,     -- geometry.coordinates[0]
    event_type      TEXT NOT NULL,     -- properties.type
    evaluation_mode TEXT NOT NULL,     -- properties.evaluation_mode

    -- Hver atburður tilheyrir degi sem er til í earthquake_days. Atburður utan
    -- tímabils beiðninnar kemst því ekki inn.
    FOREIGN KEY (utc_day) REFERENCES earthquake_days (utc_day),

    -- Afleiddu lyklarnir verða að stemma við frumgildin sem þeir eru dregnir úr.
    CHECK (event_id = source_system || event_number),
    CHECK (occurred_at LIKE utc_day || 'T%'),
    CHECK (source_system = 'SIL'),
    CHECK (event_number GLOB '[1-9]*' AND NOT event_number GLOB '*[^0-9]*'),

    -- Síur beiðninnar (provenance.json -> parameters).
    CHECK (magnitude >= 3 AND magnitude <= 7),
    CHECK (depth_km >= 0 AND depth_km <= 50),
    CHECK (latitude >= 63.7 AND latitude <= 64.1),
    CHECK (longitude >= -23 AND longitude <= -21.5),
    CHECK (event_type = 'earthquake'),
    CHECK (evaluation_mode = 'manual'),
    CHECK (length(trim(magnitude_type)) > 0)
);

-- Dagleg talning og tímaröð eru þær fyrirspurnir sem síðan byggir á.
CREATE INDEX IF NOT EXISTS idx_earthquakes_utc_day
    ON earthquakes (utc_day);

CREATE INDEX IF NOT EXISTS idx_earthquakes_occurred_at
    ON earthquakes (occurred_at);

-- Stærðum er aldrei blandað milli kvarða; samantekt er alltaf innan magnitude_type.
CREATE INDEX IF NOT EXISTS idx_earthquakes_magnitude_type
    ON earthquakes (magnitude_type, magnitude);
