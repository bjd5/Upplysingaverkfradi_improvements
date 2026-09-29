"""Einn hlaðinn grunnur fyrir fyrirspurnaprófin (issue #11).

Grunnurinn er byggður **úr sömu migrations og hleðslum og alvörugrunnurinn** —
``gagnagrunnur.keyrari.keyra`` og hleðslueining hvers gagnasafns á frosnu
eintökunum. Ekkert ``CREATE TABLE`` og engin innsetning er handskrifuð hér;
annars prófuðu prófin annan grunn en þann sem síðan byggir á.

Hann er byggður einu sinni á hverja prófkeyrslu (``hladinn_grunnur``) og
lokaður í lokin, því fimm hleðslur á hvert próf margfölduðu keyrslutímann.
Fyrirspurnirnar lesa bara; ekkert próf skrifar í þennan grunn.

``DAEMISBREYTUR`` gefur hverri fyrirspurn með ``?`` breytur sem eiga að skila
röðum — prófið sem keyrir allar fyrirspurnirnar krefst þess að hver slík eigi
línu hér, svo ný fyrirspurn sleppi ekki óprófuð.

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py``.
"""

from __future__ import annotations

import atexit
import logging
import sqlite3
import tempfile
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from vinnsla import friends_hledsla, hagstofan, jardskjalftar_hledsla  # noqa: E402
from vinnsla import mbl_hledsla, vedurstodvar_hledsla  # noqa: E402
from vinnsla import central_perk_hledsla  # noqa: E402
from vinnsla import vedurstodvar_samanburdur as vedur  # noqa: E402
from vinnsla.mbl_eintak import finna_eintok  # noqa: E402
from vinnsla.vedurstodvar_fyrirspurnir import skra_fjarlaegdarfall  # noqa: E402
from mbl_hjalp import FROSNA_EINTAKID  # noqa: E402

# Keyrarinn og hleðslurnar skrá hvert skref; það er ekki það sem prófin mæla.
for _heiti in ("gagnagrunnur.keyrari", "vinnsla"):
    logging.getLogger(_heiti).setLevel(logging.ERROR)

HAGSTOFAN_TAFLA = "SKO04208b"
# Sóknartími frosna mbl-eintaksins, lesinn úr lýsigögnum þess — ekki sleginn inn.
MBL_EINTAK = next(e.sotta_stund for e in finna_eintok()
                  if e.skraarheiti.startswith(FROSNA_EINTAKID))
_MORK = vedur.kassi(vedur.VR_II_BREIDD, vedur.VR_II_LENGD, vedur.RADIUS_KM)
_KASSI = (_MORK[1], _MORK[3], _MORK[0], _MORK[2])  # breidd á undan lengd
_HNIT = (vedur.VR_II_BREIDD, vedur.VR_II_LENGD)

DAEMISBREYTUR: dict[str, tuple] = {
    "hagstofan-hlutfoll": (HAGSTOFAN_TAFLA,),
    "hagstofan-summur": (HAGSTOFAN_TAFLA,),
    "hagstofan-munur": (HAGSTOFAN_TAFLA, "5", "07", "Alls", "Alls", "Alls"),
    "hagstofan-gagnasafn": (HAGSTOFAN_TAFLA,),
    "hagstofan-fyrirspurn": (HAGSTOFAN_TAFLA,),
    "hagstofan-viddir": (HAGSTOFAN_TAFLA,),
    "hagstofan-kodabok": (HAGSTOFAN_TAFLA,),
    "mbl-svor": (MBL_EINTAK, None, None),
    "vedurstodvar-stod-eftir-audkenni": (vedur.VALIN_STOD,),
    "vedurstodvar-stodvar-i-marghyrningi": _KASSI,
    "vedurstodvar-virkar-stodvar-i-marghyrningi": _KASSI,
    "vedurstodvar-naesta-virka-stod": _HNIT,
    "vedurstodvar-naesta-aflagda-stod": _HNIT,
    "vedurstodvar-naesta-virka-langtimastod": (*_HNIT, vedur.VIDMIDSAR - vedur.AR_AFTUR_I_TIMANN),
    "vedurstodvar-kassi-eftir-fjarlaegd": (*_HNIT, *_KASSI),
    "vedurstodvar-sokn": (vedurstodvar_hledsla.THJONUSTA,),
}

_GRUNNUR: sqlite3.Connection | None = None


def hladinn_grunnur() -> sqlite3.Connection:
    """Grunnur með öllum migrations og öllum gagnasöfnunum hlöðnum (fimm + Central Perk)."""
    global _GRUNNUR
    if _GRUNNUR is None:
        mappa = tempfile.TemporaryDirectory()
        atexit.register(mappa.cleanup)
        samband = opna(Path(mappa.name) / "fyrirspurnir.sqlite")
        atexit.register(samband.close)
        keyra(samband)
        samband.commit()
        jardskjalftar_hledsla.hlada(samband)
        hagstofan.hlada(samband)
        vedurstodvar_hledsla.hlada(samband)
        mbl_hledsla.hlada_ollu(samband)
        friends_hledsla.hlada(samband)
        central_perk_hledsla.hlada(samband)
        samband.commit()
        skra_fjarlaegdarfall(samband)
        _GRUNNUR = samband
    return _GRUNNUR
