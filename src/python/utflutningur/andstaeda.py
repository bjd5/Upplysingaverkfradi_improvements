"""Mæling á litaandstæðu samkvæmt WCAG 2.1 (regla 3.3).

Regla 3.3 setur lágmarkið 4,5:1 fyrir texta. Krafan er **mælanleg**, svo hún
er mæld hér og niðurstaðan prentuð — hún er ekki áætluð af því að liturinn
„lítur dökkur út". Myndritin teikna bæði texta (ásmerkingar, skýringar) og
fleti (súlur), og prófin nota þessa einingu til að stöðva myndrit sem fellur
undir lágmarkið.

Formúlan er sú í WCAG 2.1:

    hlutfallsleg ljósstyrkja  L = 0,2126·R + 0,7152·G + 0,0722·B
    þar sem hver þáttur C er  C/12,92            ef C <= 0,03928
                              ((C+0,055)/1,055)^2,4  annars
    andstæða                  (L_ljósari + 0,05) / (L_dekkri + 0,05)

Þröskuldarnir eru tveir og ólíkir af ásettu ráði:

* **texti** 4,5:1 — WCAG 1.4.3 (AA), og lágmarkið sem regla 3.3 nefnir.
* **grafík** 3,0:1 — WCAG 1.4.11 fyrir myndhluta sem ekki er texti, t.d.
  súluflöt gegn bakgrunni. Myndrit verkefnisins eru samt mæld gegn 4,5:1
  líka og niðurstaðan skráð, svo lesandinn sjái hvort súlan stenst
  textakröfuna þótt hún þurfi það ekki.

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
