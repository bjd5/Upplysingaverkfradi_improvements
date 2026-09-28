"""Útflutningur úr SQL-grunninum í ``web/gogn/*.json`` (regla 5.4, issue #15).

Síðasta skref gagnaflæðisins (kafli 0 í CLAUDE.md)::

    SQL-grunnur  →  flytja_ut()  →  web/gogn/<safn>.json  →  vefsíðan

Hver eining í ``UTFLUTNINGAR`` les eitt gagnasafn úr grunninum og skilar
sannreyndu umslagi (``utflutningur.json_skrif``). Enn sem komið er:
Hagstofan og veðurstöðvarnar; skjálftar, mbl og Friends bætast við síðar.

**Tenging við ``src/python/main.py``** (verk annars agents): skrefið
``flytja_ut`` þar á að kalla í :func:`flytja_ut` með ``uttaksmappa=VEFGOGN`` og
``grunnur=GAGNAGRUNNUR`` og láta :class:`UtflutningsVilla` falla upp.

Röðin er **fyrst allt lesið, svo allt skrifað**: bregðist eitt safn er engin
skrá skrifuð, ekki heldur þau sem tókust. Hver skrá er svo skrifuð atómískt.

Keyrsla frá rót verkefnisins::

    PYTHONPATH=src/python python3.12 -m utflutningur.flytja_ut [--uttak MAPPA] [--grunnur SLÓÐ]

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from sqlite3 import Connection
from typing import Any

from gagnagrunnur.tenging import ROT, opna, slod_grunns

from . import hagstofan_json, vedurstodvar_json
from .json_skrif import UtflutningsVilla, sem_baeti, skrifa_atomiskt

log = logging.getLogger(__name__)

VEFGOGN = ROT / "web" / "gogn"

# Skráarheiti -> fall sem les grunninn og skilar umslagi.
UTFLUTNINGAR: dict[str, Callable[[Connection], dict[str, Any]]] = {
    hagstofan_json.SKRAARHEITI: hagstofan_json.byggja,
    vedurstodvar_json.SKRAARHEITI: vedurstodvar_json.byggja,
}


def flytja_ut(uttaksmappa: Path = VEFGOGN, grunnur: Path | str | None = None) -> list[Path]:
    """Flytur öll útfærð gagnasöfn úr grunninum í ``uttaksmappa``.

    ``grunnur`` fylgir forgangsröð ``gagnagrunnur.tenging.slod_grunns``. Grunnur
    sem er ekki til er villa: ``opna()`` myndi annars búa til tóman grunn og
    útflutningurinn falla með óskýrari villu.

    Skilar slóðum skrifuðu skránna í sömu röð og ``UTFLUTNINGAR``.
    """
    slod = slod_grunns(grunnur)
    if not slod.is_file():
        raise UtflutningsVilla(
            f"Grunnurinn {slod} er ekki til. Byggðu hann fyrst: scripts/endurbyggja-grunn.sh"
        )

    samband = opna(slod)
    try:
        # Allt lesið og raðað í bæti áður en fyrsta skrá er snert.
        tilbuid = {heiti: sem_baeti(byggja(samband)) for heiti, byggja in UTFLUTNINGAR.items()}
    finally:
        samband.rollback()
        samband.close()

    skrifadar = []
    for heiti, baeti in tilbuid.items():
        mark = Path(uttaksmappa) / heiti
        skrifa_atomiskt(mark, baeti)
        log.info("Skrifaði %s (%d bæti)", mark, len(baeti))
        skrifadar.append(mark)
    return skrifadar


def main(rok: list[str] | None = None) -> int:
    """Skipanalínuinngangur; skilar 0 þegar allar skrár eru skrifaðar."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("--uttak", type=Path, default=VEFGOGN, help="úttaksmappa")
    thattari.add_argument("--grunnur", type=Path, default=None, help="slóð SQL-grunnsins")
    stillingar = thattari.parse_args(rok)
    flytja_ut(stillingar.uttak, stillingar.grunnur)
    return 0


if __name__ == "__main__":
    sys.exit(main())
