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


if __name__ == "__main__":
    unittest.main()
