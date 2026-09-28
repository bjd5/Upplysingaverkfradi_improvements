"""Flokkar skrár úr upprunarepo-inu eftir reglunum í config/uppruni.json.

Fyrsta regla sem passar ræður. Skrá sem engin regla nær yfir er „óflokkuð“
og kemur fram í skýrslunni — ný tegund skráar hverfur aldrei þegjandi.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
STILLING = ROT / "config" / "uppruni.json"

# Röðin hér er röðin í skýrslunni.
FLOKKAR = {
    "hragogn": "Hrágögn",
    "kodi": "Kóði",
    "prof": "Próf",
    "sida": "Síða",
    "skjolun": "Skjölun",
    "akvordun": "Þarf ákvörðun",
    "bannad": "Bannað",
    "utan": "Utan umfangs",
}
FLYTJA = ("hragogn", "kodi", "prof", "sida", "skjolun")
OFLOKKAD = "oflokkad"


class StillingarVilla(ValueError):
    """config/uppruni.json er ekki á réttu sniði."""


@dataclass(frozen=True)
class Regla:
    """Hvert skrár sem passa við `mynstur` eiga að fara."""

    mynstur: tuple[str, ...]
    flokkur: str
    rannsokn: str | None = None
    markmid: str | None = None
    athugasemd: str | None = None

    def passar(self, slod: str) -> bool:
        """Satt ef slóðin passar við eitthvert mynstur (* nær líka yfir /)."""
        return any(fnmatchcase(slod, mynstur) for mynstur in self.mynstur)


@dataclass(frozen=True)
class Stilling:
    """Innihald config/uppruni.json."""

    repo: str
    grein: str
    reglur: tuple[Regla, ...]


def _lesa_reglu(numer: int, gogn: dict) -> Regla:
    flokkur = gogn.get("flokkur")
    if flokkur not in FLOKKAR:
        raise StillingarVilla(f"Regla {numer}: óþekktur flokkur {flokkur!r}.")
    mynstur = tuple(gogn.get("mynstur", ()))
    if not mynstur:
        raise StillingarVilla(f"Regla {numer}: vantar mynstur.")
    regla = Regla(
        mynstur=mynstur,
        flokkur=flokkur,
        rannsokn=gogn.get("rannsokn"),
        markmid=gogn.get("markmid"),
        athugasemd=gogn.get("athugasemd"),
    )
    if flokkur in FLYTJA and not (regla.rannsokn and regla.markmid):
        raise StillingarVilla(f"Regla {numer} ({flokkur}): vantar rannsokn eða markmid.")
    return regla


def lesa_stillingu(slod: Path = STILLING) -> Stilling:
    """Les og sannreynir config/uppruni.json."""
    try:
        gogn = json.loads(slod.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as villa:
        raise StillingarVilla(f"Get ekki lesið {slod}: {villa}") from villa
    reglur = tuple(_lesa_reglu(i, r) for i, r in enumerate(gogn.get("reglur", []), 1))
    if not reglur:
        raise StillingarVilla(f"{slod}: engar reglur.")
    return Stilling(repo=gogn["repo"], grein=gogn["grein"], reglur=reglur)


def finna_reglu(slod: str, reglur: tuple[Regla, ...]) -> Regla | None:
    """Fyrsta regla sem passar við slóðina, eða None."""
    return next((regla for regla in reglur if regla.passar(slod)), None)
