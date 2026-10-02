"""Prófar frammistöðuþak vefsins (regla 3.4 í CLAUDE.md, issue #27).

Stærðin er reiknuð úr skrám á disk: HTML + stílskrár + skriftur + JSON-skrár
sem síðan sækir + myndir. Mælingin er ócomprimeruð og því strangari en
raunveruleg flutningsstærð. Sjá docs/frammistada.md.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""
import pathlib
import posixpath
import re
import unittest
from html.parser import HTMLParser

VEFUR = pathlib.Path(__file__).resolve().parent.parent / "web"
HAMARK_BAET = 500 * 1000  # 500 KB, regla 3.4
JSON_NAFN = re.compile(r"[\"']([a-z0-9-]+\.json)[\"']")
YTRI_SLOD = re.compile(r"^(https?:)?//", re.IGNORECASE)


class Tilvisanir(HTMLParser):
    """Safnar skrám sem síðan hleður og skriftum sem vantar defer."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skrar: list[str] = []
        self.json_skrar: list[str] = []
        self.skriftur: list[dict] = []
        self.slodir: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        eig = dict(attrs)
        for nafn in ("src", "href"):
            if nafn in eig and tag in ("link", "script", "img", "source"):
                self.slodir.append(eig[nafn])
        if tag == "link" and eig.get("rel") == "stylesheet":
            self.skrar.append(eig["href"])
        elif tag == "script" and "src" in eig:
            self.skriftur.append(eig)
            self.skrar.append(eig["src"])
        elif tag == "img" and "src" in eig:
            self.skrar.append(eig["src"])
        elif tag == "source" and "srcset" in eig:
            self.skrar.append(eig["srcset"])
        if "data-gogn" in eig:
            self.json_skrar.append(eig["data-gogn"])


def sidur() -> list[str]:
    nofn = ["index.html"]
    nofn += ["sidur/" + s.name for s in sorted((VEFUR / "sidur").glob("*.html"))]
    return nofn


def greina(sida: str) -> Tilvisanir:
    t = Tilvisanir()
    t.feed((VEFUR / sida).read_text(encoding="utf-8"))
    return t


def skrar_sidu(sida: str) -> set[pathlib.Path]:
    """Allar skrár sem fyrsta hleðsla síðunnar sækir, að henni sjálfri meðtalinni."""
    t = greina(sida)
    grunnur = posixpath.dirname(sida)
    skrar = {VEFUR / sida}
    json_nofn = list(t.json_skrar)
    for slod in t.skrar:
        skra = VEFUR / posixpath.normpath(posixpath.join(grunnur, slod))
        skrar.add(skra)
        if skra.suffix == ".js":
            json_nofn += JSON_NAFN.findall(skra.read_text(encoding="utf-8"))
    for nafn in json_nofn:
        skrar.add(VEFUR / "gogn" / nafn)
    return skrar


class TestFrammistada(unittest.TestCase):
    def test_hver_sida_undir_500_kb(self) -> None:
        for sida in sidur():
            with self.subTest(sida=sida):
                skrar = skrar_sidu(sida)
                for skra in skrar:
                    self.assertTrue(skra.is_file(), "vantar skrá: %s" % skra)
                samtals = sum(s.stat().st_size for s in skrar)
                self.assertLess(samtals, HAMARK_BAET,
                                "%s er %d bæti" % (sida, samtals))

    def test_ollum_skriftum_fylgir_defer(self) -> None:
        for sida in sidur():
            for skripta in greina(sida).skriftur:
                with self.subTest(sida=sida, src=skripta["src"]):
                    self.assertIn("defer", skripta)

    def test_engin_ytri_slod(self) -> None:
        for sida in sidur():
            for slod in greina(sida).slodir:
                with self.subTest(sida=sida, slod=slod):
                    self.assertIsNone(YTRI_SLOD.match(slod))

    def test_hver_ihlutastilskra_er_tengd(self) -> None:
        tengdar = {s for sida in sidur() for s in skrar_sidu(sida)}
        for css in sorted((VEFUR / "assets" / "css" / "components").glob("*.css")):
            with self.subTest(skra=css.name):
                self.assertIn(css, tengdar, "ónotuð stílskrá — eyða (regla 6)")


if __name__ == "__main__":
    unittest.main()
