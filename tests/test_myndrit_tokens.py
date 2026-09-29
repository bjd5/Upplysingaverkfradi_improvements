"""Prófar sjónræna kerfi myndritanna: litir, andstæða og íslenskt snið (reglur 3.1, 3.3).

Þessi próf þurfa **ekki** matplotlib: þau fjalla um lestur ``tokens.css``,
mælingu á litaandstæðu og íslenskt talna- og dagsetningarsnið (issue #17),
allt á staðalsafninu einu. Prófin á teikningunni sjálfri eru í
``test_myndrit_svg.py`` og sleppa sér þegar matplotlib er ekki til.

    python3 -m unittest discover -s tests
"""


import shutil  # noqa: E402
import tempfile  # noqa: E402
import unittest
from pathlib import Path  # noqa: E402

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from utflutningur import myndrit_litir  # noqa: E402
from utflutningur.tokens import (  # noqa: E402
    DOKKT,
    LJOST,
    SJALFGEFIN_SLOD,
    TokenVilla,
    lesa_tokens,
    thatta_lit,
)
from utflutningur.islenskt_snid import (  # noqa: E402
    islensk_dagsetning,
    islensk_prosenta,
    islensk_tala,
)


# --- Litir og andstæða ---------------------------------------------------------

# Andstæður sem WCAG 2.1 gefur upp beint — viðmið sem má ekki reka.
SVART_A_HVITU = 21.0
# #767676 er þekkta jafnvægispunkturinn: lægsti grátónn sem stenst 4,5:1 á hvítu.
MORK_GRATONN = "#767676"


class ThattunTest(unittest.TestCase):
    """Litir eru þáttaðir úr sextándasniði, annað snið er villa."""

    def test_thrir_og_sex_stafir_gefa_sama_lit(self) -> None:
        self.assertEqual((255, 255, 255), thatta_lit("#fff"))
        self.assertEqual((255, 255, 255), thatta_lit("#ffffff"))
        self.assertEqual((18, 101, 125), thatta_lit("#12657d"))

    def test_gagnsaei_er_fellt_ut_en_snidid_leyft(self) -> None:
        self.assertEqual((18, 101, 125), thatta_lit("#12657d80"))

    def test_annad_snid_en_sextandalitur_fellur(self) -> None:
        for gildi in ("rgb(10 15 21 / 6%)", "var(--adal-500)", "blátt", "#12g"):
            with self.subTest(gildi=gildi):
                with self.assertRaises(TokenVilla):
                    thatta_lit(gildi)


