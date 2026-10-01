"""Beiðnir gagnasafnanna fjögurra sem eru ein eða tvær GET-beiðnir hvert.

Hvert safn er ein ``Beidni`` og eitt ``saekja_*``-fall sem sendir hana gegnum
``sofnun.http``. Þar er svarið vistað óbreytt í ``data/raw/`` áður en nokkuð er
unnið úr því, og ekkert kall er sent sé eintakið þegar til (regla 4). Afkóðun
og útreikningar tilheyra vinnslulaginu.

Hagstofan er í eigin einingu (``sofnun.hagstofan``), því þar þarf fyrst að
sækja lýsigögn töflunnar til að byggja fyrirspurnina.

Aukabreytur ``saekja_*``-fallanna fara óbreyttar í ``sofnun.http.saekja``
(``thvinga``, ``rot``, ``opnari``, ``sofa`` …).
"""

from __future__ import annotations

from typing import Any

from . import stillingar
from .beidni import Beidni
from .frosid import frosid_svar
from .hragogn import HRAGOGN, Svar
from .http import saekja

CC_BY = "CC BY 4.0"
CC_BY_SLOD = "https://creativecommons.org/licenses/by/4.0/"


# --- 1. Jarðskjálftar á Reykjanesi --------------------------------------------
#
# Flutt úr ``src/earthquakes.py`` upprunaverkefnisins. Færibreyturnar eru þær
# sömu og frosna eintakið í ``data/raw/vedur-quakes/`` lýsir, staf fyrir staf.
# Þess vegna þekkir ``sofnun.http`` beiðnina sem þegar gerða og sækir ekki sama
# úrtakið aftur. Breytist ein færibreyta er þetta annað úrtak og önnur tala á
# síðunni — þá þarf nýtt eintak og nýja umfjöllun í ``docs/adferdafraedi.md``,
# ekki hljóða breytingu hér.

# Athugunartímabilið er hálfopið: [upphaf, endir). Atburður nákvæmlega á
# endamörkunum tilheyrir næsta tímabili.
UPPHAF = "2023-11-01T00:00:00+00:00"
ENDIR = "2024-01-01T00:00:00+00:00"

# Reykjanes. Hnitaröðin í WKT er `lengd breidd` — öfug við `lat,lon` sem flestar
# þjónustur skila — og ferillinn þarf að lokast, svo hornin eru fimm en ekki
# fjögur.
MARGHYRNINGUR = "POLYGON((-23 64.1,-23 63.7,-21.5 63.7,-21.5 64.1,-23 64.1))"

# Opinbert útgáfunúmer þjónustunnar, ekki leyndarmál. Fast gildi svo svarsniðið
# breytist ekki undir okkur þótt Veðurstofan gefi út nýja útgáfu.
UTGAFA_THJONUSTU = "2026-08-06"

# Úrtakið er lítið; margfalt stærra svar væri merki um að síurnar hafi ekki
# skilað sér og er þá ekki vistað.
HAMARK_SVARS = 2_000_000

SKJALFTA_BEIDNI = Beidni(
    thjonusta="vedur-quakes",
    veitandi="Veðurstofa Íslands",
    slod="https://api.vedur.is/quakes/events",
    heiti="events",
    skjolun="https://api.vedur.is/quakes/openapi.json",
    breytur={
        "start_time": UPPHAF,
        "end_time": ENDIR,
        "depth_min": 0,
        "depth_max": 50,
        "size_min": 3,
        "size_max": 7,
        "polygon": MARGHYRNINGUR,
        "type": "earthquake",
        "evaluation_mode": "manual",
        "format": "json",
        "system": "sil",
    },
    hausar={"x-vi-api-version": UTGAFA_THJONUSTU, "Accept": "application/json"},
    leyfi=CC_BY,
    leyfisslod=CC_BY_SLOD,
)


def saekja_skjalfta(**rok: Any) -> Svar:
    """Sækir skjálftaúrtakið og vistar það óbreytt í ``data/raw/vedur-quakes/``."""
    return saekja(SKJALFTA_BEIDNI, hamark_baeta=HAMARK_SVARS, **rok)


# --- 3. Stöðvalisti Veðurstofunnar --------------------------------------------
#
# Upprunaverkefnið sótti listann upp á nýtt í hverri byggingu og vistaði svarið
# aldrei — þess vegna birti gamla síðan aðrar tölur í dag en í gær.
#
# **Listinn er sóttur ósíaður.** Þjónustan hunsar færibreytur sem hún þekkir
# ekki og svarar samt HTTP 200, svo sía sem tekur ekki gildi sést hvergi í
# svarinu. Síurnar ``active``, ``polygon`` og ``station_id`` eru því reiknaðar
# staðbundið í vinnslulaginu — ein sókn í stað fimm, rekjanleg til eins eintaks.
#
# **Hnit VR-II eru ekki sótt hér.** Fjarlægðir eru reiknaðar frá föstum hnitum í
# ``vinnsla/vedurstodvar_samanburdur.py``. Ný uppfletting gæti skilað örlítið
# öðrum hnitum og látið samanburðinn við gömlu síðuna mæla forsendumun í stað
# gagnamunar.

STODVA_BEIDNI = Beidni(
    thjonusta="vedurstodvar",
    veitandi="Veðurstofa Íslands",
    slod="https://api.vedur.is/weather/stations",
    heiti="stations",
    skjolun="https://api.vedur.is/weather/openapi.json",
    hausar={"Accept": "application/json"},
    leyfi=CC_BY,
    leyfisslod=CC_BY_SLOD,
)


