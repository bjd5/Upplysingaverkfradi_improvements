"""Samræmi milli Friends-talnaskránna — og samsetning raðanna (issue #10).

Skrárnar sautján eru ekki óháðar: sama talan stendur oft í tveimur eða þremur
þeirra (línur Phoebe í ``_meta.json``, í ``summary.json`` og sem summa úr
``phoebe-per-episode.csv``). Grunnurinn geymir hverja tölu **einu sinni**, svo
áður en hlaðið er þarf að sanna að hinir staðirnir segi það sama. Annars
myndi grunnurinn velja eina útgáfuna hljóðlega. Hvert ósamræmi stöðvar
keyrsluna (regla 6).

Skráalistarnir (undanskildar skrár, tvöfaldir þættir) eru bornir við
``vinnsla.friends_handrit`` — sömu skilgreiningar og greiningin í #14 notar.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from . import friends_faerslur as ff
from . import friends_phoebe_faerslur as fp
from .friends_handrit import DOUBLE_EPISODE_FILES, EXCLUDED_FILES, TRANSCRIPT_SUFFIX
from .friends_skrar import HledsluVilla, lesa_csv, lesa_json
from .phoebe_skilgreiningar import FRIENDS, PHOEBE, TITLES

SUMMARY = "summary.json"
SCREENTIME_STUTT = "screentime-by-season.csv"
SCREENTIME_STUTT_DALKAR = ("season", "character", "lines", "words", "line_share")
MENTIONS_STUTT = "mentions-by-season.csv"
MENTIONS_STUTT_DALKAR = ("season", "mentions", "episodes", "mentions_per_episode")


@dataclass(frozen=True)
class Gogn:
    """Allar raðir sem fara í grunninn, sannreyndar og samræmdar."""

    meta: dict
    blokkir: list[tuple]
    thattarodir: list[tuple]
    handritsskrar: list[tuple]
    undanskildar: list[tuple]
    personur: list[tuple]
    linur: list[tuple]
    thattarodarpersonur: list[tuple]
    samskipti: list[tuple]
    skipti: list[tuple]
    vinaskipti: list[tuple]
    skipti_eftir_rod: list[tuple]
    nafntilvik: list[tuple]
    ordtok: list[tuple]
    ord: list[tuple]
    lift_ur_skra: dict[str, float]


def krefjast(skilyrdi: bool, skyring: str) -> None:
    """Stöðvar keyrsluna með skýringu ef skilyrðið bregst."""
    if not skilyrdi:
        raise HledsluVilla(f"Ósamræmi milli talnaskráa: {skyring}")


def _skrar_og_thaettir(meta: dict, thattarodir: list, skrar: list) -> None:
    krefjast(len(skrar) == ff.heiltala(meta["transcript_files_used"], "transcript_files_used"),
             f"{len(skrar)} skrár í {ff.PER_EPISODE} en _meta segir "
             f"{meta['transcript_files_used']}.")
    thaettir = sum(s[3] for s in skrar)
    krefjast(thaettir == meta["aired_episodes_covered"] == sum(t[1] for t in thattarodir),
             f"sýndir þættir: {thaettir} úr skránum, {meta['aired_episodes_covered']} í _meta.")
    eftir_rod = Counter()
    for skra in skrar:
        eftir_rod[skra[1]] += skra[3]
    krefjast(dict(eftir_rod) == dict(thattarodir), "þættir á þáttaröð stemma ekki.")
    krefjast(set(meta["transcript_files_excluded"]) == EXCLUDED_FILES
             and len(meta["transcript_files_excluded"]) == len(EXCLUDED_FILES),
             "undanskildu skrárnar eru ekki þær sem friends_handrit nefnir.")
    tvofaldar = {s[0] + TRANSCRIPT_SUFFIX for s in skrar if s[3] == 2}
    krefjast(tvofaldar == set(meta["conventions"]["double_episode_files"])
             == DOUBLE_EPISODE_FILES, "tvöföldu skrárnar stemma ekki.")


def _blokkir(meta: dict, blokkir: list) -> None:
    gaedi = meta["parse_quality"]
    alls = ff.heiltala(gaedi["total_text_blocks"], "total_text_blocks", 1)
    krefjast(sum(b[1] for b in blokkir) == alls, "blokkaflokkarnir summast ekki í heildina.")
    oflokkad = dict(blokkir)["unclassified"]
    krefjast(round(100 * oflokkad / alls, 2) == gaedi["unclassified_pct"],
             "hlutfall óflokkaðra stemmir ekki við fjöldann.")


def _plass(mappa: Path, meta: dict, skrar: list, linur: list, a_rod: dict) -> None:
    rod_skrar = {s[0]: s[1] for s in skrar}
    alls, rod_summa = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for kodi, nafn, fjoldi, ord_ in linur:
        for summa in (alls[nafn], rod_summa[(rod_skrar[kodi], nafn)]):
            summa[0] += fjoldi
            summa[1] += ord_
    for lykill in FRIENDS:
        vaent = (meta["friends_line_totals"][lykill], meta["friends_word_totals"][lykill])
        krefjast(tuple(alls[TITLES[lykill]]) == vaent,
                 f"línur/orð {lykill}: {alls[TITLES[lykill]]} úr skránum, {vaent} í _meta.")
    krefjast({k: tuple(v) for k, v in rod_summa.items()} == a_rod,
             f"línur/orð á þáttaröð í {ff.SCREENTIME} eru ekki summa skránna.")
    for rad in lesa_csv(mappa, SCREENTIME_STUTT, SCREENTIME_STUTT_DALKAR):
        lykill = (ff.rod(rad["season"], SCREENTIME_STUTT), ff.vinur(rad["character"], SCREENTIME_STUTT))
        krefjast((int(rad["lines"]), int(rad["words"])) == a_rod.get(lykill),
                 f"{SCREENTIME_STUTT} {lykill} víkur frá {ff.SCREENTIME}.")
    summary = lesa_json(mappa, SUMMARY)
    krefjast((summary["lines_total"], summary["words_total"])
             == tuple(alls[TITLES[PHOEBE]]), f"{SUMMARY} segir annað um Phoebe.")
    krefjast(summary["episodes"] == meta["aired_episodes_covered"], f"{SUMMARY}: þættir.")


def _tengsl(skipti: list, vinaskipti: list[dict], eftir_rod: list, meta: dict) -> None:
    skipti_eftir_nafni = {s[0]: s[1:] for s in skipti}
    vinir = {TITLES[v] for v in FRIENDS if v != PHOEBE}
    krefjast({r["character"] for r in vinaskipti} == vinir,
             f"{fp.TOP_TALKERS} nefnir ekki nákvæmlega vinina fimm.")
    for rad in vinaskipti:
        nafn, svor, hennar = rad["character"], int(rad["replies_to_phoebe"]), int(rad["phoebe_replies_to"])
        krefjast(skipti_eftir_nafni.get(nafn) == (svor, hennar, int(rad["shared_speaking_scenes"])),
                 f"{nafn}: {fp.TOP_TALKERS} og {fp.SPEAKS_WITH} segja ekki það sama.")
        krefjast(int(rad["adjacent_turns"]) == svor + hennar, f"{nafn}: adjacent_turns.")
        krefjast(int(rad["total_lines_in_show"])
                 == meta["friends_line_totals"][nafn.lower()], f"{nafn}: total_lines_in_show.")
        a_rod = [r for r in eftir_rod if r[1] == nafn]
        krefjast(sum(r[2] for r in a_rod) == svor and sum(r[3] for r in a_rod) == hennar,
                 f"{nafn}: ræðuskipti á þáttaröð summast ekki í heildina.")


def _naervera(mappa: Path, nafntilvik: list[dict], thattarodir: list, skrar: list) -> None:
    thaettir = dict(thattarodir)
    skrar_a_rod = Counter(s[1] for s in skrar)
    stutt = {int(r["season"]): r for r in lesa_csv(mappa, MENTIONS_STUTT, MENTIONS_STUTT_DALKAR)}
    for rad in nafntilvik:
        rod = rad["season"]
        tal = rad["mentions_in_dialogue_by_others"] + rad["mentions_in_own_dialogue"]
        krefjast(rad["mentions_in_dialogue_total"] == tal, f"þáttaröð {rod}: tal alls.")
        krefjast(rad["mentions_total"] == tal + rad["mentions_in_stage_directions"],
                 f"þáttaröð {rod}: nafntilvik alls.")
        krefjast(rad["episodes"] == thaettir[rod], f"þáttaröð {rod}: þættir.")
        krefjast(rad["transcript_files"] == skrar_a_rod[rod], f"þáttaröð {rod}: skrár.")
        krefjast(rod in stutt and int(stutt[rod]["mentions"]) == tal
                 and int(stutt[rod]["episodes"]) == thaettir[rod],
                 f"{MENTIONS_STUTT} víkur frá {fp.MENTIONS} í þáttaröð {rod}.")
    krefjast(len(stutt) == len(nafntilvik), f"{MENTIONS_STUTT}: fjöldi þáttaraða.")


def _personur(skipti: list) -> list[tuple[str, int]]:
    """Vinirnir sex og hver gestur sem ræðuskiptaskráin nefnir."""
    vinir = [TITLES[v] for v in FRIENDS]
    gestir = [s[0] for s in skipti if s[0] not in vinir]
    krefjast(TITLES[PHOEBE] not in {s[0] for s in skipti}, "Phoebe talar ekki við sjálfa sig.")
    return [(nafn, 1) for nafn in vinir] + [(nafn, 0) for nafn in gestir]


def safna(mappa: Path) -> Gogn:
    """Les allar skrárnar, sannreynir hverja færslu og samræmið milli þeirra."""
    meta = ff.lesa_meta(mappa)
    blokkir, thattarodir = ff.blokkir(meta), ff.thattarodir(meta)
    skrar, linur = ff.handritsskrar(mappa)
    thattarodarpersonur, linur_a_rod = ff.thattarodarpersonur(mappa)
    skipti, vinaskipti = fp.skipti(mappa), fp.vinaskipti(mappa)
    eftir_rod, nafntilvik = fp.skipti_eftir_rod(mappa), fp.nafntilvik(mappa)

    _skrar_og_thaettir(meta, thattarodir, skrar)
    _blokkir(meta, blokkir)
    _plass(mappa, meta, skrar, linur, linur_a_rod)
    _tengsl(skipti, vinaskipti, eftir_rod, meta)
    _naervera(mappa, nafntilvik, thattarodir, skrar)

    return Gogn(
        meta=meta, blokkir=blokkir, thattarodir=thattarodir, handritsskrar=skrar,
        undanskildar=[(heiti,) for heiti in sorted(meta["transcript_files_excluded"])],
        personur=_personur(skipti), linur=linur, thattarodarpersonur=thattarodarpersonur,
        samskipti=fp.samskipti(mappa), skipti=skipti,
        vinaskipti=[(r["character"], int(r["two_person_scene_lines"]),
                     int(r["lines_mentioning_phoebe"]), int(r["lines_naming_phoebe_at_edge"]))
                    for r in vinaskipti],
        skipti_eftir_rod=eftir_rod,
        nafntilvik=[(r["season"], r["mentions_in_dialogue_by_others"],
                     r["mentions_in_own_dialogue"], r["mentions_in_stage_directions"],
                     r["mentions_formal_phoebe"], r["mentions_nickname_pheebs"],
                     r["top_mentioner"], r["top_mentioner_count"]) for r in nafntilvik],
        ordtok=fp.ordtok(mappa), ord=fp.ord_phoebe(mappa),
        lift_ur_skra={r["character"]: float(r["interaction_lift"]) for r in vinaskipti},
    )
