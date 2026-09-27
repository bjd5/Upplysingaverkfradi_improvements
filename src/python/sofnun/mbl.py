"""Eitt eintak af forsíðu mbl.is fyrir regex-æfinguna (gagnasafn 4).

Flutt úr ``src/mbl_snapshot.py`` upprunaverkefnisins. Skriftan þar neitaði að
yfirskrifa fyrra eintak; sú varúð er hér áfram, því forsíða fréttamiðils er
**lifandi gagn**. Eintakið frá 16.9.2026 er það sem allar tölur æfingarinnar
eiga við, og nýtt eintak er ekki uppfærsla á því heldur annað gagn.

Þetta er vefsíða en ekki vefþjónusta: ekkert leyfi er gefið og HTML-ið er hrátt
svar, ekki gagnasnið sem lofað hefur verið að haldist óbreytt. Greiningin sem
les það þarf að þola að byggingin sé önnur en hún var.
"""

from __future__ import annotations

from .beidni import Beidni
from .frosid import krefjast_thvingunar
from .hragogn import HRAGOGN, Svar
from .http import saekja

# Frosna eintakið heitir eftir gamla sniðinu; ný sókn fær heitið `forsida-...`.
FROSID_MYNSTUR = "mbl-*.html"

AF_HVERJU = (
    "Forsíðan í dag er annað gagn en það sem greiningin byggir á, og tvö "
    "eintök í sömu möppu gera óljóst hvoru tölurnar tilheyra."
)

BEIDNI = Beidni(
    thjonusta="mbl",
    veitandi="mbl.is",
    slod="https://www.mbl.is/",
    heiti="forsida",
    hausar={"Accept": "text/html"},
)


def saekja_forsidu(*, thvinga: bool = False, **rok) -> Svar:
    """Sækir forsíðuna og vistar hana óbreytta í ``data/raw/mbl/``.

    Fellur með ``FrosidVilla`` sé frosna eintakið til, nema ``thvinga=True``.
    Aukabreytur fara óbreyttar í ``sofnun.http.saekja``.
    """
    krefjast_thvingunar(
        BEIDNI.thjonusta,
        FROSID_MYNSTUR,
        thvinga=thvinga,
        af_hverju=AF_HVERJU,
        rot=rok.get("rot", HRAGOGN),
    )
    return saekja(BEIDNI, thvinga=thvinga, **rok)
