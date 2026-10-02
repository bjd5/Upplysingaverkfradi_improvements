"""Prófar aðgengi vefsíðunnar (WCAG 2.1 AA, regla 3.3 og 3.5 í CLAUDE.md).

Keyrir án vafra: HTML og CSS eru lesin sem texti og andstæða er reiknuð úr
tokens.css. Grunnathuganir á lang, h1, fyrirsagnaröð, alt og stökktengli eru í
test_vefur.py; hér er það sem bætist við. Mæling í vafra er lýst í
docs/adgengi.md.
"""
import pathlib
import re
import unittest
from html.parser import HTMLParser

from test_vefur import SIDUR, VEFUR, lesa

CSS = VEFUR / "assets" / "css"
LAGMARK_TEXTI = 4.5      # WCAG 1.4.3
LAGMARK_FLOTUR = 3.0     # WCAG 1.4.11 (fókusumgjörð)

# Textalitir og fletirnir sem þeir mega standa á.
TEXTALITIR = ["texti", "texti-daufur", "tengill", "tengill-yfir", "ahersla-700"]
FLETIR = ["bak", "bak-upphaekkad", "bak-daufur"]


# --- Andstæða úr tokens.css ---------------------------------------------------

def lesa_tokens() -> tuple[dict[str, str], dict[str, str]]:
    """Skilar (ljóst, dökkt): dökka þemað er ljósa þemað með endurskilgreiningum."""
    texti = (CSS / "tokens.css").read_text(encoding="utf-8")
    dokkt_stadur = texti.index("prefers-color-scheme: dark")
    breyta = re.compile(r"--([a-z0-9-]+):\s*([^;]+);")
    ljost = {n: v.strip() for n, v in breyta.findall(texti[:dokkt_stadur])}
    dokkt = dict(ljost)
    dokkt.update({n: v.strip() for n, v in breyta.findall(texti[dokkt_stadur:])})
    return ljost, dokkt


def lykill_litur(breytur: dict[str, str], nafn: str) -> str:
    """Eltir var(--x) keðjur þar til hex-litur fæst."""
    gildi = breytur[nafn]
    while gildi.startswith("var("):
        gildi = breytur[gildi[6:-1]]
    return gildi


