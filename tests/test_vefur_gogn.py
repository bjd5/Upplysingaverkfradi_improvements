"""Stöðugreining á JS-gagnalaginu (issue #19): gogn.js og gagnahluti.js.

Vafraprófin (console, án JS, 320 px, villuástand) eru handkeyrð og ekki hluti
af þessu safni, sem keyrir á staðalsafninu einu. Hér er staðfest það sem má
lesa úr skránum sjálfum: að engin síða sæki JSON með eigin kóða, að engin
innspýtingarleið sé til, að hver hook sem JS notar sé til í HTML, að hver
gagnaskrá sem HTML vísar í sé til og á réttu sniði, og að varaleið án
JavaScript fylgi hverjum gagnahluta (regla 3.4).

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser

from test_vefur import SIDUR, VEFUR, greina, lesa, stadfaera

JS = VEFUR / "assets" / "js"
GOGN = VEFUR / "gogn"
CSS = VEFUR / "assets" / "css"

KJARNI = "assets/js/gogn.js"
BIRTING = "assets/js/gagnahluti.js"
SNID_REITIR = {"uppfaert", "heimild", "gogn"}
LYSIGOGN = "lysigogn"
REITARAETUR = ("gogn", LYSIGOGN)  # sama venja og FIELD_ROOTS í gogn.js
HAMARK_LINUR = 300
HAMARK_JS_BAETI = 30_000  # öll JS samanlagt; þak reglu 3.4 er 500 KB á síðu
TOMIR_TAGAR = {"area", "base", "br", "col", "embed", "hr", "img", "input",
               "link", "meta", "source", "track", "wbr"}
INNSPYTING = re.compile(r"\.innerHTML\b|\.outerHTML\b|insertAdjacentHTML|"
                        r"document\.write|\beval\(|new Function\(")


def js_skrar() -> list:
    return sorted(JS.glob("*.js"))


def lesa_gagnaskra(heiti: str) -> dict:
    return json.loads((GOGN / heiti).read_text(encoding="utf-8"))


def fletta(gogn, slod: str):
    """Sama uppfletting og SiteData.valueAt í gogn.js (slóð frá rót skjalsins)."""
    for lykill in slod.split("."):
        if isinstance(gogn, list) and lykill.isdigit() and int(lykill) < len(gogn):
            gogn = gogn[int(lykill)]
        elif isinstance(gogn, dict) and lykill in gogn:
            gogn = gogn[lykill]
        else:
            return None
    return gogn


class Gagnahlutar(HTMLParser):
    """Safnar gagnahlutum (data-gogn) og því sem er inni í hverjum þeirra."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hlutar: list[dict] = []
        self.stada_gagna: list[str] = []
        self.eigindi: set[str] = set()
        self._stafli: list[tuple[str, dict | None]] = []

    def _nuverandi(self) -> dict | None:
        for _, hluti in reversed(self._stafli):
            if hluti is not None:
                return hluti
        return None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        eig = dict(attrs)
        self.eigindi.update(eig)
        if "data-stada-gagna" in eig:
            self.stada_gagna.append(eig["data-stada-gagna"] or "yfirlit.json")
        hluti = self._nuverandi()
        if hluti is not None:
            if "data-gogn-reitur" in eig:
                hluti["reitir"].append(eig["data-gogn-reitur"])
            if "data-gogn-efni" in eig:
                hluti["efni"].append("hidden" in eig)
            if tag == "noscript":
                hluti["noscript"] = True
        nyr = None
        if "data-gogn" in eig:
            nyr = {"skra": eig["data-gogn"], "teiknari": eig.get("data-gogn-teiknari"),
                   "reitir": [], "efni": [], "noscript": False}
            self.hlutar.append(nyr)
        if tag not in TOMIR_TAGAR:
            self._stafli.append((tag, nyr))

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self._stafli) - 1, -1, -1):
            if self._stafli[i][0] == tag:
                del self._stafli[i:]
                return


def greina_gogn(sida: str) -> Gagnahlutar:
    safnari = Gagnahlutar()
    safnari.feed(lesa(sida))
    return safnari


