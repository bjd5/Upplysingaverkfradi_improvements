"""Atómísk skrif í ``web/gogn/``: allar skrár eða engin (issue #15, regla 6).

Hálfskrifuð JSON-skrá á ekki að geta orðið til, og síðan á ekki heldur að geta
lent í blöndu af nýrri skrá eins safns og eldri skrá annars. Þess vegna:

1. **Allt er sniðið í minni fyrst** (``snida``). Falli útflutningur eins safns
   gerist það áður en nokkuð er skrifað.
2. **Allar skrár eru skrifaðar í tímabundna möppu** innan markmöppunnar —
   sama skráakerfi, svo ``os.replace`` er atómískt. Falli skrif einnar skrár
   (fullur diskur, heimildir) er tímabundna mappan fjarlægð og engin markskrá
   hefur verið snert.
3. **Aðeins þá er hverri skrá skipt inn** með ``os.replace``. Hver skipti eru
   atómísk: lesandi sér annaðhvort gömlu skrána eða þá nýju, aldrei hálfa.

Sniðið er ákvarðað: ``ensure_ascii=False``, inndráttur 1, röð lykla eins og
einingarnar skrifa þá og ``\\n`` í lokin. Sömu gögn gefa því sömu bæti.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

INNDRATTUR = 1
FORSKEYTI_TIMABUNDIN = ".utflutningur-"


def snida(skjal: dict) -> bytes:
    """JSON-bæti skráar. ``allow_nan=False``: NaN er ekki gilt JSON og vafrinn hafnar því."""
    texti = json.dumps(skjal, ensure_ascii=False, indent=INNDRATTUR, allow_nan=False)
    return (texti + "\n").encode("utf-8")


def skrifa_allar(skrar: dict[str, bytes], mappa: Path) -> list[Path]:
    """Skrifar allar skrárnar í ``mappa`` atómískt og skilar slóðum þeirra.

    Skrá í ``mappa`` sem er ekki í ``skrar`` er látin óhreyfð.
    """
    for heiti in skrar:
        if Path(heiti).name != heiti or not heiti.endswith(".json"):
            raise ValueError(f"Óleyfilegt skráarheiti í web/gogn/: {heiti!r}")
    mappa.mkdir(parents=True, exist_ok=True)
    timabundin = Path(tempfile.mkdtemp(prefix=FORSKEYTI_TIMABUNDIN, dir=mappa))
    try:
        for heiti, baeti in skrar.items():
            with open(timabundin / heiti, "wb") as skra:
                skra.write(baeti)
                skra.flush()
                os.fsync(skra.fileno())
        for heiti in skrar:
            os.replace(timabundin / heiti, mappa / heiti)
    finally:
        _fjarlaegja(timabundin)
    return [mappa / heiti for heiti in skrar]


def _fjarlaegja(timabundin: Path) -> None:
    """Fjarlægir tímabundnu möppuna; mistakist það er það sagt, ekki þagað."""
    try:
        shutil.rmtree(timabundin)
    except OSError as villa:
        log.warning("Tókst ekki að fjarlægja tímabundna möppu %s: %s", timabundin, villa)
