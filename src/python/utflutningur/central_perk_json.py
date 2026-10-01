"""Útflutningur Central Perk-niðurstaðnanna í ``web/gogn/central-perk.json`` (#15, #24).

Les **eingöngu** úr grunninum (migration 007) gegnum
``src/sql/queries/central-perk-*.sql``:

* ``gogn`` — þrír samanburðarhópar: fjöldi handrita, miðgildi og meðaltal
  hlutdeildar Phoebe af orðum aðalpersónanna og miðgildi hlutfallsins
  „hinir fimm á móti Phoebe“.
* ``lysigogn.samantekt`` — í hve mörgum handritum og senum Phoebe syngur, og
  munur miðgilda söngs og annarra Central Perk-handrita í prósentustigum.

Aðeins skýrar söngmerkingar telja; óljós söngur er látinn eiga sig (sjá
migration 007). Aðeins tölur: enginn handritstexti (issue #3, valkostur A).

``uppfaert`` er gagnastimpill Friends-greiningarinnar (``friends-uppruni``):
Central Perk-greiningin er hluti af sömu greiningu og hleðslutíminn í
``central_perk_sources`` er ekki ákvarðaður.

Námundun: hlutdeild og munur á einum aukastaf — handritastigið er aðeins til
frosið með 0,1 % nákvæmni — og hlutfallið á tveimur. SQL skilar óafrúnnuðu,
birtingin námundar (docs/adferdafraedi.md 4.1).
"""

from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from gagnagrunnur import fyrirspurnir

from .json_skrif import byggja_umslag, ein_rod

SKRAARHEITI = "central-perk.json"
GITHUB = "github.com/"
AUKASTAFIR_HLUTDEILD = 1
AUKASTAFIR_HLUTFALL = 2

# Heiti hópanna eru birtingarefni og eiga heima hér, ekki í grunninum.
HEITI_HOPA = {
    "no_central_perk": "Engin Central Perk-sena",
    "central_perk": "Central Perk án söngs",
    "phoebe_sings": "Phoebe syngur",
}


def _keyra(samband: Connection, heiti: str) -> list:
    return fyrirspurnir.keyra(samband, heiti)


def _hopar(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"hopur": r["group_key"], "heiti": HEITI_HOPA[r["group_key"]],
         "handrit": r["transcript_files"],
         "midgildi_prosent": round(100 * r["median_phoebe_share"], AUKASTAFIR_HLUTDEILD),
         "medaltal_prosent": round(100 * r["mean_phoebe_share"], AUKASTAFIR_HLUTDEILD),
         "midgildi_hlutfall": round(r["median_friends_to_phoebe_ratio"], AUKASTAFIR_HLUTFALL)}
        for r in _keyra(samband, "central-perk-hopar")
    ]


def _samantekt(samband: Connection) -> dict[str, Any]:
    rad = ein_rod(_keyra(samband, "central-perk-samantekt"), "central-perk-samantekt")
    return {"handrit": rad["transcript_files"], "songhandrit": rad["singing_files"],
            "songsenur": rad["singing_scenes"],
            "munur_midgilda_stig": round(rad["median_difference_pp"], AUKASTAFIR_HLUTDEILD)}


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``central-perk.json``."""
    uppruni = ein_rod(_keyra(samband, "friends-uppruni"), "friends-uppruni")
    safn = uppruni["transcript_repository"]
    heimild = (f"{safn} @ {uppruni['transcript_commit'][:7]} — {GITHUB}{safn} "
               f"({uppruni['licence']})")
    lysigogn = {"samantekt": _samantekt(samband), "aukastafir": AUKASTAFIR_HLUTDEILD,
                "aukastafir_hlutfall": AUKASTAFIR_HLUTFALL}
    return byggja_umslag(uppfaert=uppruni["analysis_generated_utc"], heimild=heimild,
                         gogn=_hopar(samband), lysigogn=lysigogn)