def skriftur(sida: str) -> list[str]:
    """Skriftur síðunnar í röð, sem slóðir frá rót web/."""
    return [stadfaera(sida, s["src"]) for s in greina(sida).skriftur]


class EinFetchTest(unittest.TestCase):
    """Skilyrði #19: engin síða sækir JSON með eigin kóða."""

    def test_adeins_gogn_js_kallar_i_fetch(self) -> None:
        for skra in js_skrar():
            with self.subTest(skra=skra.name):
                fjoldi = len(re.findall(r"\bfetch\(", skra.read_text("utf-8")))
                if skra.name == "gogn.js":
                    self.assertEqual(1, fjoldi)
                else:
                    self.assertEqual(0, fjoldi, "sækir gögn framhjá gogn.js")


class InnspytingTest(unittest.TestCase):
    """Gagnaskrá má aldrei verða innspýtingarleið: aðeins createElement/textContent."""

    def test_ekkert_innerhtml_eda_eval(self) -> None:
        for skra in js_skrar():
            with self.subTest(skra=skra.name):
                texti = re.sub(r"/\*.*?\*/", "", skra.read_text("utf-8"), flags=re.DOTALL)
                self.assertEqual([], INNSPYTING.findall(texti))


class SkriftuRodTest(unittest.TestCase):
    """defer heldur röð skriftanna; lagið verður að koma á undan notendum sínum."""

    def test_notendur_lagsins_koma_a_eftir_thvi(self) -> None:
        for sida in SIDUR:
            rod = skriftur(sida)
            for i, slod in enumerate(rod):
                texti = (VEFUR / slod).read_text("utf-8")
                with self.subTest(sida=sida, skrifta=slod):
                    if "SiteData" in texti and slod != KJARNI:
                        self.assertIn(KJARNI, rod[:i], "gogn.js vantar á undan")
                    if "DataSection" in texti and slod != BIRTING:
                        self.assertIn(BIRTING, rod[:i], "gagnahluti.js vantar á undan")

    def test_sidur_med_gagnahluta_hlada_laginu(self) -> None:
        for sida in SIDUR:
            safnari = greina_gogn(sida)
            if safnari.hlutar or safnari.stada_gagna:
                with self.subTest(sida=sida):
                    rod = skriftur(sida)
                    self.assertIn(KJARNI, rod)
                    self.assertIn(BIRTING, rod)
                    self.assertLess(rod.index(KJARNI), rod.index(BIRTING))


class GagnaskrarTest(unittest.TestCase):
    """Hver gagnaskrá sem HTML vísar í er til og á sniði reglu 5.4."""

    def _visad_i(self) -> set[str]:
        skrar = set()
        for sida in SIDUR:
            safnari = greina_gogn(sida)
            skrar.update(h["skra"] for h in safnari.hlutar)
            skrar.update(safnari.stada_gagna)
        return skrar

    def test_skrarnar_eru_til_og_a_rettu_snidi(self) -> None:
        skrar = self._visad_i()
        self.assertIn("skjalftar.json", skrar, "sýnidæmið vantar")
        for heiti in skrar:
            with self.subTest(skra=heiti):
                self.assertNotIn("/", heiti, "slóðin er afstæð frá gogn/, ekki síðunni")
                self.assertTrue((GOGN / heiti).is_file(), "gagnaskráin er ekki til")
                skjal = lesa_gagnaskra(heiti)
                self.assertLessEqual(SNID_REITIR, set(skjal))
                self.assertLessEqual(set(skjal), SNID_REITIR | {LYSIGOGN},
                                     "óþekktur reitur — gogn.js hafnar skránni")
                self.assertIsInstance(skjal["gogn"], list)
                self.assertTrue(all(isinstance(r, dict) for r in skjal["gogn"]),
                                "gogn verður að vera listi af röðum")
                if LYSIGOGN in skjal:
                    self.assertIsInstance(skjal[LYSIGOGN], dict)

    def test_yfirlitid_visar_a_skrar_sem_eru_til(self) -> None:
        for faersla in lesa_gagnaskra("yfirlit.json")["gogn"]:
            with self.subTest(skra=faersla["skra"]):
                self.assertTrue((GOGN / faersla["skra"]).is_file())
                self.assertTrue((VEFUR / faersla["sida"]).is_file())

    def test_hver_reitur_er_tala_eda_strengur_i_skranni(self) -> None:
        for sida in SIDUR:
            for hluti in greina_gogn(sida).hlutar:
                skjal = lesa_gagnaskra(hluti["skra"])
                for slod in hluti["reitir"]:
                    with self.subTest(sida=sida, reitur=slod):
                        self.assertIn(slod.split(".")[0], REITARAETUR,
                                      "slóð reits byrjar á lysigogn. eða gogn.")
                        gildi = fletta(skjal, slod)
                        self.assertIsInstance(gildi, (int, float, str))
                        self.assertNotIsInstance(gildi, bool)


