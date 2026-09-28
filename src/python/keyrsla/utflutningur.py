"""``--skref flytja-ut``: grunnurinn út í ``web/gogn/`` (issue #15).

Hér er aðeins ákveðið hvaðan er lesið, hvert er skrifað og hvernig villa er
sögð; útflutningurinn sjálfur er í ``utflutningur.flytja``. Villa er vafin í
:class:`SkrefVilla` svo ``main.py`` stöðvi með útgangskóða 1 — og þá hefur
engin skrá í ``web/gogn/`` verið yfirskrifuð (skrifin eru atómísk).
"""

from __future__ import annotations

import logging
from pathlib import Path

from gagnagrunnur.tenging import ROT
from utflutningur.flytja import UTFLUTNINGSVILLUR, flytja_ut

from .villa import SkrefVilla

log = logging.getLogger(__name__)


def flytja_allt(grunnur: Path, mappa: Path) -> list[Path]:
    """Flytur öll söfnin út og skráir stærð hverrar skráar og samtöluna."""
    try:
        skrifadar = flytja_ut(grunnur, mappa)
    except UTFLUTNINGSVILLUR as villa:
        raise SkrefVilla(f"Útflutningur í {_stutt(mappa)} mistókst: {villa}") from villa
    samtals = 0
    for slod in skrifadar:
        staerd = slod.stat().st_size
        samtals += staerd
        log.info("Skrifaði %s (%d bæti).", _stutt(slod), staerd)
    log.info("Útflutningi lokið: %d skrár, %d bæti alls.", len(skrifadar), samtals)
    return skrifadar


def _stutt(slod: Path) -> str:
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)
