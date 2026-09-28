"""``web/gogn/skjalftar.json`` — Skjálftavaktin (issue #20).

Tölurnar koma **eingöngu úr grunninum** gegnum ``src/sql/queries/skjalftar-*.sql``.
Uppruni safnsins (þjónusta, beiðni, sóknartími, leyfi) er lesinn úr
``data/raw/vedur-quakes/provenance.json``: migration 002 geymir hann ekki og
skjálftahleðslan skráir sig ekki í ``fetch_log``. Það er sama skráin og
hleðslan sannreyndi úrtakið gegn, svo síðan og grunnurinn segja sama hlutinn.

Námundun: tveir aukastafir, eins og gamla síðan birti (miðgildi, dýpt, stærð).
Hlaupandi meðaltal er ný mæling (engin viðmiðstala) og fær sömu nákvæmni.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur import fyrirspurnir
from gagnagrunnur.tenging import ROT

from .skjal import Uppruni, UtflutningsVilla, ein_rod, lesa_provenance, namunda, skjal

SKRA = "skjalftar.json"
SIDA = "web/sidur/skjalftavaktin.html"
PROVENANCE = ROT / "data" / "raw" / "vedur-quakes" / "provenance.json"
HRAGOGN = "data/raw/vedur-quakes/events.json"
PROVENANCE_REITIR = ("provider", "endpoint", "fetched_at_utc", "license", "parameters")
AUKASTAFIR = 2

FYRIRSPURNIR = (
    "skjalftar-dagleg-samantekt",
    "skjalftar-dypt",
    "skjalftar-staerd-eftir-kvarda",
    "skjalftar-manadartalning",
    "skjalftar-dagleg-talning",
    "skjalftar-hlaupandi-medaltal",
)


def _uppruni(provenance: dict) -> Uppruni:
    return Uppruni(
        thjonusta=str(provenance["provider"]),
        slod=str(provenance["endpoint"]),
        leyfi=str(provenance["license"]),
        sott=str(provenance["fetched_at_utc"]),
        hragogn=HRAGOGN,
    )


def _samantekt(samband: Connection) -> dict:
    dagar = ein_rod(fyrirspurnir.keyra(samband, "skjalftar-dagleg-samantekt"), "dagleg samantekt")
    dypt = ein_rod(fyrirspurnir.keyra(samband, "skjalftar-dypt"), "dýpt")
    return {
        "atburdir": dagar["event_count"],
        "dagar": dagar["day_count"],
        "dagar_an_atburda": dagar["days_without_events"],
        "daglegur_fjoldi": {
            "lagmark": dagar["min_daily"],
            "hamark": dagar["max_daily"],
            "midgildi": namunda(dagar["median_daily"], AUKASTAFIR),
        },
        "dypt_km": {
            "lagmark": namunda(dypt["min_depth_km"], AUKASTAFIR),
            "hamark": namunda(dypt["max_depth_km"], AUKASTAFIR),
            "midgildi": namunda(dypt["median_depth_km"], AUKASTAFIR),
        },
    }


def _staerdir(samband: Connection) -> list[dict]:
    return [
        {
            "kvardi": rad["magnitude_type"],
            "fjoldi": rad["event_count"],
            "lagmark": namunda(rad["min_magnitude"], AUKASTAFIR),
            "hamark": namunda(rad["max_magnitude"], AUKASTAFIR),
            "midgildi": namunda(rad["median_magnitude"], AUKASTAFIR),
        }
        for rad in fyrirspurnir.keyra(samband, "skjalftar-staerd-eftir-kvarda")
    ]


def _dagar(samband: Connection) -> list[dict]:
    """Hver UTC-dagur tímabilsins, líka núll-dagar, með 7 daga meðaltali.

    Talningin og meðaltalið koma úr tveimur fyrirspurnum; stemmi dagarnir eða
    fjöldinn ekki á milli þeirra er stöðvað frekar en að birta tvær sögur.
    """
    talning = fyrirspurnir.keyra(samband, "skjalftar-dagleg-talning")
    medaltal = fyrirspurnir.keyra(samband, "skjalftar-hlaupandi-medaltal")
    if [(r["utc_day"], r["event_count"]) for r in talning] != [
        (r["utc_day"], r["event_count"]) for r in medaltal
    ]:
        raise UtflutningsVilla("Dagleg talning og hlaupandi meðaltal telja ekki sömu daga.")
    return [
        {
            "dagur": rad["utc_day"],
            "fjoldi": rad["event_count"],
            "medaltal_7d": namunda(rad["rolling_avg_7d"], AUKASTAFIR),
            "dagar_i_glugga": rad["days_in_window"],
        }
        for rad in medaltal
    ]


def _manudir(samband: Connection) -> list[dict]:
    return [
        {"manudur": rad["month"], "dagar": rad["day_count"], "atburdir": rad["event_count"]}
        for rad in fyrirspurnir.keyra(samband, "skjalftar-manadartalning")
    ]


def byggja(samband: Connection, provenance: Path = PROVENANCE) -> dict:
    """Skráin sem Skjálftavaktin les: samantekt, stærðir, mánuðir og dagar."""
    skjal_ = lesa_provenance(provenance, PROVENANCE_REITIR)
    uppruni = _uppruni(skjal_)
    beidni = dict(skjal_["parameters"])
    gogn = {
        "uppruni": {**uppruni.sem_gogn(), "beidni": beidni},
        "samantekt": _samantekt(samband),
        "staerd_eftir_kvarda": _staerdir(samband),
        "manudir": _manudir(samband),
        "dagar": _dagar(samband),
    }
    return skjal(uppruni, gogn)
