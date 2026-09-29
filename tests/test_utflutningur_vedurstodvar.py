"""Próf fyrir útflutning veðurstöðvanna í ``vedurstodvar.json`` (issue #15).

Grunnurinn er byggður úr frosna eintakinu í ``data/raw/vedurstodvar/`` í
tímabundinni möppu og fluttur út í aðra tímabundna möppu. Væntu tölurnar eru
lesnar úr frosna viðmiðinu (``docs/vidmid/vidmid.json``, síðan
``lotur/vefthjonustur/vedurstofan.html``) — töflunni yfir beiðnirnar og
metrunum í svörunum — ekki slegnar inn hér.

    python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import utflutningur_grunnur as ug

from gagnagrunnur.tenging import tenging  # noqa: E402
from utflutningur import vedurstodvar_json  # noqa: E402
from utflutningur.flytja_ut import flytja_ut  # noqa: E402
from utflutningur.json_skrif import UtflutningsVilla, utc_timastimpill  # noqa: E402

SIDA = "lotur/vefthjonustur/vedurstofan.html"
DALKUR_FJOLDA = "Stöðvar í svari"
LINUSKIL = " · "
EINING_METRAR = "m"
EINING_PROSENT = "%"

# Staðreyndir um frosna eintakið sem hleðsluprófin (#8) festa líka.
FJOLDI_STODVA = 778
FJOLDI_NULL_LOKAAR = 343


def setUpModule() -> None:
    global _TMP, GRUNNUR, SKRA
    _TMP = tempfile.TemporaryDirectory()
    mappa = Path(_TMP.name)
    GRUNNUR = ug.byggja_grunn(mappa / "rannsokn.sqlite")
    (mappa / "ut").mkdir()
    flytja_ut(mappa / "ut", GRUNNUR)
    SKRA = mappa / "ut" / vedurstodvar_json.SKRAARHEITI


def tearDownModule() -> None:
    _TMP.cleanup()


def vidmid_beidnir() -> dict[str, int]:
    """Fjöldatafla gömlu síðunnar: færibreytur -> stöðvar í svari."""
    return {
        str(rad["lina"]).partition(LINUSKIL)[0]: int(rad["gildi"])
        for rad in ug.vidmidsradir(SIDA)
        if rad.get("flokkur") == "tafla" and rad.get("sulka") == DALKUR_FJOLDA
    }


def vidmid_eining(eining: str) -> set[int]:
    return {int(rad["gildi"]) for rad in ug.vidmidsradir(SIDA) if rad.get("eining") == eining}


class SnidProf(unittest.TestCase):
    def setUp(self) -> None:
        self.umslag = ug.lesa_json(SKRA)

    def test_reitir_umslagsins(self) -> None:
        self.assertEqual(list(self.umslag), ["uppfaert", "heimild", "gogn", "lysigogn"])

    def test_uppfaert_er_soknartiminn_ur_provenance(self) -> None:
        provenance = ug.lesa_json(ug.VEDURSTODVAR_RA / "provenance.json")
        self.assertEqual(self.umslag["uppfaert"], utc_timastimpill(provenance["fetched_at_utc"]))

    def test_heimild_nefnir_thjonustu_og_leyfi(self) -> None:
        self.assertEqual(
            self.umslag["heimild"],
            "Veðurstofa Íslands — api.vedur.is/weather/stations (CC BY 4.0)",
        )

    def test_sokn_visar_a_frosna_eintakid(self) -> None:
        provenance = ug.lesa_json(ug.VEDURSTODVAR_RA / "provenance.json")
        sokn = self.umslag["lysigogn"]["sokn"]
        self.assertEqual(sokn["hraskra"], f"data/raw/vedurstodvar/{provenance['response_file']}")
        self.assertEqual(sokn["endapunktur"], provenance["endpoint"])
        self.assertEqual(sokn["faeribreytur"], provenance["parameters"])

    def test_stodvar_eru_radadar_eftir_fjarlaegd(self) -> None:
        metrar = [stod["metrar"] for stod in self.umslag["gogn"]]
        self.assertEqual(metrar, sorted(metrar))


class VidmidProf(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.umslag = ug.lesa_json(SKRA)
        cls.svor = cls.umslag["lysigogn"]["svor"]

    def test_778_stodvar_og_343_med_null_lokaar(self) -> None:
        self.assertEqual(self.svor["fjoldi_allra"], FJOLDI_STODVA)
        self.assertEqual(self.svor["fjoldi_virkra"], FJOLDI_NULL_LOKAAR)
        self.assertEqual(self.svor["fjoldi_aflagdra"], FJOLDI_STODVA - FJOLDI_NULL_LOKAAR)

    def test_beidnirnar_fimm_eins_og_i_vidmidinu(self) -> None:
        beidnir = {b["faeribreytur"]: b["fjoldi"] for b in self.umslag["lysigogn"]["beidnir"]}
        vidmid = vidmid_beidnir()
        self.assertEqual(len(vidmid), 5)
        self.assertEqual(beidnir, vidmid)

    def test_gogn_eru_stodvarnar_sem_polygon_skilar(self) -> None:
        beidnir = {b["faeribreytur"]: b["fjoldi"] for b in self.umslag["lysigogn"]["beidnir"]}
        gogn = self.umslag["gogn"]
        self.assertEqual(len(gogn), beidnir["polygon"])
        self.assertEqual(sum(stod["virk"] for stod in gogn), beidnir["polygon + active=true"])
        self.assertTrue(all(stod["virk"] == (stod["lokaar"] is None) for stod in gogn))

    def test_metrarnir_i_svorunum_eru_their_sem_gamla_sidan_birti(self) -> None:
        """639, 689, 50 og 2547 m — hvert svar á sér samsvörun í viðmiðinu og öfugt."""
        self.assertEqual(
            {
                self.svor["naesta_virka"]["metrar"],
                self.svor["naesta_aflagda"]["metrar"],
                self.svor["munur_metrar"],
                self.svor["langtimastod"]["metrar"],
            },
            vidmid_eining(EINING_METRAR),
        )

    def test_hlutfall_virkra_er_44_prosent(self) -> None:
        self.assertEqual({self.svor["hlutfall_virkra_prosent"]}, vidmid_eining(EINING_PROSENT))

    def test_stodvavalid(self) -> None:
        self.assertEqual(
            (self.svor["naesta_virka"]["audkenni"], self.svor["naesta_virka"]["nafn"]),
            (1469, "Reykjavík Hljómskálagarður"),
        )
        self.assertEqual(self.svor["naesta_aflagda"]["audkenni"], 2)
        self.assertEqual(self.svor["langtimastod"]["audkenni"], 1)
        self.assertEqual(self.svor["langtimastod"]["upphafsar"], 1920)
        self.assertEqual(self.svor["naesta_virka"]["upphafsar"], 2022)
        self.assertFalse(self.svor["valin_naer_aftur"])
        self.assertEqual(self.svor["vidmidunarar"], 1976)


class GrunnurinnRaedurProf(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.slod = ug.afrita_grunn(GRUNNUR, Path(tmp.name) / "afrit.sqlite")

    def _breyta(self, sql: str, breytur: tuple = ()) -> None:
        with tenging(self.slod) as samband:
            samband.execute(sql, breytur)

    def _byggja(self) -> dict:
        with tenging(self.slod) as samband:
            return vedurstodvar_json.byggja(samband)

    def test_uppfaert_kemur_ur_grunninum_ekki_ur_klukkunni(self) -> None:
        self._breyta(
            "UPDATE fetch_log SET fetched_at = ? WHERE service = ?",
            ("2001-02-03T04:05:06Z", "vedurstofa-stodvar"),
        )
        self.assertEqual(self._byggja()["uppfaert"], "2001-02-03T04:05:06+00:00")

    def test_stod_sem_vantar_stodvar_utflutning(self) -> None:
        """fetch_log segir 778 en taflan geymir 777 — hálf hleðsla má ekki fara á vefinn."""
        self._breyta("DELETE FROM weather_stations WHERE station_id = ?", (1469,))
        with self.assertRaises(UtflutningsVilla):
            self._byggja()

    def test_engin_sokn_skrad_stodvar_utflutning(self) -> None:
        self._breyta("DELETE FROM fetch_log WHERE service = ?", ("vedurstofa-stodvar",))
        with self.assertRaises(UtflutningsVilla):
            self._byggja()


if __name__ == "__main__":
    unittest.main()
