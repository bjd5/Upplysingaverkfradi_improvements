"""Útflutningur Central Perk-greiningarinnar í ``web/gogn/phoebe-central-perk.json`` (#15, #24).

**Spurningin:** Í hve mörgum handritum syngur Phoebe í Central Perk, og talar
hún hlutfallslega meira í þeim en í öðrum? Les **eingöngu** úr grunninum
(migration 007) gegnum ``src/sql/queries/central-perk-*.sql``:

* ``gogn`` — ein lína á hverja handritsskrá (227): þáttakóði, samanburðarhópur
  og hlutdeild Phoebe í línum handritsins. Punktar myndarinnar.
* ``lysigogn.samantekt`` — 227 handrit, 19 sönghandrit, 24 söngsenur og
  munur miðgilda (söngur − Central Perk án söngs) í prósentustigum.
* ``lysigogn.hopar`` — hóparnir þrír í birtingarröð með fjölda handrita,
  miðgildi og meðaltali hlutdeildar og hlutfalli hinna fimm á móti Phoebe.
* ``lysigogn.songhandrit`` — sönghandritin 19, og ``segdir`` — segðirnar sem
  greiningin keyrði, orðréttar, með því sem þær grípa og sleppa.
* ``lysigogn.uppruni`` — handritasafn og greining pinnuð á commit, og leyfið.

**Af hverju ``uppfaert`` er breytingartími frosnu skránna.** Migration 007
geymir engan gagnastimpil, aðeins ``loaded_at`` (klukka hleðslunnar, sem
gerði úttakið óákvarðað). Greiningin skrifaði skrárnar sem voru frystar, og
``docs/vidmid/provenance.json`` skráir hvenær (``breytt_utc``) við hlið
SHA-256 hverrar skrár. Skrárnar eru fundnar **eftir summunni sem grunnurinn
geymir**, ekki eftir heiti, og ``uppfaert`` er nýjasti tími þeirra
(2026-09-17T09:47:17Z). Finnist summa ekki nákvæmlega einu sinni er stöðvað.

**Námundun í útflutningi:** hlutdeild og hlutföll með einum aukastaf, eins og
gamla síðan og myndin birtu (13,1 / 14,4 / 18,6 %, munur 4,2 pp). Handritastigið
er aðeins til frosið með einum aukastaf (prómill í grunninum).
"""

from __future__ import annotations

import json
from sqlite3 import Connection, Row
from typing import Any

from gagnagrunnur import fyrirspurnir
from gagnagrunnur.tenging import ROT

from .json_skrif import UtflutningsVilla, byggja_umslag, ein_rod

SKRAARHEITI = "phoebe-central-perk.json"
GITHUB = "github.com/"
AUKASTAFIR = 1
PROSENT = 100

# Heiti hópanna eins og samanburðartafla gömlu síðunnar nefndi þau. Grunnurinn
# geymir aðeins lyklana; heitin eru framsetning, ekki gögn.
HOPAHEITI = {
    "no_central_perk": "Engin Central Perk-sena",
    "central_perk": "Central Perk, enginn Phoebe-söngur",
    "phoebe_sings": "Phoebe syngur í Central Perk",
}


def _runna(gildi: float) -> float:
    return round(gildi, AUKASTAFIR)


def _keyra(samband: Connection, heiti: str) -> list[Row]:
    return fyrirspurnir.keyra(samband, heiti)


def _uppfaert(uppruni: Row, skrar: list[Row]) -> str:
    """Nýjasti ``breytt_utc`` frosnu skránna, fundnar eftir SHA-256 í provenance."""
    slod = ROT / uppruni["provenance_file"]
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as villa:
        raise UtflutningsVilla(f"Gat ekki lesið {slod}: {villa}") from villa
    faerslur = [skra for safn in skjal.get("sofn", []) for skra in safn.get("skrar", [])]
    timar = []
    for skra in skrar:
        fundnar = [f for f in faerslur if f.get("sha256") == skra["sha256"]]
        if len(fundnar) != 1 or not fundnar[0].get("breytt_utc"):
            raise UtflutningsVilla(
                f"{skra['file_name']} (sha256 {skra['sha256'][:12]}…) finnst {len(fundnar)} "
                f"sinnum með breytt_utc í {uppruni['provenance_file']}, ekki einu sinni."
            )
        timar.append(fundnar[0]["breytt_utc"])
    if not timar:
        raise UtflutningsVilla("Engar frosnar Central Perk-skrár í grunninum — er hann hlaðinn?")
    return max(timar)


def _hopar(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"hopur": r["group_key"], "heiti": HOPAHEITI[r["group_key"]],
         "handrit": r["transcript_files"],
         "midgildi_prosent": _runna(PROSENT * r["median_phoebe_share"]),
         "medaltal_prosent": _runna(PROSENT * r["mean_phoebe_share"]),
         "hinir_fimm_a_moti_phoebe": _runna(r["median_friends_to_phoebe_ratio"])}
        for r in _keyra(samband, "central-perk-hopar")
    ]


def _handrit(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"handrit": r["episode_code"], "hopur": r["group_key"],
         "hlutdeild_prosent": _runna(r["phoebe_share_pct"])}
        for r in _keyra(samband, "central-perk-handrit")
    ]


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``phoebe-central-perk.json``."""
    uppruni = ein_rod(_keyra(samband, "central-perk-uppruni"), "central-perk-uppruni")
    samantekt = ein_rod(_keyra(samband, "central-perk-samantekt"), "central-perk-samantekt")
    gogn = _handrit(samband)
    if len(gogn) != samantekt["transcript_files"]:
        raise UtflutningsVilla(
            f"{len(gogn)} handritslínur en samantektin telur {samantekt['transcript_files']}."
        )
    songhandrit = [r["episode_code"] for r in _keyra(samband, "central-perk-songhandrit")]
    if len(songhandrit) != samantekt["singing_files"]:
        raise UtflutningsVilla("Sönghandritin stemma ekki við samantektina.")
    safn = uppruni["transcript_repository"]
    lysigogn = {
        "samantekt": {"handritsskrar": samantekt["transcript_files"],
                      "songhandrit": samantekt["singing_files"],
                      "songsenur": samantekt["singing_scenes"],
                      "munur_midgilda_prosentustig": _runna(samantekt["median_difference_pp"])},
        "hopar": _hopar(samband),
        "songhandrit": songhandrit,
        "segdir": [{"heiti": r["pattern_name"], "mynstur": r["pattern"],
                    "gripur": r["catches"], "sleppur": r["misses"]}
                   for r in _keyra(samband, "central-perk-segdir")],
        "uppruni": {"handritasafn": safn, "handritasafn_commit": uppruni["transcript_commit"],
                    "greining": uppruni["analysis_repository"],
                    "greining_commit": uppruni["analysis_commit"],
                    "greiningarskrifta": uppruni["analysis_script"],
                    "leyfi": uppruni["licence"]},
        "aukastafir": AUKASTAFIR,
    }
    heimild = (f"{safn} @ {uppruni['transcript_commit'][:7]} — {GITHUB}{safn} "
               f"({uppruni['licence']})")
    return byggja_umslag(
        uppfaert=_uppfaert(uppruni, _keyra(samband, "central-perk-frosnar-skrar")),
        heimild=heimild, gogn=gogn, lysigogn=lysigogn,
    )
