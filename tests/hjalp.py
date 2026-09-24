"""Sameiginleg hjálp fyrir prófin.

Prófin eru keyrð með staðalsafninu einu (regla 10 — engir nýir pakkar)::

    python3 -m unittest discover -s tests

Innflutningur þessarar einingar setur ``src/python`` á ``sys.path`` svo prófin
nái í pakkana án uppsetningar.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
PYTHON_ROT = ROT / "src" / "python"
ENDURBYGGINGARSKRIFTA = ROT / "scripts" / "endurbyggja-grunn.sh"

if str(PYTHON_ROT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROT))


def skrifa_migration(mappa: Path, numer: int, heiti: str, sql: str) -> Path:
    """Skrifar migration-skrá í prófunarmöppu og skilar slóðinni."""
    slod = mappa / f"{numer:03d}_{heiti}.sql"
    slod.write_text(sql, encoding="utf-8")
    return slod
