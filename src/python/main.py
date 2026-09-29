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
from keyrsla.hledsla import hlada_ollum, krefjast_adfanga
from keyrsla.urvinnsla import handritamappa, vinna_allt
from keyrsla.villa import SkrefVilla
from sofnun.saekja_allt import SofnunVilla
from utflutningur import flytja_ut as utflutningur
from sofnun.saekja_allt import safna as safna_gogn

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

    Skrefið sendir ekkert netkall þegar gögnin liggja þegar í data/raw/ — þau
    eru skilað úr geymslunni. Nýtt eintak er sótt vísvitandi með
    ``scripts/saekja-gogn.sh <safn> --thvinga``, ekki héðan: síðan á að byggjast
    eins í hvert sinn.
    """
    nidurstada = safna_gogn()
    if nidurstada.netlaus:
        log.info("Söfnun lokið án netkalls — öll gögn lágu í data/raw/.")


def vinna() -> None:
    """Keyrir vinnslurnar sem skrifa afleiddar töflur í data/processed/.

    Netlausu vinnslurnar (skjálftar, veðurstöðvar) keyra alltaf. Phoebe og
    Central Perk þurfa Friends-handritin, sem eru utan repo-sins (#3), og keyra
    aðeins sé ``FRIENDS_HANDRIT_MAPPA`` stillt — annars er það sagt í viðvörun.
    Sjá ``keyrsla.urvinnsla``.
    """
    vinna_allt(GOGN_UNNIN, handritamappa())


def hlada() -> None:
    """Byggir grunninn úr migrations og hleður öllum gagnasöfnunum í hann.

    Regla 5: öll uppbygging grunnsins kemur úr src/sql/migrations/, keyrð í
    númeraröð, og fyrirspurnir eru alltaf með breytum. Vanti frosið aðfang
    einhvers safns er stöðvað áður en grunnurinn er snertur; söfnin eru hlaðin
    í einni færslu (sjá ``keyrsla.hledsla`` um röðina).
    """
    krefjast_adfanga()
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

    with tenging(GAGNAGRUNNUR) as samband:
        hladin = hlada_ollum(samband)
    log.info("Hlóð %d gagnasöfnum í %s.", len(hladin), GAGNAGRUNNUR)


def flytja_ut() -> None:
    """Flytur niðurstöður úr grunninum út sem JSON í web/gogn/ (regla 5.4, #15).

    Hver skrá er á forminu ``{"uppfaert", "heimild", "gogn"[, "lysigogn"]}``
    og er skrifuð atómískt; bregðist eitt safn er engin skrá skrifuð. Söfn sem
    eiga enn engan útflutning eru nefnd í viðvörun (``utflutningur.flytja_ut``).
    Villa verður að :class:`SkrefVilla` og þar með útgangskóða 1.
    """
    try:
        skrifadar = utflutningur.flytja_ut(VEFGOGN, GAGNAGRUNNUR)
    except utflutningur.UTFLUTNINGSVILLUR as villa:
        raise SkrefVilla(f"Útflutningur í {VEFGOGN} brást: {villa}") from villa
    log.info("Flutti út %d skrár í %s.", len(skrifadar), VEFGOGN)


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
        except (SofnunVilla, SkrefVilla) as villa:
            # Hrágagn vantar eða er ósannreynanlegt, eða safn/vinnsla brást.
            # Næstu skref myndu byggja tölur á ófullgerðum gögnum, svo flæðið
            # stöðvast hér (reglur 4 og 6).
            log.error("%s", villa)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
