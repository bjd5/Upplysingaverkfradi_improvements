"""Próf fyrir hleðslu jarðskjálftanna í SQL-grunninn (issue #6).

Hin prófin (``test_jardskjalftar.py``) sannreyna lesturinn úr frosna svarinu.
Hér er prófað það sem aðeins sést **í grunninum sjálfum**:

* fjöldatölurnar sem verkið á að hitta — 334 atburðir, 61 dagur, enginn
  ``magnitude_type`` ``NULL`` — lesnar með fyrirspurn eftir hleðslu,
* að dagleg talning stemmi **dag fyrir dag** við tölurnar sem gamla síðan
  birti (``docs/vidmid/generated/earthquakes-results.md``); víki tala er það
  villa (regla 8),
* að CHECK- og FOREIGN KEY-skilyrði migration 002 séu seinni varnarlínan:
  færsla utan sía beiðninnar kemst ekki inn þótt hún kæmi framhjá hleðslunni.

Allar fyrirspurnir eru með breytum (regla 5).
"""

from __future__ import annotations

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from vinnsla.jardskjalftar_afmorkun import SkjalftaVilla, lesa_afmorkun  # noqa: E402
from vinnsla.jardskjalftar_hledsla import hlada  # noqa: E402

VIDMID = ROT / "docs" / "vidmid" / "generated" / "earthquakes-results.md"
PROVENANCE = ROT / "data" / "raw" / "vedur-quakes" / "provenance.json"

VAENTIR_ATBURDIR = 334
VAENTIR_DAGAR = 61
VAENTIR_NULLDAGAR = 43
VAENT_HAMARK = 187
VAENTUR_HAMARKSDAGUR = "2023-11-10"

# Dagalína viðmiðsins: <time datetime="2023-11-01"> ... count-value">1</span>
VIDMIDSMYNSTUR = re.compile(
    r'<time datetime="(\d{4}-\d{2}-\d{2})">.*?earthquake-count-value">(\d+)</span>'
)

# Gild færsla eins og hún lítur út í grunninum — notuð til að prófa að
# skilyrði migration 002 hafni breyttum útgáfum hennar. Dálkaröðin er lesin
# úr lyklunum svo hún geti ekki farið á skjön við gildin.
GILD_FAERSLA: dict[str, object] = {
    "event_id": "SIL1235710",
    "source_system": "SIL",
    "event_number": "1235710",
    "occurred_at": "2023-11-01T00:56:41.645Z",
    "utc_day": "2023-11-01",
    "magnitude": 3.74,
    "magnitude_type": "Mlw",
    "depth_km": 5.126,
    "latitude": 63.86282,
    "longitude": -22.52034,
    "event_type": "earthquake",
    "evaluation_mode": "manual",
}
DALKAR = tuple(GILD_FAERSLA)

