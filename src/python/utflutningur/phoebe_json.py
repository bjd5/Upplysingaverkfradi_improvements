"""Útflutningur Phoebe-tölfræðinnar í ``web/gogn/phoebe-tolfraedi.json`` (#15, #24).

Les **eingöngu** úr grunninum (migration 006) gegnum
``src/sql/queries/friends-*.sql``. Þrjú mælitæki síðunnar:

* ``gogn`` — **pláss** eftir þáttaröð: ein lína á hvern vin í hverri
  þáttaröð (10 × 6) með línum, orðum, hlutdeild í línum þáttaraðarinnar og
  sæti innan hennar. Tímaröðin sem síðan teiknar.
* ``lysigogn.plass_alls`` — línur, orð og hlutdeild hvers vinar yfir alla
  þættina; ``jafn_hlutur_prosent`` er sjötti hlutinn (100/6) til samanburðar.
* ``lysigogn.tengsl`` — ræðuskipti við Phoebe leiðrétt fyrir málgleði (lift).
* ``lysigogn.naervera`` — nafntilvik Phoebe eftir þáttaröð.
* ``lysigogn.umfang`` og ``uppruni`` — 227 handritsskrár, 236 þættir,
  þáttunargæðin, handritasafnið pinnað á commit og leyfisstaðan.

Aðeins samantektir: línutaflan á handritsskrá (227 × 6) fer ekki út. Engin
setning úr handritunum er í grunninum (issue #3, valkostur A) og því engin hér.

``uppfaert`` er ``friends_sources.analysis_generated_utc``: hvenær greiningin
reiknaði tölurnar. Handritin sjálf eru pinnuð á commit, ekki dagsetningu.

Námundun: hlutdeild og nafntilvik á þátt á tveimur aukastöfum (99/24 = 4,125
verður 4,12 eins og á gömlu síðunni). ``lift`` og prósenturnar í tengslum og
þáttunargæðum koma námundaðar úr sýnum migration 006 (skjalfest undantekning
í fyrirspurnunum) og fara óbreyttar út.
"""

from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from gagnagrunnur import fyrirspurnir

from .json_skrif import byggja_umslag, ein_rod

SKRAARHEITI = "phoebe-tolfraedi.json"
GITHUB = "github.com/"
AUKASTAFIR = 2


def _runna(gildi: float) -> float:
    return round(gildi, AUKASTAFIR)


def _keyra(samband: Connection, heiti: str) -> list:
    return fyrirspurnir.keyra(samband, heiti)


def _uppruni(rad: Any) -> dict[str, Any]:
    return {"handritasafn": rad["transcript_repository"],
            "handritasafn_commit": rad["transcript_commit"],
            "greining": rad["analysis_repository"], "greining_commit": rad["analysis_commit"],
            "greiningarskrifta": rad["analysis_script"], "leyfi": rad["licence"]}


def _umfang(samband: Connection) -> dict[str, Any]:
    rad = ein_rod(_keyra(samband, "friends-umfang"), "friends-umfang")
    gaedi = ein_rod(_keyra(samband, "friends-thattunargaedi"), "friends-thattunargaedi")
    return {
        "handritsskrar": rad["transcript_files"], "thaettir": rad["aired_episodes"],
        "skrar_med_tvo_thaetti": rad["double_episode_files"], "thattaradir": rad["seasons"],
        "undanskildar_skrar": rad["excluded_files"],
        "thattunargaedi": {
            "textablokkir": gaedi["total_blocks"], "tilsvor": gaedi["speaker_lines"],
            "svidsfyrirsagnir": gaedi["scene_headings"],
            "svidsleidbeiningar": gaedi["stage_directions"],
            "oflokkad": gaedi["unclassified"], "oflokkad_prosent": gaedi["unclassified_pct"]},
    }


def _plass_eftir_thattarod(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"thattarod": r["season"], "persona": r["character_name"], "linur": r["lines"],
         "ord": r["words"], "hlutdeild_prosent": _runna(r["line_share_pct"]),
         "saeti": r["rank_by_lines"]}
        for r in _keyra(samband, "friends-plass-eftir-thattarod")
    ]


def _plass_alls(samband: Connection) -> list[dict[str, Any]]:
    radir = _keyra(samband, "friends-plass-alls")
    # Hlutdeild af línum vinanna sex, svo hún sé sambærileg við sjötta hlutann.
    samtals = sum(r["lines"] for r in radir)
    return [{"persona": r["character_name"], "linur": r["lines"], "ord": r["words"],
             "hlutdeild_prosent": _runna(100 * r["lines"] / samtals),
             "saeti": r["rank_by_lines"]} for r in radir]


def _tengsl(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"persona": r["character_name"], "radskipti": r["adjacent_turns"],
         "linur": r["total_lines"], "hlutdeild_radskipta_prosent": r["adjacency_share_pct"],
         "vaent_hlutdeild_prosent": r["expected_share_pct"], "lift": r["interaction_lift"],
         "saeti": r["lift_rank"]}
        for r in _keyra(samband, "friends-interaction-lift")
    ]


def _naervera(samband: Connection) -> list[dict[str, Any]]:
    return [
        {"thattarod": r["season"], "thaettir": r["episodes"],
         "i_tali_annarra": r["in_dialogue_by_others"], "i_eigin_tali": r["in_own_dialogue"],
         "i_tali": r["in_dialogue"], "i_svidsleidbeiningum": r["in_stage_directions"],
         "alls": r["mentions_total"], "phoebe": r["formal_phoebe"],
         "gaelunafn": r["nickname_pheebs"],
         "i_tali_a_thatt": _runna(r["dialogue_mentions_per_episode"]),
         "nefnir_oftast": r["top_mentioner"], "nefnir_oftast_fjoldi": r["top_mentioner_count"]}
        for r in _keyra(samband, "friends-nafntilvik-eftir-thattarod")
    ]


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``phoebe-tolfraedi.json``."""
    uppruni = ein_rod(_keyra(samband, "friends-uppruni"), "friends-uppruni")
    safn = uppruni["transcript_repository"]
    heimild = (f"{safn} @ {uppruni['transcript_commit'][:7]} — {GITHUB}{safn} "
               f"({uppruni['licence']})")
    plass = _plass_alls(samband)
    lysigogn = {
        "uppruni": _uppruni(uppruni),
        "umfang": _umfang(samband),
        "plass_alls": plass,
        "tengsl": _tengsl(samband),
        "naervera": _naervera(samband),
        "jafn_hlutur_prosent": _runna(100 / len(plass)),
        "aukastafir": AUKASTAFIR,
    }
    return byggja_umslag(uppfaert=uppruni["analysis_generated_utc"], heimild=heimild,
                         gogn=_plass_eftir_thattarod(samband), lysigogn=lysigogn)
