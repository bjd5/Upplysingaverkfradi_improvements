"""Litahlutverk myndritanna og andstæðukröfurnar sem þau verða að standast.

Myndritin taka liti **eingöngu** úr ``tokens.css`` (regla 3.1). Þessi eining
segir hvaða token hvert hlutverk notar og hvaða andstæðu það verður að ná gegn
bakgrunni myndritsins (regla 3.3). Hún flytur ekki inn matplotlib, svo
andstæðuprófin keyra alltaf á staðalsafninu einu — líka þar sem teikniprófin
sleppa sér.

Kröfurnar eru tvenns konar og ólíkar af ásettu ráði:

* **4,5:1** fyrir allt sem ber merkingu: texta, súluflöt og núll-merkið.
  Issue #17 krefst 4,5:1 fyrir myndritið og WCAG 1.4.11 krefst aðeins 3:1 fyrir
  grafík, svo strangari krafan er valin.
* **3,0:1** fyrir ásana sjálfa — lína sem afmarkar flöt (WCAG 1.4.11).

``--myndrit-grind`` er ekki mælt: hjálparlínurnar eru skraut og bera enga
merkingu, svo þær mega vera daufar. Það er skráð hér svo enginn haldi síðar að
mælingin hafi gleymst.

Súluflötur og núll-merki eru **ekki** mæld hvort gegn öðru. Munurinn á þeim er
borinn af lögun (súla / hringur) og texta í skýringu, ekki af lit — sjá
``myndrit_skjalftar.py`` og prófið sem fellur ef núll-dagar greinast á lit einum.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from .andstaeda import KRAFA_GRAFIK, KRAFA_TEXTI, Maeling, maela_thema
from .tokens import Thema

BAKGRUNNUR = "--myndrit-bak"
FLOTUR = "--myndrit-flotur"
NULL = "--myndrit-null"
TEXTI = "--myndrit-texti"
TEXTI_DAUFT = "--myndrit-texti-dauft"
AS = "--myndrit-as"
GRIND = "--myndrit-grind"

# (heiti í skýrslu, framgrunns-token, bakgrunns-token, krafa)
KROFUR: tuple[tuple[str, str, str, float], ...] = (
    ("súluflötur", FLOTUR, BAKGRUNNUR, KRAFA_TEXTI),
    ("núll-merki", NULL, BAKGRUNNUR, KRAFA_TEXTI),
    ("ásmerkingar", TEXTI, BAKGRUNNUR, KRAFA_TEXTI),
    ("heimildarlína", TEXTI_DAUFT, BAKGRUNNUR, KRAFA_TEXTI),
    ("ásar", AS, BAKGRUNNUR, KRAFA_GRAFIK),
)


def maela_myndritaliti(themu: dict[str, Thema]) -> list[Maeling]:
    """Mælir öll merkingarberandi litahlutverk í öllum þemum, í fastri röð."""
    return [
        maeling
        for heiti in sorted(themu)
        for maeling in maela_thema(themu[heiti], KROFUR)
    ]


def fallnar(themu: dict[str, Thema]) -> list[Maeling]:
    """Skilar þeim mælingum sem standast ekki kröfuna — tómur listi ef allt stenst."""
    return [maeling for maeling in maela_myndritaliti(themu) if not maeling.stenst]