SQL_SETJA = (
    "INSERT INTO earthquakes ("
    "    event_id, source_system, event_number, occurred_at, utc_day,"
    "    magnitude, magnitude_type, depth_km, latitude, longitude,"
    "    event_type, evaluation_mode"
    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


def vidmidstalning() -> dict[str, int]:
    """Les daglegu talninguna sem gamla síðan birti."""
    texti = VIDMID.read_text(encoding="utf-8")
    return {dagur: int(n) for dagur, n in VIDMIDSMYNSTUR.findall(texti)}


class HledsluProf(unittest.TestCase):
    """Hleðslan keyrð frá enda til enda á frosnu gögnunum."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.samband = opna(Path(cls._tmp.name) / "rannsokn.sqlite")
        keyra(cls.samband)
        cls.talning = hlada(cls.samband)
        cls.samband.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()

    def _tala(self, sql: str, breytur: tuple[object, ...] = ()) -> int:
        return self.samband.execute(sql, breytur).fetchone()[0]

    # --- fjöldatölurnar sem verkið á að hitta ----------------------------

    def test_grunnurinn_geymir_334_atburdi(self) -> None:
        self.assertEqual(self._tala("SELECT count(*) FROM earthquakes"), VAENTIR_ATBURDIR)

    def test_grunnurinn_geymir_61_dag(self) -> None:
        self.assertEqual(
            self._tala("SELECT count(*) FROM earthquake_days"), VAENTIR_DAGAR
        )

    def test_dagar_an_atburdar_eru_radir_en_ekki_eydur(self) -> None:
        nulldagar = self._tala(
            "SELECT count(*) FROM earthquake_days WHERE event_count = ?", (0,)
        )

        self.assertEqual(nulldagar, VAENTIR_NULLDAGAR)

    def test_magnitude_type_er_aldrei_null(self) -> None:
        self.assertEqual(
            self._tala("SELECT count(*) FROM earthquakes WHERE magnitude_type IS NULL"),
            0,
        )
        self.assertEqual(
            self._tala(
                "SELECT count(*) FROM earthquakes WHERE trim(magnitude_type) = ?", ("",)
            ),
            0,
        )

    def test_hladan_skilar_somu_tolum_og_grunnurinn(self) -> None:
        self.assertEqual(self.talning.atburdir, VAENTIR_ATBURDIR)
        self.assertEqual(self.talning.dagar, VAENTIR_DAGAR)

    # --- enginn atburður utan sía beiðninnar -----------------------------

    def test_enginn_atburdur_utan_sia_beidninnar(self) -> None:
        afmorkun = lesa_afmorkun(PROVENANCE)
        utan = self._tala(
            "SELECT count(*) FROM earthquakes WHERE "
            "magnitude < ? OR magnitude > ? OR depth_km < ? OR depth_km > ? OR "
            "latitude < ? OR latitude > ? OR longitude < ? OR longitude > ? OR "
            "event_type <> ? OR evaluation_mode <> ? OR source_system <> ?",
            (
                afmorkun.staerd_min,
                afmorkun.staerd_max,
                afmorkun.dypt_min,
                afmorkun.dypt_max,
                afmorkun.breidd_min,
                afmorkun.breidd_max,
                afmorkun.lengd_min,
                afmorkun.lengd_max,
                afmorkun.atburdategund,
                afmorkun.matsadferd,
                afmorkun.kerfi.upper(),
            ),
        )

        self.assertEqual(utan, 0)

    def test_allir_atburdir_eru_innan_timabilsins(self) -> None:
        utan = self._tala(
            "SELECT count(*) FROM earthquakes e WHERE NOT EXISTS ("
            "    SELECT 1 FROM earthquake_days d WHERE d.utc_day = e.utc_day)"
        )

        self.assertEqual(utan, 0)

    # --- samanburður við tölurnar sem gamla síðan birti ------------------

    def test_dagleg_talning_stemmir_vid_vidmidid(self) -> None:
        vaent = vidmidstalning()
        raun = {
            rad["utc_day"]: rad["event_count"]
            for rad in self.samband.execute(
                "SELECT utc_day, event_count FROM earthquake_days"
            )
        }

        self.assertEqual(len(vaent), VAENTIR_DAGAR, "viðmiðið á að telja 61 dag")
        self.assertEqual(raun, vaent)

    def test_event_count_stemmir_vid_radirnar_i_earthquakes(self) -> None:
        osamraemi = self.samband.execute(
            "SELECT d.utc_day FROM earthquake_days d "
            "LEFT JOIN earthquakes e ON e.utc_day = d.utc_day "
            "GROUP BY d.utc_day HAVING d.event_count <> count(e.event_id)"
        ).fetchall()

        self.assertEqual([rad["utc_day"] for rad in osamraemi], [])

    def test_haesti_dagurinn_er_sa_sami_og_a_gomlu_sidunni(self) -> None:
        rad = self.samband.execute(
            "SELECT utc_day, event_count FROM earthquake_days "
            "ORDER BY event_count DESC, utc_day LIMIT ?",
            (1,),
        ).fetchone()

        self.assertEqual(rad["utc_day"], VAENTUR_HAMARKSDAGUR)
        self.assertEqual(rad["event_count"], VAENT_HAMARK)

    # --- endurkeyranleiki ------------------------------------------------

    def test_endurkeyrsla_gefur_somu_tolur(self) -> None:
        aftur = hlada(self.samband)
        self.samband.commit()

        self.assertEqual(aftur.atburdir, VAENTIR_ATBURDIR)
        self.assertEqual(aftur.dagar, VAENTIR_DAGAR)


class SkilyrdiGrunnsinsProf(unittest.TestCase):
    """Migration 002 er seinni varnarlínan — ekki aðeins skjölun."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna(Path(self._tmp.name) / "rannsokn.sqlite")
        keyra(self.samband)
        self.samband.execute(
            "INSERT INTO earthquake_days (utc_day, event_count) VALUES (?, ?)",
            ("2023-11-01", 1),
        )

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def _rod(self, **breytt: object) -> tuple[object, ...]:
        gildi = {**GILD_FAERSLA, **breytt}
        return tuple(gildi[dalkur] for dalkur in DALKAR)

    def test_gild_faersla_kemst_inn(self) -> None:
        self.samband.execute(SQL_SETJA, self._rod())

        self.assertEqual(
            self.samband.execute("SELECT count(*) FROM earthquakes").fetchone()[0], 1
        )

    def test_of_stor_skjalfti_er_hafnad(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(SQL_SETJA, self._rod(magnitude=7.4))

    def test_hnit_utan_reits_er_hafnad(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(SQL_SETJA, self._rod(latitude=65.5))

    def test_sjalfvirkt_mat_er_hafnad(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(SQL_SETJA, self._rod(evaluation_mode="automatic"))

    def test_kvardi_sem_vantar_er_hafnad(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(SQL_SETJA, self._rod(magnitude_type=None))

    def test_dagur_utan_timabils_er_hafnad(self) -> None:
        """FOREIGN KEY: atburður á degi sem á sér enga línu kemst ekki inn."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(
                SQL_SETJA,
                self._rod(occurred_at="2024-02-01T00:56:41.645Z", utc_day="2024-02-01"),
            )

    def test_afleiddur_lykill_sem_stemmir_ekki_er_hafnad(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(SQL_SETJA, self._rod(event_number="9999999"))

    def test_tvitekid_audkenni_er_hafnad(self) -> None:
        self.samband.execute(SQL_SETJA, self._rod())

        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(SQL_SETJA, self._rod())


class OkeyrdMigrationProf(unittest.TestCase):
    """Hleðsla á grunn án taflnanna stöðvast með skýrri villu, ekki OperationalError."""

    def test_hledsla_an_migration_stodvast(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            samband = opna(Path(mappa) / "tom.sqlite")
            try:
                with self.assertRaises(SkjalftaVilla) as samhengi:
                    hlada(samband)
            finally:
                samband.close()

        self.assertIn("earthquakes", str(samhengi.exception))


if __name__ == "__main__":
    unittest.main()