def birta(hex_litur: str) -> float:
    rgb = [int(hex_litur[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def andstaeda(a: str, b: str) -> float:
    hatt, lagt = sorted((birta(a), birta(b)), reverse=True)
    return (hatt + 0.05) / (lagt + 0.05)


class AndstaedaTest(unittest.TestCase):
    """Regla 3.3 — textaandstæða minnst 4,5:1 í báðum þemum."""

    def test_textalitir_a_ollum_flotum(self) -> None:
        for thema, breytur in zip(("ljóst", "dökkt"), lesa_tokens()):
            for texti in TEXTALITIR:
                for flotur in FLETIR:
                    with self.subTest(thema=thema, texti=texti, flotur=flotur):
                        hlutfall = andstaeda(lykill_litur(breytur, texti),
                                             lykill_litur(breytur, flotur))
                        self.assertGreaterEqual(hlutfall, LAGMARK_TEXTI)

    def test_texti_a_adallit(self) -> None:
        for thema, breytur in zip(("ljóst", "dökkt"), lesa_tokens()):
            with self.subTest(thema=thema):
                self.assertGreaterEqual(
                    andstaeda(lykill_litur(breytur, "texti-a-lit"),
                              lykill_litur(breytur, "adal-500")), LAGMARK_TEXTI)

    def test_fokusumgjord_sest_a_ollum_flotum(self) -> None:
        for thema, breytur in zip(("ljóst", "dökkt"), lesa_tokens()):
            for flotur in FLETIR:
                with self.subTest(thema=thema, flotur=flotur):
                    self.assertGreaterEqual(
                        andstaeda(lykill_litur(breytur, "fokus"),
                                  lykill_litur(breytur, flotur)), LAGMARK_FLOTUR)


# --- Lyklaborð ----------------------------------------------------------------

def css_skrar() -> list[pathlib.Path]:
    return sorted(p for p in CSS.rglob("*.css") if p.name != "tokens.css")


class FokusTest(unittest.TestCase):
    """Regla 3.3 — aldrei outline: none án staðgengils."""

    def test_grunnfokus_er_til(self) -> None:
        base = (CSS / "base.css").read_text(encoding="utf-8")
        self.assertRegex(base, r":focus-visible\s*\{[^}]*outline:\s*var\(--fokus-breidd\)")

    def test_outline_none_hefur_stadgengil(self) -> None:
        for skra in css_skrar():
            texti = skra.read_text(encoding="utf-8")
            for regla in re.finditer(r"([^{}]+)\{([^}]*outline:\s*(?:none|0)\b[^}]*)\}", texti):
                with self.subTest(skra=skra.name, veljari=regla.group(1).strip()):
                    # Má aðeins slökkva á tenglinum þegar umlykjandi eining
                    # (:focus-within) teiknar umgjörðina í staðinn.
                    self.assertIn(":focus-visible", regla.group(1))
                    self.assertRegex(texti, r":focus-within\s*\{[^}]*outline:\s*var\(--fokus-breidd\)")

    def test_stokktengill_syndur_vid_fokus(self) -> None:
        layout = "".join(p.read_text(encoding="utf-8") for p in CSS.rglob("*.css"))
        self.assertRegex(layout, r"\.stokk-tengill:focus[^{]*\{")


class SmellifletirTest(unittest.TestCase):
    """Regla 3.5 — snertifletir minnst 44 × 44 px."""

    def test_smellisvaedi_er_44px(self) -> None:
        self.assertIn("--smellisvaedi:   44px", (CSS / "tokens.css").read_text(encoding="utf-8"))

    def test_tenglar_i_haus_og_braudmylsnu_fylla_flotinn(self) -> None:
        for skra in ("components/braudmylsna.css", "components/undirvalmynd.css", "layout.css"):
            with self.subTest(skra=skra):
                self.assertIn("min-height: var(--smellisvaedi)",
                              (CSS / skra).read_text(encoding="utf-8"))

    def test_braudmylsna_hefur_lagmarksbreidd(self) -> None:
        # Stutt heiti („Þema“) urðu 39 px breið án þessa.
        self.assertIn("min-width: var(--smellisvaedi)",
                      (CSS / "components/braudmylsna.css").read_text(encoding="utf-8"))


# --- Töflur, myndir og JavaScript slökkt ---------------------------------------

class TaflaSafnari(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.toflur = 0
        self.skjalftar = 0
        self.fyrirsagnarhaus: list[dict] = []
        self.noscript = 0
        self.gagnahlutar = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        a = dict(attrs)
        if tag == "table":
            self.toflur += 1
        elif tag == "caption":
            self.skjalftar += 1
        elif tag == "th":
            self.fyrirsagnarhaus.append(a)
        elif tag == "noscript":
            self.noscript += 1
        if "data-gogn" in a:
            self.gagnahlutar += 1


class EfniTest(unittest.TestCase):
    def test_statiskar_toflur_hafa_caption_og_th_scope(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                s = TaflaSafnari()
                s.feed(lesa(sida))
                self.assertEqual(s.toflur, s.skjalftar, "tafla án <caption>")
                for th in s.fyrirsagnarhaus:
                    self.assertIn(th.get("scope"), ("col", "row", "colgroup", "rowgroup"))

    def test_toflur_byggdar_med_js_hafa_caption_og_scope(self) -> None:
        js = (VEFUR / "assets/js/gagnahluti.js").read_text(encoding="utf-8")
        self.assertIn('element("caption"', js)
        self.assertIn('.scope = "col"', js)

    def test_gagnahlutar_hafa_noscript_varaleid(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                s = TaflaSafnari()
                s.feed(lesa(sida))
                self.assertGreaterEqual(s.noscript, s.gagnahlutar)

    def test_hver_sida_merkir_nuverandi_stad(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                self.assertIn("aria-current", lesa(sida))

    def test_allar_myndir_hafa_alt_attribute(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                for tag in re.findall(r"<img\b[^>]*>", lesa(sida)):
                    self.assertRegex(tag, r'\balt="')


if __name__ == "__main__":
    unittest.main()
