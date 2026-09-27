"""Stöðvalisti Veðurstofunnar (gagnasafn 3).

Flutt úr ``src/vedurstofa_stodvar.py`` upprunaverkefnisins. Þar sótti skriftan
listann upp á nýtt í hverri byggingu og vistaði svarið aldrei — þess vegna
birti gamla síðan aðrar tölur í dag en í gær. Hér fer sóknin gegnum
``sofnun.http``, sem vistar svarið óbreytt áður en nokkuð er unnið úr því, svo
tölurnar á síðunni eiga sér fast eintak að baki.

**Listinn er sóttur ósíaður.** Þjónustan hunsar færibreytur sem hún þekkir ekki
og svarar samt HTTP 200, svo sía sem tekur ekki gildi sést hvergi í svarinu.
Síurnar ``active``, ``polygon`` og ``station_id`` velja hvort eð er úr þessu
sama mengi og eru því reiknaðar staðbundið í vinnslulaginu — ein sókn í stað
fimm, og niðurstaðan er rekjanleg til eins eintaks.

**Hnit VR-II eru ekki sótt hér.** Fjarlægðir eru reiknaðar frá föstum hnitum
sem ``src/python/vinnsla/vedurstodvar_samanburdur.py`` geymir
(``VR_II_BREIDD``, ``VR_II_LENGD``, ``VR_II_HEIMILD``) — flett upp einu sinni í
Nominatim í upprunaverkefninu 3.9.2026 og endurnotuð óbreytt síðan. Ný
uppfletting gæti skilað örlítið öðrum hnitum, fært allar fjarlægðir og látið
samanburðinn við gömlu síðuna mæla forsendumun í stað gagnamunar.
Viðmiðunarpunktur á að vera fastur, ekki sóttur í hverri keyrslu.
"""

from __future__ import annotations

from .beidni import Beidni
from .hragogn import Svar
from .http import saekja

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


def saekja_stodvar(**rok) -> Svar:
    """Sækir ósíaða stöðvalistann í ``data/raw/vedurstodvar/``.

    Sé listinn þegar til er ekkert kall sent. Aukabreytur fara óbreyttar í
    ``sofnun.http.saekja`` (``thvinga``, ``rot``, ``opnari``, ``sofa`` …).
    """
    return saekja(BEIDNI, **rok)
