"""Keyrslupunktur gagnasöfnunar — eitt safn í einu eða allt í röð.

Hvert gagnasafn á sína einingu; þessi skrifta bindur þær saman og gefur þeim
skipanalínu. Keyrsla frá rót verkefnisins::

    scripts/saekja-gogn.sh listi
    scripts/saekja-gogn.sh skjalftar
    scripts/saekja-gogn.sh allt

Einingin er **aldrei keyrð beint** (``python3 src/python/sofnun/saekja_allt.py``).
Þá færi ``src/python/sofnun`` fremst á ``sys.path`` og ``urllib`` fyndi
``sofnun/http.py`` í stað ``http`` úr staðalsafninu. Skriftan í ``scripts/``
keyrir hana sem einingu (``python3 -m sofnun.saekja_allt``) og sneiðir hjá því.

**Sjálfgefin keyrsla sendir ekkert netkall** (regla 4). Hvert safn sem þegar
liggur í ``data/raw/`` er skilað úr geymslunni, hvort sem provenance þess er á
sniði ``sofnun.beidni`` eða á eldra sniði sem ``sofnun.frosid`` þekkir.
``--thvinga`` er meðvituð ákvörðun um að sækja nýtt eintak þrátt fyrir það.

Söfnin eru keyrð sjálfstætt: eitt sem bregst stöðvar ekki hin. Ástæðan er TMDB,
sem krefst lykils sem ekki er til í verkefninu — það á ekki að fella söfnun
skjálftanna með sér. Hver villa er þó sögð upphátt og ber áhrif á skilagildið
(regla 6).
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from . import hagstofan, sofn
from .frosid import FrosidVilla
from .hagstofan import HagstofuVilla
from .hragogn import HragagnaVilla, Svar
from .http import HttpVilla
from .stillingar import StillingaVilla

log = logging.getLogger("sofnun")

# Villur sem lýsa sér sjálfar og bera aldrei lykil. Allt annað fær að falla
# óbreytt upp úr skriftunni — óvænt villa á ekki að líta út eins og vænt
# niðurstaða (regla 6).
VAENTAR_VILLUR = (HttpVilla, FrosidVilla, HagstofuVilla, HragagnaVilla)

# Heiti safns -> (aðgerð, lýsing fyrir lesanda). Röðin ræður keyrsluröð `allt`.
SOFN: dict[str, tuple[Callable[..., object], str]] = {
    "skjalftar": (sofn.saekja_skjalfta, "Jarðskjálftar á Reykjanesi"),
    "hagstofan": (hagstofan.saekja_hagstofuna, "Brautskráning af háskólastigi"),
    "vedurstodvar": (sofn.saekja_stodvar, "Stöðvalisti Veðurstofunnar"),
    "mbl": (sofn.saekja_forsidu, "Fréttayfirlit mbl.is"),
    "tmdb": (sofn.saekja_tmdb, "Friends og hlutverk Phoebe hjá TMDB"),
}


class SofnunVilla(RuntimeError):
    """Eitt eða fleiri söfn brugðust. Skilaboðin telja hvaða og hvers vegna."""


@dataclass
class Nidurstada:
    """Samantekt á söfnunarkeyrslu — hvað var sótt, hvað lá fyrir, hvað brást."""

    sott: list[str] = field(default_factory=list)      # söfn sem sendu netkall
    ur_safni: list[str] = field(default_factory=list)  # lágu þegar í data/raw/
    ovirk: dict[str, str] = field(default_factory=dict)      # stillingu vantar
    brugdust: dict[str, str] = field(default_factory=dict)   # raunveruleg villa

    @property
    def netlaus(self) -> bool:
        """``True`` þegar ekkert safn sendi netkall."""
        return not self.sott


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


def keyra(heiti: Sequence[str], *, thvinga: bool = False) -> Nidurstada:
    """Sækir söfnin í röð og skilar samantekt.

    Söfn sem vantar stillingu — í reynd TMDB án lykils — eru skráð **óvirk** en
    ekki brostin: það er skjalfest staða verkefnisins (``data/raw/frysting.json``)
    og ekki merki um að keyrslan hafi mistekist. Villan er samt sögð upphátt.
    """
    nidurstada = Nidurstada()
    for nafn in heiti:
        try:
            svor = saekja_safn(nafn, thvinga=thvinga)
        except StillingaVilla as villa:
            log.warning("%s er óvirkt: %s", nafn, villa)
            nidurstada.ovirk[nafn] = str(villa)
        except VAENTAR_VILLUR as villa:
            log.error("%s brást: %s", nafn, villa)
            nidurstada.brugdust[nafn] = str(villa)
        else:
            skra = nidurstada.ur_safni if all(s.ur_safni for s in svor) else nidurstada.sott
            skra.append(nafn)
    return nidurstada


def samantekt(nidurstada: Nidurstada) -> None:
    """Skráir niðurstöðuna í eina línu á hvern flokk."""
    for texti, sofn in (
        ("úr data/raw/ (ekkert kall)", nidurstada.ur_safni),
        ("sótt af netinu", nidurstada.sott),
    ):
        if sofn:
            log.info("%d %s: %s", len(sofn), texti, ", ".join(sofn))
    if nidurstada.ovirk:
        log.warning(
            "%d óvirk (stillingu vantar): %s",
            len(nidurstada.ovirk), ", ".join(nidurstada.ovirk),
        )
    if nidurstada.brugdust:
        log.error(
            "%d brugðust: %s", len(nidurstada.brugdust), ", ".join(nidurstada.brugdust)
        )


def safna(heiti: Sequence[str] | None = None, *, thvinga: bool = False) -> Nidurstada:
    """Sækir söfnin og fellur með ``SofnunVilla`` hafi eitthvert brugðist.

    Þetta er inngangurinn sem ``src/python/main.py`` notar: þar á söfnunarskrefið
    að stöðva flæðið þegar gagn vantar, en ekki þegar safn er einfaldlega óvirkt.
    """
    nidurstada = keyra(list(heiti) if heiti is not None else list(SOFN), thvinga=thvinga)
    samantekt(nidurstada)
    if nidurstada.brugdust:
        raise SofnunVilla(
            f"{len(nidurstada.brugdust)} af {len(SOFN)} söfnum brugðust: "
            + "; ".join(f"{nafn} — {bod}" for nafn, bod in nidurstada.brugdust.items())
        )
    return nidurstada


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
    try:
        safna(heiti, thvinga=valkostir.thvinga)
    except SofnunVilla:
        # Villurnar sjálfar eru þegar skráðar hver fyrir sig í keyra().
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
