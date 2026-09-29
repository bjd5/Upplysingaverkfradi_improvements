"""Útflutningur úr SQL-grunninum í ``web/gogn/*.json`` (regla 5.4, issue #15).

Síðasta skref gagnaflæðisins (kafli 0 í CLAUDE.md)::

    SQL-grunnur  →  flytja_ut()  →  web/gogn/<safn>.json  →  vefsíðan

Hver eining í ``UTFLUTNINGAR`` les eitt gagnasafn úr grunninum og skilar
sannreyndu umslagi (``utflutningur.json_skrif``): skjálftar, Hagstofan,
veðurstöðvar, mbl.is og Phoebe-tölfræðin. ``yfirlit.json`` (forsíðan) er
reiknað úr umslögunum. Söfnin í ``AN_UTFLUTNINGS`` eiga enn engan útflutning;
hver keyrsla segir það í viðvörun svo það gleymist ekki (regla 6).

``src/python/main.py --skref flytja-ut`` (og ``allt``) kallar í
:func:`flytja_ut` og breytir villu í útgangskóða 1.

Röðin er **fyrst allt lesið, svo allt skrifað**: bregðist eitt safn er engin
skrá skrifuð, ekki heldur þau sem tókust. Skrárnar eru svo skrifaðar saman
atómískt (``json_skrif.skrifa_allar_atomiskt``): falli skrif einnar — t.d.
fullur diskur — er engin markskrá leyst af hólmi.

Keyrsla frá rót verkefnisins::

    PYTHONPATH=src/python python3.12 -m utflutningur.flytja_ut [--uttak MAPPA] [--grunnur SLÓÐ]

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path
from sqlite3 import Connection
from typing import Any

from gagnagrunnur.fyrirspurnir import FyrirspurnaVilla
from gagnagrunnur.tenging import ROT, opna, slod_grunns

from . import hagstofan_json, mbl_json, phoebe_json, skjalftar_json, vedurstodvar_json
from . import yfirlit_json
from .json_skrif import UtflutningsVilla, sem_baeti, skrifa_allar_atomiskt

log = logging.getLogger(__name__)

VEFGOGN = ROT / "web" / "gogn"

# Skráarheiti -> fall sem les grunninn og skilar umslagi.
UTFLUTNINGAR: dict[str, Callable[[Connection], dict[str, Any]]] = {
    skjalftar_json.SKRAARHEITI: skjalftar_json.byggja,
    hagstofan_json.SKRAARHEITI: hagstofan_json.byggja,
    vedurstodvar_json.SKRAARHEITI: vedurstodvar_json.byggja,
    mbl_json.SKRAARHEITI: mbl_json.byggja,
    phoebe_json.SKRAARHEITI: phoebe_json.byggja,
}


# Allar skrár sem útflutningurinn skrifar, í röð: söfnin og svo forsíðuyfirlitið.
SKRAR: tuple[str, ...] = (*UTFLUTNINGAR, yfirlit_json.SKRAARHEITI)

# Villur sem þýða að gögnin eða grunnurinn standast ekki — main.py gerir þær
# að SkrefVilla. Annað (TypeError, KeyError …) er forritunarvilla og fellur óvafið.
UTFLUTNINGSVILLUR = (UtflutningsVilla, FyrirspurnaVilla, sqlite3.Error, OSError)

# Söfn sem eru hlaðin í grunninn en eiga enn engan útflutning (#15).
# Central Perk er í grunninum (#71, migration 007) en á ekki útflutning enn;
# TMDB var aldrei fryst og er ekki í grunninum.
AN_UTFLUTNINGS: tuple[str, ...] = (
    "Central Perk (phoebe-central-perk.html)",
    "TMDB (phoebe-tmdb.html) — ekki í grunninum",
)


def flytja_ut(uttaksmappa: Path = VEFGOGN, grunnur: Path | str | None = None) -> list[Path]:
    """Flytur öll útfærð gagnasöfn úr grunninum í ``uttaksmappa``.

    ``grunnur`` fylgir forgangsröð ``gagnagrunnur.tenging.slod_grunns``. Grunnur
    sem er ekki til er villa: ``opna()`` myndi annars búa til tóman grunn og
    útflutningurinn falla með óskýrari villu.

    Skilar slóðum skrifuðu skránna í sömu röð og ``UTFLUTNINGAR``, og
    ``yfirlit.json`` síðast.
    """
    slod = slod_grunns(grunnur)
    if not slod.is_file():
        raise UtflutningsVilla(
            f"Grunnurinn {slod} er ekki til. Byggðu hann fyrst: scripts/endurbyggja-grunn.sh"
        )

    samband = opna(slod)
    try:
        # Allt lesið og raðað í bæti áður en fyrsta skrá er snert.
        umslog = {heiti: byggja(samband) for heiti, byggja in UTFLUTNINGAR.items()}
    finally:
        samband.rollback()
        samband.close()
    umslog[yfirlit_json.SKRAARHEITI] = yfirlit_json.byggja(umslog)
    tilbuid = {heiti: sem_baeti(umslag) for heiti, umslag in umslog.items()}

    skrifadar = skrifa_allar_atomiskt(Path(uttaksmappa), tilbuid)
    for mark in skrifadar:
        log.info("Skrifaði %s (%d bæti)", mark, len(tilbuid[mark.name]))
    log.info("Samtals %d bæti í %d skrám.", sum(map(len, tilbuid.values())), len(tilbuid))
    log.warning(
        "Enginn útflutningur enn fyrir: %s — síður þeirra fá ekki gögn úr web/gogn/ (#15).",
        "; ".join(AN_UTFLUTNINGS),
    )
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
