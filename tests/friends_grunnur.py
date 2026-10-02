"""Sameiginleg hjálp fyrir Friends-hleðsluprófin (issue #10).

* ``vidmid_gildi`` flettir staðfestri tölu upp í ``docs/vidmid/vidmid.json``
  eftir heiti hennar. Tölurnar eru **lesnar** þaðan, aldrei handskrifaðar í
  prófin, og hver uppfletting krefst nákvæmlega einnar samsvörunar — tvær
  samsvaranir gerðu það tvírætt hvaða tala er borin saman.
* ``vidmid_aukastafir`` segir á hve mörgum aukastöfum kommutala er borin
  saman: þeim sem gamla síðan sýndi. Vikmörk (``delta``) hleypa nágrönnum í gegn.
* ``Afrit`` er tímabundið afrit af talnamöppunni og provenance-skránni.
  Prófin sem þurfa gallaða skrá skemma afritið, aldrei frumritin (regla 10),
  og geta „endurundirritað“ afritið svo SHA-staðfestingin hleypi gallanum
  áfram til næsta varnarlags.

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py``.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path
from hjalp import ROT

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from vinnsla.friends_skrar import PROVENANCE, SAFN, STATS_MAPPA  # noqa: E402

VIDMID = ROT / "docs" / "vidmid" / "vidmid.json"
# Íslensk tugabrot: komma og svo aukastafirnir („2,95 %“, „61.161“ hefur enga).
AUKASTAFIR = re.compile(r",(\d+)")


def vidmid_gildi(heiti: str, stadfestar: list[dict] | None = None) -> float | int:
    """Staðfesta talan með þessu heiti; nákvæmlega ein samsvörun eða villa."""
    if stadfestar is None:
        stadfestar = json.loads(VIDMID.read_text(encoding="utf-8"))["stadfestar"]
    samsvaranir = [s for s in stadfestar if s["heiti"] == heiti]
    if len(samsvaranir) != 1:
        raise AssertionError(
            f"{heiti!r} á {len(samsvaranir)} samsvaranir í vidmid.json, ekki eina."
        )
    return samsvaranir[0]["gildi"]


def vidmid_aukastafir(heiti: str) -> int:
    """Aukastafir tölunnar eins og gamla síðan birti hana („2,95 %“ -> 2).

    Lesið úr textanum á síðunni, ekki úr fleytitölunni: JSON geymir 2,90 sem
    2.9 og týnir aukastaf. Allir staðir tölunnar í HTML-inu verða að sýna
    jafnmarga aukastafi, og tala sem stendur hvergi þar er villa.
    """
    skjal = json.loads(VIDMID.read_text(encoding="utf-8"))
    (stadfest,) = [s for s in skjal["stadfestar"] if s["heiti"] == heiti]
    textar = [r["texti"] for r in skjal["gogn"] if r["id"] in stadfest["stadir_i_html"]]
    fjoldi = {len(m.group(1)) if (m := AUKASTAFIR.search(t)) else 0 for t in textar}
    if len(textar) != len(stadfest["stadir_i_html"]) or len(fjoldi) != 1:
        raise AssertionError(f"{heiti!r}: aukastafir ekki ótvíræðir í {textar}.")
    return fjoldi.pop()


def opna_med_toflum(mappa: Path):
    """Tómur grunnur í ``mappa`` með öllum migrations keyrðum."""
    samband = opna(mappa / "friends.sqlite")
    keyra(samband)
    return samband


class Afrit:
    """Tímabundið afrit af talnamöppunni og provenance, til að skemma."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.mappa = self.rot / "phoebe-stats"
        shutil.copytree(STATS_MAPPA, self.mappa)
        self.provenance = self.rot / "provenance.json"
        shutil.copy2(PROVENANCE, self.provenance)

    def loka(self) -> None:
        self._tmp.cleanup()

    def lesa(self, heiti: str) -> str:
        """Innihald skrárinnar með línuskilum óbreyttum (CSV-skrárnar nota CRLF)."""
        with (self.mappa / heiti).open(encoding="utf-8", newline="") as skra:
            return skra.read()

    def skrifa(self, heiti: str, texti: str, undirrita: bool = True) -> None:
        """Skrifar skrá í afritið; ``undirrita`` uppfærir summuna í provenance."""
        (self.mappa / heiti).write_text(texti, encoding="utf-8", newline="")
        if undirrita:
            self.undirrita(heiti)

    def undirrita(self, heiti: str) -> None:
        """Setur SHA-256 skrárinnar eins og hún er nú í provenance-afritið."""
        skjal = json.loads(self.provenance.read_text(encoding="utf-8"))
        summa = hashlib.sha256((self.mappa / heiti).read_bytes()).hexdigest()
        fundid = 0
        for safn in skjal["sofn"]:
            if safn["heiti"] != SAFN:
                continue
            for skra in safn["skrar"]:
                if Path(skra["slod"]).name == heiti:
                    skra["sha256"] = summa
                    fundid += 1
        if fundid != 1:
            raise AssertionError(f"{heiti} fannst {fundid} sinnum í provenance-afritinu.")
        self.provenance.write_text(json.dumps(skjal, ensure_ascii=False), encoding="utf-8")
