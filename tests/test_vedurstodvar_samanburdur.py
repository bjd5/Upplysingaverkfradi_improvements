"""Próf fyrir samanburðinn á veðurstöðvum — að hann mæli gagnamun og ekki sinn eigin.

Prófin eru NETLAUS: þau lesa frosna eintakið og gervigögn, aldrei þjónustuna.
Þau festa ekki tölur dagsins í dag — nýtt eintak MÁ víkja frá viðmiðinu og próf
sem krefðist samsvörunar myndi falla þegar Veðurstofan breytir stöðvaskrá.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT / "src" / "python"))

from vinnsla import vedurstodvar_samanburdur as samanburdur  # noqa: E402
from vinnsla import vedurstodvar_skjal  # noqa: E402

# Gervistöðvar: tvær í kassanum um VR-II (ein virk), ein langt í burtu.
# Hnit 1469 eru raunveruleg (úr frosna svarinu) svo 639 m viðmiðið sé prófanlegt.
NALAEG_VIRK = {"station": 1469, "name": "Nálæg virk", "lat": 64.1410522461,
               "lon": -21.9436302185, "start": 2022, "ending": None}
NALAEG_AFLOGD = {"station": 2, "name": "Nálæg aflögð", "lat": 64.1330, "lon": -21.9500,
                 "start": 1961, "ending": 1963}
FJARLAEG_GOMUL = {"station": 422, "name": "Fjarlæg gömul", "lat": 65.6835, "lon": -18.1002,
                  "start": 1920, "ending": None}
STODVAR = [NALAEG_VIRK, NALAEG_AFLOGD, FJARLAEG_GOMUL]


class SiuProf(unittest.TestCase):
    def test_er_virk_raest_af_ending(self) -> None:
        self.assertTrue(samanburdur.er_virk(NALAEG_VIRK))
        self.assertFalse(samanburdur.er_virk(NALAEG_AFLOGD))

    def test_kassi_er_breidari_i_lengd_en_breidd(self) -> None:
        """Lengdargráða styttist í cos(breidd), svo kassinn er ekki ferningur í gráðum."""
        min_lengd, min_breidd, max_lengd, max_breidd = samanburdur.kassi(
            samanburdur.VR_II_BREIDD, samanburdur.VR_II_LENGD, samanburdur.RADIUS_KM
        )
        self.assertGreater(max_lengd - min_lengd, max_breidd - min_breidd)

    def test_fjarlaeg_stod_er_utan_kassans(self) -> None:
        mork = samanburdur.kassi(samanburdur.VR_II_BREIDD, samanburdur.VR_II_LENGD,
                                 samanburdur.RADIUS_KM)
        self.assertTrue(samanburdur.i_kassa(NALAEG_VIRK, mork))
        self.assertFalse(samanburdur.i_kassa(FJARLAEG_GOMUL, mork))

    def test_siutolur_eru_reiknadar_ur_osiada_svarinu(self) -> None:
        tolur = samanburdur.telja_siur(STODVAR)
        self.assertEqual(tolur["engin sía"], 3)
        self.assertEqual(tolur["`active=true`"], 2)
        self.assertEqual(tolur["`polygon`"], 2)
        self.assertEqual(tolur["`polygon` + `active=true`"], 1)
        self.assertEqual(tolur[f"`station_id={samanburdur.VALIN_STOD}`"], 1)

    def test_haversine_gefur_thekkta_fjarlaegd(self) -> None:
        """639 m milli VR-II og stöðvar 1469 er talan sem gamla síðan birti."""
        metrar = samanburdur.haversine_km(
            samanburdur.VR_II_BREIDD, samanburdur.VR_II_LENGD,
            NALAEG_VIRK["lat"], NALAEG_VIRK["lon"]
        ) * 1000
        self.assertAlmostEqual(metrar, 639, delta=1)


class SvorProf(unittest.TestCase):
    def test_thrju_stodvavol_eru_reiknud(self) -> None:
        svor = samanburdur.svor_nuna(STODVAR)
        self.assertEqual(svor["naesta"][0], NALAEG_VIRK["station"])
        self.assertEqual(svor["naesta_aflogd"][0], NALAEG_AFLOGD["station"])
        # Nálæga virka stöðin hóf mælingar 2022 og dugar ekki 50 ár aftur.
        self.assertEqual(svor["langtimastod"][0], FJARLAEG_GOMUL["station"])

    def test_engin_staekk_stod_stodvar_keyrslu(self) -> None:
        with self.assertRaises(samanburdur.SamanburdarVilla):
            samanburdur.svor_nuna([NALAEG_AFLOGD])


class VidmidsthattunProf(unittest.TestCase):
    """Viðmiðstölurnar eru lesnar úr viðmiðinu, ekki slegnar inn (regla 8)."""

    def _med_vidmidi(self, texti: str):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        tmp.write(texti)
        tmp.close()
        return mock.patch.object(samanburdur, "VIDMID_SIUR", Path(tmp.name))

    def test_taflan_er_thattud(self) -> None:
        tafla = (
            "| Færibreytur | Hvað | Stöðvar |\n|---|---|---:|\n"
            "| engin sía | allar | 778 |\n| `active=true` | virkar | 343 |\n"
        )
        with self._med_vidmidi(tafla):
            self.assertEqual(
                samanburdur.lesa_vidmid_siur(), {"engin sía": 778, "`active=true`": 343}
            )

    def test_tolulaus_tafla_stodvar_keyrslu(self) -> None:
        with self._med_vidmidi("| Færibreytur | Stöðvar |\n|---|---|\n"):
            with self.assertRaises(samanburdur.SamanburdarVilla):
                samanburdur.lesa_vidmid_siur()

    def test_vantandi_vidmid_stodvar_keyrslu(self) -> None:
        with mock.patch.object(samanburdur, "VIDMID_SIUR", Path("/engin/slod.md")):
            with self.assertRaises(samanburdur.SamanburdarVilla):
                samanburdur.lesa_vidmid_siur()

    def test_sia_sem_vidmidid_nefnir_ekki_stodvar_keyrslu(self) -> None:
        """Samanburður við tölu sem er ekki til væri ekki samanburður."""
        with self._med_vidmidi("| Færibreytur | Stöðvar |\n|---|---:|\n| engin sía | 778 |\n"):
            with self.assertRaises(samanburdur.SamanburdarVilla):
                samanburdur.byggja_samanburd()


class FrosidEintakProf(unittest.TestCase):
    """Samanburðurinn á að ganga upp á raunverulegu frosna eintakinu."""

    def setUp(self) -> None:
        self.samanburdur = samanburdur.byggja_samanburd()

    def test_allar_fimm_siur_eru_bornar_saman(self) -> None:
        self.assertEqual(len(self.samanburdur["siur"]), 5)
        for sia in self.samanburdur["siur"]:
            self.assertIsInstance(sia["munur"], int)

    def test_oll_thrju_stodvavol_eru_borin_saman(self) -> None:
        self.assertEqual(set(self.samanburdur["svor"]), set(vedurstodvar_skjal.SVARA_HEITI))

    def test_skjalid_ber_hverja_tolu_sem_reiknud_var(self) -> None:
        texti = vedurstodvar_skjal.byggja_skjal(self.samanburdur)
        for sia in self.samanburdur["siur"]:
            self.assertIn(str(sia["nuna"]), texti)
        self.assertIn(self.samanburdur["eintak"], texti)

    def test_skjalid_a_diski_er_i_takt_vid_gognin(self) -> None:
        """Afleitt skjal sem er handbreytt er ekki lengur afleitt (regla 10)."""
        a_diski = samanburdur.UTTAK.read_text(encoding="utf-8")
        nytt = vedurstodvar_skjal.byggja_skjal(self.samanburdur)
        self.assertEqual(a_diski, nytt)


if __name__ == "__main__":
    unittest.main()
