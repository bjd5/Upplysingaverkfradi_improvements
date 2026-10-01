"""Prófar að tölurnar sem standa í HTML Skjálftavaktarinnar séu þær sömu og í gagnaskránni.

Taflan undir myndritinu er í HTML-inu sjálfu svo hún virki án JavaScript
(docs/myndrit.md). Hún er því ekki afleidd sjálfkrafa — þetta próf er
trygging reglu 8: hver tala á síðunni á sér rekjanlega leið í web/gogn/.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""

from __future__ import annotations

import html
import json
import re
import unittest

from test_vefur import VEFUR, lesa

SIDA = "sidur/skjalftavaktin.html"
GOGN = VEFUR / "gogn" / "skjalftar.json"
MANADARSTYTTINGAR = ("jan.", "feb.", "mars", "apr.", "maí", "jún.", "júl.", "ág.",
                     "sep.", "okt.", "nóv.", "des.")
LINA = re.compile(r"<tr><td>(.*?)</td><td(?: class=\"myndrit__null\")?>(.*?)</td></tr>")
ALT = re.compile(r'<img class="myndrit__mynd"[^>]*?alt="([^"]*)"', re.DOTALL)


def _dagsetning(iso: str) -> str:
    ar, manudur, dagur = iso.split("-")
    return f"{int(dagur)}. {MANADARSTYTTINGAR[int(manudur) - 1]} {ar}"


class TaflaUndirMyndritiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gogn = json.loads(GOGN.read_text("utf-8"))["gogn"]
        cls.sida = lesa(SIDA)

    def test_taflan_er_sama_og_dagalistinn_i_gagnaskranni(self) -> None:
        lesid = [(d, html.unescape(n)) for d, n in LINA.findall(self.sida)]
        vaent = [
            (_dagsetning(d["dagur"]),
             "0 — enginn atburður" if d["fjoldi"] == 0 else f"{d['fjoldi']:,}".replace(",", "."))
            for d in self.gogn["dagar"]
        ]
        self.assertEqual(lesid, vaent)

    def test_nulldagar_eru_merktir_med_ordum_en_ekki_lit_einum(self) -> None:
        nulldagar = sum(1 for d in self.gogn["dagar"] if d["fjoldi"] == 0)
        self.assertEqual(self.sida.count("0 — enginn atburður"), nulldagar)
        self.assertEqual(nulldagar, self.gogn["samantekt"]["dagar_an_atburda"])

    def test_alt_textinn_nefnir_tolur_ur_gagnaskranni(self) -> None:
        alt = ALT.search(self.sida).group(1)
        samantekt = self.gogn["samantekt"]
        for tala in (samantekt["daglegur_fjoldi"]["hamark"], samantekt["dagar_an_atburda"],
                     samantekt["dagar"]):
            with self.subTest(tala=tala):
                self.assertRegex(alt, rf"\b{tala}\b")


if __name__ == "__main__":
    unittest.main()
