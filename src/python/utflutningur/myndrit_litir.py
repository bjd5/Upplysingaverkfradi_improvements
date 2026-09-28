"""Litahlutverk myndritanna og mæling á andstæðu þeirra (reglur 3.1 og 3.3).

Myndritin taka liti **eingöngu** úr ``tokens.css``. Þessi eining segir hvaða
token hvert hlutverk notar og **mælir** hvort það nær kröfunni gegn bakgrunni
myndritsins — krafan er ekki áætluð af því að liturinn „lítur dökkur út".
Hún flytur ekki inn matplotlib, svo andstæðuprófin keyra alltaf á
staðalsafninu einu, líka þar sem teikniprófin sleppa sér.

Formúlan er sú í WCAG 2.1:

    hlutfallsleg ljósstyrkja  L = 0,2126·R + 0,7152·G + 0,0722·B
    þar sem hver þáttur C er  C/12,92            ef C <= 0,03928
                              ((C+0,055)/1,055)^2,4  annars
    andstæða                  (L_ljósari + 0,05) / (L_dekkri + 0,05)

Kröfurnar eru tvær og ólíkar af ásettu ráði:

* **4,5:1** (WCAG 1.4.3, regla 3.3) fyrir allt sem ber merkingu: texta,
  súluflöt og núll-merkið. WCAG 1.4.11 krefst aðeins 3:1 fyrir grafík, en
  issue #17 krefst 4,5:1 fyrir myndritið, svo strangari krafan er valin.
* **3,0:1** (WCAG 1.4.11) fyrir ásana sjálfa — lína sem afmarkar flöt.

``--myndrit-grind`` er ekki mælt: hjálparlínurnar eru skraut og bera enga
merkingu. Súluflötur og núll-merki eru ekki mæld hvort gegn öðru; munurinn á
þeim er borinn af lögun og texta í skýringu, ekki af lit — sjá
``myndrit_skjalftar.py``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from dataclasses import dataclass

from .tokens import Thema, thatta_lit



KRAFA_TEXTI = 4.5
KRAFA_GRAFIK = 3.0

_LJOSSTYRKJA_VOG = (0.2126, 0.7152, 0.0722)
_LINULEG_MORK = 0.03928
_LINULEGUR_DEILIR = 12.92
_SVID = 255.0


@dataclass(frozen=True)
class Maeling:
    """Ein mæld litasamsetning, tilbúin til birtingar í skjölun og PR-i."""

    heiti: str
    framgrunnur: str
    bakgrunnur: str
    hlutfall: float
    krafa: float

    @property
    def stenst(self) -> bool:
        return self.hlutfall >= self.krafa

    def lina(self) -> str:
        """Ein lína sem manneskja les: ``heiti  #fff á #000  21,0:1  krafa 4,5:1  OK``."""
        merki = "stenst" if self.stenst else "FELLUR"
        return (
            f"{self.heiti}: {self.framgrunnur} á {self.bakgrunnur} — "
            f"{self.hlutfall:.2f}:1 (krafa {self.krafa:.1f}:1) {merki}"
        )


def ljosstyrkja(litur: str) -> float:
    """Hlutfallsleg ljósstyrkja litar á forminu ``#rrggbb`` (0,0–1,0)."""
    thaettir = []
    for gildi in thatta_lit(litur):
        c = gildi / _SVID
        thaettir.append(
            c / _LINULEGUR_DEILIR
            if c <= _LINULEG_MORK
            else ((c + 0.055) / 1.055) ** 2.4
        )
    return sum(vog * thattur for vog, thattur in zip(_LJOSSTYRKJA_VOG, thaettir))


def andstaeda(fyrri: str, sidari: str) -> float:
    """Andstæðuhlutfall tveggja lita (1,0–21,0). Röðin skiptir ekki máli."""
    a, b = ljosstyrkja(fyrri), ljosstyrkja(sidari)
    ljosari, dekkri = max(a, b), min(a, b)
    return (ljosari + 0.05) / (dekkri + 0.05)


def maela(
    heiti: str,
    framgrunnur: str,
    bakgrunnur: str,
    krafa: float = KRAFA_TEXTI,
) -> Maeling:
    """Mælir eina samsetningu og skilar niðurstöðunni óbreyttri — dæmir ekki."""
    return Maeling(
        heiti=heiti,
        framgrunnur=framgrunnur,
        bakgrunnur=bakgrunnur,
        hlutfall=andstaeda(framgrunnur, bakgrunnur),
        krafa=krafa,
    )


def maela_thema(thema: Thema, por: tuple[tuple[str, str, str, float], ...]) -> list[Maeling]:
    """Mælir lista af ``(heiti, framgrunns-token, bakgrunns-token, krafa)`` í einu þema."""
    return [
        maela(f"{thema.heiti}: {heiti}", thema.litur(fram), thema.litur(bak), krafa)
        for heiti, fram, bak, krafa in por
    ]


# --- Litahlutverk myndritanna ---------------------------------------------------
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
