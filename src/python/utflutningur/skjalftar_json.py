"""Útflutningur Skjálftavaktarinnar í ``web/gogn/skjalftar.json`` (issue #15, #20).

Tölurnar koma **eingöngu úr grunninum** (migration 002) gegnum
``src/sql/queries/skjalftar-*.sql``. ``gogn`` er hlutur — síðan les reiti
inni í ``gogn`` (``data-gogn-reitur``, docs/vefur-gogn.md), svo samantektin
verður að vera þar en ekki í ``lysigogn``:

* ``samantekt`` — 334 atburðir, 61 dagur, dagleg dreifing og dýpt.
* ``dagar`` — ein lína á hvern UTC-dag tímabilsins, **líka dagana án
  atburðar**: fjöldi atburða og hlaupandi 7 daga meðaltal (glugginn endar á
  deginum; ``dagar_i_glugga`` < 7 fyrstu sex dagana).
* ``staerd_eftir_kvarda`` — stærð innan hvers kvarða; ``manudir`` — mánaðartölur;
  ``syni`` — fyrstu átta atburðirnir, frumgildin óbreytt.

``lysigogn`` geymir söfnunarlýsinguna: beiðnina sem var send og afmörkun hennar.

**Af hverju ``uppfaert`` er sóknartíminn úr provenance.json.** Migration 002
geymir ekki hvenær svarið var sótt og skjálftahleðslan skráir sig ekki í
``fetch_log``. Sóknartíminn (``fetched_at_utc``, 2026-09-10T11:46:23Z) er því
lesinn úr ``data/raw/vedur-quakes/provenance.json`` — sömu skrá og hleðslan
sannreyndi úrtakið gegn — ásamt útgefanda, slóð og leyfi. Klukkan við
útflutning er aldrei notuð: sami grunnur gefur sömu bæti.

**Námundun í útflutningi:** tveir aukastafir, eins og gamla síðan birti
miðgildi, dýpt og stærðir. Hlaupandi meðaltalið er ný mæling (engin
viðmiðstala) og fær sömu nákvæmni.
"""

from __future__ import annotations

import json
from pathlib import Path
from sqlite3 import Connection
from typing import Any
from urllib.parse import urlsplit

from gagnagrunnur import fyrirspurnir
from gagnagrunnur.tenging import ROT

from .json_skrif import UtflutningsVilla, byggja_umslag, ein_rod

SKRAARHEITI = "skjalftar.json"
PROVENANCE = ROT / "data" / "raw" / "vedur-quakes" / "provenance.json"
HRASKRA = "data/raw/vedur-quakes/events.json"
PROVENANCE_REITIR = ("provider", "endpoint", "fetched_at_utc", "license", "parameters")
AUKASTAFIR = 2


def _runna(gildi: float) -> float:
    return round(gildi, AUKASTAFIR)


def lesa_provenance(slod: Path = PROVENANCE) -> dict[str, Any]:
    """Uppruni skjálftasafnsins — það eina sem grunnurinn geymir ekki."""
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as villa:
        raise UtflutningsVilla(f"Gat ekki lesið {slod}: {villa}") from villa
    vantar = [reitur for reitur in PROVENANCE_REITIR if not skjal.get(reitur)]
    if vantar:
        raise UtflutningsVilla(f"{slod} vantar reitina {', '.join(vantar)}.")
    return skjal


def _heimild(provenance: dict[str, Any]) -> str:
    slod = urlsplit(str(provenance["endpoint"]))
    return f"{provenance['provider']} — {slod.netloc}{slod.path} ({provenance['license']})"


