"""Köll í vefþjónustur. Vistar svör óbreytt í data/raw/ (regla 4).

Öll gagnasöfnun fer í gegnum ``saekja``:

    from sofnun import Beidni, saekja

    svar = saekja(Beidni(
        thjonusta="vedur-quakes",
        veitandi="Veðurstofa Íslands",
        slod="https://api.vedur.is/quakes/events",
        heiti="events",
        breytur={"format": "json"},
    ))

``sofnun.http`` sér um samskiptin (auðkenning, hraðatakmörkun, endurtilraunir),
``sofnun.hragogn`` um geymsluna, ``sofnun.beidni`` um provenance-sniðið og
``sofnun.stillingar`` um umhverfisbreytur og ``.env``.
"""

from .beidni import Beidni
from .hragogn import HragagnaVilla, Svar
from .http import HttpVilla, saekja
from .stillingar import StillingaVilla

__all__ = ["Beidni", "HragagnaVilla", "HttpVilla", "StillingaVilla", "Svar", "saekja"]
