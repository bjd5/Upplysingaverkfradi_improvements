"""Stöðvalisti Veðurstofunnar og hnitauppfletting (gagnasafn 3).

Flutt úr ``src/vedurstofa_stodvar.py`` upprunaverkefnisins. Þar sótti skriftan
listann upp á nýtt í hverri byggingu og vistaði svarið aldrei — þess vegna
birti gamla síðan aðrar tölur í dag en í gær. Hér fer sóknin gegnum
``sofnun.http``, sem vistar svarið óbreytt áður en nokkuð er unnið úr því.

**Listinn er sóttur ósíaður.** Þjónustan hunsar færibreytur sem hún þekkir ekki
og svarar samt HTTP 200, svo sía sem tekur ekki gildi sést hvergi í svarinu.
Síurnar ``active``, ``polygon`` og ``station_id`` velja hvort eð er úr þessu
sama mengi og eru því reiknaðar staðbundið í vinnslulaginu — ein sókn í stað
fjögurra, og niðurstaðan er rekjanleg til eins eintaks.

Hnitauppflettingin í Nominatim er sérstakt gagnasafn frá annarri þjónustu með
eigin skilmála, svo hún fær sína eigin möppu undir ``data/raw/``.
"""

from __future__ import annotations

from .beidni import Beidni
from .hragogn import Svar
from .http import saekja

# Heimilisfang VR-II. Uppflettingin er gerð einu sinni; hnitin eru síðan föst
# viðmiðun sem fjarlægðir í vinnslulaginu eru reiknaðar frá.
VR_II = "Hjarðarhagi 6, 107 Reykjavík"

BEIDNI = Beidni(
    thjonusta="vedurstodvar",
    veitandi="Veðurstofa Íslands",
    slod="https://api.vedur.is/weather/stations",
    heiti="stations",
    skjolun="https://api.vedur.is/weather/openapi.json",
    hausar={"Accept": "application/json"},
    leyfi="CC BY 4.0",
    leyfisslod="https://creativecommons.org/licenses/by/4.0/",
)

NOMINATIM_BEIDNI = Beidni(
    thjonusta="nominatim",
    veitandi="OpenStreetMap Nominatim",
    slod="https://nominatim.openstreetmap.org/search",
    heiti="vr-ii",
    skjolun="https://nominatim.org/release-docs/latest/api/Search/",
    breytur={"q": VR_II, "format": "json"},
    hausar={"Accept": "application/json"},
    leyfi="ODbL 1.0",
    leyfisslod="https://opendatacommons.org/licenses/odbl/1-0/",
)


def saekja_stodvar(**rok) -> Svar:
    """Sækir ósíaða stöðvalistann í ``data/raw/vedurstodvar/``.

    Aukabreytur fara óbreyttar í ``sofnun.http.saekja``.
    """
    return saekja(BEIDNI, **rok)


def saekja_hnit_vr_ii(**rok) -> Svar:
    """Flettir upp hnitum VR-II hjá Nominatim og vistar svarið óbreytt.

    Nominatim er samfélagsþjónusta með stranga hraðatakmörkun og krefst
    auðkennandi ``User-Agent`` — hvort tveggja sér ``sofnun.http`` um. Þetta er
    ein uppfletting, ekki lykkja yfir heimilisföng.
    """
    return saekja(NOMINATIM_BEIDNI, **rok)