def _dagar(samband: Connection) -> list[dict[str, Any]]:
    """Dagatalningin og meðaltalið; segi fyrirspurnirnar tvær ólíkt er stöðvað."""
    talning = fyrirspurnir.keyra(samband, "skjalftar-dagleg-talning")
    medaltal = fyrirspurnir.keyra(samband, "skjalftar-hlaupandi-medaltal")
    if [(r["utc_day"], r["event_count"]) for r in talning] != [
        (r["utc_day"], r["event_count"]) for r in medaltal
    ]:
        raise UtflutningsVilla("Dagleg talning og hlaupandi meðaltal telja ekki sömu daga.")
    return [
        {"dagur": r["utc_day"], "fjoldi": r["event_count"],
         "medaltal_7d": _runna(r["rolling_avg_7d"]), "dagar_i_glugga": r["days_in_window"]}
        for r in medaltal
    ]


def _samantekt(samband: Connection) -> dict[str, Any]:
    dagar = ein_rod(fyrirspurnir.keyra(samband, "skjalftar-dagleg-samantekt"),
                    "skjalftar-dagleg-samantekt")
    dypt = ein_rod(fyrirspurnir.keyra(samband, "skjalftar-dypt"), "skjalftar-dypt")
    return {
        "atburdir": dagar["event_count"],
        "dagar": dagar["day_count"],
        "dagar_an_atburda": dagar["days_without_events"],
        "daglegur_fjoldi": {"lagmark": dagar["min_daily"], "hamark": dagar["max_daily"],
                            "midgildi": _runna(dagar["median_daily"])},
        "dypt_km": {"lagmark": _runna(dypt["min_depth_km"]),
                    "hamark": _runna(dypt["max_depth_km"]),
                    "midgildi": _runna(dypt["median_depth_km"])},
    }


def _staerdir(samband: Connection) -> list[dict[str, Any]]:
    """Stærð innan hvers kvarða — Mlw og Mw blandast aldrei í eitt miðgildi."""
    return [
        {"kvardi": r["magnitude_type"], "fjoldi": r["event_count"],
         "lagmark": _runna(r["min_magnitude"]), "hamark": _runna(r["max_magnitude"]),
         "midgildi": _runna(r["median_magnitude"])}
        for r in fyrirspurnir.keyra(samband, "skjalftar-staerd-eftir-kvarda")
    ]


def _manudir(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"manudur": r["month"], "dagar": r["day_count"], "atburdir": r["event_count"]}
        for r in fyrirspurnir.keyra(samband, "skjalftar-manadartalning")
    ]


def _syni(samband: Connection) -> list[dict[str, Any]]:
    """Fyrstu atburðirnir með frumgildin óbreytt — lesandinn sér hvað er í hrágögnunum."""
    return [
        {"audkenni": r["event_id"], "timi": r["occurred_at"], "staerd": r["magnitude"],
         "kvardi": r["magnitude_type"], "dypt_km": r["depth_km"],
         "breidd": r["latitude"], "lengd": r["longitude"]}
        for r in fyrirspurnir.keyra(samband, "skjalftar-syni")
    ]


def byggja(samband: Connection, provenance: Path = PROVENANCE) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``skjalftar.json``."""
    uppruni = lesa_provenance(provenance)
    gogn = _dagar(samband)
    if not gogn:
        raise UtflutningsVilla("Engir skjálftadagar í grunninum — er safnið hlaðið (--skref hlada)?")
    samantekt = _samantekt(samband)
    if samantekt["dagar"] != len(gogn) or samantekt["atburdir"] != sum(d["fjoldi"] for d in gogn):
        raise UtflutningsVilla("Samantektin og dagatalningin segja ekki sömu sögu.")
    efni = {
        "samantekt": samantekt,
        "dagar": gogn,
        "staerd_eftir_kvarda": _staerdir(samband),
        "manudir": _manudir(samband),
        "syni": _syni(samband),
    }
    lysigogn = {
        "sokn": {"endapunktur": uppruni["endpoint"], "faeribreytur": uppruni["parameters"],
                 "hraskra": HRASKRA, "leyfi": uppruni["license"],
                 "leyfi_slod": uppruni.get("license_url")},
        "aukastafir": AUKASTAFIR,
    }
    return byggja_umslag(uppfaert=uppruni["fetched_at_utc"], heimild=_heimild(uppruni),
                         gogn=efni, lysigogn=lysigogn)
