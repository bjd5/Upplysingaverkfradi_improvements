"""Stöðugreining á mbl-síðunni (issue #23): „Reglulegar segðir á fréttasíðu“.

Almennu vefprófin (test_vefur.py, test_vefur_gogn.py) ná yfir aðskilnað,
fyrirsagnir, hooks og reiti. Hér er það sem er sérstakt fyrir þessa síðu:
að hvert svar í mbl.json eigi sér stað á síðunni og öfugt (regla 8), að engin
tala, svar eða mynstur sé harðkóðað í HTML eða JS, og að höfundarréttarmatið
á sýnishornum haldi. Vafraprófin (Chromium) eru handkeyrð.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import re
import unittest

from test_vefur import SIDUR, VEFUR, lesa

SIDA = "sidur/mbl-regex.html"
SKRIFTA = VEFUR / "assets" / "js" / "mbl-regex.js"
STILL = "assets/css/components/mynstur.css"
GAGNASKRA = VEFUR / "gogn" / "mbl.json"
TEIKNARAR = ("mbl-eintak", "mbl-svor", "mbl-mynstur")
# Fréttaslóð ber fyrirsögn fréttarinnar — höfundarréttarvarið efni.
FRETTASLOD = "/frettir/"
# Stuttar tölur (11, 43) og mynsturlínur (\s*) finnast af tilviljun í hvaða
# kóða sem er; svarstrengirnir sjálfir („11 °C“) ná yfir stuttu tölurnar.
MINNST_TALA = 4
MINNST_LINA = 8


def gagnaskra() -> dict:
    return json.loads(GAGNASKRA.read_text(encoding="utf-8"))


def islensk_tala(tala: int | float) -> str:
    """Sama snið og SiteData.formatNumber: 2188 → 2.188, 121.33 → 121,33."""
    heil, _, brot = str(tala).partition(".")
    heil = re.sub(r"\B(?=(\d{3})+(?!\d))", ".", heil)
    return heil + ("," + brot if brot and brot != "0" else "")


def greinar(html: str) -> dict[str, str]:
    """{lykill: upphafstagg} fyrir hverja mynsturgrein á síðunni."""
    return {m.group(1): m.group(0)
            for m in re.finditer(r'<article\b[^>]*data-mbl-svar="([^"]+)"[^>]*>', html)}


class SvorOgMynsturTest(unittest.TestCase):
    """Regla 8: hvert svar er tengt mynstrinu sem framkallaði það."""

    def setUp(self) -> None:
        self.html = lesa(SIDA)
        self.svor = gagnaskra()["gogn"]

    def test_hvert_svar_a_ser_eina_grein_og_ofugt(self) -> None:
        lyklar = [svar["lykill"] for svar in self.svor]
        self.assertEqual(len(lyklar), len(set(lyklar)), "tvítekinn lykill í mbl.json")
        self.assertEqual(sorted(lyklar), sorted(greinar(self.html)))

    def test_akkeri_greinar_passar_vid_lykil(self) -> None:
        for lykill, tagg in greinar(self.html).items():
            with self.subTest(lykill=lykill):
                self.assertRegex(lykill, r"^[a-z0-9-]+$")
                self.assertIn('id="svar-%s"' % lykill, tagg)

    def test_teiknararnir_eru_a_sidunni_og_skradir(self) -> None:
        skrifta = SKRIFTA.read_text("utf-8")
        for teiknari in TEIKNARAR:
            with self.subTest(teiknari=teiknari):
                self.assertIn('data-gogn-teiknari="%s"' % teiknari, self.html)
                self.assertIn('registerRenderer("%s"' % teiknari, skrifta)

    def test_hver_gagnahluti_les_mbl_json(self) -> None:
        skrar = re.findall(r'data-gogn="([^"]+)"', self.html)
        self.assertEqual(["mbl.json"] * len(TEIKNARAR), skrar)

    def test_takmarkanir_eru_birtar(self) -> None:
        self.assertIn('id="takmarkanir-titill"', self.html)
        self.assertIn('id="adferd-titill"', self.html)


class EkkertHardkodadTest(unittest.TestCase):
    """Öll svör, tölur og mynstur koma úr mbl.json gegnum gagnalagið."""

    def setUp(self) -> None:
        self.skjal = gagnaskra()
        self.skrar = {SIDA: lesa(SIDA), "mbl-regex.js": SKRIFTA.read_text("utf-8")}

    def test_engin_svor_i_html_eda_js(self) -> None:
        for svar in self.skjal["gogn"]:
            tala = islensk_tala(svar["gildi"])
            gildin = [svar["svar"], svar["spurning"]] + ([tala] if len(tala) >= MINNST_TALA else [])
            for gildi in gildin:
                for heiti, texti in self.skrar.items():
                    with self.subTest(skra=heiti, gildi=gildi):
                        self.assertFalse(gildi in texti, "harðkóðað: " + gildi)

    def test_engin_mynstur_i_html_eda_js(self) -> None:
        for svar in self.skjal["gogn"]:
            for mynstur in (svar["mynstur"], svar["afmorkun_mynstur"]):
                if not mynstur:
                    continue
                for lina in (l.strip() for l in mynstur.splitlines()):
                    if len(lina) < MINNST_LINA:
                        continue
                    for heiti, texti in self.skrar.items():
                        with self.subTest(skra=heiti, lina=lina[:30]):
                            self.assertFalse(lina in texti, "harðkóðað mynstur: " + lina)
            for heiti, texti in self.skrar.items():
                with self.subTest(skra=heiti, mynstur=svar["mynstur_heiti"]):
                    self.assertFalse(svar["mynstur_heiti"] in texti, svar["mynstur_heiti"])

    def test_engin_lysigogn_eintaksins_i_html_eda_js(self) -> None:
        eintak = self.skjal["lysigogn"]["eintak"]
        for gildi in (eintak["md5"], islensk_tala(eintak["baeti"]), eintak["sott"][:10]):
            for heiti, texti in self.skrar.items():
                with self.subTest(skra=heiti, gildi=gildi):
                    self.assertFalse(gildi in texti, "harðkóðað: " + gildi)

    def test_skriftan_les_nyja_snidid(self) -> None:
        """gogn er listi svaranna og eintakið er í lysigogn (#74)."""
        skrifta = self.skrar["mbl-regex.js"]
        self.assertIn("doc.lysigogn.eintak", skrifta)
        self.assertIn("doc.gogn.forEach", skrifta)
        self.assertNotRegex(skrifta, r"doc\.gogn\.(svor|uppruni|eintok)")

    def test_reitir_fylgja_slodavenjunni(self) -> None:
        for slod in re.findall(r'data-gogn-reitur="([^"]+)"', self.skrar[SIDA]):
            with self.subTest(slod=slod):
                self.assertTrue(slod.startswith("lysigogn.eintak."), slod)


class HofundarretturTest(unittest.TestCase):
    """Fréttatexti mbl.is birtist ekki; sýnishorn aðeins úr byggingu síðunnar."""

    def test_synishorn_adeins_i_merktum_greinum_og_stutt(self) -> None:
        skrifta = SKRIFTA.read_text("utf-8")
        hamark = int(re.search(r"const MAX_SAMPLE = (\d+);", skrifta).group(1))
        merktar = {k for k, tagg in greinar(lesa(SIDA)).items() if "data-mbl-synishorn" in tagg}
        for svar in gagnaskra()["gogn"]:
            if svar["lykill"] not in merktar:
                continue
            with self.subTest(lykill=svar["lykill"]):
                self.assertNotIn(FRETTASLOD, svar["synishorn"], "fréttaslóð ber fyrirsögn")
                self.assertLessEqual(len(svar["synishorn"]), hamark)

    def test_frettaslod_er_aldrei_merkt(self) -> None:
        merktar = {k for k, tagg in greinar(lesa(SIDA)).items() if "data-mbl-synishorn" in tagg}
        for svar in gagnaskra()["gogn"]:
            if FRETTASLOD in svar["synishorn"]:
                with self.subTest(lykill=svar["lykill"]):
                    self.assertNotIn(svar["lykill"], merktar)


class EinPerSiduTest(unittest.TestCase):
    """mynstur.css og mbl-regex.js tilheyra þessari síðu einni."""

    def test_adeins_mbl_sidan_notar_skrarnar(self) -> None:
        for sida in SIDUR:
            texti = lesa(sida)
            with self.subTest(sida=sida):
                notar = "mynstur.css" in texti or "mbl-regex.js" in texti
                self.assertEqual(sida == SIDA, notar)
        self.assertTrue((VEFUR / STILL).is_file())


if __name__ == "__main__":
    unittest.main()
