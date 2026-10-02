"""Stöðugreining á Veðurstöðvasíðunni (issue #22).

Staðfestir það sem má lesa úr skránum sjálfum: að hver tala á síðunni komi úr
web/gogn/vedurstodvar.json gegnum gagnalagið (engin slegin inn), að síðusértæku
hooks vísi á rétta tegund gildis eftir slóðavenjunni (lysigogn. / gogn.), að
sóknardagurinn standi efst, að staða stöðvar sé í orðum og með tákni, og að
gagnaskráin sjálf sé innbyrðis samkvæm (fjöldinn stemmir við frosna svarið).

Vafraprófin (console, 320 px, án JS, Tab-rötun) eru handkeyrð í Chromium.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""
from __future__ import annotations

import html
import re
import unittest

from test_vefur import VEFUR, lesa
from test_vefur_gogn import fletta, greina_gogn, lesa_gagnaskra, skriftur

SIDA = "sidur/vedurstodvar.html"
SKRA = "vedurstodvar.json"
SIDUSKRA = "assets/js/vedurstodvar.js"
RAETUR = ("lysigogn.", "gogn.")
# Einu tölustafirnir sem mega standa fastir í efninu: stöðukóðinn í
# athugasemdinni um að HTTP 200 þýði ekki að sían hafi virkað.
LEYFDAR_TOLUR = {"200"}
HOOK = re.compile(r'data-vedur-(texti|janei|stada)="([^"]*)"')


def efni() -> str:
    return re.search(r"<main\b.*?</main>", lesa(SIDA), re.DOTALL).group(0)


def hooks() -> list[tuple[str, str]]:
    return HOOK.findall(lesa(SIDA))


class SlodirTest(unittest.TestCase):
    """Síðusértæku hooks fylgja sömu slóðavenju og data-gogn-reitur."""

    def setUp(self) -> None:
        self.skjal = lesa_gagnaskra(SKRA)

    def test_hooks_eru_til(self) -> None:
        tegundir = {tegund for tegund, _ in hooks()}
        self.assertEqual(tegundir, {"texti", "janei", "stada"})
        self.assertIn("data-vedur-sott", lesa(SIDA))

    def test_slodir_byrja_a_rot(self) -> None:
        for tegund, slod in hooks():
            with self.subTest(tegund=tegund, slod=slod):
                self.assertTrue(slod.startswith(RAETUR), slod)

    def test_texti_er_heiltala_eda_strengur(self) -> None:
        for tegund, slod in hooks():
            if tegund == "texti":
                with self.subTest(slod=slod):
                    gildi = fletta(self.skjal, slod)
                    self.assertIsInstance(gildi, (int, str))
                    self.assertNotIsInstance(gildi, bool)

    def test_janei_er_satt_eda_osatt(self) -> None:
        for tegund, slod in hooks():
            if tegund == "janei":
                with self.subTest(slod=slod):
                    self.assertIsInstance(fletta(self.skjal, slod), bool)

    def test_stada_visar_a_stod(self) -> None:
        for tegund, slod in hooks():
            if tegund == "stada":
                with self.subTest(slod=slod):
                    stod = fletta(self.skjal, slod)
                    self.assertIsInstance(stod, dict)
                    self.assertIn("lokaar", stod)
                    self.assertIn("nafn", stod)


class EngarSlegnarTolurTest(unittest.TestCase):
    """Regla 8: hver tala á síðunni kemur úr gagnaskránni."""

    def test_engir_tolustafir_i_fostum_texta(self) -> None:
        texti = re.sub(r"<code>.*?</code>", "", efni(), flags=re.DOTALL)
        texti = html.unescape(re.sub(r"<[^>]+>", " ", texti))
        tolur = set(re.findall(r"\d+(?:[.,]\d+)*", texti)) - LEYFDAR_TOLUR
        self.assertEqual(tolur, set())

    def test_allir_hlutar_lesa_somu_skra_gegnum_lagid(self) -> None:
        hlutar = greina_gogn(SIDA).hlutar
        self.assertGreaterEqual(len(hlutar), 5)
        for hluti in hlutar:
            with self.subTest(teiknari=hluti["teiknari"]):
                self.assertEqual(hluti["skra"], SKRA)
                self.assertTrue(hluti["noscript"])

    def test_teiknararnir_eru_i_siduskranni(self) -> None:
        self.assertEqual(skriftur(SIDA)[-1], SIDUSKRA)
        skrad = set(re.findall(r'registerRenderer\("([\w-]+)"',
                               (VEFUR / SIDUSKRA).read_text("utf-8")))
        notad = {h["teiknari"] for h in greina_gogn(SIDA).hlutar}
        self.assertLessEqual(notad, skrad)
        self.assertIn("vedurstodvar-stodvar", notad)
        self.assertIn("vedurstodvar-beidnir", notad)


class FrosidEintakTest(unittest.TestCase):
    """Sérkrafa #22: lesandinn má ekki halda að hann sjái lifandi stöðu."""

    def test_sokardagur_stendur_a_undan_fyrirsogninni(self) -> None:
        sida = lesa(SIDA)
        self.assertLess(sida.index("data-vedur-sott"), sida.index("<h1"))
        self.assertLess(sida.index("Frosið eintak"), sida.index("<h1"))

    def test_fyrirvarinn_stendur_an_javascript(self) -> None:
        # Fyrirvarinn er utan data-gogn-efni, svo hann hverfur ekki án JS.
        fyrirvari = re.search(r'<p class="vedur-fyrirvari">(.*?)</p>', lesa(SIDA),
                              re.DOTALL)
        self.assertIsNotNone(fyrirvari)
        self.assertIn("breytist", fyrirvari.group(1))

    def test_takmarkanir_og_fravik_birt(self) -> None:
        self.assertIn("Takmarkanir og frávik frá gömlu síðunni", efni())
        self.assertIn("Ný söfnun, ekki afrit", efni())