class TokensTest(unittest.TestCase):
    """tokens.css er eina heimildin um liti — líka fyrir Python."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.themu = lesa_tokens()

    def test_baedi_themu_lesast(self) -> None:
        self.assertEqual({LJOST, DOKKT}, set(self.themu))

    def test_tilvisanir_eru_uppleystar(self) -> None:
        # --bak-upphaekkad er bein gildi, --texti vísar í --gra-700 með var().
        ljost = self.themu[LJOST]
        self.assertEqual("#ffffff", ljost.litur("--bak-upphaekkad"))
        self.assertEqual(ljost.litur("--gra-700"), ljost.litur("--texti"))

    def test_dokkt_thema_erfir_thad_sem_thad_endurskilgreinir_ekki(self) -> None:
        ljost, dokkt = self.themu[LJOST], self.themu[DOKKT]
        # --bak er endurskilgreint í dökku þemanu ...
        self.assertNotEqual(ljost.litur("--bak"), dokkt.litur("--bak"))
        # ... en bilaskalinn er ekki, svo hann erfist óbreyttur.
        self.assertEqual(ljost.texti("--bil-4"), dokkt.texti("--bil-4"))

    def test_oskilgreint_token_fellur_med_skyringu(self) -> None:
        with self.assertRaises(TokenVilla) as samhengi:
            self.themu[LJOST].texti("--litur-sem-er-ekki-til")
        self.assertIn("tokens.css", str(samhengi.exception))

    def test_myndritatokens_eru_til_i_badum_themum(self) -> None:
        """Myndritin sækja liti undir --myndrit-*; vanti þau er reglan 3.1 brotin."""
        naudsynleg = (
            "--myndrit-bak",
            "--myndrit-flotur",
            "--myndrit-null",
            "--myndrit-texti",
            "--myndrit-texti-dauft",
            "--myndrit-as",
            "--myndrit-grind",
        )
        for heiti, thema in self.themu.items():
            for nafn in naudsynleg:
                with self.subTest(thema=heiti, token=nafn):
                    self.assertRegex(thema.litur(nafn), r"^#[0-9a-f]{6}$")


class AndstaedaTest(unittest.TestCase):
    """WCAG-formúlan er mæld, ekki áætluð."""

    def test_svart_a_hvitu_er_hamarkid(self) -> None:
        self.assertAlmostEqual(
            SVART_A_HVITU, myndrit_litir.andstaeda("#000000", "#ffffff"), places=2
        )

    def test_sami_litur_gefur_eitt(self) -> None:
        self.assertAlmostEqual(1.0, myndrit_litir.andstaeda("#12657d", "#12657d"))

    def test_rodin_skiptir_ekki_mali(self) -> None:
        self.assertAlmostEqual(
            myndrit_litir.andstaeda("#12657d", "#ffffff"),
            myndrit_litir.andstaeda("#ffffff", "#12657d"),
        )

    def test_thekktur_jafnvaegispunktur_stenst_textakrofuna(self) -> None:
        maeling = myndrit_litir.maela("mörk", MORK_GRATONN, "#ffffff")
        self.assertTrue(maeling.stenst, maeling.lina())
        self.assertLess(maeling.hlutfall, 4.6, "jafnvægispunkturinn á að liggja rétt yfir 4,5")

    def test_maeling_sem_fellur_er_merkt_sem_fallin(self) -> None:
        maeling = myndrit_litir.maela("of ljóst", "#d8dee6", "#ffffff")
        self.assertFalse(maeling.stenst)
        self.assertIn("FELLUR", maeling.lina())


class MyndritaKrofurTest(unittest.TestCase):
    """Hvert merkingarberandi --myndrit-* hlutverk stenst kröfu sína í BÁÐUM þemum.

    Prófið er líka keyrt á falsaðri tokens.css þar sem það á að bresta, svo það
    sé ekki grænt af tilviljun (lærdómurinn af #47).
    """

    # Grátónn undir 4,5:1 á hvítu (3,45:1) en yfir henni á --gra-800 (5,08:1),
    # svo aðeins ljósa þemað á að falla.
    OF_DAUFT = "#8a8a8a"

    def test_raunverulegu_tokens_standast(self) -> None:
        maelingar = myndrit_litir.maela_myndritaliti(lesa_tokens())
        self.assertEqual(2 * len(myndrit_litir.KROFUR), len(maelingar))
        for maeling in maelingar:
            with self.subTest(maeling=maeling.heiti):
                self.assertTrue(maeling.stenst, maeling.lina())

    def test_merkingarberar_eru_maeldir_gegn_4_5(self) -> None:
        """Súla, núll-merki og texti bera merkingu og fá textakröfuna (#17)."""
        krofur = {fram: krafa for _, fram, _, krafa in myndrit_litir.KROFUR}
        for token in (
            myndrit_litir.FLOTUR,
            myndrit_litir.NULL,
            myndrit_litir.TEXTI,
            myndrit_litir.TEXTI_DAUFT,
        ):
            with self.subTest(token=token):
                self.assertEqual(myndrit_litir.KRAFA_TEXTI, krofur[token])

    def _falsad(self, texti: str) -> dict:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "tokens.css"
            shutil.copyfile(SJALFGEFIN_SLOD, slod)
            upprunalegt = slod.read_text(encoding="utf-8")
            slod.write_text(upprunalegt.replace(*texti), encoding="utf-8")
            return lesa_tokens(slod)

    def test_fellur_ef_ljosa_themad_fer_undir(self) -> None:
        themu = self._falsad(
            ("--myndrit-null:        var(--ahersla-700);",
             f"--myndrit-null:        {self.OF_DAUFT};")
        )
        fallnar = myndrit_litir.fallnar(themu)
        self.assertTrue(fallnar)
        self.assertTrue(all(m.heiti.startswith(LJOST) for m in fallnar), fallnar)

    def test_fellur_ef_dokka_themad_fer_undir(self) -> None:
        # Aðeins dökka þemað breytist: --ahersla-700 er endurskilgreint þar.
        themu = self._falsad(
            ("--ahersla-700:    #e08a4a;", "--ahersla-700:    #6b4a33;")
        )
        fallnar = myndrit_litir.fallnar(themu)
        self.assertEqual([f"{DOKKT}: núll-merki"], [m.heiti for m in fallnar])



# --- Íslenskt snið -------------------------------------------------------------

class TolurTest(unittest.TestCase):
    def test_tugabrotskomma_og_thusundapunktur(self) -> None:
        self.assertEqual("5,5", islensk_tala(5.475, 1))
        self.assertEqual("1.234,50", islensk_tala(1234.5, 2))
        self.assertEqual("1.000.000", islensk_tala(1_000_000))
        self.assertEqual("187", islensk_tala(187))

    def test_ekkert_enskt_snid_laekur_i_gegn(self) -> None:
        for gildi in (0.5, 12345.678, 70.49):
            with self.subTest(gildi=gildi):
                texti = islensk_tala(gildi, 2)
                self.assertIn(",", texti)
                self.assertNotRegex(texti, r"\.\d{2}$")

    def test_neikvaedir_aukastafir_falla(self) -> None:
        with self.assertRaises(ValueError):
            islensk_tala(1.0, -1)

    def test_prosenta(self) -> None:
        self.assertEqual("70,5%", islensk_prosenta(43, 61))
        with self.assertRaises(ValueError):
            islensk_prosenta(1, 0)


class DagsetningarTest(unittest.TestCase):
    def test_stytt_og_fullt(self) -> None:
        self.assertEqual("1. nóv.", islensk_dagsetning("2023-11-01"))
        self.assertEqual("31. desember 2023", islensk_dagsetning("2023-12-31", stytt=False, med_ari=True))
        self.assertEqual("15. maí", islensk_dagsetning("2024-05-15"))

    def test_rangt_snid_fellur(self) -> None:
        for gildi in ("2023-13-01", "1.11.2023", ""):
            with self.subTest(gildi=gildi):
                with self.assertRaises(ValueError):
                    islensk_dagsetning(gildi)


if __name__ == "__main__":
    unittest.main()
