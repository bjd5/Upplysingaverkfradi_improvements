"""Íslenskt talna- og dagsetningarsnið fyrir texta sem myndritin birta.

Myndrit á íslenskri síðu skrifar ``5,5`` en ekki ``5.5`` og ``1.234`` en ekki
``1,234``. Sniðið er **ekki** sótt úr ``locale``: kerfisstaðfærslan er ólík milli
véla, og sama SVG verður að koma út á hverri vél (sjá ákvörðunarprófið í
``test_myndrit_svg.py``). Þess vegna er sniðið skrifað hér beint.

Eingöngu staðalsafnið (regla 10), svo prófin á einingunni keyra alltaf.
"""

from __future__ import annotations

from datetime import date

MANADARHEITI = (
    "janúar", "febrúar", "mars", "apríl", "maí", "júní",
    "júlí", "ágúst", "september", "október", "nóvember", "desember",
)
# Styttingar eftir venju Árnastofnunar; stuttu heitin eru ekki stytt frekar.
MANADARSTYTTINGAR = (
    "jan.", "feb.", "mars", "apr.", "maí", "júní",
    "júlí", "ág.", "sept.", "okt.", "nóv.", "des.",
)

_ENSKT_THUSUND = ","
_ENSKT_TUGABROT = "."
_ISLENSKT_THUSUND = "."
_ISLENSKT_TUGABROT = ","
_BRADABIRGDA = "\0"


def islensk_tala(gildi: float, aukastafir: int = 0) -> str:
    """Skilar tölu með íslenskum þúsundaskilum og tugabrotskommu: ``1.234,5``."""
    if aukastafir < 0:
        raise ValueError(f"Fjöldi aukastafa má ekki vera neikvæður: {aukastafir}.")
    enskt = f"{gildi:,.{aukastafir}f}"
    return (
        enskt.replace(_ENSKT_THUSUND, _BRADABIRGDA)
        .replace(_ENSKT_TUGABROT, _ISLENSKT_TUGABROT)
        .replace(_BRADABIRGDA, _ISLENSKT_THUSUND)
    )


def islensk_prosenta(hluti: float, heild: float, aukastafir: int = 1) -> str:
    """Skilar hlutfalli sem prósentu með íslenskri tugabrotskommu: ``70,5%``."""
    if heild == 0:
        raise ValueError("Hlutfall af núlli er ekki skilgreint.")
    return f"{islensk_tala(100 * hluti / heild, aukastafir)}%"


def islensk_dagsetning(iso_dagur: str, stytt: bool = True, med_ari: bool = False) -> str:
    """Skilar ``YYYY-MM-DD`` sem ``1. nóv.`` (stytt) eða ``1. nóvember`` (fullt).

    Rangt snið fellur með ``ValueError`` frá ``date.fromisoformat`` — það er
    aldrei gískað á dagsetningu.
    """
    dagur = date.fromisoformat(iso_dagur)
    heiti = (MANADARSTYTTINGAR if stytt else MANADARHEITI)[dagur.month - 1]
    texti = f"{dagur.day}. {heiti}"
    return f"{texti} {dagur.year}" if med_ari else texti