class StadaIOrdumTest(unittest.TestCase):
    """Regla 3.3: virk/aflögð er aldrei aðeins litur."""

    def test_stada_hefur_ord_og_takn(self) -> None:
        js = (VEFUR / SIDUSKRA).read_text("utf-8")
        for texti in ("✓ Virk", "✕ Aflögð"):
            with self.subTest(texti=texti):
                self.assertIn(texti, js)

    def test_sulan_er_falin_skjalesurum(self) -> None:
        js = (VEFUR / SIDUSKRA).read_text("utf-8")
        self.assertIn('setAttribute("aria-hidden", "true")', js)


class GagnaskraSamkvaemTest(unittest.TestCase):
    """Fjöldinn á síðunni stemmir við frosna svarið (skilyrði #22)."""

    def setUp(self) -> None:
        skjal = lesa_gagnaskra(SKRA)
        self.stodvar = skjal["gogn"]
        self.lysi = skjal["lysigogn"]
        self.beidnir = {b["faeribreytur"]: b["fjoldi"] for b in self.lysi["beidnir"]}

    def test_stodvar_i_toflunni_eru_polygon_svarid(self) -> None:
        self.assertEqual(len(self.stodvar), self.beidnir["polygon"])

    def test_virkar_i_kassanum_eru_polygon_og_active(self) -> None:
        virkar = [s for s in self.stodvar if s["lokaar"] is None]
        self.assertEqual(len(virkar), self.beidnir["polygon + active=true"])

    def test_virk_er_tomt_lokaar(self) -> None:
        for stod in self.stodvar:
            with self.subTest(stod=stod["audkenni"]):
                self.assertEqual(stod["virk"], stod["lokaar"] is None)

    def test_radad_eftir_fjarlaegd(self) -> None:
        metrar = [s["metrar"] for s in self.stodvar]
        self.assertEqual(metrar, sorted(metrar))

    def test_svorin_eru_fyrstu_stodvarnar_i_rodinni(self) -> None:
        svor = self.lysi["svor"]
        fyrsta_virka = next(s for s in self.stodvar if s["lokaar"] is None)
        fyrsta_aflagda = next(s for s in self.stodvar if s["lokaar"] is not None)
        self.assertEqual(svor["naesta_virka"]["audkenni"], fyrsta_virka["audkenni"])
        self.assertEqual(svor["naesta_aflagda"]["audkenni"], fyrsta_aflagda["audkenni"])
        self.assertEqual(svor["munur_metrar"],
                         abs(fyrsta_aflagda["metrar"] - fyrsta_virka["metrar"]))

    def test_heildarfjoldi_stemmir(self) -> None:
        svor = self.lysi["svor"]
        self.assertEqual(svor["fjoldi_allra"], self.beidnir["engin sía"])
        self.assertEqual(svor["fjoldi_allra"], self.lysi["sokn"]["fjoldi_stodva"])
        self.assertEqual(svor["fjoldi_virkra"], self.beidnir["active=true"])
        self.assertEqual(svor["fjoldi_virkra"] + svor["fjoldi_aflagdra"],
                         svor["fjoldi_allra"])


if __name__ == "__main__":
    unittest.main()
