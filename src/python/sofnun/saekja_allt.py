"""Keyrslupunktur gagnasöfnunar — eitt safn í einu eða allt í röð.

Hvert gagnasafn á sína einingu; þessi skrifta bindur þær saman og gefur þeim
skipanalínu. Keyrsla frá rót verkefnisins::

    scripts/saekja-gogn.sh listi
    scripts/saekja-gogn.sh skjalftar
    scripts/saekja-gogn.sh allt

Einingin er **aldrei keyrð beint** (``python3 src/python/sofnun/saekja_allt.py``).
Þá færi ``src/python/sofnun`` fremst á ``sys.path`` og ``urllib`` fyndi
``sofnun/http.py`` í stað ``http`` úr staðalsafninu. Skriftan í ``scripts/``
keyrir hana sem einingu og sneiðir hjá því.

Sjálfgefið sækir ekkert safn sem þegar er til í ``data/raw/`` (regla 4).
``--thvinga`` er meðvituð ákvörðun um að sækja nýtt eintak þrátt fyrir það.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence

from . import hagstofan, mbl, skjalftar, tmdb, vedurstodvar
from .frosid import FrosidVilla
from .hagstofan import HagstofuVilla
from .hragogn import HragagnaVilla, Svar
from .http import HttpVilla
from .stillingar import StillingaVilla

log = logging.getLogger("sofnun")

# Villur sem lýsa sér sjálfar og bera aldrei lykil. Allt annað fær að falla
# óbreytt upp úr skriftunni — óvænt villa á ekki að líta út eins og vænt
# niðurstaða (regla 6).
VAENTAR_VILLUR = (
    HttpVilla,
    FrosidVilla,
    HagstofuVilla,
    HragagnaVilla,
    StillingaVilla,
)

# Heiti safns -> (aðgerð, lýsing fyrir lesanda). Röðin ræður keyrsluröð `allt`.
SOFN: dict[str, tuple[Callable[..., object], str]] = {
    "skjalftar": (skjalftar.saekja_skjalfta, "Jarðskjálftar á Reykjanesi"),
    "hagstofan": (hagstofan.saekja_hagstofuna, "Brautskráning af háskólastigi"),
    "vedurstodvar": (vedurstodvar.saekja_stodvar, "Stöðvalisti Veðurstofunnar"),
    "nominatim": (vedurstodvar.saekja_hnit_vr_ii, "Hnit VR-II"),
    "mbl": (mbl.saekja_forsidu, "Forsíða mbl.is"),
    "tmdb": (tmdb.saekja_tmdb, "Friends og hlutverk Phoebe hjá TMDB"),
}


def _sem_listi(nidurstada: object) -> list[Svar]:
    """Sum söfn eru eitt svar, önnur tvö. Hér verða þau öll að lista."""
    if isinstance(nidurstada, Svar):
        return [nidurstada]
    return list(nidurstada)  # type: ignore[arg-type]


def saekja_safn(heiti: str, *, thvinga: bool = False) -> list[Svar]:
    """Sækir eitt safn og skilar svörunum sem það skilaði."""
    adgerd, lysing = SOFN[heiti]
    log.info("%s — %s", heiti, lysing)
    svor = _sem_listi(adgerd(thvinga=thvinga))
    for svar in svor:
        hvadan = "úr data/raw/" if svar.ur_safni else "sótt núna"
        log.info("  %s (%s, %d bæti)", svar.slod_skrar.name, hvadan, len(svar.baeti))
    return svor


def keyra(heiti: Sequence[str], *, thvinga: bool = False) -> int:
    """Sækir söfnin í röð og skilar fjölda þeirra sem brugðust.

    Eitt safn sem bregst stöðvar ekki hin: TMDB án lykils á ekki að fella
    söfnun skjálftanna. Hver villa er þó skráð og skilagildið ber hana áfram.
    """
    brugdust = 0
    for nafn in heiti:
        try:
            saekja_safn(nafn, thvinga=thvinga)
        except VAENTAR_VILLUR as villa:
            log.error("%s brást: %s", nafn, villa)
            brugdust += 1
    return brugdust


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(
        description="Sækir hrágögn rannsóknarinnar í data/raw/."
    )
    thattari.add_argument(
        "safn",
        choices=[*SOFN, "allt", "listi"],
        help="Hvaða safn á að sækja, 'allt' fyrir öll í röð, 'listi' til að telja þau upp.",
    )
    thattari.add_argument(
        "--thvinga",
        action="store_true",
        help="Sækja nýtt eintak þótt gagnið sé þegar til í data/raw/.",
    )
    valkostir = thattari.parse_args(rok)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)-8s %(message)s", stream=sys.stderr
    )

    if valkostir.safn == "listi":
        for nafn, (_, lysing) in SOFN.items():
            print(f"{nafn:<14} {lysing}")
        return 0

    heiti = list(SOFN) if valkostir.safn == "allt" else [valkostir.safn]
    brugdust = keyra(heiti, thvinga=valkostir.thvinga)
    if brugdust:
        log.error("%d af %d söfnum brugðust.", brugdust, len(heiti))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
