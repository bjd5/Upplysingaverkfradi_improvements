"""Próf: tölurnar í HTML-töflum veðurstöðvasíðunnar stemma við vedurstodvar.json.

Taflan er í HTML-inu sjálfu svo hún virki án JavaScript (regla 3.4); því þarf
að sanna að hún fylgi útfluttu gögnunum (regla 8). Staðalsafnið eitt.
"""

from __future__ import annotations

import json
import re
import unittest

from test_vefur import lesa

SIDA = "sidur/vedurstodvar.html"


def tala(texti: str) -> int:
    return int(texti.replace(".", ""))


class VedurstodvarSidaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.html = lesa(SIDA)
        self.json = json.loads(lesa("gogn/vedurstodvar.json"))

    def lina(self, tafla_id: str) -> list[list[str]]:
        blokk = re.search(rf'id="{tafla_id}".*?</tbody>', self.html, re.DOTALL).group(0)
        return [
            [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", r)]
            for r in re.findall(r"<tr>(.*?)</tr>", blokk, re.DOTALL)[1:]
        ]

    def test_stodvataflan_stemmir_vid_json(self) -> None:
        rodin = self.lina("stodvataflan")
        gogn = self.json["gogn"]
        self.assertEqual(len(rodin), len(gogn))
        for lina, stod in zip(rodin, gogn):
            self.assertEqual(lina[0], stod["nafn"])
            self.assertEqual(int(lina[1]), stod["audkenni"])
            self.assertEqual(int(lina[2]), stod["upphafsar"])
            self.assertEqual(lina[3], "tómt" if stod["lokaar"] is None else str(stod["lokaar"]))
            self.assertEqual(lina[4], "Virk" if stod["virk"] else "Aflögð")
            self.assertEqual(tala(lina[5]), stod["metrar"])

    def test_beidnatalan_og_fjoldinn_stemma(self) -> None:
        svor = self.json["lysigogn"]["svor"]
        self.assertEqual((svor["fjoldi_allra"], svor["fjoldi_virkra"]), (778, 343))
        for beidni in self.json["lysigogn"]["beidnir"]:
            self.assertRegex(self.html, rf"<code>{re.escape(beidni['faeribreytur'])}</code>.*?>{beidni['fjoldi']}<")
        self.assertIn("778", self.html)
        self.assertIn("343", self.html)

    def test_soknardagurinn_er_ahberandi_og_i_takt_vid_json(self) -> None:
        dagur = self.json["uppfaert"][:10]
        self.assertRegex(self.html, rf'class="frosid__dagur">Sótt <time datetime="{dagur}">')
        self.assertIn("breytist", self.html)


if __name__ == "__main__":
    unittest.main()
