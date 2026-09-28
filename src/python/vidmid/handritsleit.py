"""Leit að samfelldum handritstexta í Friends-talnaskránum sem eru í git.

Þetta repo er opið og Friends-handritin eru höfundarréttarvarin. Valkostur A í
issue #3 leyfir afleiddu **tölurnar** í git — línufjölda, senur, hlutföll,
tíðnitöflur — því þær eru staðreyndir um textann en ekki textinn. Skilyrðið sem
gerir það löglegt er að engin skrá geymi samfellda setningu úr þáttunum.

Þetta tól staðfestir skilyrðið í stað þess að treysta því. Reglan:

1. **Gagnareitur** má hafa að hámarki `ORDATHAK_GAGNAREITS` orð og **ekkert**
   setningamerki. Setning endar á punkti, upphrópun eða spurningarmerki; reitur
   sem geymir talningu gerir það ekki.
2. **Undanþegnir reitir** — aðferðarlýsingar verkefnisins og þáttatitlar — eru
   taldir upp í `handritsreitir.py` með ástæðu og **frystri SHA-256**. Undanþága
   getur því ekki orðið felustaður: breytist innihald undanþegins reits fellur
   prófið jafnt og ef nýr reitur bryti regluna.
3. Undanþága sem finnst ekki, eða sem reitur þarf ekki lengur, fellir prófið
   líka. Listinn má hvorki rotna né vera víðari en þörf er á.

Tólið **prentar ekki innihald** brotlegs strengs, aðeins staðsetningu og
mælingar. Væri hann handritstexti myndi prentunin afrita hann í logga og
CI-úttök — nákvæmlega það sem á að koma í veg fyrir.

**Afmörkun:** leitin les aðeins JSON- og CSV-talnaskrárnar sem
`handritsreitir.py` telur upp — sjá docs/adferdafraedi.md, kafla 1.5.2.

Keyrsla:
    python3 src/python/vidmid/handritsleit.py stadfesta
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

try:  # keyrt beint: python3 src/python/vidmid/handritsleit.py
    from handritsreitir import (
        MOPPUR,
        ORDATHAK_GAGNAREITS,
        STAKAR_SKRAR,
        UNDANTEKNINGAR,
        VIDAUKAR,
    )
except ImportError:  # flutt inn sem eining innan pakkans
    from .handritsreitir import (
        MOPPUR,
        ORDATHAK_GAGNAREITS,
        STAKAR_SKRAR,
        UNDANTEKNINGAR,
        VIDAUKAR,
    )

ROT = Path(__file__).resolve().parents[3]

# Setningamerki: punktur, upphrópun, spurningarmerki eða úrfellingarmerki sem
# lokar orði, eða sem er fylgt af nýju hástafsorði. Tugabrot eru undanskilin
# (`2.95`, `10.16`) — annars myndi hver prósentutala reiknast sem setning.
SETNINGAMERKI = re.compile(
    r"(?<![0-9])[.!?…](?=\s|$)"
    r"|[.!?…]\s+(?=[A-ZÁÉÍÓÚÝÞÆÖ])"
)

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("handritsleit")


@dataclass(frozen=True)
class Frava:
    """Eitt frávik: hvar það er og hvað mældist. Ekki innihaldið sjálft."""

    slod: str
    reitur: str
    skyring: str

    def __str__(self) -> str:
        return f"{self.slod} :: {self.reitur} — {self.skyring}"


def setningamerki(gildi: str) -> int:
    """Skilar fjölda setningamerkja í streng."""
    return len(SETNINGAMERKI.findall(gildi))


def _strengir_json(hlutur: object, leid: str = "") -> Iterator[tuple[str, str]]:
    """Gengur JSON-tré og skilar (leið, strengur) fyrir hvert strengjagildi.

    Listaliðir fá `[]` í leiðina en ekki vísi: reitur er reitur hvort hann
    kemur einu sinni fyrir eða 227 sinnum.
    """
    if isinstance(hlutur, dict):
        for lykill, gildi in hlutur.items():
            yield from _strengir_json(gildi, f"{leid}.{lykill}")
    elif isinstance(hlutur, list):
        for gildi in hlutur:
            yield from _strengir_json(gildi, f"{leid}[]")
    elif isinstance(hlutur, str):
        yield leid or ".", hlutur


def _strengir_csv(slod: Path) -> Iterator[tuple[str, str]]:
    """Skilar (dálkheiti, gildi) fyrir hvern reit í CSV-skrá."""
    with slod.open(encoding="utf-8", newline="") as skra:
        lesari = csv.reader(skra)
        try:
            haus = next(lesari)
        except StopIteration:
            raise ValueError(f"CSV-skrá án haus: {slod}") from None
        for rod in lesari:
            for visir, gildi in enumerate(rod):
                yield (haus[visir] if visir < len(haus) else f"dalkur{visir}"), gildi


def reitir(slod: Path) -> dict[str, list[str]]:
    """Skilar öllum strengjagildum skráar, flokkuðum eftir reit."""
    if slod.suffix == ".json":
        par = _strengir_json(json.loads(slod.read_text(encoding="utf-8")))
    elif slod.suffix == ".csv":
        par = _strengir_csv(slod)
    else:
        raise ValueError(f"Óþekkt skráarsnið: {slod}")

    safn: dict[str, list[str]] = {}
    for reitur_heiti, gildi in par:
        safn.setdefault(reitur_heiti, []).append(gildi)
    return safn


def skrar(rot: Path = ROT) -> tuple[list[Path], list[str]]:
    """Skilar skránum sem á að skanna og frávikum um staðsetningar sem vantar."""
    fundnar: list[Path] = []
    frabrigdi: list[str] = []

    for heiti in MOPPUR:
        mappa = rot / heiti
        if not mappa.is_dir():
            frabrigdi.append(f"Mappa sem á að skanna er ekki til: {heiti}")
            continue
        i_moppu = sorted(p for p in mappa.iterdir() if p.suffix in VIDAUKAR)
        if not i_moppu:
            frabrigdi.append(f"Mappa án skannanlegra skráa: {heiti}")
        fundnar.extend(i_moppu)

    for heiti in STAKAR_SKRAR:
        slod = rot / heiti
        if not slod.is_file():
            frabrigdi.append(f"Skrá sem á að skanna er ekki til: {heiti}")
            continue
        fundnar.append(slod)

    return fundnar, frabrigdi


def _sha_reits(gildin: list[str]) -> str:
    """SHA-256 af öllum gildum reitsins, skeytt saman með línuskilum."""
    return hashlib.sha256("\n".join(gildin).encode("utf-8")).hexdigest()


def brotlegt(gildi: str) -> bool:
    """Brýtur strengurinn almennu regluna um gagnareiti?"""
    return len(gildi.split()) > ORDATHAK_GAGNAREITS or setningamerki(gildi) > 0


def leita(rot: Path = ROT) -> tuple[list[Frava], dict[str, int]]:
    """Skannar allar skrár og skilar frávikum ásamt talningu.

    Frávik er hvort sem er: gagnareitur sem lítur út eins og texti, undanþeginn
    reitur sem hefur breyst, eða undanþága sem á sér ekki stað í skránum.
    """
    skannadar, vantar = skrar(rot)
    fravik = [Frava("(staðsetning)", "-", skyring) for skyring in vantar]
    notadar: set[tuple[str, str]] = set()
    onaudsynlegar: set[tuple[str, str]] = set()
    fjoldi_strengja = 0

    for slod in skannadar:
        birt = slod.relative_to(rot).as_posix()
        for reitur_heiti, gildin in reitir(slod).items():
            fjoldi_strengja += len(gildin)
            lykill = (slod.name, reitur_heiti)
            brotleg = [g for g in gildin if brotlegt(g)]
            undantekning = UNDANTEKNINGAR.get(lykill)

            if undantekning is None:
                for gildi in brotleg:
                    fravik.append(
                        Frava(
                            birt,
                            reitur_heiti,
                            f"lítur út eins og texti: {len(gildi.split())} orð, "
                            f"{setningamerki(gildi)} setningamerki, "
                            f"{len(gildi)} stafir (ekkert undanþegið)",
                        )
                    )
                continue

            notadar.add(lykill)
            if not brotleg:
                onaudsynlegar.add(lykill)
            reiknad = _sha_reits(gildin)
            if reiknad != undantekning.sha256:
                fravik.append(
                    Frava(
                        birt,
                        reitur_heiti,
                        "undanþeginn reitur hefur breyst — SHA-256 "
                        f"{reiknad[:16]} en pinnað {undantekning.sha256[:16]}. "
                        "Lestu hann yfir og pinnaðu upp á nýtt ef hann er enn "
                        f"{undantekning.flokkur}",
                    )
                )

    for lykill in sorted(set(UNDANTEKNINGAR) - notadar):
        fravik.append(
            Frava(lykill[0], lykill[1], "undanþága á sér ekki stað — dauð færsla")
        )
    for lykill in sorted(onaudsynlegar):
        fravik.append(
            Frava(
                lykill[0],
                lykill[1],
                "undanþágu er ekki þörf lengur — reiturinn stenst almennu regluna",
            )
        )

    talning = {
        "skrar": len(skannadar),
        "strengir": fjoldi_strengja,
        "undantekningar": len(UNDANTEKNINGAR),
        "fravik": len(fravik),
    }
    return fravik, talning


def stadfesta() -> int:
    """Skilar 0 sé enginn samfelldur handritstexti í talnaskránum, annars 1."""
    fravik, talning = leita()
    if fravik:
        # Regla 6: villur eru aldrei þaggaðar.
        for eitt in fravik:
            log.error("%s", eitt)
        log.error(
            "%d frávik — ekki er unnt að staðfesta að afleiðurnar séu textalausar",
            len(fravik),
        )
        return 1

    log.info(
        "%d talnaskrár, %d strengjagildi, %d undanþágur — engin samfelld setning",
        talning["skrar"],
        talning["strengir"],
        talning["undantekningar"],
    )
    return 0


AÐGERÐIR = {"stadfesta": stadfesta}


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("adgerd", choices=[*AÐGERÐIR], help="stadfesta")
    return AÐGERÐIR[thattari.parse_args(rok).adgerd]()


if __name__ == "__main__":
    sys.exit(main())
