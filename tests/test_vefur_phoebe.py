"""Phoebe-síðurnar (issue #24): tölur í HTML-töflum og staðreyndalistum eru þær
sömu og í ``web/gogn/``, og fullyrðingar í texta standast gögnin.

Taflan við hvert myndrit er í HTML-inu sjálfu svo hún virki án JavaScript
(docs/myndrit.md kafli 7). Sú tala á samt að eiga sér rekjanlega leið í
gagnaskrána (regla 8): hvert reitargildi hefur ``data-reitur`` (lykill), næsta
``data-rod`` ofar (röðin, t.d. ``gogn[thattarod=1,persona=Phoebe]``) og næsta
``data-skra`` ofar (gagnaskráin). Prófið ber textann saman við gagnaskrána á
íslensku talnasniði.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser

from test_vefur import VEFUR, lesa

SIDUR = ("sidur/phoebe-tolfraedi.html", "sidur/phoebe-central-perk.html")
SIA = re.compile(r"(\w+)\[(.+)\]")
TOMIR_TAGAR = {"img", "br", "meta", "link", "input", "hr"}


def gagnaskra(heiti: str) -> dict:
    return json.loads((VEFUR / "gogn" / heiti).read_text(encoding="utf-8"))


def snid(gildi: float) -> str:
    """Íslenskt talnasnið eins og SiteData.formatNumber: 61161 → 61.161, 4.12 → 4,12."""
    if isinstance(gildi, int):
        return f"{gildi:,}".replace(",", ".")
    texti = repr(gildi)
    return (texti[:-2] if texti.endswith(".0") else texti).replace(".", ",")


def sla_upp(skjal: dict, slod: str):
    """Slóð eins og ``lysigogn.tengsl[persona=Monica]``; sía krefst nákvæmlega einnar raðar."""
    nuna = skjal
    for hluti in slod.split("."):
        sia = SIA.fullmatch(hluti)
        if not sia:
            nuna = nuna[hluti]
            continue
        skilyrdi = dict(s.split("=") for s in sia.group(2).split(","))
        radir = [r for r in nuna[sia.group(1)]
                 if all(str(r[lykill]) == gildi for lykill, gildi in skilyrdi.items())]
        if len(radir) != 1:
            raise AssertionError(f"{slod}: {len(radir)} raðir passa, á að vera ein")
        nuna = radir[0]
    return nuna


class Reitir(HTMLParser):
    """Safnar (skrá, röð, lykill, texti) fyrir hvern þátt með data-reitur."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.reitir: list[tuple[str, str, str, str]] = []
        self._stafli: list[dict] = []
        self._opinn: dict | None = None

    def _naesta(self, lykill: str) -> str | None:
        for hluti in reversed(self._stafli):
            if lykill in hluti["eig"]:
                return hluti["eig"][lykill]
        return None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in TOMIR_TAGAR:
            return
        hluti = {"tag": tag, "eig": dict(attrs), "texti": ""}
        self._stafli.append(hluti)
        if "data-reitur" in hluti["eig"]:
            self._opinn = hluti

    def handle_data(self, data: str) -> None:
        if self._opinn is not None:
            self._opinn["texti"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag in TOMIR_TAGAR or not self._stafli:
            return
        hluti = self._stafli[-1]
        if hluti is self._opinn:
            eig = hluti["eig"]
            self.reitir.append((self._naesta("data-skra"), self._naesta("data-rod"),
                                eig["data-reitur"], hluti["texti"].strip()))
            self._opinn = None
        self._stafli.pop()


class TolurAMotiGognum(unittest.TestCase):
    def test_hver_tala_i_html_er_su_sama_og_i_gagnaskranni(self) -> None:
        for sida in SIDUR:
            reitir = Reitir()
            reitir.feed(lesa(sida))
            with self.subTest(sida=sida, fjoldi=len(reitir.reitir)):
                self.assertGreater(len(reitir.reitir), 20, "síðan á að hafa töflur og tölur")
            for skra, rod, lykill, texti in reitir.reitir:
                with self.subTest(sida=sida, skra=skra, rod=rod, lykill=lykill):
                    self.assertTrue(skra and rod, "data-skra eða data-rod vantar ofar")
                    gildi = sla_upp(gagnaskra(skra), rod)[lykill]
                    self.assertEqual(texti, snid(gildi))


class FullyrdingarIText(unittest.TestCase):
    """Setningar í texta síðnanna sem tölur ná ekki yfir — prófaðar svo þær úreldist ekki."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tol = gagnaskra("phoebe-tolfraedi.json")
        cls.cp = gagnaskra("central-perk.json")

    def test_phoebe_er_i_sjotta_saeti_og_undir_jofnum_hlut_alla_thattarodina(self) -> None:
        phoebe = sla_upp(self.tol, "lysigogn.plass_alls[persona=Phoebe]")
        self.assertEqual(phoebe["saeti"], 6)
        jafn = self.tol["lysigogn"]["jafn_hlutur_prosent"]
        radir = [r for r in self.tol["gogn"] if r["persona"] == "Phoebe"]
        self.assertEqual(len(radir), 10)
        self.assertTrue(all(r["hlutdeild_prosent"] < jafn for r in radir))

    def test_tveir_vinir_tala_meira_vid_phoebe_en_malgledin_skyrir(self) -> None:
        yfir_einum = [r for r in self.tol["lysigogn"]["tengsl"] if r["lift"] > 1]
        self.assertEqual(len(yfir_einum), 2)

    def test_phoebe_syngur_i_faum_handritum_en_a_staerri_hlut(self) -> None:
        hopar = {r["hopur"]: r for r in self.cp["gogn"]}
        songur = hopar["phoebe_sings"]
        self.assertLess(songur["handrit"], min(r["handrit"] for k, r in hopar.items()
                                               if k != "phoebe_sings"))
        self.assertGreater(songur["midgildi_prosent"],
                           max(r["midgildi_prosent"] for k, r in hopar.items()
                               if k != "phoebe_sings"))
        self.assertEqual(sum(r["handrit"] for r in hopar.values()),
                         self.cp["lysigogn"]["samantekt"]["handrit"])


if __name__ == "__main__":
    unittest.main()
