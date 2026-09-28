"""Hlaðinn grunnur og útfluttar skrár fyrir útflutningsprófin (issue #15).

Grunnurinn er byggður **eins og ``main.py --skref hlada`` byggir hann** —
migrations og ``keyrsla.hledsla.hlada_ollum`` á frosnu söfnunum — í tímabundna
möppu. Ekkert er handskrifað hér; annars prófuðu prófin annan grunn en þann sem
síðan byggir á. ``data/`` er aðeins lesið og ``web/gogn/`` aldrei skrifað.

Byggt einu sinni á prófkeyrslu og hreinsað í lokin (``atexit``).

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py``.
"""

from __future__ import annotations

import atexit
import json
import logging
import tempfile
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import tenging  # noqa: E402
from keyrsla.hledsla import hlada_ollum  # noqa: E402
from utflutningur.flytja import flytja_ut  # noqa: E402

for _heiti in ("gagnagrunnur", "keyrsla", "vinnsla", "utflutningur"):
    logging.getLogger(_heiti).setLevel(logging.ERROR)

_TMP = tempfile.TemporaryDirectory()
atexit.register(_TMP.cleanup)
TMP = Path(_TMP.name)

_GRUNNUR: Path | None = None
_UTTAK: Path | None = None


def byggja_grunn(slod: Path) -> Path:
    """Nýr grunnur á ``slod`` úr migrations og öllum fimm söfnunum."""
    with tenging(slod) as samband:
        keyra(samband)
    with tenging(slod) as samband:
        hlada_ollum(samband)
    return slod


def grunnur() -> Path:
    """Sameiginlegi grunnurinn — byggður í fyrsta kalli."""
    global _GRUNNUR
    if _GRUNNUR is None:
        _GRUNNUR = byggja_grunn(TMP / "utflutningur.sqlite")
    return _GRUNNUR


def uttak() -> Path:
    """Mappa með skránum sem útflutningurinn skrifaði úr sameiginlega grunninum."""
    global _UTTAK
    if _UTTAK is None:
        _UTTAK = TMP / "gogn"
        flytja_ut(grunnur(), _UTTAK)
    return _UTTAK


def lesa(heiti: str) -> dict:
    """Ein útflutt skrá, lesin sem JSON."""
    return json.loads((uttak() / heiti).read_text(encoding="utf-8"))


def baeti_moppu(mappa: Path) -> dict[str, bytes]:
    """Heiti og bæti allra skráa í möppunni (ekki undirmöppur)."""
    return {slod.name: slod.read_bytes() for slod in sorted(mappa.iterdir()) if slod.is_file()}
