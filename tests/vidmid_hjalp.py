"""Hjálparkóði samanburðarins við gömlu síðuna (docs/samanburdur.md).

Hver efnisleg tala í ``docs/vidmid/vidmid.json`` fær nákvæmlega einn flokk:
``stemmir`` og ``vikur`` ráðast af raunverulegum samanburði við
``web/gogn/*.json`` — flokkurinn er aldrei skrifaður inn. ``á ekki við`` og
``ekki borið saman`` eru ákvarðanir með skráðri ástæðu. Röð sem fær engan
flokk, eða tvo, fellir samanburðinn (``Afgreidsla.lokid``).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
GOGN_MAPPA = ROT / "web" / "gogn"
STEMMIR, VIKUR, EKKI_VID, EKKI_BORID = "stemmir", "vikur", "á ekki við", "ekki borið saman"
SKEKKJA = 1e-9
HLUTI_AF_TEXTA = "tala í texta, nafni eða lista, ekki niðurstaða"
UTAN_UMFANGS = "lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3)"
BIDSTADA = "biðstaða — nýja síðan birtir engar tölur úr þessu efni"


def lesa_vidmid() -> dict:
    """Les viðmiðið óbreytt."""
    return json.loads(VIDMID_JSON.read_text(encoding="utf-8"))


def lesa_gogn(skra: str) -> dict:
    """Les útflutta JSON-skrá úr web/gogn/ (skjalið allt: gogn, lysigogn, heimild)."""
    return json.loads((GOGN_MAPPA / f"{skra}.json").read_text(encoding="utf-8"))


def snida(gildi: object) -> str:
    """Snið talna í skjalinu: þúsundaskil með punkti, aukastafir með kommu."""
    if gildi is None:
        return "—"
    if isinstance(gildi, (list, tuple)):
        return "–".join(snida(g) for g in gildi)
    if isinstance(gildi, str):
        return gildi
    if float(gildi).is_integer():
        return f"{int(gildi):,}".replace(",", ".") if abs(gildi) >= 10000 else str(int(gildi))
    return str(gildi).replace(".", ",")


@dataclass(frozen=True)
class Nidurstada:
    """Ein viðmiðstala og hvað varð um hana."""

    id: str
    sida: str
    ny_sida: str
    flokkur: str
    maeling: str
    gamalt: str
    nytt: str
    astaeda: str


def _jafnt(a: object, b: object) -> bool:
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_jafnt(x, y) for x, y in zip(a, b))
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if a is None or b is None:
        return False
    return math.isclose(a, b, abs_tol=SKEKKJA)


class Afgreidsla:
    """Flokkar efnislegar tölur einnar gamallar síðu."""

    def __init__(self, vidmid: dict, sida: str, ny_sida: str) -> None:
        self.sida, self.ny_sida = sida, ny_sida
        self.rader = {r["id"].split("#")[1]: r for r in vidmid["gogn"]
                      if r["sida"] == sida and r["visst"]}
        self.nidurstodur: dict[str, Nidurstada] = {}

    def milli(self, fyrsta: str, sidasta: str) -> list[str]:
        """Númer raða á bilinu (aðeins efnislegar raðir eru til)."""
        return [nr for nr in self.rader if fyrsta <= nr <= sidasta]

    def _skra(self, nr: str, flokkur: str, mae: str, nytt: str, astaeda: str,
              gamalt: object = None) -> None:
        if nr not in self.rader:
            raise AssertionError(f"{self.sida}#{nr} er ekki efnisleg tala í viðmiðinu")
        if nr in self.nidurstodur:
            raise AssertionError(f"{self.sida}#{nr} flokkuð tvisvar")
        rod = self.rader[nr]
        if gamalt is None:
            gamalt = rod["bil"] if rod["gildi"] is None else rod["gildi"]
        self.nidurstodur[nr] = Nidurstada(
            rod["id"], self.sida, self.ny_sida, flokkur, mae, snida(gamalt), nytt, astaeda)

    def bera(self, nr: str, nytt: object, mae: str, astaeda: str = "") -> None:
        """Ber gamla gildið við það nýja; ``astaeda`` er skýring ef þau víkja."""
        rod = self.rader[nr]
        gamalt = rod["texti"] if isinstance(nytt, str) else (
            rod["bil"] if rod["gildi"] is None else rod["gildi"])
        flokkur = STEMMIR if _jafnt(gamalt, nytt) else VIKUR
        self._skra(nr, flokkur, mae, snida(nytt), astaeda if flokkur == VIKUR else "", gamalt)

    def sleppa(self, nrs: list[str] | str, flokkur: str, astaeda: str) -> None:
        """Flokkar raðir án samanburðar, með skráðri ástæðu."""
        for nr in [nrs] if isinstance(nrs, str) else nrs:
            self._skra(nr, flokkur, "", "", astaeda)

    def lokid(self) -> list[Nidurstada]:
        """Skilar niðurstöðum í röð viðmiðsins; fellur ef einhver tala fékk engan flokk."""
        vantar = set(self.rader) - set(self.nidurstodur)
        if vantar:
            raise AssertionError(f"{self.sida}: óflokkaðar tölur {sorted(vantar)}")
        return [self.nidurstodur[nr] for nr in self.rader]
