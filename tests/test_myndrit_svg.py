"""Prófar myndritalagið og sýnidæmið fyrir #20 (issue #17).

Öll prófin hér **teikna**, og teikning þarfnast matplotlib. matplotlib er
samþykkt eingöngu fyrir ``src/python/utflutningur/`` og er ekki í
staðalsafninu, svo hver klasi sleppir sér þegar pakkinn er ekki til. Þá keyrir
``python3 -m unittest discover -s tests`` áfram á staðalsafninu einu og prófin
birtast sem *skipped*, ekki sem villa (skilyrði ákvörðunarinnar á #17).

Prófin á litum og andstæðu, sem þurfa ekki matplotlib, eru í
``test_myndrit_tokens.py`` og keyra alltaf.

Með matplotlib::

    <python með matplotlib> -m unittest tests/test_myndrit_svg.py
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from dataclasses import replace

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from utflutningur import myndrit_litir as hlutverk  # noqa: E402
from utflutningur.tokens import DOKKT, LJOST, lesa_tokens  # noqa: E402
from vinnsla.jardskjalftar import lesa_skjalfta  # noqa: E402
from vinnsla.jardskjalftar_afmorkun import lesa_afmorkun  # noqa: E402
from vinnsla.jardskjalftar_talning import dagar_an_atburda, dagleg_talning  # noqa: E402

HEFUR_MATPLOTLIB = importlib.util.find_spec("matplotlib") is not None
ASTAEDA = "matplotlib er ekki uppsett; samþykkt eingöngu fyrir utflutningur/ (#17)"

VAENTIR_DAGAR = 61
VAENTIR_NULLDAGAR = 43
# Þak á hverja SVG-skrá. Síðan öll má vera 500 KB (regla 3.4); eitt myndrit
# fær brot af því svo síða með nokkrum myndritum haldist langt undir.
HAMARK_BAETI = 40_000


def _dagatalning():
    afmorkun = lesa_afmorkun()
    return dagleg_talning(lesa_skjalfta(None, afmorkun), afmorkun)


@unittest.skipUnless(HEFUR_MATPLOTLIB, ASTAEDA)
class AkvardadUttakTest(unittest.TestCase):
    """Sömu gögn og sömu tokens gefa sömu bæti (lærdómurinn af #47)."""

    @classmethod
    def setUpClass(cls) -> None:
        from utflutningur import myndrit_skjalftar

        cls.mod = myndrit_skjalftar
        cls.dagatalning = _dagatalning()
        cls.themu = lesa_tokens()

    def test_sama_svg_tvisvar_i_rod(self) -> None:
        for heiti, thema in self.themu.items():
            with self.subTest(thema=heiti):
                fyrra = self.mod.teikna_svg(self.dagatalning, thema)
                sidara = self.mod.teikna_svg(self.dagatalning, thema)
                self.assertEqual(fyrra, sidara)

    def test_profid_greinir_oakvardad_uttak(self) -> None:
        """Án fasta saltsins og með Date í lýsigögnum VERÐA tvær teikningar ólíkar.

        Sannar að prófið hér að ofan getur brostið — það er ekki grænt af
        tilviljun eins og fingrafarið í #47.
        """
        import matplotlib

        from utflutningur import myndrit

        thema = self.themu[LJOST]

        def oakvardad() -> bytes:
            with myndrit.thema_samhengi(thema):
                matplotlib.rcParams["svg.hashsalt"] = None
                mynd = self.mod.byggja_mynd(self.dagatalning, thema)
                buffer = io.BytesIO()
                mynd.savefig(buffer, format="svg")
                return buffer.getvalue()

        self.assertNotEqual(oakvardad(), oakvardad())

    def test_engin_dagsetning_i_lysigognum(self) -> None:
        svg = self.mod.teikna_svg(self.dagatalning, self.themu[LJOST]).decode()
        self.assertNotIn("<dc:date>", svg)

    def test_vistudu_skrarnar_eru_i_takt_vid_gogn_og_tokens(self) -> None:
        """SVG í web/assets/img/ er afleiða; breytist tokens.css verður að endurteikna."""
        import matplotlib

        from utflutningur import myndrit

        for heiti, skraarheiti in self.mod.SKRAARHEITI.items():
            with self.subTest(skra=skraarheiti):
                slod = myndrit.MYNDAMAPPA / skraarheiti
                self.assertTrue(slod.is_file(), f"{slod} vantar — keyrðu myndrit_skjalftar")
                # Önnur matplotlib-útgáfa teiknar önnur bæti; þá er samanburðurinn
                # ekki um gögnin heldur um útgáfuna, og honum er sleppt með skýringu.
                utgafa = f"Matplotlib v{matplotlib.__version__},"
                if utgafa.encode() not in slod.read_bytes():
                    self.skipTest(f"{skraarheiti} var teiknuð með annarri matplotlib-útgáfu")
                self.assertEqual(
                    slod.read_bytes(),
                    self.mod.teikna_svg(self.dagatalning, self.themu[heiti]),
                    f"{skraarheiti} er úrelt. Endurteiknaðu: "
                    "PYTHONPATH=src/python python -m utflutningur.myndrit_skjalftar",
                )


@unittest.skipUnless(HEFUR_MATPLOTLIB, ASTAEDA)
class StaerdOgLeturTest(unittest.TestCase):
    """Regla 3.4: lítil skrá og ekkert innfellt letur."""

    @classmethod
    def setUpClass(cls) -> None:
        from utflutningur import myndrit_skjalftar

        dagatalning = _dagatalning()
        cls.svg = {
            heiti: myndrit_skjalftar.teikna_svg(dagatalning, thema)
            for heiti, thema in lesa_tokens().items()
        }

    def test_skrarnar_eru_undir_thakinu(self) -> None:
        for heiti, baeti in self.svg.items():
            with self.subTest(thema=heiti):
                self.assertLess(len(baeti), HAMARK_BAETI)

    def test_texti_er_texti_en_ekki_innfelldir_ferlar(self) -> None:
        for heiti, baeti in self.svg.items():
            svg = baeti.decode()
            with self.subTest(thema=heiti):
                self.assertIn("<text", svg)
                self.assertNotIn('id="DejaVuSans', svg, "letur innfellt sem ferlar")

    def test_texti_er_a_islensku_med_islenskum_tugabrotum(self) -> None:
        svg = self.svg[LJOST].decode()
        for brot in ("lograkvarði", "Dagur (UTC)", "1. nóv.", "15. des.", "70,5%"):
            with self.subTest(brot=brot):
                self.assertIn(brot, svg)
        self.assertNotIn("70.5", svg)


@unittest.skipUnless(HEFUR_MATPLOTLIB, ASTAEDA)
class NulldagarTest(unittest.TestCase):
    """Regla 3.3: núll-dagar greinast á lögun og texta, ekki á lit einum."""

    @classmethod
    def setUpClass(cls) -> None:
        from utflutningur import myndrit, myndrit_skjalftar

        cls.myndrit = myndrit
        cls.mod = myndrit_skjalftar
        cls.dagatalning = _dagatalning()
        cls.themu = lesa_tokens()

    def _byggja(self, thema):
        with self.myndrit.thema_samhengi(thema):
            return self.mod.byggja_mynd(self.dagatalning, thema)

    def _nullmerki(self, mynd):
        (asar,) = mynd.axes
        merki = [lina for lina in asar.lines if lina.get_gid() == self.mod.MERKI_NULL]
        self.assertEqual(1, len(merki), "núll-dagar eiga að vera eitt sér-merkt lag")
        return asar, merki[0]

    def test_gognin_eru_thau_sem_vid_buumst_vid(self) -> None:
        self.assertEqual(VAENTIR_DAGAR, len(self.dagatalning))
        self.assertEqual(VAENTIR_NULLDAGAR, dagar_an_atburda(self.dagatalning))

    def test_hver_nulldagur_hefur_merki_og_enga_sulu(self) -> None:
        asar, merki = self._nullmerki(self._byggja(self.themu[LJOST]))
        nulldagar = [x for x, d in enumerate(self.dagatalning) if d.event_count == 0]
        self.assertEqual(nulldagar, [int(x) for x in merki.get_xdata()])

        sulumidjur = {round(p.get_x() + p.get_width() / 2) for p in asar.patches}
        self.assertFalse(sulumidjur & set(nulldagar), "súla teiknuð á núll-degi")
        self.assertEqual(VAENTIR_DAGAR - VAENTIR_NULLDAGAR, len(asar.patches))

    def test_nulldagar_greinast_thott_litirnir_seu_eins(self) -> None:
        """Fellur ef munurinn á núll-degi og súludegi er borinn af lit einum.

        Þemað er falsað svo núll-merkið hafi NÁKVÆMLEGA lit súlnanna. Ef
        myndritið greindi dagana aðeins á lit væru þeir nú ógreinanlegir; hér
        verður lögun merkisins og skýringartextinn að standa eftir.
        """
        for heiti, thema in self.themu.items():
            gildi = dict(thema.gildi)
            gildi[hlutverk.NULL] = gildi[hlutverk.FLOTUR]
            litblint = replace(thema, gildi=gildi)
            with self.subTest(thema=heiti):
                asar, merki = self._nullmerki(self._byggja(litblint))
                self.assertEqual(litblint.litur(hlutverk.FLOTUR), merki.get_markeredgecolor())
                # Lögun: merki (ekki súla) og opið, svo það lítur ekki út eins og lítil súla.
                self.assertNotIn(merki.get_marker(), ("None", "", " ", None, "s"))
                self.assertEqual("none", merki.get_markerfacecolor())
                # Texti: skýringin nefnir núll-dagana með orðum.
                skyring = [t.get_text() for t in asar.get_legend().get_texts()]
                self.assertIn(self.mod.SKYRING_NULL, skyring)
                self.assertIn("0", self.mod.SKYRING_NULL)

    def test_litirnir_koma_ur_tokens(self) -> None:
        from matplotlib.colors import to_hex

        for heiti, thema in self.themu.items():
            with self.subTest(thema=heiti):
                mynd = self._byggja(thema)
                asar, merki = self._nullmerki(mynd)
                self.assertEqual(thema.litur(hlutverk.BAKGRUNNUR), to_hex(mynd.get_facecolor()))
                self.assertEqual(
                    {thema.litur(hlutverk.FLOTUR)},
                    {to_hex(p.get_facecolor()) for p in asar.patches},
                )
                self.assertEqual(thema.litur(hlutverk.NULL), merki.get_markeredgecolor())

    def test_themun_eru_olik(self) -> None:
        ljost = self.mod.teikna_svg(self.dagatalning, self.themu[LJOST])
        dokkt = self.mod.teikna_svg(self.dagatalning, self.themu[DOKKT])
        self.assertNotEqual(ljost, dokkt)


if __name__ == "__main__":
    unittest.main()
