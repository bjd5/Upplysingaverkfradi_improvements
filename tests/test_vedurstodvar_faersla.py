"""Próf fyrir sannreyningu á einni færslu úr stöðvaskrá Veðurstofunnar (issue #8).

Hér er engin tenging við grunninn — prófuð er þýðingin úr svari þjónustunnar
yfir í ``Stod``, áður en nokkuð fer í ``weather_stations``.

Kjarninn sem má ekki bila: **ólokið tímabil verður ``None``, aldrei tómstrengur.**
Stöð sem mælir enn hefur ekkert lokaár og það er annað en að hafa lokaárið ``""``.
Læddist tómstrengur inn teldist stöðin virk í ``end_year IS NOT NULL`` og
``end_year IS NULL`` hætti að vera marktækt skilyrði. Tómstrengur er því **villa**
hér en ekki gildi sem er þýtt yfir í NULL í kyrrþey (regla 6).

Prófin eru netlaus: þau lesa frosna eintakið og gervifærslur, aldrei þjónustuna.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vinnsla.vedurstodvar_faersla import (  # noqa: E402
    FaersluVilla,
    Stod,
    sannreyna_faerslu,
    sannreyna_svar,
)

ROT = Path(__file__).resolve().parents[1]
FROSID = ROT / "data" / "raw" / "vedurstodvar"

# Staðreyndir um frosna eintakið sjálft. Það er SHA-staðfest og breytist ekki,
# svo þessar tölur eru fastar — um eintakið, ekki um lifandi stöðu stöðvaskrár.
FJOLDI_STODVA = 778
FJOLDI_VIRKRA = 343

# Raunveruleg færsla úr frosna eintakinu, notuð sem grunnur að gervifærslum.
GILD: dict = {
    "station": 1469,
    "name": "Reykjavík Hljómskálagarður",
    "abbr": "hljom",
    "type": "sj",
    "lat": 64.1410522461,
    "lon": -21.9436302185,
    "ele": 4.5,
    "wigos": "0-352-0-001469",
    "owner": "Veðurstofa Íslands",
    "start": 2022,
    "ending": None,
}


def faersla(**breytingar) -> dict:
    """Gild færsla með tilteknum reitum breyttum."""
    return {**GILD, **breytingar}


class LokaarProf(unittest.TestCase):
    """Reiturinn ``ending``: ártal, ekkert — og aldrei tómstrengur."""

    def test_olokid_timabil_verdur_none(self) -> None:
        stod = sannreyna_faerslu(faersla(ending=None), 0)
        self.assertIsNone(stod.end_year)
        self.assertTrue(stod.er_virk)

    def test_lokad_timabil_verdur_artal(self) -> None:
        stod = sannreyna_faerslu(faersla(start=1961, ending=1963), 0)
        self.assertEqual(stod.end_year, 1963)
        self.assertFalse(stod.er_virk)

    def test_tomstrengur_i_lokaari_er_villa_en_ekki_null(self) -> None:
        """Tómstrengur er ekki þýddur yfir í NULL — hann stöðvar hleðsluna."""
        with self.assertRaises(FaersluVilla) as samhengi:
            sannreyna_faerslu(faersla(ending=""), 7)

        bod = str(samhengi.exception)
        self.assertIn("Færsla 7", bod)
        self.assertIn("ending", bod)
        # Villuboðin eiga að segja AF HVERJU þetta skiptir máli.
        self.assertIn("end_year IS NULL", bod)

    def test_artal_sem_texti_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(faersla(start=1961, ending="1963"), 0)

    def test_lokaar_fyrir_upphafsar_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla) as samhengi:
            sannreyna_faerslu(faersla(start=1980, ending=1963), 0)
        self.assertIn("1980", str(samhengi.exception))


class ValfrjalsirReitirProf(unittest.TestCase):
    """``wigos`` og ``owner`` mega vanta — en þá sem NULL, ekki sem tómstrengur."""

    def test_reitur_sem_vantar_verdur_none(self) -> None:
        stod = sannreyna_faerslu(faersla(wigos=None, owner=None), 0)
        self.assertIsNone(stod.wigos_id)
        self.assertIsNone(stod.owner)

    def test_tomstrengur_i_valfrjalsum_reit_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(faersla(wigos=""), 0)

    def test_bil_eitt_og_ser_er_ekki_gildi(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(faersla(owner="   "), 0)


class SnidProf(unittest.TestCase):
    """Snið sem víkur frá því sem eintakið var sannreynt á stöðvar keyrslu."""

    def test_vantandi_reitur_stodvar_thattun(self) -> None:
        an_heitis = {reitur: gildi for reitur, gildi in GILD.items() if reitur != "name"}
        with self.assertRaises(FaersluVilla) as samhengi:
            sannreyna_faerslu(an_heitis, 3)
        self.assertIn("name", str(samhengi.exception))

    def test_bool_telst_ekki_heiltala(self) -> None:
        """``True`` er heiltala í Python en ekki gilt stöðvarauðkenni."""
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(faersla(station=True), 0)

    def test_artal_utan_marka_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(faersla(start=1200), 0)

    def test_tomt_heiti_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(faersla(name=""), 0)

    def test_faersla_sem_er_ekki_hlutur_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_faerslu(["ekki hlutur"], 0)

    def test_sem_rad_fylgir_dalkarod_toflunnar(self) -> None:
        """Röðin verður að vera sú sama og í INSERT-setningu hleðslunnar."""
        stod = sannreyna_faerslu(faersla(), 0)
        self.assertEqual(
            stod.sem_rad(),
            (
                1469,
                "Reykjavík Hljómskálagarður",
                "hljom",
                "sj",
                64.1410522461,
                -21.9436302185,
                4.5,
                "0-352-0-001469",
                "Veðurstofa Íslands",
                2022,
                None,
            ),
        )


class SvarProf(unittest.TestCase):
    """Allt svarið: listi af stöðvum með einkvæmum auðkennum."""

    def test_svar_verdur_ad_vera_listi(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_svar({"stodvar": []})

    def test_tomt_svar_er_villa(self) -> None:
        with self.assertRaises(FaersluVilla):
            sannreyna_svar([])

    def test_tvitekid_audkenni_stodvar_svar(self) -> None:
        with self.assertRaises(FaersluVilla) as samhengi:
            sannreyna_svar([faersla(), faersla(name="Annað heiti")])
        self.assertIn("1469", str(samhengi.exception))

    def test_rod_svarsins_helst(self) -> None:
        stodvar = sannreyna_svar([faersla(station=2), faersla(station=1)])
        self.assertEqual([stod.station_id for stod in stodvar], [2, 1])


class FrosnaEintakidProf(unittest.TestCase):
    """Frosna eintakið sjálft stenst sannreyninguna — allar 778 færslurnar."""

    @classmethod
    def setUpClass(cls) -> None:
        provenance = json.loads(
            (FROSID / "provenance.json").read_text(encoding="utf-8")
        )
        svar = json.loads(
            (FROSID / provenance["response_file"]).read_text(encoding="utf-8")
        )
        cls.stodvar: list[Stod] = sannreyna_svar(svar)

    def test_allar_faerslur_standast_sannreyningu(self) -> None:
        self.assertEqual(len(self.stodvar), FJOLDI_STODVA)

    def test_fjoldi_med_olokid_timabil(self) -> None:
        virkar = [stod for stod in self.stodvar if stod.end_year is None]
        self.assertEqual(len(virkar), FJOLDI_VIRKRA)

    def test_ekkert_lokaar_er_tomstrengur(self) -> None:
        """Lokaárið er heiltala eða ``None`` — ekkert þar á milli."""
        onnur_gerd = [
            stod.end_year
            for stod in self.stodvar
            if stod.end_year is not None and type(stod.end_year) is not int
        ]
        self.assertEqual(onnur_gerd, [])

    def test_audkenni_eru_einkvaem(self) -> None:
        audkenni = [stod.station_id for stod in self.stodvar]
        self.assertEqual(len(set(audkenni)), FJOLDI_STODVA)


if __name__ == "__main__":
    unittest.main()
