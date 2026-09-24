"""Frystir hrágögnin sem rannsóknin byggir á — ein skipun fyrir allt (regla 4).

Söfnin komast hingað þrjár ólíkar leiðir og skriftan sameinar þær:

===============  =========================================================
``afrit``        Söfn sem voru þegar vistuð í upprunaverkefninu eru afrituð
                 óbreytt og sannreynd gegn provenance sem fylgdi þeim.
``vedurstodvar`` Eina safnið sem átti sér ekkert eintak. Eitt eintak er sótt.
``tmdb``         Krefst lykils. Er hann ekki til er safnið skráð ófryst.
``stadfesta``    Reiknar SHA-256 upp á nýtt og ber við ``frysting.json``.
===============  =========================================================

Keyrsla frá rót verkefnisins::

    python3 src/python/sofnun/frysta.py allt
    python3 src/python/sofnun/frysta.py stadfesta

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:  # keyrt beint: python3 src/python/sofnun/frysta.py
    import frysta_afrit
    import frysta_vedurstodvar
    from frysting import ROT, log, skra_ofryst, stadfesta
except ImportError:  # flutt inn sem eining innan pakkans
    from . import frysta_afrit, frysta_vedurstodvar
    from .frysting import ROT, log, skra_ofryst, stadfesta

TMDB_BREYTA = "TMDB_TOKEN"
UMHVERFISSKRA = ROT / ".env"


def lykill_til(heiti: str) -> bool:
    """Segir hvort lykill sé tiltækur — í umhverfinu eða í ``.env``.

    Gildið sjálft er hvorki skilað, prentað né skráð: lykill fer aldrei í úttak,
    logg né git (regla 4). Aðeins svarið „er hann til?" fer héðan.
    """
    if os.environ.get(heiti, "").strip():
        return True
    if not UMHVERFISSKRA.is_file():
        return False
    for lina in UMHVERFISSKRA.read_text(encoding="utf-8").splitlines():
        lina = lina.strip()
        if lina.startswith("#") or "=" not in lina:
            continue
        nafn, _, gildi = lina.partition("=")
        if nafn.strip() == heiti and gildi.strip():
            return True
    return False


def tmdb() -> int:
    """Skráir TMDB-safnið. Sækir ekkert — sjá skýringu í ``frysting.json``.

    Ekkert eintak af TMDB-svörunum er á disknum; aðeins samantektin í
    ``docs/vidmid/generated/phoebe-tmdb-summary.md`` er eftir. Söfnunin sjálf á
    heima í sameiginlega HTTP-laginu (P2.1, issue #12) þar sem lyklameðferð og
    hraðatakmörkun eru leyst á einum stað — ekki í tvígang hér.
    """
    if lykill_til(TMDB_BREYTA):
        af_hverju = (
            f"{TMDB_BREYTA} er til staðar en söfnunin er ekki útfærð hér. Hún bíður "
            "sameiginlega HTTP-lagsins (P2.1, issue #12) svo lyklameðferð og "
            "hraðatakmörkun séu á einum stað."
        )
        hvad_vantar = "söfnunarleið (issue #12), ekki lykill"
        log.warning("TMDB: %s", af_hverju)
    else:
        af_hverju = (
            f"{TMDB_BREYTA} er ekki til í umhverfinu né í .env, svo ekkert er hægt að "
            "sækja. Ekkert eintak er á disknum heldur — aðeins samantektin í "
            "docs/vidmid/generated/phoebe-tmdb-summary.md er eftir af safninu."
        )
        hvad_vantar = f"{TMDB_BREYTA} í .env"
        log.warning(
            "TMDB: %s vantar — sleppi safninu og skrái það ófryst. Hin söfnin halda áfram.",
            TMDB_BREYTA,
        )

    skra_ofryst(
        "tmdb",
        af_hverju,
        hvad_vantar,
    )
    return 0


def allt() -> int:
    """Keyrir allar frystingar í röð og staðfestir niðurstöðuna."""
    for adgerd in (frysta_afrit.frysta, frysta_vedurstodvar.frysta, tmdb):
        stada = adgerd()
        if stada:
            return stada
    return stadfesta()


AÐGERÐIR = {
    "afrit": frysta_afrit.frysta,
    "vedurstodvar": frysta_vedurstodvar.frysta,
    "tmdb": tmdb,
    "stadfesta": stadfesta,
    "allt": allt,
}


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("adgerd", choices=[*AÐGERÐIR], help="hvað á að frysta")
    return AÐGERÐIR[thattari.parse_args(rok).adgerd]()


if __name__ == "__main__":
    sys.exit(main())
