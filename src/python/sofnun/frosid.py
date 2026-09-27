"""Vörn gegn því að sækja aftur það sem þegar er fryst (regla 4).

``sofnun.hragogn.finna_fyrra_svar`` þekkir eintak á provenance-sniðinu sem
``sofnun.beidni`` skrifar. Tvö söfn úr upprunaverkefninu voru hins vegar fryst
á **eldri sniðum** sem bera ekki þá reiti sem fingrafarið byggir á:

* ``data/raw/hagstofan/provenance.json`` skráir ``methods`` (fleirtölu, tvær
  aðferðir í einni skrá) og ``sha256`` sem kort af skráarheiti í summu.
* ``data/raw/mbl/mbl-*.json`` er lýsigagnaskrá á sniði skriftunnar sjálfrar og
  heitir ekki ``provenance.json``.

Lagið sér þau því ekki og myndi senda beiðnina aftur. Fyrir mbl.is væri það
beinlínis skaðlegt: forsíðan í dag er annað gagn en forsíðan sem greiningin
byggir á, og tvö eintök í sömu möppu gera það óljóst hvort þeirra tölurnar koma
úr.

Þess vegna stöðva söfnunareiningarnar sig sjálfar þegar frosið eintak finnst.
``thvinga=True`` er leiðin fram hjá — meðvituð ákvörðun um að sækja nýtt
eintak, ekki sjálfgefin hegðun.
"""

from __future__ import annotations

from pathlib import Path

from .hragogn import HRAGOGN, mappa_safns


class FrosidVilla(RuntimeError):
    """Frosið eintak er þegar til og ný sókn myndi skyggja á það."""


def frosin_eintok(thjonusta: str, mynstur: str, rot: Path = HRAGOGN) -> list[Path]:
    """Skilar frosnum skrám safnsins sem passa við ``mynstur`` (glob)."""
    mappa = mappa_safns(thjonusta, rot)
    if not mappa.is_dir():
        return []
    return sorted(skra for skra in mappa.glob(mynstur) if skra.is_file())


def krefjast_thvingunar(
    thjonusta: str,
    mynstur: str,
    *,
    thvinga: bool,
    af_hverju: str,
    rot: Path = HRAGOGN,
) -> None:
    """Fellur með ``FrosidVilla`` sé eintak til og ``thvinga`` ekki sett.

    ``af_hverju`` segir lesandanum hvað tapast við nýja sókn — villan á að
    útskýra ákvörðunina, ekki bara stöðva keyrsluna (regla 6).
    """
    if thvinga:
        return
    til = frosin_eintok(thjonusta, mynstur, rot)
    if not til:
        return
    heiti = ", ".join(skra.name for skra in til)
    raise FrosidVilla(
        f"{thjonusta}: frosið eintak er þegar til ({heiti}). {af_hverju} "
        f"Sæktu nýtt eintak vísvitandi með thvinga=True ef það er ætlunin."
    )
