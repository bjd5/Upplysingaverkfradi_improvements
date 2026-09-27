"""Skjálftaúrtakið af Reykjanesi — ein GET-beiðni (gagnasafn 1).

Flutt úr ``src/earthquakes.py`` upprunaverkefnisins, þar sem sama skrifta sótti
gögnin, afkóðaði þau og skrifaði skýrslu. Hér er **aðeins sóknin**; afkóðun og
útreikningar tilheyra vinnslulaginu.

Færibreyturnar eru þær sömu og frosna eintakið í ``data/raw/vedur-quakes/``
lýsir, staf fyrir staf. Þess vegna þekkir ``sofnun.http`` beiðnina sem þegar
gerða og sækir ekki sama úrtakið aftur (regla 4). Breytist ein færibreyta er
þetta annað úrtak og önnur tala á síðunni — þá þarf nýtt eintak og nýja
umfjöllun í ``docs/adferdafraedi.md``, ekki hljóða breytingu hér.
"""

from __future__ import annotations

from .beidni import Beidni
from .hragogn import Svar
from .http import saekja

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

BEIDNI = Beidni(
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
    leyfi="CC BY 4.0",
    leyfisslod="https://creativecommons.org/licenses/by/4.0/",
)


def saekja_skjalfta(**rok) -> Svar:
    """Sækir skjálftaúrtakið og vistar það óbreytt í ``data/raw/vedur-quakes/``.

    Sé úrtakið þegar til er ekkert kall sent. Aukabreytur fara óbreyttar í
    ``sofnun.http.saekja`` (``thvinga``, ``rot``, ``opnari``, ``sofa`` …).
    """
    return saekja(BEIDNI, hamark_baeta=HAMARK_SVARS, **rok)
