"""Útflutningur úr grunninum í ``web/gogn/`` — síðasta skref gagnaflæðisins (#15).

    SQL-grunnur  →  src/sql/queries/  →  utflutningur.<safn>  →  web/gogn/*.json

Ein eining á hvert gagnasafn og ein skrá á hverja síðu sem á gögn í grunninum:

=========================  ==================================  ===========
skrá                       síða                                eining
=========================  ==================================  ===========
``skjalftar.json``         ``sidur/skjalftavaktin.html`` (#20)  ``skjalftar``
``hagstofan.json``         ``sidur/hagstofan.html`` (#21)       ``hagstofan``
``vedurstodvar.json``      ``sidur/vedurstodvar.html`` (#22)    ``vedurstodvar``
``mbl.json``               ``sidur/mbl-regex.html`` (#23)       ``mbl``
``phoebe-tolfraedi.json``  ``sidur/phoebe-tolfraedi.html`` (#24) ``phoebe``
``yfirlit.json``           ``index.html`` (``stada-gagna.js``)  hér
=========================  ==================================  ===========

Central Perk og TMDB eru ekki í grunninum og fá því enga skrá hér: skrá úr
annarri heimild en grunninum bryti einstefnu gagnaflæðisins (kafli 0).

``yfirlit.json`` heldur sniði sem ``web/assets/js/stada-gagna.js`` les óbreytt:
``gogn`` er listi (JS-ið telur færslurnar) og ``heimild`` strengur. Hver færsla
er ein útflutt skrá; ``uppfaert`` er nýjasti gagnastimpill þeirra.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur.tenging import opna
from vinnsla.vedurstodvar_fyrirspurnir import skra_fjarlaegdarfall

from . import hagstofan, mbl, phoebe, skjalftar, vedurstodvar
from .skjal import UtflutningsVilla
from .skrifa import skrifa_allar, snida

log = logging.getLogger(__name__)

YFIRLIT = "yfirlit.json"
VEFROT = "web/"

# Villur sem þýða að gögnin duga ekki: eigin villur eininganna og lesarans
# (RuntimeError), gildisvillur, diskur og SQL. TypeError, KeyError o.þ.h. eru
# forritunarvillur og fá að falla óvafðar.
UTFLUTNINGSVILLUR = (RuntimeError, ValueError, OSError, sqlite3.Error)


@dataclass(frozen=True)
class Safn:
    """Eitt útflutt safn: skráin, síðan sem les hana og fallið sem byggir hana."""

    skra: str
    sida: str
    fyrirspurnir: tuple[str, ...]
    byggja: Callable[[Connection], dict]


SOFN: tuple[Safn, ...] = tuple(
    Safn(eining.SKRA, eining.SIDA, eining.FYRIRSPURNIR, eining.byggja)
    for eining in (skjalftar, hagstofan, vedurstodvar, mbl, phoebe)
)


def _thjonusta(heimild: str) -> str:
    """Þjónustuheitið fremst í heimildarstrengnum (``Veðurstofa Íslands — …``)."""
    return heimild.split(" — ")[0]


def yfirlit(skjol: dict[str, dict], sofn: tuple[Safn, ...] = SOFN) -> dict:
    """``yfirlit.json``: ein færsla á útflutta skrá, á sniðinu sem stada-gagna.js les."""
    faerslur = [
        {
            "skra": safn.skra,
            "sida": safn.sida.removeprefix(VEFROT),
            "uppfaert": skjol[safn.skra]["uppfaert"],
            "heimild": skjol[safn.skra]["heimild"],
        }
        for safn in sofn
    ]
    if not faerslur:
        raise UtflutningsVilla("Ekkert safn til að flytja út.")
    thjonustur = list(dict.fromkeys(_thjonusta(f["heimild"]) for f in faerslur))
    # ISO-strengirnir eru allir á sama UTC-sniði (skjal.utc_stimpill), svo
    # strengjaröð er tímaröð.
    return {
        "uppfaert": max(f["uppfaert"] for f in faerslur),
        "heimild": ", ".join(thjonustur),
        "gogn": faerslur,
    }


def byggja_allar(samband: Connection, sofn: tuple[Safn, ...] = SOFN) -> dict[str, dict]:
    """Byggir allar skrárnar í minni; engin er skrifuð fyrr en allar hafa tekist."""
    skra_fjarlaegdarfall(samband)
    skjol: dict[str, dict] = {}
    for safn in sofn:
        try:
            skjol[safn.skra] = safn.byggja(samband)
        except UTFLUTNINGSVILLUR as villa:
            raise UtflutningsVilla(f"Útflutningur {safn.skra} mistókst: {villa}") from villa
        log.info("Byggði %s.", safn.skra)
    skjol[YFIRLIT] = yfirlit(skjol, sofn)
    return skjol


def flytja_ut(grunnur: Path, mappa: Path, sofn: tuple[Safn, ...] = SOFN) -> list[Path]:
    """Les grunninn og skrifar allar skrárnar í ``mappa`` — allar eða engar.

    Grunnurinn er aðeins lesinn. Sé hann ekki til er stöðvað: ``opna`` myndi
    annars búa til tóman grunn og útflutningurinn þegja um það.
    """
    if not grunnur.is_file():
        raise UtflutningsVilla(
            f"Grunnurinn {grunnur} er ekki til — keyrðu `--skref hlada` á undan útflutningi."
        )
    samband = opna(grunnur)
    try:
        skjol = byggja_allar(samband, sofn)
    finally:
        samband.rollback()
        samband.close()
    baeti = {heiti: snida(skjal) for heiti, skjal in skjol.items()}
    return skrifa_allar(baeti, mappa)
