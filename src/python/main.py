"""Keyrslupunktur fyrir gagnaflæði verkefnisins.

Flæðið er einstefna (sjá kafla 0 í CLAUDE.md):

    Vefþjónusta -> data/raw/ -> hreinsun -> SQL-grunnur -> web/gogn/*.json

Keyrsla:
    python src/python/main.py --skref allt
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from gagnagrunnur.keyrari import MigrationVilla, keyra
from gagnagrunnur.tenging import slod_grunns, tenging

ROT = Path(__file__).resolve().parents[2]
GOGN_HRA = ROT / "data" / "raw"
GOGN_UNNIN = ROT / "data" / "processed"
GAGNAGRUNNUR = slod_grunns()
VEFGOGN = ROT / "web" / "gogn"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rannsokn")


def safna() -> None:
    """Sækir gögn frá vefþjónustum og vistar svörin óbreytt í data/raw/.

    Regla 4: hrágögnum er aldrei breytt eftir á, og hver söfnun er skráð
    með þjónustu, slóð, tímastimpli og breytum.
    """
    log.info("Söfnun: ekki útfærð enn — sjá src/python/sofnun/")
    raise NotImplementedError("Útfæra í src/python/sofnun/")


def vinna() -> None:
    """Hreinsar og samræmir hrágögn yfir í data/processed/."""
    log.info("Vinnsla: ekki útfærð enn — sjá src/python/vinnsla/")
    raise NotImplementedError("Útfæra í src/python/vinnsla/")


def hlada() -> None:
    """Byggir grunninn úr migrations og setur hreinsuð gögn í hann.

    Regla 5: öll uppbygging grunnsins kemur úr src/sql/migrations/, keyrð í
    númeraröð, og fyrirspurnir eru alltaf með breytum.
    """
    with tenging(GAGNAGRUNNUR) as samband:
        keyrdar = keyra(samband)

    if keyrdar:
        log.info(
            "Keyrði %d migration: %s",
            len(keyrdar),
            ", ".join(m.skraarheiti for m in keyrdar),
        )
    else:
        log.info("Grunnurinn hefur þegar allar migrations — ekkert var keyrt.")

    log.info("Hleðsla gagnasafnanna sjálfra: ekki útfærð enn — sjá issue #6–#10.")


def flytja_ut() -> None:
    """Flytur niðurstöður úr grunninum út sem JSON í web/gogn/.

    Regla 5.4: hver skrá er á forminu
    {"uppfaert": "<ISO>", "heimild": "...", "gogn": [...]}
    """
    log.info("Útflutningur: ekki útfærður enn — sjá src/python/utflutningur/")
    raise NotImplementedError("Útfæra í src/python/utflutningur/")


SKREF = {
    "safna": safna,
    "vinna": vinna,
    "hlada": hlada,
    "flytja-ut": flytja_ut,
}


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description="Gagnaflæði rannsóknarverkefnisins")
    thattari.add_argument(
        "--skref",
        choices=[*SKREF, "allt"],
        default="allt",
        help="Hvaða skref á að keyra (sjálfgefið: allt)",
    )
    valkostir = thattari.parse_args(rok)

    for mappa in (GOGN_HRA, GOGN_UNNIN, GAGNAGRUNNUR.parent, VEFGOGN):
        mappa.mkdir(parents=True, exist_ok=True)

    adgerdir = SKREF.values() if valkostir.skref == "allt" else [SKREF[valkostir.skref]]

    for adgerd in adgerdir:
        try:
            adgerd()
        except NotImplementedError as villa:
            # Regla 6: villur eru aldrei þaggaðar — en hér er þetta vænt ástand
            # meðan verkefnið er í uppbyggingu.
            log.warning("%s", villa)
        except MigrationVilla as villa:
            # Sagan stemmir ekki við migration-skrárnar: grunnurinn er ekki
            # endurbyggjanlegur og keyrslan heldur ekki áfram (regla 5).
            log.error("%s", villa)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
