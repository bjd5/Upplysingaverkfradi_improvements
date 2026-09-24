-- 001_gagnasofnun.sql
-- Skráning á hverri gagnasöfnun úr vefþjónustu (regla 4).
-- Migration er ALDREI breytt eftir keyrslu — ný migration í staðinn (regla 5).

CREATE TABLE IF NOT EXISTS fetch_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    service       TEXT    NOT NULL,   -- heiti vefþjónustunnar
    endpoint      TEXT    NOT NULL,   -- slóðin sem kallað var í
    params        TEXT,               -- breytur sem sendar voru (JSON)
    fetched_at    TEXT    NOT NULL,   -- ISO 8601 tímastimpill
    status_code   INTEGER,            -- HTTP staða svarsins
    record_count  INTEGER,            -- fjöldi færslna í svarinu
    raw_file      TEXT    NOT NULL,   -- slóð á óbreytta svarið í data/raw/
    notes         TEXT
);

CREATE INDEX IF NOT EXISTS idx_fetch_log_service
    ON fetch_log (service, fetched_at);
