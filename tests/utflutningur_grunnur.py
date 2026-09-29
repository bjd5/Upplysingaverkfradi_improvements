"""Sameiginleg umgjörð fyrir útflutningsprófin (issue #15).

Grunnurinn er byggður úr sömu migrations og frosnu ``data/raw/`` og
alvörugrunnurinn, í tímabundinni möppu. Útflutningurinn skrifar líka í
tímabundna möppu — **aldrei** í ``web/gogn/``.

Hjálpareining, ekki prófskrá: ``unittest discover`` hleður henni aðeins þegar
próf flytja hana inn.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import tenging  # noqa: E402
from vinnsla import hagstofan, vedurstodvar_hledsla  # noqa: E402

# Keyrarinn varar við götum í migration-númerum og hleðslurnar skrá hvert
# skref. Hvorugt er það sem prófin mæla.
for _heiti in ("gagnagrunnur.keyrari", "vinnsla.hagstofan", "vinnsla.vedurstodvar_hledsla",
               "utflutningur.flytja_ut"):
    logging.getLogger(_heiti).setLevel(logging.ERROR)

VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
HAGSTOFAN_RA = ROT / "data" / "raw" / "hagstofan"
VEDURSTODVAR_RA = ROT / "data" / "raw" / "vedurstodvar"


def byggja_grunn(slod: Path) -> Path:
    """Keyrir migrations og hleður Hagstofunni og veðurstöðvunum í nýjan grunn."""
    with tenging(slod) as samband:
        keyra(samband)
    with tenging(slod) as samband:
        hagstofan.hlada(samband)
        vedurstodvar_hledsla.hlada(samband)
    return slod


def afrita_grunn(fra: Path, til: Path) -> Path:
    """Afrit sem próf má skemma án þess að snerta sameiginlega grunninn."""
    shutil.copyfile(fra, til)
    return til


def lesa_json(slod: Path) -> dict:
    return json.loads(slod.read_text(encoding="utf-8"))


def vidmidsradir(sida: str) -> list[dict]:
    """Allar tölur frosna viðmiðsins á einni síðu gömlu síðunnar."""
    return [rad for rad in lesa_json(VIDMID_JSON)["gogn"] if rad.get("sida") == sida]
