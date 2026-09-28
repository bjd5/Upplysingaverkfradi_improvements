"""Eitt eintak af fréttayfirliti mbl.is fyrir regex-æfinguna (gagnasafn 4).

Flutt úr ``src/mbl_snapshot.py`` upprunaverkefnisins. Skriftan þar neitaði að
yfirskrifa fyrra eintak; sú varúð er hér áfram, því fréttasíða er **lifandi
gagn**. Eintakið frá 16.9.2026 er það sem allar tölur æfingarinnar eiga við, og
nýtt eintak er ekki uppfærsla á því heldur annað gagn. Þess vegna skilar
sjálfgefin keyrsla frosna eintakinu og sækir ekkert, líka eftir að nýrra eintak
hefur verið sótt með ``thvinga=True``: viðmiðið færist ekki af sjálfu sér.

**Slóðin er ``/frettir/``, ekki forsíðan sjálf.** Það er slóðin sem
``data/raw/mbl/mbl-20260916T120851Z.json`` skráir í ``source_url`` og þar með
sú síða sem tölurnar eru reiknaðar af. Endurbyggingaráætlunin kallar safnið
„mbl.is forsíða", en lýsigögn frosna eintaksins ráða: sókn á aðra slóð gæfi
annað HTML og aðrar tölur.

Þetta er vefsíða en ekki vefþjónusta: ekkert leyfi er gefið og HTML-ið er hrátt
svar, ekki gagnasnið sem lofað hefur verið að haldist óbreytt. Greiningin sem
les það þarf að þola að byggingin sé önnur en hún var.
"""

from __future__ import annotations

from .beidni import Beidni
from .frosid import frosid_svar
from .hragogn import HRAGOGN, Svar
from .http import saekja

# Frosna eintakið heitir eftir gamla sniðinu; ný sókn fær heitið `frettir-...`
# og skyggir þannig ekki á það sem greiningin byggir á.
FROSID_MYNSTUR = "mbl-*.html"

BEIDNI = Beidni(
    thjonusta="mbl",
    veitandi="mbl.is",
    slod="https://www.mbl.is/frettir/",
    heiti="frettir",
    hausar={"Accept": "text/html"},
)


def saekja_forsidu(*, thvinga: bool = False, **rok) -> Svar:
    """Skilar frosna eintakinu, eða sækir nýtt sé ``thvinga=True``.

    Sjálfgefið er ekkert kall sent (regla 4). Nýtt eintak er vistað við hlið
    frosna eintaksins og yfirskrifar það ekki. Aukabreytur fara óbreyttar í
    ``sofnun.http.saekja``.
    """
    if not thvinga:
        frosid = frosid_svar(BEIDNI.thjonusta, FROSID_MYNSTUR, rok.get("rot", HRAGOGN))
        if frosid is not None:
            return frosid
    return saekja(BEIDNI, thvinga=thvinga, **rok)
