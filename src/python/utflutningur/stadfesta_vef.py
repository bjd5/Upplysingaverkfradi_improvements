"""Staðfestir gagnaskrárnar í ``web/gogn/`` áður en ``web/`` er birt (issue #28).

GitHub Pages birtir ``web/`` eins og hún liggur í repo-inu; enginn
byggingarferill keyrir útflutninginn aftur. Týnd eða gölluð gagnaskrá færi því
beint á netið og lesandinn sæi villubox í stað talna. Birtingin
(``.github/workflows/pages.yml``) keyrir þessa einingu fyrst og stöðvast ef
eitthvað af þessu bregst:

* **Hver ``*.json`` í ``web/gogn/``** er UTF-8 og gilt JSON, og umslagið stenst
  sömu kröfur og útflutningurinn setur við skrif. Lesið umslag fer í gegnum
  :func:`json_skrif.sem_baeti` — sama fall, ekki afrit: skyldureitir og engir
  aðrir, ``uppfaert`` staðlaður UTC-tími, óauð ``heimild``, ``gogn`` listi með
  færslum, ekkert ``NaN`` og stærðarþak.
* **Hver skrá sem útflutningurinn skrifar** (:data:`flytja_ut.SKRAR`) er til.
* **Hver gagnaskrá sem síða vísar í** er til: ``data-gogn``,
  ``data-stada-gagna`` (autt eigindi þýðir ``yfirlit.json``, eins og í
  ``stada-gagna.js``) og tenglar á ``gogn/…`` (varaleiðin í ``<noscript>``).

Allar villur eru taldar upp í einni keyrslu svo ein lagfæring dugi.
Útgangskóði 1 ef einhver fannst.

Keyrsla frá rót verkefnisins::

    scripts/stadfesta-vef.sh [--vefur MAPPA]

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import json
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from .flytja_ut import SKRAR, VEFGOGN
from .json_skrif import KODUN, UtflutningsVilla, sem_baeti
from .yfirlit_json import SKRAARHEITI as YFIRLIT

VEFUR = VEFGOGN.parent
GAGNAMAPPA = VEFGOGN.name

# Eigindin sem síður nota til að nefna gagnaskrá (docs/vefur-gogn.md, kaflar 2 og 5).
EIGINDI_GAGNAHLUTA = "data-gogn"
EIGINDI_STODU = "data-stada-gagna"
EIGINDI_SLODA = ("href", "src")

ENDURGERD = "Keyrðu útflutninginn (src/python/main.py --skref flytja-ut) og committaðu skrána."


class Visanir(HTMLParser):
    """Safnar skráarheitunum í ``gogn/`` sem ein síða vísar í."""

    def __init__(self, sida: str) -> None:
        super().__init__(convert_charrefs=True)
        self.mappa = posixpath.dirname(sida)
        self.skrar: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        eigindi = dict(attrs)
        if eigindi.get(EIGINDI_GAGNAHLUTA):
            self.skrar.add(eigindi[EIGINDI_GAGNAHLUTA])
        if EIGINDI_STODU in eigindi:
            self.skrar.add(eigindi[EIGINDI_STODU] or YFIRLIT)
        for nafn in EIGINDI_SLODA:
            heiti = self._i_gagnamoppu(eigindi.get(nafn))
            if heiti:
                self.skrar.add(heiti)

    def _i_gagnamoppu(self, slod: str | None) -> str | None:
        """Skráarheitið ef staðbundin slóð lendir í ``gogn/``, annars None."""
        if not slod:
            return None
        hluti = urlsplit(slod)
        if hluti.scheme or hluti.netloc or not hluti.path:
            return None
        full = posixpath.normpath(posixpath.join(self.mappa, hluti.path))
        forskeyti = GAGNAMAPPA + "/"
        return full[len(forskeyti):] if full.startswith(forskeyti) else None


def visanir_sidna(vefur: Path) -> list[tuple[str, str]]:
    """``(síða, skráarheiti)`` fyrir hverja gagnaskrá sem HTML-síða í ``vefur`` vísar í."""
    ut: list[tuple[str, str]] = []
    for skra in sorted(vefur.rglob("*.html")):
        sida = skra.relative_to(vefur).as_posix()
        safnari = Visanir(sida)
        safnari.feed(skra.read_text(encoding=KODUN))
        ut += [(sida, heiti) for heiti in sorted(safnari.skrar)]
    return ut


def galli_i_skra(slod: Path) -> str | None:
    """Lýsing á því sem er að gagnaskránni, eða None ef hún stenst snið útflutningsins."""
    try:
        umslag = json.loads(slod.read_bytes().decode(KODUN))
    except OSError as villa:
        return f"er ekki hægt að lesa ({villa.strerror})."
    except UnicodeDecodeError as villa:
        return f"er ekki UTF-8 ({villa.reason} á bæti {villa.start})."
    except json.JSONDecodeError as villa:
        return f"er ekki gilt JSON (lína {villa.lineno}, dálkur {villa.colno}: {villa.msg})."
    try:
        sem_baeti(umslag)
    except UtflutningsVilla as villa:
        return f"stenst ekki snið útflutningsins (regla 5.4): {villa}"
    return None


def stadfesta(vefur: Path = VEFUR) -> list[str]:
    """Skilar öllum villum í ``vefur``; tómur listi þýðir að birta má."""
    gogn = vefur / GAGNAMAPPA
    synd = vefur.name + "/" + GAGNAMAPPA
    if not gogn.is_dir():
        return [f"Mappan {synd}/ er ekki til. {ENDURGERD}"]

    villur: list[str] = []
    for slod in sorted(gogn.glob("*.json")):
        galli = galli_i_skra(slod)
        if galli:
            villur.append(f"{synd}/{slod.name} {galli}")
    for heiti in SKRAR:
        if not (gogn / heiti).is_file():
            villur.append(f"{synd}/{heiti} vantar. {ENDURGERD}")
    for sida, heiti in visanir_sidna(vefur):
        if Path(heiti).name != heiti:
            villur.append(f"{sida} nefnir gagnaskrána {heiti!r}; það á að vera "
                          f"skráarheiti í {GAGNAMAPPA}/ án möppu.")
        elif not (gogn / heiti).is_file():
            villur.append(f"{sida} vísar í {GAGNAMAPPA}/{heiti}, sem er ekki til.")
    return villur


def main(rok: list[str] | None = None) -> int:
    """Skipanalínuinngangur; skilar 0 ef birta má, annars 1."""
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("--vefur", type=Path, default=VEFUR,
                          help="mappan sem á að birta (sjálfgefið web/)")
    vefur = thattari.parse_args(rok).vefur

    villur = stadfesta(vefur)
    if villur:
        print(f"Birting stöðvuð — {vefur} stenst ekki staðfestingu. "
              f"Fjöldi villna: {len(villur)}.", file=sys.stderr)
        for villa in villur:
            print(f"  VILLA: {villa}", file=sys.stderr)
        return 1
    fjoldi = len(list((vefur / GAGNAMAPPA).glob("*.json")))
    print(f"{vefur} má birta: {fjoldi} gagnaskrár standast snið útflutningsins "
          "og allar sem síðurnar vísa í eru til.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
