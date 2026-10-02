"""Stöðugreining á Hagstofusíðunni (issue #21).

Almennu reglurnar (aðskilnaður, reitir sem vísa á tölur, noscript, hooks) eru
prófaðar í test_vefur.py og test_vefur_gogn.py. Hér er það sem er sérstakt
fyrir þessa síðu: að engin niðurstöðutala sé harðkóðuð, að fastar raðir sem
reitir vísa í séu raðirnar sem textinn segir, að JS námundi ekki og að
takmarkanirnar standi á síðunni (regla 8).

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import re
import unittest

from test_vefur import VEFUR, lesa
from test_vefur_gogn import fletta, greina_gogn

SIDA = "sidur/hagstofan.html"
SKRA = "hagstofan.json"
JS = VEFUR / "assets" / "js" / "hagstofan.js"
STODUREITIR = ("brautskradir", "brottfallnir", "enn_i_nami")
# Tölur sem síðan nefnir af ásettu ráði í föstum texta: summa flokkanna og
# frávikin sem námundun getur valdið (takmörkun sem regla 8 krefst að sé birt).
LEYFDAR_I_TEXTA = {"100", "99,9", "100,1"}


def skjal() -> dict:
    return json.loads((VEFUR / "gogn" / SKRA).read_text(encoding="utf-8"))


def snid(gildi: float) -> str:
    """Sama snið og SiteData.formatNumber fyrir tölur undir þúsund."""
    return (str(int(gildi)) if float(gildi).is_integer() else str(gildi)).replace(".", ",")


def reitir() -> list[str]:
    return [r for h in greina_gogn(SIDA).hlutar for r in h["reitir"]]


def html_texti() -> str:
    """Sýnilegur texti síðunnar, án eiginda (slóðir í reitum eru ekki efni)."""
    return re.sub(r"<[^>]+>", " ", lesa(SIDA))


class GagnahlutiTest(unittest.TestCase):
    def test_sidan_les_hagstofuskrana_med_teiknara(self) -> None:
        hlutar = greina_gogn(SIDA).hlutar
        self.assertEqual([SKRA], [h["skra"] for h in hlutar])
        self.assertEqual("hagstofan", hlutar[0]["teiknari"])
        self.assertIn('registerRenderer("hagstofan"', JS.read_text("utf-8"))

    def test_toflustadir_i_html_og_js_stemma(self) -> None:
        i_html = set(re.findall(r'data-hagstofan-tafla="([a-z]+)"', lesa(SIDA)))
        i_js = set(re.findall(r'slot\(root, "([a-z]+)"\)', JS.read_text("utf-8")))
        self.assertEqual(i_html, i_js)
        self.assertEqual(5, len(i_html))


class EngarHardkodadarTolurTest(unittest.TestCase):
    """Sérhver niðurstöðutala kemur úr gagnaskránni, aldrei úr HTML eða JS."""

    def _nidurstodutolur(self) -> set[str]:
        gogn = skjal()
        tolur = {snid(rod[r]) for rod in gogn["gogn"] for r in STODUREITIR + ("samtals",)}
        tolur |= {snid(m["prosentustig"]) for m in gogn["lysigogn"]["munir"]}
        tolur.add(gogn["lysigogn"]["afmorkun"][0]["kodi"])  # innritunarárið
        return tolur - LEYFDAR_I_TEXTA

    def test_engin_nidurstodutala_i_html(self) -> None:
        texti = html_texti()
        for tala in self._nidurstodutolur():
            with self.subTest(tala=tala):
                self.assertIsNone(re.search(r"(?<![\d,])" + re.escape(tala) + r"(?![\d,])", texti))

    def test_engin_nidurstodutala_i_js(self) -> None:
        texti = re.sub(r"/\*.*?\*/", "", JS.read_text("utf-8"), flags=re.DOTALL)
        for tala in self._nidurstodutolur():
            with self.subTest(tala=tala):
                self.assertNotIn('"' + tala + '"', texti)
                self.assertIsNone(re.search(r"(?<![\w.])" + re.escape(tala.replace(",", "."))
                                            + r"(?![\w.])", texti))

    def test_js_namundar_ekki_og_fyllir_ekki_upp(self) -> None:
        texti = JS.read_text("utf-8")
        for bannad in ("toFixed", "toPrecision", "Math.round", "Math.floor", "Math.ceil",
                       "padEnd", "padStart", "maximumFractionDigits"):
            with self.subTest(bannad=bannad):
                self.assertNotIn(bannad, texti)


class FastarRadirTest(unittest.TestCase):
    """gogn.<n> í reit er aðeins leyft þegar röðin er föst — hér er staðfest hver hún er."""

    def test_fastar_radir_eru_thaer_sem_textinn_segir(self) -> None:
        gogn = skjal()
        vaentanlegt = {
            "gogn.0": {"namssvid_kodi": "Alls", "kyn_kodi": "Alls"},
            "gogn.10": {"namssvid_kodi": "07", "kyn_kodi": "1"},
            "gogn.11": {"namssvid_kodi": "07", "kyn_kodi": "2"},
            "lysigogn.afmorkun.0": {"vidd": "Innritunarár"},
            "lysigogn.afmorkun.1": {"vidd": "Tími", "kodi": "n+3"},
            "lysigogn.munir.1": {"lysing": "Konur miðað við karla í verkfræði"},
            "lysigogn.munir.2": {"lysing": "Konur miðað við karla á öllum sviðum"},
        }
        for slod in vaentanlegt:
            with self.subTest(slod=slod):
                self.assertTrue(any(r.startswith(slod + ".") for r in reitir()),
                                "reiturinn er ekki lengur á síðunni")
                rod = fletta(gogn, slod)
                for lykill, gildi in vaentanlegt[slod].items():
                    self.assertEqual(gildi, rod[lykill])

    def test_lykiltolur_fylgja_stodunum_i_rod(self) -> None:
        stodur = skjal()["lysigogn"]["stodur"]
        for i, reitur in enumerate(STODUREITIR):
            with self.subTest(reitur=reitur):
                self.assertEqual(reitur, stodur[i]["reitur"])
                self.assertIn("gogn.0." + reitur, reitir())
                self.assertIn(f"lysigogn.stodur.{i}.heiti", reitir())

    def test_daemid_i_js_er_valid_i_fyrirspurninni(self) -> None:
        texti = JS.read_text("utf-8")
        daemi = dict(re.findall(r'"([^"]+)": "([^"]+)"',
                                re.search(r"const EXAMPLE = \{(.*?)\};", texti).group(1)))
        viddir = {v["kodi"]: v for v in skjal()["lysigogn"]["viddir"]}
        for vidd, kodi in daemi.items():
            with self.subTest(vidd=vidd):
                valid = [g["kodi"] for g in viddir[vidd]["gildi"] if g["valid"]]
                self.assertIn(kodi, valid)


class AdgengiOgHeidarleikiTest(unittest.TestCase):
    def test_radafyrirsagnir_og_munur_ekki_i_lit_einum(self) -> None:
        texti = JS.read_text("utf-8")
        self.assertIn('th.scope = "row"', texti)
        for merki in ("▲", "▼", "hærri", "lægri"):
            with self.subTest(merki=merki):
                self.assertIn(merki, texti)

    def test_takmarkanir_birtar(self) -> None:
        texti = html_texti()
        for krafa in ("Takmarkanir", "Leyfi óstaðfest", "99,9", "100,1", "n+3",
                      "Prósentur, ekki fjöldi", "Einn árgangur"):
            with self.subTest(krafa=krafa):
                self.assertIn(krafa, texti)

    def test_nidurstadan_a_undan_adferdinni(self) -> None:
        texti = lesa(SIDA)
        self.assertLess(texti.index('id="nidurstada-titill"'), texti.index('id="adferd-titill"'))
        self.assertIn("data-hagstofan-fyrirspurn", texti)


if __name__ == "__main__":
    unittest.main()
