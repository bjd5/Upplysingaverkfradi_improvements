"""Prófar að web/ sé tilbúin til birtingar á undirslóð (issue #28).

Sama prófið keyrir í GitHub Actions áður en síðan er birt: stöðvast birtingin
ef gagnaskrá vantar eða er gölluð, ef slóð byrjar á `/` (brotnar á
`/<repo>/`), eða ef leyndarmál sést í web/ (regla 4 og 9.6; repo-ið er opið).

Keyrt með staðalsafninu einu:
    python3 -m unittest discover -s tests -p "test_vefur_birting.py"
"""
import json
import pathlib
import re
import unittest

VEFUR = pathlib.Path(__file__).resolve().parent.parent / "web"
GOGN = VEFUR / "gogn"
SNID_REITIR = {"uppfaert", "heimild", "gogn"}
TEXTASKRAR = {".html", ".css", ".js", ".json", ".svg"}
# Slóð sem byrjar á einum `/` vísar á rót vefþjónsins, ekki á `/<repo>/`.
ROT_SLOD = re.compile(
    r"""(?:href|src|action|poster)\s*=\s*["']/(?!/)"""
    r"""|url\(\s*["']?/(?!/)"""
    r"""|(?:fetch|import)\(\s*["']/(?!/)""",
    re.IGNORECASE,
)
# Dæmigerð snið á lyklum og táknum; nöfn umhverfisbreyta eru líka bönnuð.
LEYNDARMAL = re.compile(
    r"TMDB_TOKEN|Authorization\s*:|Bearer\s+[A-Za-z0-9._-]{16,}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"sk-[A-Za-z0-9]{20,}|api[_-]?key\s*[:=]\s*[\"'][^\"']{8,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    re.IGNORECASE,
)


def textaskrar() -> list:
    return sorted(p for p in VEFUR.rglob("*")
                  if p.is_file() and p.suffix in TEXTASKRAR)


class GagnaskrarTest(unittest.TestCase):
    def test_gagnaskrar_eru_til_og_a_sniði_reglu_5_4(self) -> None:
        skrar = sorted(GOGN.glob("*.json"))
        self.assertTrue(skrar, "web/gogn/ er tóm: síðan byggðist með tómum köflum")
        for skra in skrar:
            with self.subTest(skra=skra.name):
                try:
                    skjal = json.loads(skra.read_text(encoding="utf-8"))
                except json.JSONDecodeError as villa:
                    self.fail("gölluð JSON-skrá: %s" % villa)
                self.assertTrue(SNID_REITIR <= set(skjal), "vantar reit")
                self.assertTrue(skjal["gogn"], "tómt `gogn`")


class SlodirTest(unittest.TestCase):
    def test_engin_slod_byrjar_a_skastriki(self) -> None:
        for skra in textaskrar():
            with self.subTest(skra=str(skra.relative_to(VEFUR))):
                fundir = ROT_SLOD.findall(skra.read_text(encoding="utf-8"))
                self.assertEqual(fundir, [], "slóð frá rót")

    def test_engin_slod_fer_ut_fyrir_web(self) -> None:
        for skra in sorted(VEFUR.rglob("*.html")):
            texti = skra.read_text(encoding="utf-8")
            for slod in re.findall(r"""(?:href|src)=["']([^"'#?]+)""", texti):
                if re.match(r"^[a-z][a-z0-9+.-]*:|^//", slod, re.IGNORECASE):
                    continue
                with self.subTest(skra=skra.name, slod=slod):
                    ut = (skra.parent / slod).resolve()
                    self.assertTrue(ut.is_relative_to(VEFUR.resolve()),
                                    "vísar út fyrir web/")


class LeyndarmalTest(unittest.TestCase):
    def test_ekkert_leyndarmal_i_web(self) -> None:
        for skra in textaskrar():
            with self.subTest(skra=str(skra.relative_to(VEFUR))):
                fundur = LEYNDARMAL.search(skra.read_text(encoding="utf-8"))
                self.assertIsNone(fundur, "lítur út eins og leyndarmál: %r"
                                  % (fundur and fundur.group(0)[:12]))

    def test_engar_umhverfisskrar_i_web(self) -> None:
        for p in VEFUR.rglob("*"):
            self.assertFalse(p.name.startswith(".env")
                             or p.suffix in {".key", ".pem"}, str(p))


if __name__ == "__main__":
    unittest.main()
