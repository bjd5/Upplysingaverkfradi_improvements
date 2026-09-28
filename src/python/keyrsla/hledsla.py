"""Hleðsla allra gagnasafnanna í grunninn — ``--skref hlada`` (issue #39).

Hvert safn á sína hleðslueiningu í ``vinnsla/`` (#6–#10; Central Perk er #10 líka). Hér er aðeins
ákveðið **hvaða** söfn eru hlaðin, **í hvaða röð** og **hvað gerist ef eitt
vantar**; innviðum eininganna er ekki breytt, kallað er í opinberu föllin.

Röðin er röð migration-skránna (002–007):

* Engin tafla vísar í töflu annars safns — allir framandi lyklar eru innan
  safns og hver hleðsla skrifar foreldri á undan barni. Migrations 001–007
  eru keyrðar á undan, svo allar töflur eru til.
* Hagstofan og veðurstöðvarnar skrifa báðar í sameiginlegu töfluna
  ``fetch_log`` (001), þar sem ``id`` fær næsta lausa gildi. Föst röð gefur
  því sömu auðkenni í hverri byggingu — það sem ``endurbyggja-grunn.sh``
  staðfestir með fingrafarinu.

**Vanti frosið safn stöðvast allt** (regla 6): fyrst er gengið úr skugga um að
aðföng allra safna séu til, *áður* en grunnurinn er snertur, og öllum sem vantar
lýst í einni villu. Falli hleðsla á leiðinni er villan vafin í
:class:`SkrefVilla` með heiti safnsins, og öll söfnin eru í einni færslu svo
grunnurinn situr ekki eftir með hluta þeirra.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur.tenging import ROT
from vinnsla import friends_hledsla, hagstofan, jardskjalftar_hledsla, mbl_hledsla
from vinnsla import central_perk_hledsla, vedurstodvar_hledsla
from vinnsla.friends_skrar import STATS_MAPPA
from vinnsla.jardskjalftar import ATBURDIR
from vinnsla.mbl_eintak import MBL_MAPPA

from .villa import SkrefVilla

log = logging.getLogger(__name__)

# Villur sem hleðslueiningarnar kasta þegar gögnin standast ekki: eigin
# villuklasar þeirra (RuntimeError/ValueError), lestur af diski og SQL-skorður.
# Annað (TypeError, KeyError …) er forritunarvilla og fær að falla óvafið.
HLEDSLUVILLUR = (RuntimeError, ValueError, OSError, sqlite3.Error)


@dataclass(frozen=True)
class Safn:
    """Eitt gagnasafn: heiti, issue, frosna aðfangið og hleðslufallið."""

    heiti: str
    issue: int
    frosid: Path
    hlada: Callable[[Connection, Path], str]

    @property
    def merki(self) -> str:
        return f"{self.heiti} (#{self.issue})"


def _hlada_skjalftum(samband: Connection, slod: Path) -> str:
    talning = jardskjalftar_hledsla.hlada(samband, slod)
    return f"{talning.atburdir} atburðir á {talning.dagar} UTC-dögum"


def _hlada_hagstofu(samband: Connection, mappa: Path) -> str:
    return f"{hagstofan.hlada(samband, mappa)} mælingar"


def _hlada_stodvum(samband: Connection, mappa: Path) -> str:
    nidurstada = vedurstodvar_hledsla.hlada(samband, mappa)
    return f"{nidurstada.fjoldi} stöðvar, {nidurstada.virkar} enn starfræktar"


def _hlada_mbl(samband: Connection, mappa: Path) -> str:
    hledslur = mbl_hledsla.hlada_ollu(samband, mappa)
    # Svörin lesin aftur úr SQL: eintak með fjögur svör af fimm stöðvar hér.
    for hledsla in hledslur:
        mbl_hledsla.stadfesta_svor(samband, hledsla.eintak.sotta_stund)
    return f"{len(hledslur)} eintök, {mbl_hledsla.SVOR_A_EINTAK} svör á hvert"


def _hlada_friends(samband: Connection, mappa: Path) -> str:
    fjoldi = friends_hledsla.hlada(samband, mappa)
    return (
        f"{fjoldi['friends_transcript_files']} handritsskrár, "
        f"{fjoldi['friends_episode_lines']} línuraðir"
    )


def _hlada_central_perk(samband: Connection, mappa: Path) -> str:
    fjoldi = central_perk_hledsla.hlada(samband, mappa)
    return (
        f"{fjoldi['central_perk_transcript_files']} handritsskrár, "
        f"{fjoldi['central_perk_patterns']} segðir"
    )


# Röð migration-skránna — sjá haus skrárinnar um af hverju.
SOFN: tuple[Safn, ...] = (
    Safn("Jarðskjálftar", 6, ATBURDIR, _hlada_skjalftum),
    Safn("Hagstofan", 7, hagstofan.HRAGOGN, _hlada_hagstofu),
    Safn("Veðurstöðvar", 8, vedurstodvar_hledsla.FROSID, _hlada_stodvum),
    Safn("mbl.is", 9, MBL_MAPPA, _hlada_mbl),
    Safn("Friends", 10, STATS_MAPPA, _hlada_friends),
    Safn("Central Perk", 10, central_perk_hledsla.adfang.ADFANGSMAPPA, _hlada_central_perk),
)


def _stutt(slod: Path) -> str:
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)


def _er_til(slod: Path) -> bool:
    """Skrá sem er til, eða mappa sem er til og ekki tóm."""
    if slod.is_dir():
        return any(slod.iterdir())
    return slod.is_file()


def krefjast_adfanga(sofn: tuple[Safn, ...] | None = None) -> None:
    """Stöðvar ef frosið aðfang einhvers safns vantar — og nefnir þau öll.

    Kallað áður en grunnurinn er opnaður: það sem vantar á að sjást í einni
    villu, ekki eitt í einu yfir margar keyrslur.
    """
    vantar = [s for s in (SOFN if sofn is None else sofn) if not _er_til(s.frosid)]
    if vantar:
        lysing = "; ".join(f"{s.merki}: {_stutt(s.frosid)}" for s in vantar)
        raise SkrefVilla(
            f"Frosið gagnasafn vantar — ekkert var hlaðið. {lysing}. Hrágögnin "
            "eiga að liggja í git (data/raw/README.md, data/processed/README.md); "
            "sæktu þau með scripts/saekja-gogn.sh eða endurheimtu þau úr git."
        )


def hlada_ollum(samband: Connection, sofn: tuple[Safn, ...] | None = None) -> list[str]:
    """Hleður hverju safni í röð í færslu kallandans og skilar yfirliti á safn.

    Kallandinn á færsluna (``gagnagrunnur.tenging.tenging``): falli eitt safn er
    öllum rúllað til baka, svo grunnurinn geymir annaðhvort öll söfnin eða ekkert
    þeirra.
    """
    sofn = SOFN if sofn is None else sofn
    krefjast_adfanga(sofn)
    yfirlit: list[str] = []
    for safn in sofn:
        try:
            lysing = safn.hlada(samband, safn.frosid)
        except HLEDSLUVILLUR as villa:
            raise SkrefVilla(
                f"Hleðsla {safn.merki} úr {_stutt(safn.frosid)} mistókst: {villa}"
            ) from villa
        log.info("Hlóð %s: %s.", safn.merki, lysing)
        yfirlit.append(f"{safn.merki}: {lysing}")
    return yfirlit