class AnJavascriptTest(unittest.TestCase):
    """Regla 3.4: gagnahluti er læsilegur án JS og sýnir aldrei auða reiti."""

    def test_hver_gagnahluti_hefur_varaleid(self) -> None:
        for sida in SIDUR:
            for hluti in greina_gogn(sida).hlutar:
                with self.subTest(sida=sida, skra=hluti["skra"]):
                    self.assertTrue(hluti["noscript"], "<noscript> vantar í hlutann")

    def test_efni_er_falid_thar_til_js_fyllir_thad(self) -> None:
        for sida in SIDUR:
            for hluti in greina_gogn(sida).hlutar:
                with self.subTest(sida=sida, skra=hluti["skra"]):
                    self.assertTrue(all(hluti["efni"]), "data-gogn-efni án hidden")
                    if hluti["reitir"]:
                        self.assertTrue(hluti["efni"], "reitir utan data-gogn-efni")


class HooksTest(unittest.TestCase):
    """Hver hook sem JS notar er til í HTML, og hver klasi sem JS býr til í CSS."""

    def test_valdir_hooks_eru_til_i_html(self) -> None:
        eigindi = set()
        for sida in SIDUR:
            eigindi |= greina_gogn(sida).eigindi
        for skra in js_skrar():
            texti = skra.read_text("utf-8")
            # Valkvæður hook sem skriftan býr til sjálf ef hann vantar er undanþeginn.
            buinn_til = {"data-" + re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), k)
                         for k in re.findall(r"\.dataset\.(\w+) = ", texti)}
            for hook in set(re.findall(r"\[(data-[a-z-]+)", texti)) - buinn_til:
                with self.subTest(skra=skra.name, hook=hook):
                    self.assertIn(hook, eigindi)

    def test_teiknarar_eru_skradir(self) -> None:
        for sida in SIDUR:
            rod = skriftur(sida)
            skrad = set()
            for slod in rod:
                skrad |= set(re.findall(r'registerRenderer\("([\w-]+)"',
                                        (VEFUR / slod).read_text("utf-8")))
            for hluti in greina_gogn(sida).hlutar:
                if hluti["teiknari"]:
                    with self.subTest(sida=sida, teiknari=hluti["teiknari"]):
                        self.assertIn(hluti["teiknari"], skrad)

    def test_klasar_sem_js_byr_til_eru_i_css(self) -> None:
        css = "".join(p.read_text("utf-8") for p in CSS.rglob("*.css"))
        for skra in js_skrar():
            texti = skra.read_text("utf-8")
            klasar = re.findall(r'element\("\w+", "([a-z_-]+)"', texti)
            klasar += re.findall(r'className = "([a-z_-]+)"', texti)
            for klasi in klasar:
                with self.subTest(skra=skra.name, klasi=klasi):
                    self.assertIn("." + klasi, css)


class FrammistadaTest(unittest.TestCase):
    """Regla 3.4 og 6: litlar skrár, eitt hlutverk hver."""

    def test_js_skrar_eru_litlar(self) -> None:
        samtals = 0
        for skra in js_skrar():
            with self.subTest(skra=skra.name):
                texti = skra.read_text("utf-8")
                self.assertLessEqual(len(texti.splitlines()), HAMARK_LINUR)
                samtals += len(texti.encode("utf-8"))
        self.assertLessEqual(samtals, HAMARK_JS_BAETI)


if __name__ == "__main__":
    unittest.main()
