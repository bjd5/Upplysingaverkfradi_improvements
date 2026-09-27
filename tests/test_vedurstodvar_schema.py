"""Próf fyrir töfluna ``weather_stations`` úr migration 004 (issue #8).

Sannreyning í Python dugir ekki ein og sér: hún ver aðeins þá leið sem
hleðslan fer. Skilyrðin sem æfingin byggir á verða líka að standa í töflunni
sjálfri, svo hvaða innsetning sem er — úr prófi, úr nýrri einingu, úr
sqlite3-skel — geti ekki búið til rað sem gerir ``WHERE``-skilyrðin ómarktæk.

Mikilvægasta skilyrðið: **lokaár er heiltala eða NULL, aldrei tómstrengur.**
``end_year IS NULL`` telur 343 stöðvar en ``end_year = ''`` telur 0, og
tómstrengur læðist óséður í gegnum ``end_year IS NOT NULL`` sem virk stöð.

Hér er líka staðfest að athugasemdin í migration-skránni segi að taflan geymi
**frosið eintak með tiltekinni sóknardagsetningu**, ekki lifandi stöðu.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402

ROT = Path(__file__).resolve().parents[1]
MIGRATION = ROT / "src" / "sql" / "migrations" / "004_vedurstodvar.sql"
PROVENANCE = ROT / "data" / "raw" / "vedurstodvar" / "provenance.json"

INNSETNING = """
INSERT INTO weather_stations (
    station_id, name, abbr, station_type, lat, lon,
    elevation_m, wigos_id, owner, start_year, end_year
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# Gild rað í dálkaröð töflunnar; prófin breyta einum reit í senn.
GILD_RAD: tuple = (
    1469, "Reykjavík Hljómskálagarður", "hljom", "sj",
    64.1410522461, -21.9436302185, 4.5,
    "0-352-0-001469", "Veðurstofa Íslands", 2022, None,
)

# Vísar í GILD_RAD, svo prófin þurfi ekki að telja dálka.
AUDKENNI, HEITI, WIGOS, BREIDD, UPPHAFSAR, LOKAAR = 0, 1, 7, 4, 9, 10

GERD_LOKAARS = "SELECT typeof(end_year) FROM weather_stations WHERE station_id = ?"
GERD_UPPHAFSARS = "SELECT typeof(start_year) FROM weather_stations WHERE station_id = ?"


def rad_med(visir: int, gildi) -> tuple:
    """Gild rað með einum reit skipt út."""
    breytt = list(GILD_RAD)
    breytt[visir] = gildi
    return tuple(breytt)


class ToflunProf(unittest.TestCase):
    """Taflan er byggð úr migration 004 í tímabundnum grunni.

    Migrations eru keyrðar einu sinni fyrir hvern prófunarflokk; hvert próf fær
    tóma töflu. Innsetning sem fellur á CHECK rúllar aðeins sjálfri sér til baka
    í SQLite, svo næsta próf byrjar hreint.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.samband = opna(Path(cls._tmp.name) / "prof.sqlite")
        keyra(cls.samband)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self.samband.rollback()
        self.samband.execute("DELETE FROM weather_stations")

    def setja_inn(self, rad: tuple) -> None:
        """Setur inn eina rað með breytum — aldrei strengjasamsetning (regla 5)."""
        self.samband.execute(INNSETNING, rad)

    def gerd(self, fyrirspurn: str) -> str:
        """``typeof()`` gildisins sem raunverulega lenti í dálkinum.

        Fyrirspurnin er föst og auðkennið kemur inn sem breyta — dálkanafn er
        aldrei límt inn í SQL með strengjasamsetningu (regla 5).
        """
        return self.samband.execute(fyrirspurn, (1469,)).fetchone()[0]


class LokaarSkilyrdiProf(ToflunProf):
    """Kjarni æfingarinnar: NULL og tómstrengur eru ekki það sama."""

    def test_null_lokaar_er_leyft(self) -> None:
        self.setja_inn(GILD_RAD)
        fjoldi = self.samband.execute(
            "SELECT COUNT(*) FROM weather_stations WHERE end_year IS NULL"
        ).fetchone()[0]
        self.assertEqual(fjoldi, 1)

    def test_tomstrengur_i_lokaari_kemst_ekki_inn(self) -> None:
        """Án þessa skilyrðis teldist stöðin virk í ``end_year IS NOT NULL``."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(LOKAAR, ""))

    def test_texti_sem_er_ekki_tala_kemst_ekki_i_lokaarid(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(LOKAAR, "í gangi"))

    def test_lokaar_fyrir_upphafsar_kemst_ekki_inn(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(LOKAAR, 1900))

    def test_artal_i_lokaari_er_leyft(self) -> None:
        self.setja_inn(rad_med(LOKAAR, 2024))
        lokaar = self.samband.execute(
            "SELECT end_year FROM weather_stations WHERE station_id = ?", (1469,)
        ).fetchone()[0]
        self.assertEqual(lokaar, 2024)

    def test_lokaarid_er_heiltala_eda_null_og_ekkert_thar_a_milli(self) -> None:
        """Ekkert gildi kemst í dálkinn sem ``end_year IS NULL`` misreiknar.

        SQLite-dálkur með INTEGER-sækni umbreytir tölustreng í heiltölu ÁÐUR en
        CHECK keyrir, svo ``'2024'`` verður 2024 og er þá rétt geymt gildi en
        ekki texti. Textinn sem er ekki tala — tómstrengur þar með — fær enga
        slíka umbreytingu og stöðvast á CHECK. Hvor leiðin sem farin er stendur
        skilyrðið sem æfingin byggir á: gerðin er ``integer`` eða ``null``.
        """
        # Fyrst það sem á að stöðvast, meðan taflan er tóm — svo frumlykillinn
        # geti ekki verið ástæða þess að innsetningin falli.
        for ogilt in ("", "í gangi", "  "):
            with self.subTest(gildi=ogilt), self.assertRaises(sqlite3.IntegrityError):
                self.setja_inn(rad_med(LOKAAR, ogilt))

        self.setja_inn(rad_med(LOKAAR, "2024"))
        self.assertEqual(self.gerd(GERD_LOKAARS), "integer")


class ADrirDalkarProf(ToflunProf):
    """Hinir dálkarnir: tómstrengur er ekki „vantar“ og auðkenni eru einkvæm."""

    def test_tomstrengur_i_wigos_kemst_ekki_inn(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(WIGOS, ""))

    def test_wigos_ma_vanta_sem_null(self) -> None:
        self.setja_inn(rad_med(WIGOS, None))
        self.assertEqual(
            self.samband.execute("SELECT COUNT(*) FROM weather_stations").fetchone()[0],
            1,
        )

    def test_tomt_heiti_kemst_ekki_inn(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(HEITI, ""))

    def test_hnit_utan_marka_komast_ekki_inn(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(BREIDD, 95.0))

    def test_upphafsar_er_heiltala_eftir_innsetningu(self) -> None:
        """Tölustrengur er umbreyttur af INTEGER-sækni; texti sem er ekki tala fellur."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(UPPHAFSAR, "frá upphafi"))

        self.setja_inn(rad_med(UPPHAFSAR, "2022"))
        self.assertEqual(self.gerd(GERD_UPPHAFSARS), "integer")

    def test_tvitekid_audkenni_kemst_ekki_inn(self) -> None:
        """Frumlykillinn gerir ``station_id = ?`` að leit að nákvæmlega einni stöð."""
        self.setja_inn(GILD_RAD)
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(HEITI, "Sama stöð, annað heiti"))

    def test_audkenni_verdur_ad_vera_jakvaed_heiltala(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.setja_inn(rad_med(AUDKENNI, 0))


class AthugasemdProf(unittest.TestCase):
    """Athugasemdin í 004 verður að segja hvað taflan geymir — og hvað ekki."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.texti = MIGRATION.read_text(encoding="utf-8")
        cls.provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    def test_segir_ad_eintakid_se_frosid_en_ekki_lifandi_stada(self) -> None:
        self.assertIn("FROSIÐ EINTAK, EKKI LIFANDI STAÐA", self.texti)

    def test_nefnir_soknardagsetninguna_ur_provenance(self) -> None:
        """Sóknardagsetningin er lesin úr provenance, ekki slegin inn hér."""
        sott = str(self.provenance["fetched_at_utc"])
        self.assertIn(sott, self.texti)
        self.assertIn(sott.split("T")[0], self.texti)

    def test_nefnir_eintakid_og_uppruna_thess(self) -> None:
        self.assertIn(str(self.provenance["response_file"]), self.texti)
        self.assertIn(str(self.provenance["endpoint"]), self.texti)

    def test_nefnir_skilyrdid_um_null_lokaar(self) -> None:
        self.assertIn("LOKAÁR STARFRÆKSLU ER NULL, ALDREI TÓMSTRENGUR", self.texti)


if __name__ == "__main__":
    unittest.main()
