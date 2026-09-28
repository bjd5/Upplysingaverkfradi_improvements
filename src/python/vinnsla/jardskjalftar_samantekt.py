"""Lýsandi tölfræði um skjálftaúrtakið (issue #14, pakki P2.3).

Þetta eru tölurnar sem gamla síðan birti undir „Nánar um tölurnar“: miðgildi,
lágmark og hámark daglegs fjölda, dagar án atburðar, dýptarbil og miðgildi
dýptar, og stærðartafla þar sem **hver stærðarkvarði er talinn sér**.

Kvarðarnir eru ekki lagðir saman af ásettu ráði: ``Mlw`` og ``Mw`` eru ekki sama
talan og mega ekki lenda í sama miðgildi. Vanti kvarðann hafnar sannreyningin í
``jardskjalftar.py`` færslunni; hér er því alltaf kvarði til að telja eftir.

Einingin er hrein talnavinnsla — hún les engar skrár og skrifar engar. Tölurnar
eru **óafrúnnaðar**; snyrting fyrir birtingu (tveir aukastafir, íslenskt
tugabrotskomma) er hlutverk birtingarlagsins, ekki vinnslunnar (regla 2 og
flæðið í kafla 0).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median

try:  # keyrt sem eining innan pakkans (venjulega leiðin)
    from .jardskjalftar import Skjalfti
    from .jardskjalftar_afmorkun import SkjalftaVilla
    from .jardskjalftar_talning import (
        DagsTalning,
        ManadarTalning,
        dagar_an_atburda,
        manadartalning,
    )
except ImportError:  # keyrt beint úr möppunni
    from jardskjalftar import Skjalfti
    from jardskjalftar_afmorkun import SkjalftaVilla
    from jardskjalftar_talning import (
        DagsTalning,
        ManadarTalning,
        dagar_an_atburda,
        manadartalning,
    )


@dataclass(frozen=True)
class Dreifing:
    """Lýsandi tölfræði um eina talnaröð — óafrúnnuð."""

    fjoldi: int
    lagmark: float
    hamark: float
    midgildi: float


@dataclass(frozen=True)
class Kvardadreifing:
    """Dreifing skjálftastærða innan eins skráðs stærðarkvarða."""

    magnitude_type: str
    dreifing: Dreifing


@dataclass(frozen=True)
class Samantekt:
    """Allar samantektartölur úrtaksins á einum stað."""

    atburdir: int
    dagar: int
    fyrsti_dagur: str
    sidasti_dagur: str
    dagleg_dreifing: Dreifing
    dagar_an_atburda: int
    dypt_km: Dreifing
    staerdir: tuple[Kvardadreifing, ...]
    manudir: tuple[ManadarTalning, ...]


def dreifing(gildi: Sequence[float]) -> Dreifing:
    """Reiknar fjölda, lágmark, hámark og miðgildi talnaraðar.

    Tóm röð er villa, ekki núll: lágmark og miðgildi tómrar raðar eru ekki til,
    og tala sem er ekki til má ekki birtast sem núll á síðunni (regla 8).
    """
    if not gildi:
        raise SkjalftaVilla(
            "Tóm talnaröð hefur ekkert lágmark, hámark né miðgildi. "
            "Samantekt yfir tómt úrtak er ekki gerð."
        )
    return Dreifing(
        fjoldi=len(gildi),
        lagmark=min(gildi),
        hamark=max(gildi),
        midgildi=median(gildi),
    )


def staerdir_eftir_kvarda(skjalftar: list[Skjalfti]) -> list[Kvardadreifing]:
    """Dreifing skjálftastærða, einn kvarði í einu, í stafrófsröð kvarðanna.

    Kvarðarnir eru **aldrei** lagðir saman: stærð í ``Mlw`` og stærð í ``Mw``
    eru ekki sama mælingin og eiga ekki sama miðgildi.
    """
    eftir_kvarda: dict[str, list[float]] = {}
    for skjalfti in skjalftar:
        eftir_kvarda.setdefault(skjalfti.magnitude_type, []).append(skjalfti.magnitude)

    return [
        Kvardadreifing(magnitude_type=kvardi, dreifing=dreifing(eftir_kvarda[kvardi]))
        for kvardi in sorted(eftir_kvarda)
    ]


def draga_saman(
    skjalftar: list[Skjalfti], dagatalning: list[DagsTalning]
) -> Samantekt:
    """Dregur úrtakið saman í þær tölur sem skýrslan birtir.

    Krefst þess að dagatalningin sé sú sem ``jardskjalftar_talning`` gerði fyrir
    **sömu** atburði: stemmi samtalan ekki við fjölda atburða er önnur röðin
    komin úr öðru úrtaki og keyrslan stöðvast.
    """
    if not dagatalning:
        raise SkjalftaVilla(
            "Dagatalningin er tóm. Tímabil beiðninnar telur minnst einn UTC-dag."
        )

    talin = sum(dagur.event_count for dagur in dagatalning)
    if talin != len(skjalftar):
        raise SkjalftaVilla(
            f"Dagatalningin telur {talin} atburði en úrtakið hefur "
            f"{len(skjalftar)}. Tölurnar koma ekki úr sama úrtaki."
        )

    return Samantekt(
        atburdir=len(skjalftar),
        dagar=len(dagatalning),
        fyrsti_dagur=dagatalning[0].utc_day,
        sidasti_dagur=dagatalning[-1].utc_day,
        dagleg_dreifing=dreifing([dagur.event_count for dagur in dagatalning]),
        dagar_an_atburda=dagar_an_atburda(dagatalning),
        dypt_km=dreifing([skjalfti.depth_km for skjalfti in skjalftar]),
        staerdir=tuple(staerdir_eftir_kvarda(skjalftar)),
        manudir=tuple(manadartalning(dagatalning)),
    )
