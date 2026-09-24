"""Tenging við SQL-grunn rannsóknarinnar.

Grunnurinn er afleiða, ekki frumgagn: hann verður eingöngu til úr
``src/sql/migrations/`` og ``data/raw/`` og fer aldrei í git (regla 5).
Þessi eining sér um tvennt sem má ekki mistakast:

* **foreign_keys er kveikt.** SQLite hunsar ``PRAGMA foreign_keys`` inni í
  færslu, svo hún er sett áður en færslustýring er tekin yfir — og staðfest
  á eftir. Þögul afþökkun á tilvísunarheilindum er ekki í boði (regla 6).
* **Hver lota endar á commit eða rollback.** Aldrei hálfkláruð færsla.

Slóð grunnsins ræðst í þessari röð:

1. slóðin sem fallinu er gefin,
2. umhverfisbreytan ``RANNSOKN_GRUNNUR`` (notuð í prófum og endurbyggingu),
3. ``data/db/rannsokn.sqlite``.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# autocommit=False kom í Python 3.12. Án þess er DDL utan færslu og migration
# sem fellur skilur eftir sig hálfbyggðan grunn — sjá keyrari.beita().
LAGMARKS_PYTHON = (3, 12)

if sys.version_info < LAGMARKS_PYTHON:
    raise RuntimeError(
        f"Python {LAGMARKS_PYTHON[0]}.{LAGMARKS_PYTHON[1]} eða nýrra þarf til að "
        f"migrations keyri í heilli færslu; fann "
        f"{sys.version_info[0]}.{sys.version_info[1]}."
    )

ROT = Path(__file__).resolve().parents[3]
SJALFGEFIN_SLOD = ROT / "data" / "db" / "rannsokn.sqlite"
UMHVERFISBREYTA = "RANNSOKN_GRUNNUR"


def slod_grunns(slod: Path | str | None = None) -> Path:
    """Skilar slóð grunnsins eftir forgangsröðinni sem lýst er í haus skrárinnar."""
    if slod is not None:
        return Path(slod)
    ur_umhverfi = os.environ.get(UMHVERFISBREYTA)
    if ur_umhverfi:
        return Path(ur_umhverfi)
    return SJALFGEFIN_SLOD


def opna(slod: Path | str | None = None) -> sqlite3.Connection:
    """Opnar tengingu með foreign_keys á og handvirkri færslustýringu.

    Kallandinn ber ábyrgð á commit/rollback og á að loka tengingunni.
    Notaðu ``tenging()`` í staðinn nema þú þurfir að stýra því sjálf(ur).
    """
    skra = slod_grunns(slod)
    skra.parent.mkdir(parents=True, exist_ok=True)

    # Pragman verður að vera sett utan færslu, því er byrjað í autocommit.
    samband = sqlite3.connect(skra, autocommit=True)
    samband.row_factory = sqlite3.Row
    samband.execute("PRAGMA foreign_keys = ON")

    kveikt = samband.execute("PRAGMA foreign_keys").fetchone()[0]
    if kveikt != 1:
        samband.close()
        raise RuntimeError(
            f"Tókst ekki að kveikja á foreign_keys fyrir {skra}. "
            "Grunnurinn væri þá án tilvísunarheilinda og er því ekki opnaður."
        )

    samband.autocommit = False
    return samband


@contextmanager
def tenging(slod: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Opnar grunninn og lokar færslunni rétt hvernig sem lotan endar.

    Eðlileg lok -> commit. Villa -> rollback og villan heldur áfram upp
    (regla 6: villur eru aldrei þaggaðar).
    """
    samband = opna(slod)
    try:
        yield samband
    except BaseException:
        samband.rollback()
        raise
    else:
        samband.commit()
    finally:
        samband.close()
