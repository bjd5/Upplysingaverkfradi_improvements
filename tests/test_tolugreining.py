"""Próf fyrir tölugreiningu: íslenskt tölusnið og hvað er EKKI niðurstaða.

Keyrsla::

    python3 -m unittest discover -s tests

Dæmin hér eru tekin óbreytt úr byggðu gömlu síðunni. Þess vegna er þetta próf
á viðmiðinu sjálfu og ekki aðeins á segðunum: breytist flokkunin, breytist
viðmiðið sem P2.8 mælir nýju síðuna við.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PYTHON_ROT = Path(__file__).resolve().parents[1] / "src" / "python"
if str(PYTHON_ROT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROT))

from vidmid.tolugreining import finna_tolur  # noqa: E402


def eitt(texti: str):
    """Eina talan í textanum — fellur ef þær eru fleiri eða engin."""
    tolur = finna_tolur(texti)
    if len(tolur) != 1:
        raise AssertionError(f"{texti!r} gaf {len(tolur)} tölur: "
                             f"{[t.texti for t in tolur]}")
    return tolur[0]


class ThusundaskilProf(unittest.TestCase):
    """Þúsundaskil eru bæði punktur og bil í gamla verkefninu."""

    def test_bil_sem_thusundaskil(self) -> None:
        self.assertEqual(eitt("Af 70 553 textablokkum").gildi, 70553)

    def test_punktur_sem_thusundaskil(self) -> None:
        self.assertEqual(eitt("Þátta 61.161 línur").gildi, 61161)

    def test_bil_klofnar_ekki_i_tvaer_tolur(self) -> None:
        tolur = finna_tolur("61 161 sem tilsvör og 2 078 óflokkuð")
        self.assertEqual([t.gildi for t in tolur], [61161, 2078])

    def test_tvaer_sjalfstaedar_tolur_renna_ekki_saman(self) -> None:
        tolur = finna_tolur("30 dagar · Samtals 330")
        self.assertEqual([t.gildi for t in tolur], [30, 330])


class AukastafirOgHlutfollProf(unittest.TestCase):
    def test_komma_er_aukastafamerki(self) -> None:
        self.assertEqual(eitt("miðgildi 4,67 km").gildi, 4.67)

    def test_hlutfall_med_bili_fyrir_prosentumerki(self) -> None:
        tolur = finna_tolur("2 078 (2,95 %) standa óflokkuð")
        self.assertEqual([(t.gildi, t.eining) for t in tolur],
                         [(2078, None), (2.95, "%")])

    def test_hlutfall_an_bils(self) -> None:
        self.assertEqual(eitt("er 84,3% , samanborið").gildi, 84.3)

    def test_hlutfallstala(self) -> None:
        tala = eitt("hlutfallið 6,7:1")
        self.assertEqual((tala.tegund, tala.gildi), ("hlutfallstala", 6.7))

    def test_bil_heldur_endapunktum(self) -> None:
        tala = eitt("Dýpt: 0,07–11,26 km")
        self.assertEqual((tala.tegund, tala.bil, tala.eining),
                         ("bil", (0.07, 11.26), "km"))

    def test_unicode_minus(self) -> None:
        self.assertEqual(eitt("Lengdargráða −23").gildi, -23)


class EiningarProf(unittest.TestCase):
    def test_beygd_eining_er_nafngreind(self) -> None:
        self.assertEqual(eitt("á 61 UTC-dögum").eining, "dagar")

    def test_eining_ur_naesta_ordi(self) -> None:
        self.assertEqual(eitt("334 yfirfarna").eining, None)
        self.assertEqual(eitt("236 þætti").eining, "þættir")


class EkkiNidurstadaProf(unittest.TestCase):
    """Tölur sem líta út eins og niðurstöður en eru það ekki."""

    def test_timastimpill(self) -> None:
        tala = eitt("Sótt (UTC): 2026-09-10T11:46:23Z")
        self.assertEqual(tala.tegund, "timastimpill")
        self.assertFalse(tala.visst)

    def test_iso_dagsetning(self) -> None:
        self.assertEqual(eitt("frá 2023-11-01 til").tegund, "dagsetning")

    def test_islensk_dagsetning(self) -> None:
        for texti in ("18. desember 2023", "8.–13. nóvember", "01.11.",
                      "1.11.2023"):
            with self.subTest(texti=texti):
                tala = eitt(texti)
                self.assertEqual(tala.tegund, "dagsetning")
                self.assertFalse(tala.visst)

    def test_klukka_med_kommu_a_eftir(self) -> None:
        # Fyrri útgáfa sló þessu upp sem hlutfallstölu af því að eftirlitið
        # leyfði ekki kommu strax á eftir tímanum.
        self.assertEqual(eitt("kl. 00:00, sjá").tegund, "klukka")

    def test_thattaraudkenni(self) -> None:
        for texti in ("0405", "0212-0213"):
            with self.subTest(texti=texti):
                self.assertEqual(eitt(texti).tegund, "thattaraudkenni")

    def test_issue_tilvisun(self) -> None:
        self.assertEqual(eitt("sjá issue #14").tegund, "tilvisun")

    def test_audkenni_med_tolustaf(self) -> None:
        for texti in ("utf8", "SHA-256", "n+3", "tAPP-v1"):
            with self.subTest(texti=texti):
                self.assertEqual(eitt(texti).tegund, "aukenni")

    def test_css_og_litur(self) -> None:
        self.assertEqual(eitt("1px").tegund, "css")
        self.assertEqual(eitt("#223dc4").tegund, "litur")

    def test_ar_er_ekki_nidurstada(self) -> None:
        tala = eitt("árið 1920.")
        self.assertEqual(tala.tegund, "ar")
        self.assertFalse(tala.visst)

    def test_regex_kvardi(self) -> None:
        self.assertEqual(eitt(".{0,80}").tegund, "kodatala")

    def test_ekkert_er_thaggad(self) -> None:
        """Tala sem er ekki niðurstaða er áfram skráð, bara visst=False."""
        tolur = finna_tolur("Sótt 2023-11-01, sjá #14 og 0405 og utf8")
        self.assertEqual(len(tolur), 4)
        self.assertTrue(all(not t.visst for t in tolur))


class BandstrikEkkiMinusProf(unittest.TestCase):
    """Bandstrik inni í auðkenni er skiltákn, ekki mínus (issue #38).

    Fyrri útgáfa klauf keðjuna á bandstrikinu og las seinni hlutann sem
    neikvæða tölu. Það skilaði þrettán færslum í viðmiðinu sem gamla síðan
    birtir ekki — og hefði skilað óútskýranlegum frávikum í #16. Dæmin hér eru
    tekin óbreytt úr byggðu gömlu síðunni; þau festa hverja mynd fyrir sig svo
    hnökrinn komi ekki aftur.
    """

    def test_wigos_audkenni_er_eitt_audkenni(self) -> None:
        # 0-20000-0-04030 gaf áður 0, -20000, -0 og -04030 — fjórar „tölur“.
        tala = eitt('"wigos" : "0-20000-0-04030"')
        self.assertEqual((tala.texti, tala.tegund, tala.gildi),
                         ("0-20000-0-04030", "aukenni", None))
        self.assertFalse(tala.visst)

    def test_hnit_i_beidnisslod_gefa_enga_neikvaeda_tolu(self) -> None:
        # POLYGON((-23 64.1,...)) prósentukóðað: ((-23 gaf áður -23.
        tolur = finna_tolur(
            "&polygon=POLYGON%28%28-23+64.1%2C-23+63.7%29%29&format=json")
        self.assertEqual([t.gildi for t in tolur if t.gildi is not None
                          and t.gildi < 0], [])

    def test_lon_i_stodvasvari_heldur_minusnum(self) -> None:
        # Hér stendur formerkið eitt og sér: þetta ER negatíf lengdargráða.
        tala = eitt('"lon" : -21.9081897736')
        self.assertEqual(tala.gildi, -21.9081897736)

    def test_skyrslunumer_er_eitt_audkenni(self) -> None:
        # VÍ 2009-013 gaf áður árið 2009 og heiltöluna -013.
        tolur = finna_tolur("Veðurstofan fjallar um Mlw í skýrslu VÍ 2009-013")
        self.assertEqual([(t.texti, t.tegund) for t in tolur],
                         [("2009-013", "aukenni")])

    def test_thattaaudkenni_tvofalds_handrits(self) -> None:
        # 1017-1018 gaf áður heiltölurnar 1017 og -1018, báðar visst=True.
        tala = eitt("sérefni ( 1017-1018 )")
        self.assertEqual((tala.texti, tala.tegund), ("1017-1018", "aukenni"))
        self.assertFalse(tala.visst)

    def test_minus_eitt_og_ser_er_afram_minus(self) -> None:
        """Raunverulegar neikvæðar tölur úr gömlu síðunni tapast ekki."""
        for texti, gildi in (("Lengdargráða −23 til", -23),
                             ("til −21,5; breiddargráða", -21.5),
                             ("Hnit VR-II (64,1386922, -21,9556406) voru",
                              -21.9556406)):
            with self.subTest(texti=texti):
                tolur = finna_tolur(texti)
                self.assertIn(gildi, [t.gildi for t in tolur])

    def test_sertaekari_keðjur_halda_tegund_sinni(self) -> None:
        """Dagsetning, þáttaauðkenni og árabil eru líka tölur með bandstriki."""
        for texti, tegund in (("2023-11-01", "dagsetning"),
                              ("0212-0213", "thattaraudkenni"),
                              ("2014-2023", "arabil"),
                              ("2026-W35", "vika")):
            with self.subTest(texti=texti):
                self.assertEqual(eitt(texti).tegund, tegund)

    def test_keðjan_er_skrad_ekki_hent(self) -> None:
        """Keðjan fellur ekki út þegjandi — hún er skráð sem auðkenni."""
        tolur = finna_tolur("skrárnar 0212-0213 og 1017-1018 eru tvöfaldar")
        self.assertEqual([t.texti for t in tolur], ["0212-0213", "1017-1018"])


class ProsentukodunEkkiHlutfallProf(unittest.TestCase):
    """% á eftir tveimur sextándastöfum er prósentukóðun, ekki hlutfall (#44).

    Fyrri útgáfa las tölustafina á UNDAN % sem hlutfall, en í prósentukóðaðri
    slóð tilheyrir % næsta kóðatákninu, ekki tölunni á undan: ``%3A`` er
    tvípunktur, ekki „3A prósent“. Dæmin eru tekin óbreytt úr
    beiðnislóð Skjálftavaktarinnar sem stendur í ``capstone/earthquakes.html``.
    """

    def test_prosentukodadur_tvipunktur(self) -> None:
        # %3A er tvípunktur. Fyrri útgáfa las "00%" sem 0%.
        tolur = finna_tolur("start_time=2023-11-01T00%3A00")
        self.assertIn(("00", "heiltala"),
                      [(t.texti, t.tegund) for t in tolur])
        self.assertNotIn("hlutfall", [t.tegund for t in tolur])

    def test_prosentukodud_svigi(self) -> None:
        # %28 er opnunarsvigi. Fyrri útgáfa las "28%" sem 28%.
        tolur = finna_tolur("polygon=POLYGON%28%28-23")
        self.assertIn(("28", "heiltala"),
                      [(t.texti, t.tegund) for t in tolur])
        self.assertNotIn("hlutfall", [t.tegund for t in tolur])

    def test_prosentukodud_lokunarsvigi(self) -> None:
        # %29 er lokunarsvigi. Fyrri útgáfa las "29%" sem 29%.
        tolur = finna_tolur("64.1%2C-21.5+63.7%29&type=earthquake")
        self.assertIn(("29", "heiltala"),
                      [(t.texti, t.tegund) for t in tolur])
        self.assertNotIn("hlutfall", [t.tegund for t in tolur])

    def test_oll_beidnisslodin_gefur_enga_falska_hlutfallstolu(self) -> None:
        # Nákvæma slóðin úr docs/vidmid/generated/earthquakes-source.md.
        slod = (
            "https://api.vedur.is/quakes/events?start_time="
            "2023-11-01T00%3A00%3A00%2B00%3A00&end_time="
            "2024-01-01T00%3A00%3A00%2B00%3A00&depth_min=0&depth_max=50"
            "&size_min=3&size_max=7&polygon=POLYGON%28%28-23+64.1%2C-23"
            "+63.7%2C-21.5+63.7%2C-21.5+64.1%2C-23+64.1%29%29"
            "&type=earthquake&evaluation_mode=manual&format=json&system=sil"
        )
        tolur = finna_tolur(slod)
        self.assertEqual([t for t in tolur if t.tegund == "hlutfall"], [])

    def test_ekta_hlutfall_a_eftir_venjulegu_orði_helst_oskert(self) -> None:
        """Vörnin gildir aðeins þegar tveir sextándastafir fylgja beint á eftir."""
        for texti in ("2 078 (2,95 %) standa óflokkuð",
                      "343 af 778, eða um 44 %.",
                      "hlutfallið er 28%"):
            with self.subTest(texti=texti):
                self.assertIn("hlutfall",
                              [t.tegund for t in finna_tolur(texti)])


if __name__ == "__main__":
    unittest.main()
