"""Dagatalning og mánaðartalning skjálftaúrtaksins (issue #14, pakki P2.3).

Fjórða skrefið í upprunaskriftunni ``src/earthquakes.py`` — *telja*. Hin þrjú
fyrri (sækja, sannreyna, hreinsa með regex) eru þegar flutt: sóknin í
``sofnun/skjalftar.py``, sannreyningin og regex-lyklarnir í
``vinnsla/jardskjalftar.py``. Þessi eining **endurtekur ekki** þá vinnu heldur
kallar í hana.

Tvær talningar, hvor á sínu þrepi:

* **Dagatalning** — ein lína á hvern UTC-dag tímabilsins. Dagur án atburðar fær
  gildið núll, ekki enga línu: núll er niðurstaða en ekki eyða. Röðin kemur úr
  ``jardskjalftar_afmorkun.dagar`` og talningin úr
  ``jardskjalftar.talning_eftir_degi``; hér er hún aðeins færð í raðaðan lista
  svo úttakið hafi fasta röð.
* **Mánaðartalning** — samtölur hvers UTC-mánaðar, í tímaröð. Þetta eru tölurnar
  sem gamla síðan sýndi undir hverri mánaðartöflu (330 í nóvember, 4 í desember).

Einingin gerir ekkert I/O og engar skrár: hún tekur sannreynda atburði og skilar
tölum. Lestur er í ``jardskjalftar.py``, skrif í ``jardskjalftar_uttak.py``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

try:  # keyrt sem eining innan pakkans (venjulega leiðin)
    from .jardskjalftar import Skjalfti, talning_eftir_degi
    from .jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, dagar, lesa_afmorkun
except ImportError:  # keyrt beint úr möppunni
    from jardskjalftar import Skjalfti, talning_eftir_degi
    from jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, dagar, lesa_afmorkun

# Daglykillinn er á forminu YYYY-MM-DD og mánaðarlykillinn er fyrstu sjö
# stafirnir hans. Fastinn er nefndur svo talan 7 standi hvergi nakin í kóðanum.
MANADARLENGD = len("YYYY-MM")


@dataclass(frozen=True)
class DagsTalning:
    """Fjöldi atburða á einum UTC-degi tímabilsins.

    Heiti reitanna eru þau sömu og dálkarnir í ``earthquake_days`` og í
    ``daily.csv``, svo sama talan heiti sama nafni alla leið.
    """

    utc_day: str
    event_count: int


@dataclass(frozen=True)
class ManadarTalning:
    """Samtala eins UTC-mánaðar og hve margir dagar hans eru í úrtakinu."""

    month: str  # YYYY-MM
    day_count: int
    event_count: int


def dagleg_talning(
    skjalftar: list[Skjalfti], afmorkun: Afmorkun | None = None
) -> list[DagsTalning]:
    """Telur atburði á hvern UTC-dag tímabilsins, í tímaröð.

    Sérhver dagur frá upphafi beiðninnar (meðtöldu) til enda hennar
    (undanskildum) fær línu, líka dagarnir þar sem enginn atburður stóðst
    síurnar. Atburður utan tímabilsins stöðvar keyrsluna með ``SkjalftaVilla``
    í ``talning_eftir_degi``; hann má ekki hverfa þegjandi úr talningunni.
    """
    afmorkun = afmorkun if afmorkun is not None else lesa_afmorkun()
    dagalisti = dagar(afmorkun)
    talning = talning_eftir_degi(skjalftar, dagalisti)
    return [DagsTalning(utc_day=dagur, event_count=talning[dagur]) for dagur in dagalisti]


def manadartalning(dagatalning: list[DagsTalning]) -> list[ManadarTalning]:
    """Dregur dagatalninguna saman í samtölur hvers UTC-mánaðar, í tímaröð.

    Mánuður sem á sér daga í úrtakinu fær línu þótt samtalan sé núll — sama
    regla og um dagana sjálfa.
    """
    atburdir: Counter[str] = Counter()
    dagafjoldi: Counter[str] = Counter()

    for dagur in dagatalning:
        manudur = _manadarlykill(dagur.utc_day)
        atburdir[manudur] += dagur.event_count
        dagafjoldi[manudur] += 1

    return [
        ManadarTalning(
            month=manudur,
            day_count=dagafjoldi[manudur],
            event_count=atburdir[manudur],
        )
        for manudur in sorted(dagafjoldi)
    ]


def dagar_an_atburda(dagatalning: list[DagsTalning]) -> int:
    """Fjöldi UTC-daga þar sem enginn atburður stóðst síur beiðninnar.

    Talan segir **ekki** að enginn jarðskjálfti hafi orðið þann dag, heldur að
    enginn þeirra hafi verið innan úrtaksins. Sá greinarmunur er birtur á
    síðunni og má ekki tapast í talningunni (regla 8).
    """
    return sum(1 for dagur in dagatalning if dagur.event_count == 0)


def _manadarlykill(utc_day: str) -> str:
    """Skilar YYYY-MM úr daglykli; annað snið er villa, ekki afrúnnað gildi."""
    manudur = utc_day[:MANADARLENGD]
    if len(utc_day) < MANADARLENGD or utc_day[4] != "-":
        raise SkjalftaVilla(
            f"Daglykillinn {utc_day!r} er ekki á forminu YYYY-MM-DD og gefur "
            "því engan mánaðarlykil."
        )
    return manudur
