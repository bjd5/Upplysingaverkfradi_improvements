"""Prófar beinagrind vefsíðunnar gegn reglum 2, 3.2, 3.3 og 3.4 í CLAUDE.md.

Beinagrindin er afrituð í níu HTML-skrár af því að verkefnið hefur engan
byggingarferil. Þessi próf eru trygging fyrir því að afritin haldist í takt
þegar síðuverkin (P3.4-P3.11) fylla efnishlutana.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""
import pathlib
import posixpath
import re
import unittest
from collections import deque
from html.parser import HTMLParser

VEFUR = pathlib.Path(__file__).resolve().parent.parent / "web"

SIDUR = [
    "index.html",
    "sidur/adferdafraedi.html",
    "sidur/hagstofan.html",
    "sidur/mbl-regex.html",
    "sidur/phoebe-central-perk.html",
    "sidur/phoebe-tmdb.html",
    "sidur/phoebe-tolfraedi.html",
    "sidur/skjalftavaktin.html",
    "sidur/vedurstodvar.html",
]

HAMARK_SMELLIR = 3


def lesa(sida: str) -> str:
    return (VEFUR / sida).read_text(encoding="utf-8")


def stadfaera(sida: str, slod: str) -> str:
    """Breytir afstæðri slóð á síðu í slóð frá rót web/."""
    grunnur = posixpath.dirname(sida)
    return posixpath.normpath(posixpath.join(grunnur, slod))


class Safnari(HTMLParser):
    """Safnar því sem prófin þurfa: fyrirsögnum, tenglum, myndum, skriftum."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fyrirsagnir: list[int] = []
        self.tenglar: list[str] = []
        self.myndir: list[dict] = []
        self.skriftur: list[dict] = []
        self.stilar: list[str] = []
        self.atburdarof: list[str] = []
        self.stiltag = False
        self.innri_skrifta: list[str] = []
        self._i_skriftu_an_src = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        eig = dict(attrs)
        for nafn in eig:
            if nafn.startswith("on"):
                self.atburdarof.append("%s[%s]" % (tag, nafn))
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.fyrirsagnir.append(int(tag[1]))
        elif tag == "a" and "href" in eig:
            self.tenglar.append(eig["href"])
        elif tag == "img":
            self.myndir.append(eig)
        elif tag == "script":
            self.skriftur.append(eig)
            self._i_skriftu_an_src = "src" not in eig
        elif tag == "style":
            self.stiltag = True
        elif tag == "link" and eig.get("rel") == "stylesheet":
            self.stilar.append(eig.get("href", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._i_skriftu_an_src = False

    def handle_data(self, gogn: str) -> None:
        if self._i_skriftu_an_src and gogn.strip():
            self.innri_skrifta.append(gogn.strip()[:40])


def greina(sida: str) -> Safnari:
    safnari = Safnari()
    safnari.feed(lesa(sida))
    return safnari


class AdskilnadurTest(unittest.TestCase):
    """Regla 2 — HTML, CSS og JS blandast aldrei."""

    def test_engir_inline_stilar_eda_skriftur(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                safnari = greina(sida)
                self.assertFalse(safnari.stiltag, "<style> í HTML")
                self.assertEqual([], safnari.innri_skrifta, "kóði inni í <script>")
                self.assertEqual([], safnari.atburdarof, "onclick eða sambærilegt")
                self.assertNotIn(" style=", lesa(sida), 'style="..." attribute')

    def test_allar_skriftur_med_defer(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                for skrifta in greina(sida).skriftur:
                    self.assertIn("src", skrifta)
                    self.assertIn("defer", skrifta)


class MerkingTest(unittest.TestCase):
    """Regla 3.3 — merkingarbært HTML og aðgengi."""

    def test_islenskt_tungumal_og_ein_h1(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                self.assertIn('<html lang="is">', lesa(sida))
                self.assertEqual(1, greina(sida).fyrirsagnir.count(1))

    def test_fyrirsagnir_an_stokka(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                stig = greina(sida).fyrirsagnir
                for fyrra, sidara in zip(stig, stig[1:]):
                    self.assertLessEqual(sidara - fyrra, 1,
                                         "stokkid yfir fyrirsagnarstig: %s" % stig)

    def test_kennileiti_og_stokktengill(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                texti = lesa(sida)
                for tag in ("<header", "<nav", "<main", "<article", "<footer"):
                    self.assertIn(tag, texti, "vantar %s>" % tag)
                self.assertIn('class="stokk-tengill" href="#efni"', texti)
                self.assertIn('id="efni"', texti)

    def test_myndir_hafa_alt(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                for mynd in greina(sida).myndir:
                    self.assertIn("alt", mynd, "mynd án alt-texta")

    def test_braudmylsna_a_ollum_undirsidum(self) -> None:
        for sida in SIDUR:
            if sida == "index.html":
                continue
            with self.subTest(sida=sida):
                self.assertIn('class="braudmylsna', lesa(sida))


class SamraemiTest(unittest.TestCase):
    """Regla 3.2 — sami haus og fótur, á sama stað, í sömu röð."""

    @staticmethod
    def _hluti(sida: str, tag: str) -> str:
        leit = re.search(r"<%s class=\"(haus|fotur)\".*?</%s>" % (tag, tag),
                         lesa(sida), re.DOTALL)
        assert leit, "fann ekki <%s> á %s" % (tag, sida)
        # Slóðir og merking núverandi síðu eru það EINA sem má vera ólíkt.
        texti = leit.group(0)
        texti = re.sub(r' aria-current="[^"]*"', "", texti)
        texti = re.sub(r'href="(\.\./)?', 'href="', texti)
        return re.sub(r'href="sidur/', 'href="', texti)

    def test_haus_eins_a_ollum_sidum(self) -> None:
        vidmid = self._hluti(SIDUR[0], "header")
        for sida in SIDUR[1:]:
            with self.subTest(sida=sida):
                self.assertEqual(vidmid, self._hluti(sida, "header"))

    def test_fotur_eins_a_ollum_sidum(self) -> None:
        vidmid = self._hluti(SIDUR[0], "footer")
        for sida in SIDUR[1:]:
            with self.subTest(sida=sida):
                self.assertEqual(vidmid, self._hluti(sida, "footer"))

    def test_nuverandi_sida_merkt_i_valmynd(self) -> None:
        for sida in SIDUR:
            with self.subTest(sida=sida):
                haus = re.search(r"<header.*?</header>", lesa(sida), re.DOTALL)
                self.assertIn('aria-current=', haus.group(0),
                              "núverandi síða ekki merkt í valmynd")


class TenglarTest(unittest.TestCase):
    """Engin brotin slóð, ekkert efni lengra en þrjá smelli frá forsíðu."""

    @staticmethod
    def _innri(safnari: Safnari, sida: str) -> list[str]:
        ut = []
        for slod in safnari.tenglar:
            if slod.startswith(("http://", "https://", "mailto:", "#")):
                continue
            ut.append(stadfaera(sida, slod.split("#")[0]))
        return ut

    def test_allar_slodir_eru_til(self) -> None:
        for sida in SIDUR:
            safnari = greina(sida)
            slodir = self._innri(safnari, sida)
            slodir += [stadfaera(sida, s) for s in safnari.stilar]
            slodir += [stadfaera(sida, s["src"]) for s in safnari.skriftur]
            for slod in slodir:
                with self.subTest(sida=sida, slod=slod):
                    self.assertTrue((VEFUR / slod).exists(), "brotin slóð")

    def test_engar_munadarlausar_sidur(self) -> None:
        skrar = {str(p.relative_to(VEFUR)) for p in VEFUR.rglob("*.html")}
        self.assertEqual(set(SIDUR), skrar, "HTML-skrár í web/ passa ekki við níu síður")

    def test_hamark_thrir_smellir_fra_forsidu(self) -> None:
        dypt = {"index.html": 0}
        rod = deque(["index.html"])
        while rod:
            sida = rod.popleft()
            for naest in self._innri(greina(sida), sida):
                if naest in SIDUR and naest not in dypt:
                    dypt[naest] = dypt[sida] + 1
                    rod.append(naest)
        for sida in SIDUR:
            with self.subTest(sida=sida):
                self.assertIn(sida, dypt, "ekki hægt að rata á síðuna")
                self.assertLessEqual(dypt[sida], HAMARK_SMELLIR)


class SjonraentKerfiTest(unittest.TestCase):
    """Regla 3.1 — öll gildi eiga heima í tokens.css."""

    @staticmethod
    def _adrar_css() -> list[pathlib.Path]:
        return [p for p in (VEFUR / "assets/css").rglob("*.css")
                if p.name != "tokens.css"]

    @staticmethod
    def _an_athugasemda(skra: pathlib.Path) -> str:
        """Reglan nær til gilda, ekki skýringartexta — svo athugasemdir fara út."""
        return re.sub(r"/\*.*?\*/", "", skra.read_text("utf-8"), flags=re.DOTALL)

    def test_engin_px_tala_utan_tokens(self) -> None:
        for skra in self._adrar_css():
            with self.subTest(skra=skra.name):
                self.assertEqual([], re.findall(r"\d+px", self._an_athugasemda(skra)))

    def test_enginn_hardkodadur_litur_utan_tokens(self) -> None:
        mynstur = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
        for skra in self._adrar_css():
            with self.subTest(skra=skra.name):
                self.assertEqual([], mynstur.findall(self._an_athugasemda(skra)))

    def test_dokkt_thema_endurskilgreinir_adeins_tokens(self) -> None:
        texti = (VEFUR / "assets/css/tokens.css").read_text("utf-8")
        self.assertIn("prefers-color-scheme: dark", texti)
        hluti = texti[texti.index("prefers-color-scheme: dark"):]
        for lina in hluti.splitlines()[1:]:
            hreint = lina.strip()
            if hreint and not hreint.startswith(("--", "/*", "*", "}", "{", ":root")):
                self.fail("dökkt þema skilgreinir annað en tokens: %r" % hreint)


if __name__ == "__main__":
    unittest.main()
