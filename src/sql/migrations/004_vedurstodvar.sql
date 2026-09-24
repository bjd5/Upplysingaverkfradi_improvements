-- 004_vedurstodvar.sql
-- Stöðvaskrá Veðurstofu Íslands (issue #8).
--
-- Heimild:  https://api.vedur.is/weather/stations  ·  CC BY 4.0
-- Eintak:   data/raw/vedurstodvar/stations-20260924T112218Z.json
-- Uppruni:  data/raw/vedurstodvar/provenance.json (slóð, hausar, SHA-256)
-- Sótt:     2026-09-24T11:22:18Z  ·  778 stöðvar  ·  343 þeirra enn starfræktar
--
-- ÞETTA ER FROSIÐ EINTAK, EKKI LIFANDI STAÐA.
-- Gamla verkefnið sótti þennan lista upp á nýtt í hverri einustu CI-byggingu og
-- vistaði hráa svarið aldrei. Veðurstöðvasíðan gat því birt aðrar tölur í dag en
-- í gær án þess að nokkur tæki eftir því, og engin bygging var endurtekjanleg.
-- Taflan hér er hlaðin úr EINU eintaki með tiltekinni sóknardagsetningu. Tölurnar
-- eru þar með endurtekjanlegar — en þær eldast: stöð sem bætist við eða er tekin
-- niður eftir 2026-09-24 sést ekki hér fyrr en nýtt eintak er fryst.
-- Samanburður frosna eintaksins við gömlu síðuna: docs/vedurstodvar-samanburdur.md
--
-- LOKAÁR STARFRÆKSLU ER NULL, ALDREI TÓMSTRENGUR.
-- Stöð sem mælir enn hefur ekkert lokaár, og það er annað en að hafa lokaárið
-- "". Munurinn ræður úrslitum í WHERE-skilyrði: `end_year IS NULL` telur 343
-- stöðvar en `end_year = ''` telur 0 — og tómstrengur læðist óséður í gegnum
-- `end_year IS NOT NULL` sem virk stöð. Þess vegna er tómstrengur bannaður með
-- CHECK-skilyrði hér að neðan en ekki aðeins í hleðslunni.
--
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).

CREATE TABLE IF NOT EXISTS weather_stations (
    -- station_id er auðkennið sem þjónustan sjálf gefur (reiturinn "station").
    -- Það er notað óbreytt sem frumlykill svo `station_id = ?` sé bein síun.
    station_id   INTEGER NOT NULL PRIMARY KEY,
    name         TEXT    NOT NULL,   -- heiti stöðvar, íslenskt
    abbr         TEXT    NOT NULL,   -- skammstöfun þjónustunnar (ekki einkvæm)
    station_type TEXT    NOT NULL,   -- tegund: sk, sj, ur, vf í þessu eintaki
    lat          REAL    NOT NULL,   -- breiddargráða, WGS84
    lon          REAL    NOT NULL,   -- lengdargráða, WGS84
    elevation_m  REAL    NOT NULL,   -- hæð yfir sjávarmáli í metrum
    wigos_id     TEXT,               -- WIGOS-auðkenni; NULL þar sem það vantar
    owner        TEXT,               -- eigandi stöðvar; NULL þar sem hann vantar
    start_year   INTEGER NOT NULL,   -- fyrsta ár mælinga
    end_year     INTEGER,            -- lokaár mælinga; NULL = stöðin mælir enn

    CONSTRAINT weather_stations_station_id_heiltala
        CHECK (typeof(station_id) = 'integer' AND station_id > 0),
    CONSTRAINT weather_stations_texti_ekki_tomur
        CHECK (name <> '' AND abbr <> '' AND station_type <> ''),
    -- Tómstrengur er ekki "vantar" — vanti gildið á það að vera NULL.
    CONSTRAINT weather_stations_valfrjalst_null_ekki_tomstrengur
        CHECK ((wigos_id IS NULL OR wigos_id <> '')
           AND (owner    IS NULL OR owner    <> '')),
    CONSTRAINT weather_stations_hnit_innan_marka
        CHECK (lat BETWEEN -90.0 AND 90.0 AND lon BETWEEN -180.0 AND 180.0),
    CONSTRAINT weather_stations_upphafsar_heiltala
        CHECK (typeof(start_year) = 'integer' AND start_year > 0),
    -- Kjarni æfingarinnar: lokaárið er annaðhvort heiltala eða NULL. Tómstrengur
    -- kemst ekki inn, svo `end_year IS NULL` er áreiðanleg skilgreining á virkri
    -- stöð og ekkert WHERE-skilyrði þarf að giska á snið gildisins.
    CONSTRAINT weather_stations_lokaar_null_eda_heiltala
        CHECK (end_year IS NULL
               OR (typeof(end_year) = 'integer' AND end_year >= start_year))
);

-- Síurnar þrjár sem æfingin notar eru studdar beint:
--   station_id = ?          -> frumlykillinn sjálfur
--   end_year IS NULL        -> idx_weather_stations_active
--   hnit innan marghyrnings -> idx_weather_stations_position
CREATE INDEX IF NOT EXISTS idx_weather_stations_active
    ON weather_stations (end_year);

CREATE INDEX IF NOT EXISTS idx_weather_stations_position
    ON weather_stations (lat, lon);

-- Spurningin "dygði stöðin til að bera saman við veður fyrir 50 árum?" les
-- upphafsárið jafnt lokaárinu.
CREATE INDEX IF NOT EXISTS idx_weather_stations_start_year
    ON weather_stations (start_year);
