"""Sameiginleg hjálp fyrir Central Perk-hleðsluprófin (issue #10).

* ``vidmidstala`` flettir tölu gömlu Central Perk-síðunnar upp í
  ``docs/vidmid/vidmid.json`` (``gogn``) eftir töflulínu og dálki, eða eftir
  textanum í inngangsmálsgreininni. Hver uppfletting krefst **nákvæmlega
  einnar** samsvörunar; tölurnar eru lesnar þaðan, aldrei handskrifaðar.
* ``Afrit`` er tímabundið afrit af frosnu skránum þremur og provenance, til að
  skemma í bresta-prófunum — aldrei frumritin (regla 10).
* ``OTENGD_FORSKEYTI``: tímabundin undanþága í heildarprófunum þar til
  hleðslan er tengd ``keyrsla/hledsla.py`` (bíður P2.7, #15). Prófið
  ``test_undanthagan_fellur_thegar_tengt`` fellur um leið og safnið bætist í
  ``SOFN`` — þá á að fjarlægja undanþáguna.

Hjálpareining, ekki prófskrá.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path
from hjalp import ROT

from vinnsla.central_perk_adfang import ADFANGSMAPPA, PROVENANCE, SAFN, SKRAR  # noqa: E402

VIDMID = ROT / "docs" / "vidmid" / "vidmid.json"
SIDA = "phoebe-central-perk.html"
INNGANGUR = "Phoebe syngur samkvæmt skýrum sviðslýsingum"
SONGLISTI = "Handritin með skýrt Phoebe-söngtilvik"
OTENGD_FORSKEYTI = "central_perk_"
SAFNSHEITI = "Central Perk"


def _gogn() -> list[dict]:
    return [g for g in json.loads(VIDMID.read_text(encoding="utf-8"))["gogn"]
            if g["sida"] == SIDA]


def _ein(samsvaranir: list[dict], lysing: str) -> dict:
    if len(samsvaranir) != 1:
        raise AssertionError(f"{lysing} á {len(samsvaranir)} samsvaranir í vidmid.json, ekki eina.")
    return samsvaranir[0]


def vidmidstala(lina: str, dalkur: str) -> float | int:
    """Tala úr samanburðartöflunni: töflulína (hópur) og dálkur."""
    return _ein([g for g in _gogn() if g["flokkur"] == "tafla"
                 and g["lina"] == lina and g["sulka"] == dalkur],
                f"{lina} / {dalkur}")["gildi"]


def inngangstala(texti: str) -> float | int:
    """Tala úr niðurstöðumálsgreininni, eftir birtum texta hennar (t.d. ``18,6%``)."""
    return _ein([g for g in _gogn() if g["flokkur"] == "malsgrein"
                 and g["samhengi"].startswith(INNGANGUR) and g["texti"] == texti],
                f"inngangur {texti!r}")["gildi"]


def songhandrit() -> list[str]:
    """Sönghandritin sem síðan taldi upp, í birtingarröð."""
    return [g["texti"] for g in _gogn() if g["samhengi"].startswith(SONGLISTI)]


class Afrit:
    """Tímabundið afrit af frosnu skránum og provenance, til að skemma."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.mappa = self.rot / "generated"
        self.mappa.mkdir()
        for heiti in SKRAR:
            shutil.copy2(ADFANGSMAPPA / heiti, self.mappa / heiti)
        self.provenance = self.rot / "provenance.json"
        shutil.copy2(PROVENANCE, self.provenance)

    def loka(self) -> None:
        self._tmp.cleanup()

    def lesa(self, heiti: str) -> str:
        with (self.mappa / heiti).open(encoding="utf-8", newline="") as skra:
            return skra.read()

    def skipta(self, heiti: str, gamalt: str, nytt: str, undirrita: bool = True,
               fjoldi: int = 1) -> None:
        """Skiptir ``gamalt`` út (verður að finnast) og endurundirritar að vild."""
        texti = self.lesa(heiti)
        if gamalt not in texti:
            raise AssertionError(f"{gamalt!r} finnst ekki í {heiti}.")
        (self.mappa / heiti).write_text(texti.replace(gamalt, nytt, fjoldi),
                                        encoding="utf-8", newline="")
        if undirrita:
            self.undirrita(heiti)

    def undirrita(self, heiti: str) -> None:
        """Setur SHA-256 skrárinnar eins og hún er nú í provenance-afritið."""
        skjal = json.loads(self.provenance.read_text(encoding="utf-8"))
        summa = hashlib.sha256((self.mappa / heiti).read_bytes()).hexdigest()
        fundid = 0
        for safn in skjal["sofn"]:
            if safn["heiti"] == SAFN:
                for skra in safn["skrar"]:
                    if Path(skra["slod"]).name == heiti:
                        skra["sha256"] = summa
                        fundid += 1
        if fundid != 1:
            raise AssertionError(f"{heiti} fannst {fundid} sinnum í provenance-afritinu.")
        self.provenance.write_text(json.dumps(skjal, ensure_ascii=False), encoding="utf-8")
