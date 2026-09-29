"""Talnaskrár Friends-greiningarinnar: SHA-staðfesting og lestur (issue #10).

Hleðslan les **aðeins** afleiddu tölurnar í ``data/processed/phoebe-stats/``
— aldrei handritin (issue #3, valkostur A). Skrárnar þar eru um leið frosna
viðmiðið, svo ekkert í þeim má breytast.

Áður en nokkur skrá er lesin er SHA-256 hverrar þeirra borin við summuna í
``docs/vidmid/provenance.json`` (safnið ``phoebe-stats``) — sama hugsun og í
``sofnun.frosid``: ósannreynt eintak fer ekki lengra. Mappan verður líka að
geyma nákvæmlega þær skrár sem provenance nefnir, hvorki fleiri né færri, svo
engin skrá hverfi hljóðlega úr hleðslunni og engin laumist inn (regla 6).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

from gagnagrunnur.tenging import ROT

STATS_MAPPA = ROT / "data" / "processed" / "phoebe-stats"
PROVENANCE = ROT / "docs" / "vidmid" / "provenance.json"

# Heiti safnsins í provenance.json.
SAFN = "phoebe-stats"
FJOLDI_SKRAA = 17


class HledsluVilla(RuntimeError):
    """Talnaskrárnar eru ekki þær sem voru frystar, eða stangast á."""


@dataclass(frozen=True)
class Skra:
    """Ein staðfest talnaskrá."""

    heiti: str
    sha256: str
    staerd: int


def stutt_slod(slod: Path) -> str:
    """Slóð afstæð við rót verkefnisins þegar hún liggur þar, annars full slóð."""
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)


def lesa_summur(provenance: Path = PROVENANCE) -> dict[str, str]:
    """Skráð SHA-256 hverrar talnaskrár safnsins, eftir skráarheiti.

    Safnið verður að finnast nákvæmlega einu sinni; tvö söfn með sama heiti
    gerðu það tvírætt hvor summan gildir.
    """
    if not provenance.is_file():
        raise HledsluVilla(
            f"Vantar {stutt_slod(provenance)} — án skráðra summa er ekki hægt að "
            "staðfesta talnaskrárnar og þær fara ekki í grunninn (regla 4)."
        )
    skjal = json.loads(provenance.read_text(encoding="utf-8"))
    sofn = [s for s in skjal.get("sofn", []) if s.get("heiti") == SAFN]
    if len(sofn) != 1:
        raise HledsluVilla(
            f"{stutt_slod(provenance)} nefnir safnið {SAFN!r} {len(sofn)} sinnum; "
            "það verður að vera nákvæmlega einu sinni."
        )
    summur: dict[str, str] = {}
    for skra in sofn[0].get("skrar", []):
        heiti = Path(str(skra["slod"])).name
        if heiti in summur:
            raise HledsluVilla(f"Provenance nefnir {heiti} tvisvar í safninu {SAFN}.")
        summur[heiti] = str(skra["sha256"])
    if len(summur) != FJOLDI_SKRAA:
        raise HledsluVilla(
            f"Provenance nefnir {len(summur)} talnaskrár í {SAFN}, ekki {FJOLDI_SKRAA}."
        )
    return summur


def stadfesta_skrar(
    mappa: Path = STATS_MAPPA, provenance: Path = PROVENANCE
) -> list[Skra]:
    """Staðfestir að mappan geymi nákvæmlega skráðu skrárnar, óbreyttar.

    Stöðvar við fyrsta frávik: skrá sem vantar, skrá umfram, eða summu sem
    víkur frá provenance. Skilar skránum í stafrófsröð.
    """
    summur = lesa_summur(provenance)
    if not mappa.is_dir():
        raise HledsluVilla(f"Talnamappan {stutt_slod(mappa)} er ekki til.")
    a_diski = {p.name for p in mappa.iterdir() if p.is_file()}
    vantar = sorted(set(summur) - a_diski)
    umfram = sorted(a_diski - set(summur))
    if vantar or umfram:
        raise HledsluVilla(
            f"{stutt_slod(mappa)} stemmir ekki við provenance: "
            f"vantar {vantar or 'ekkert'}, umfram {umfram or 'ekkert'}."
        )

    skrar = []
    for heiti in sorted(summur):
        baeti = (mappa / heiti).read_bytes()
        summa = hashlib.sha256(baeti).hexdigest()
        if summa != summur[heiti]:
            raise HledsluVilla(
                f"{heiti} stemmir ekki við provenance.\n"
                f"  skráð SHA-256:   {summur[heiti]}\n"
                f"  á diski SHA-256: {summa}\n"
                "Skráin er ekki lengur það sem var fryst og fer því ekki í grunninn."
            )
        skrar.append(Skra(heiti=heiti, sha256=summa, staerd=len(baeti)))
    return skrar


def lesa_csv(mappa: Path, heiti: str, dalkar: tuple[str, ...]) -> list[dict[str, str]]:
    """Les CSV-skrá og krefst nákvæmlega þessara dálka í þessari röð."""
    texti = (mappa / heiti).read_text(encoding="utf-8")
    lesari = csv.DictReader(io.StringIO(texti, newline=""))
    if tuple(lesari.fieldnames or ()) != dalkar:
        raise HledsluVilla(
            f"{heiti}: dálkarnir eru {lesari.fieldnames}, vænt {list(dalkar)}."
        )
    radir = list(lesari)
    for numer, rad in enumerate(radir, start=2):
        if None in rad or any(gildi is None for gildi in rad.values()):
            raise HledsluVilla(f"{heiti} lína {numer}: rangur fjöldi reita.")
    if not radir:
        raise HledsluVilla(f"{heiti} er tóm — engin tala til að hlaða.")
    return radir


def lesa_json(mappa: Path, heiti: str) -> dict:
    """Les JSON-skjal sem verður að vera hlutur (dict)."""
    skjal = json.loads((mappa / heiti).read_text(encoding="utf-8"))
    if not isinstance(skjal, dict):
        raise HledsluVilla(f"{heiti} er ekki JSON-hlutur.")
    return skjal
