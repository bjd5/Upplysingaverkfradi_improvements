"""``web/gogn/phoebe-tolfraedi.json`` — Phoebe-tölfræði (issue #24).

Þrjú mælitæki síðunnar — **pláss** (línur og orð), **nærvera** (nafntilvik) og
**tengsl** (ræðuskipti leiðrétt fyrir málgleði) — auk umfangs safnsins og
gæðamats þáttunarinnar. Allt úr ``src/sql/queries/friends-*.sql``.

Aðeins samantektir: línutaflan á handritsskrá (227 × 6) fer ekki út, heldur
summur á þáttaröð og yfir alla þættina (#15 um stærð).

Engin setning úr handritunum fer út (issue #3, valkostur A) — aðeins talningar,
hlutföll og persónunöfn, sem grunnurinn geymir einn.

``uppfaert`` er ``analysis_generated_utc``: hvenær greiningin reiknaði
tölurnar. Handritin sjálf eru pinnuð á commit, ekki dagsetningu.

Námundun (eins og gamla síðan og talnaskrárnar): hlutdeild og nafntilvik á
þátt tveir aukastafir. ``interaction_lift`` og prósenturnar í þáttunargæðum
koma námundaðar úr sýnum migration 006 (skjöluð undantekning, sjá
fyrirspurnirnar) og fara óbreyttar út.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from sqlite3 import Connection

from gagnagrunnur import fyrirspurnir

from .skjal import Uppruni, ein_rod, namunda, skjal

SKRA = "phoebe-tolfraedi.json"
SIDA = "web/sidur/phoebe-tolfraedi.html"
GITHUB = "https://github.com/"
AUKASTAFIR = 2

FYRIRSPURNIR = (
    "friends-uppruni",
    "friends-umfang",
    "friends-thattunargaedi",
    "friends-plass-alls",
    "friends-plass-eftir-thattarod",
    "friends-interaction-lift",
    "friends-nafntilvik-eftir-thattarod",
)


def _uppruni(samband: Connection) -> tuple[Uppruni, dict]:
    rad = ein_rod(fyrirspurnir.keyra(samband, "friends-uppruni"), "friends_sources")
    uppruni = Uppruni(
        thjonusta=rad["transcript_repository"],
        slod=GITHUB + rad["transcript_repository"],
        leyfi=rad["licence"],
        sott=rad["analysis_generated_utc"],
        hragogn=f"{rad['transcript_repository']}@{rad['transcript_commit']}",
    )
    auki = {
        "handrit_commit": rad["transcript_commit"],
        "greining": rad["analysis_repository"],
        "greining_commit": rad["analysis_commit"],
        "greiningarskrifta": rad["analysis_script"],
    }
    return uppruni, auki


def _umfang(samband: Connection) -> dict:
    rad = ein_rod(fyrirspurnir.keyra(samband, "friends-umfang"), "umfang")
    gaedi = ein_rod(fyrirspurnir.keyra(samband, "friends-thattunargaedi"), "þáttunargæði")
    return {
        "handritsskrar": rad["transcript_files"],
        "thaettir": rad["aired_episodes"],
        "skrar_med_tvo_thaetti": rad["double_episode_files"],
        "thattaradir": rad["seasons"],
        "undanskildar_skrar": rad["excluded_files"],
        "thattunargaedi": {
            "textablokkir": gaedi["total_blocks"],
            "tilsvor": gaedi["speaker_lines"],
            "svidsfyrirsagnir": gaedi["scene_headings"],
            "svidsleidbeiningar": gaedi["stage_directions"],
            "oflokkad": gaedi["unclassified"],
            "oflokkad_prosent": gaedi["unclassified_pct"],
        },
    }


def _plass(samband: Connection) -> dict:
    alls = [
        {"persona": r["character_name"], "linur": r["lines"], "ord": r["words"],
         "saeti": r["rank_by_lines"]}
        for r in fyrirspurnir.keyra(samband, "friends-plass-alls")
    ]
    eftir_thattarod = [
        {"thattarod": r["season"], "persona": r["character_name"], "linur": r["lines"],
         "ord": r["words"], "hlutdeild_prosent": namunda(r["line_share_pct"], AUKASTAFIR),
         "saeti": r["rank_by_lines"]}
        for r in fyrirspurnir.keyra(samband, "friends-plass-eftir-thattarod")
    ]
    return {"alls": alls, "eftir_thattarod": eftir_thattarod}


def _tengsl(samband: Connection) -> list[dict]:
    return [
        {"persona": r["character_name"], "radskipti": r["adjacent_turns"],
         "linur": r["total_lines"], "hlutdeild_radskipta_prosent": r["adjacency_share_pct"],
         "vaent_hlutdeild_prosent": r["expected_share_pct"], "lift": r["interaction_lift"],
         "saeti": r["lift_rank"]}
        for r in fyrirspurnir.keyra(samband, "friends-interaction-lift")
    ]


def _naervera(samband: Connection) -> list[dict]:
    return [
        {"thattarod": r["season"], "thaettir": r["episodes"],
         "i_tali_annarra": r["in_dialogue_by_others"], "i_eigin_tali": r["in_own_dialogue"],
         "i_tali": r["in_dialogue"], "i_svidsleidbeiningum": r["in_stage_directions"],
         "alls": r["mentions_total"], "phoebe": r["formal_phoebe"],
         "gaelunafn": r["nickname_pheebs"],
         "i_tali_a_thatt": namunda(r["dialogue_mentions_per_episode"], AUKASTAFIR),
         "nefnir_oftast": r["top_mentioner"], "nefnir_oftast_fjoldi": r["top_mentioner_count"]}
        for r in fyrirspurnir.keyra(samband, "friends-nafntilvik-eftir-thattarod")
    ]


def byggja(samband: Connection) -> dict:
    """Skráin sem Phoebe-tölfræðisíðan les."""
    uppruni, auki = _uppruni(samband)
    gogn = {
        "uppruni": {**uppruni.sem_gogn(), **auki},
        "umfang": _umfang(samband),
        "plass": _plass(samband),
        "tengsl": _tengsl(samband),
        "naervera": _naervera(samband),
    }
    return skjal(uppruni, gogn)