def saekja_stodvar(**rok: Any) -> Svar:
    """Sækir ósíaða stöðvalistann í ``data/raw/vedurstodvar/``."""
    return saekja(STODVA_BEIDNI, **rok)


# --- 4. Fréttayfirlit mbl.is ---------------------------------------------------
#
# Fréttasíða er **lifandi gagn**. Eintakið frá 16.9.2026 er það sem allar tölur
# regex-æfingarinnar eiga við, og nýtt eintak er ekki uppfærsla á því heldur
# annað gagn. Sjálfgefin keyrsla skilar því frosna eintakinu, líka eftir að
# nýrra eintak hefur verið sótt með ``thvinga=True``.
#
# **Slóðin er ``/frettir/``, ekki forsíðan sjálf.** Það er slóðin sem frosna
# eintakið skráir í ``source_url``; sókn á aðra slóð gæfi annað HTML og aðrar
# tölur. Þetta er vefsíða en ekki vefþjónusta: ekkert leyfi er gefið og
# greiningin þarf að þola að byggingin sé önnur en hún var.

# Frosna eintakið heitir eftir gamla sniðinu; ný sókn fær heitið `frettir-...`
# og skyggir þannig ekki á það sem greiningin byggir á.
MBL_FROSID_MYNSTUR = "mbl-*.html"

MBL_BEIDNI = Beidni(
    thjonusta="mbl",
    veitandi="mbl.is",
    slod="https://www.mbl.is/frettir/",
    heiti="frettir",
    hausar={"Accept": "text/html"},
)


def saekja_forsidu(*, thvinga: bool = False, **rok: Any) -> Svar:
    """Skilar frosna eintakinu, eða sækir nýtt sé ``thvinga=True``.

    Nýtt eintak er vistað við hlið frosna eintaksins og yfirskrifar það ekki.
    """
    if not thvinga:
        frosid = frosid_svar(MBL_BEIDNI.thjonusta, MBL_FROSID_MYNSTUR, rok.get("rot", HRAGOGN))
        if frosid is not None:
            return frosid
    return saekja(MBL_BEIDNI, thvinga=thvinga, **rok)


# --- 5. TMDB — Friends og hlutverk Phoebe --------------------------------------
#
# Tvö köll: grunnupplýsingar þáttarins og ``aggregate_credits``, sem safnar öllum
# hlutverkum sömu manneskju í eina færslu — þess vegna er þáttafjöldi Phoebe
# réttur þar en tvítalinn í venjulegu ``credits``.
#
# **Eina safnið sem krefst lykils.** Hann kemur úr ``TMDB_TOKEN`` og er gefinn
# ``sofnun.http`` sem leynihaus: hann fer í beiðnina og hvergi annað — ekki í
# provenance, logg né villuboð (regla 4). Safnið er skráð ófryst í
# ``data/raw/frysting.json`` þar til lykill er settur inn.

LYKILS_BREYTA = "TMDB_TOKEN"
LYKILS_SKYRING = (
    "hún geymir „API Read Access Token\" af https://www.themoviedb.org/settings/api"
)

TMDB_GRUNNSLOD = "https://api.themoviedb.org/3"
TMDB_SKJOLUN = "https://developer.themoviedb.org/reference/tv-series-details"
THATTUR = 1668          # Friends á TMDB: https://www.themoviedb.org/tv/1668-friends

# Tungumálið er hluti af úrtakinu: hlutverkaheiti eru þýdd og önnur stilling
# gæfi önnur nöfn í sömu reitum.
TUNGUMAL = "en-US"


def _tmdb_beidni(vidskeyti: str, heiti: str) -> Beidni:
    """Byggir beiðni á TMDB-endapunkt. Lykillinn kemur hvergi hér nærri."""
    return Beidni(
        thjonusta="tmdb",
        veitandi="The Movie Database (TMDB)",
        slod=f"{TMDB_GRUNNSLOD}/tv/{THATTUR}{vidskeyti}",
        heiti=heiti,
        skjolun=TMDB_SKJOLUN,
        breytur={"language": TUNGUMAL},
        hausar={"Accept": "application/json"},
        leyfi="TMDB Terms of Use",
        leyfisslod="https://www.themoviedb.org/terms-of-use",
    )


THATTAR_BEIDNI = _tmdb_beidni("", "thattur")
LEIKARA_BEIDNI = _tmdb_beidni("/aggregate_credits", "leikarar")


def leynihausar(lykill: str | None = None) -> dict[str, str]:
    """Skilar auðkenningarhausnum. Lykillinn kemur úr umhverfinu nema hann sé gefinn."""
    gildi = lykill if lykill is not None else stillingar.krefjast(
        LYKILS_BREYTA, LYKILS_SKYRING
    )
    return {"Authorization": f"Bearer {gildi}"}


def saekja_tmdb(*, lykill: str | None = None, **rok: Any) -> tuple[Svar, Svar]:
    """Sækir þátt og leikaraskrá og skilar báðum svörum."""
    hausar = leynihausar(lykill)
    thattur = saekja(THATTAR_BEIDNI, leynihausar=hausar, **rok)
    leikarar = saekja(LEIKARA_BEIDNI, leynihausar=hausar, **rok)
    return thattur, leikarar
