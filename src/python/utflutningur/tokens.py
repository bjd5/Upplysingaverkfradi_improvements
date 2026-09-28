"""Lestur á sjónræna kerfinu úr ``web/assets/css/tokens.css`` (regla 3.1).

Regla 3.1 segir að **öll** gildi fyrir liti, letur og bil séu skilgreind í
``tokens.css`` og að enginn harðkóðaður litur sé annars staðar. Myndrit sem
Python teiknar er ekki undanskilið: litur skrifaður inn í Python-skriftu er
sama reglubrotið og litur skrifaður inn í aðra CSS-skrá — hann er þá til á
tveimur stöðum og þeir ganga úr takt við fyrsta þemabreytingu.

Þess vegna er ``tokens.css`` **lesin** þegar myndritið er teiknað. Skráin er
eina heimildin; Python þekkir engan lit sjálfur. Kostnaðurinn er lítill
þáttari (hér að neðan) og hann er metinn ódýrari en tvær heimildir um sama
gildi.

Skráin hefur tvö sett af gildum og bæði eru lesin:

* ``:root`` — ljósa þemað.
* ``:root`` inni í ``@media (prefers-color-scheme: dark)`` — þau gildi sem
  dökka þemað endurskilgreinir. Þemað erfir allt annað úr ljósa settinu.

Þetta þýðir að myndrit fæst í báðum þemum úr sömu heimild, og síðan getur
valið milli þeirra með ``<picture>`` án JavaScript.

Eingöngu staðalsafnið (regla 10): matplotlib kemur hvergi nærri þessari
einingu, svo prófin á henni keyra alltaf.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
SJALFGEFIN_SLOD = ROT / "web" / "assets" / "css" / "tokens.css"

LJOST = "ljost"
DOKKT = "dokkt"

_DOKKT_SKILYRDI = "prefers-color-scheme: dark"
_ATHUGASEMD = re.compile(r"/\*.*?\*/", re.DOTALL)
_YFIRLYSING = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
_TILVISUN = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*\)")
_HAMARK_DYPT = 10


class TokenVilla(Exception):
    """Token vantar, er ólesanlegt eða vísar í sjálft sig.

    Villan er alltaf kastað — aldrei skilað sjálfgefnu gildi. Myndrit með
    ágiskaðan lit lítur út fyrir að vera í lagi og er það ekki (regla 6).
    """


@dataclass(frozen=True)
class Thema:
    """Fullgert sett af tokens fyrir eitt þema, með allar ``var()`` uppleystar."""

    heiti: str
    gildi: dict[str, str]

    def texti(self, nafn: str) -> str:
        """Skilar gildi tokens sem texta, t.d. ``--letur-texti``."""
        if nafn not in self.gildi:
            raise TokenVilla(
                f"Token {nafn} er ekki í {self.heiti}-þemanu í tokens.css. "
                f"Skilgreindu það þar — ekki í Python."
            )
        return self.gildi[nafn]

    def litur(self, nafn: str) -> str:
        """Skilar lit tokens á forminu ``#rrggbb``, eins og matplotlib vill hafa hann."""
        r, g, b = self.rgb(nafn)
        return f"#{r:02x}{g:02x}{b:02x}"

    def rgb(self, nafn: str) -> tuple[int, int, int]:
        """Skilar lit tokens sem (r, g, b) í 0–255."""
        return thatta_lit(self.texti(nafn), samhengi=f"{nafn} ({self.heiti})")


def thatta_lit(gildi: str, samhengi: str = "") -> tuple[int, int, int]:
    """Þáttar ``#rgb``, ``#rrggbb`` eða ``#rrggbbaa`` í (r, g, b).

    Gagnsæi er fellt út: myndritin nota gegnheila liti svo litaandstæðan sem
    mæld er sé sú sama og sést á skjánum. Annað snið en ``#`` er villa —
    ``rgb(... / 6%)`` úr skuggatokens er ekki litur sem myndrit á að teikna.
    """
    hreint = gildi.strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{8}", hreint):
        raise TokenVilla(
            f"Gildið {gildi!r} {samhengi} er ekki sextándalitur. "
            f"Myndrit teikna aðeins gegnheila liti úr tokens.css."
        )
    stafir = hreint[1:]
    if len(stafir) == 3:
        stafir = "".join(s * 2 for s in stafir)
    return (int(stafir[0:2], 16), int(stafir[2:4], 16), int(stafir[4:6], 16))


def lesa_tokens(slod: Path | str | None = None) -> dict[str, Thema]:
    """Les ``tokens.css`` og skilar ``{"ljost": Thema, "dokkt": Thema}``.

    Dökka þemað er ljósa þemað með þeim gildum sem ``@media`` blokkin
    endurskilgreinir — sama erfðaleið og vafrinn fer.
    """
    skra = Path(slod) if slod is not None else SJALFGEFIN_SLOD
    if not skra.is_file():
        raise TokenVilla(f"Fann ekki tokens.css á {skra}.")
    texti = _ATHUGASEMD.sub("", skra.read_text(encoding="utf-8"))

    ljos_hluti, dokkur_hluti = _kljufa_thema(texti, skra)
    hra_ljos = _yfirlysingar(ljos_hluti)
    if not hra_ljos:
        raise TokenVilla(f"Fann engin tokens í :root í {skra}.")
    hra_dokk = dict(hra_ljos)
    hra_dokk.update(_yfirlysingar(dokkur_hluti))

    return {
        LJOST: Thema(LJOST, _leysa(hra_ljos)),
        DOKKT: Thema(DOKKT, _leysa(hra_dokk)),
    }


def _kljufa_thema(texti: str, skra: Path) -> tuple[str, str]:
    """Skilar (ljósi hluti, dökkur hluti) úr skránni.

    Dökka þemað er allt sem kemur eftir ``prefers-color-scheme: dark``; regla
    3.1 leyfir aðeins endurskilgreiningu á tokens þar, svo skilin eru skýr.
    """
    staerd = texti.find(_DOKKT_SKILYRDI)
    if staerd == -1:
        raise TokenVilla(
            f"Fann ekki {_DOKKT_SKILYRDI} í {skra}. Dökkt þema er krafa (regla 3.1)."
        )
    return texti[:staerd], texti[staerd:]


def _yfirlysingar(hluti: str) -> dict[str, str]:
    """Safnar ``--nafn: gildi;`` úr texta. Síðasta yfirlýsing gildir, eins og í CSS."""
    return {nafn: gildi.strip() for nafn, gildi in _YFIRLYSING.findall(hluti)}


def _leysa(hra: dict[str, str]) -> dict[str, str]:
    """Leysir allar ``var(--x)`` tilvísanir innan sama þema."""
    return {nafn: _leysa_eitt(nafn, hra, dypt=0) for nafn in hra}


def _leysa_eitt(nafn: str, hra: dict[str, str], dypt: int) -> str:
    if dypt > _HAMARK_DYPT:
        raise TokenVilla(
            f"Token {nafn} vísar í sjálft sig (eða of djúpt) í tokens.css."
        )
    gildi = hra[nafn]

    def skipta(leit: re.Match[str]) -> str:
        tilvisun = leit.group(1)
        if tilvisun not in hra:
            raise TokenVilla(
                f"Token {nafn} vísar í {tilvisun}, sem er ekki skilgreint í tokens.css."
            )
        return _leysa_eitt(tilvisun, hra, dypt + 1)

    return _TILVISUN.sub(skipta, gildi).strip()
