"""Próf fyrir fingrafarið — mælitækið á að grunnurinn sé afleiða (regla 5)."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import skrifa_migration  # noqa: E402

from gagnagrunnur.fingrafar import (  # noqa: E402
    GAGNASAGNIR,
    KEYRSLUSAGNIR,
    _oruggt_nafn,
    er_gagnastimpill,
    er_keyrslustimpill,
    er_timastimpill,
    fingrafar,
    lysing,
    oflokkadir_stimplar,
)
from gagnagrunnur.keyrari import MIGRATIONS_MAPPA, keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402

MIGRATION = "CREATE TABLE maelingar (id INTEGER PRIMARY KEY, stadur TEXT);"

# Stimplar sem migrations verkefnisins bera í dag, flokkaðir. Prófið krefst
# þess að þeir finnist allir, svo það geti ekki staðist á tómum grunni.
THEKKTIR_KEYRSLUSTIMPLAR = frozenset({"applied_at", "loaded_at", "extracted_at"})
THEKKTIR_GAGNASTIMPLAR = frozenset({"fetched_at", "occurred_at"})

# Mörkin: óflokkuð sögn, tvíræð sögn og tímastimpill utan nafnavenjunnar.
OFLOKKADIR = ("created_at", "saved_at", "Loaded_At")


class HvitlistiProf(unittest.TestCase):
    """Auðkenni er ekki hægt að binda sem breytu, svo það er sannreynt (regla 5)."""

    def test_gild_nofn_eru_vitnud(self) -> None:
        self.assertEqual(_oruggt_nafn("schema_migrations"), '"schema_migrations"')

    def test_hafnar_nofnum_utan_hvitlistans(self) -> None:
        for nafn in ('maelingar"; DROP TABLE maelingar; --', "tafla með bili", "1tafla", ""):
            with self.subTest(nafn=nafn), self.assertRaises(ValueError):
                _oruggt_nafn(nafn)


class FingrafarProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        self.migrations = self.mappa / "migrations"
        self.migrations.mkdir()
        skrifa_migration(self.migrations, 1, "grunnur", MIGRATION)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _byggja(self, heiti: str):
        samband = opna(self.mappa / f"{heiti}.sqlite")
        keyra(samband, self.migrations)
        return samband

    def test_tveir_eins_grunnar_gefa_sama_fingrafar(self) -> None:
        a, b = self._byggja("a"), self._byggja("b")
        try:
            self.assertEqual(fingrafar(a), fingrafar(b))
        finally:
            a.close()
            b.close()

    def test_timastimpill_hefur_ekki_ahrif(self) -> None:
        """applied_at segir hvenær var byggt, ekki hvað — hann telur ekki með."""
        samband = self._byggja("a")
        try:
            fyrir = fingrafar(samband)
            samband.execute(
                "UPDATE schema_migrations SET applied_at = ?", ("1999-01-01T00:00:00+00:00",)
            )
            samband.commit()
            self.assertEqual(fingrafar(samband), fyrir)
        finally:
            samband.close()

    def test_olik_gogn_gefa_olikt_fingrafar(self) -> None:
        samband = self._byggja("a")
        try:
            fyrir = fingrafar(samband)
            samband.execute("INSERT INTO maelingar (stadur) VALUES (?)", ("Reykjanes",))
            samband.commit()
            self.assertNotEqual(fingrafar(samband), fyrir)
        finally:
            samband.close()

    def test_lysing_telur_upp_toflur_og_skema(self) -> None:
        samband = self._byggja("a")
        try:
            texti = lysing(samband)
        finally:
            samband.close()
        self.assertIn("# skema", texti)
        self.assertIn("maelingar", texti)
        self.assertIn("schema_migrations", texti)


class FlokkunProf(unittest.TestCase):
    """Hver ``*_at``-dálkur er annaðhvort keyrslu- eða gagnastimpill (#47).

    Óflokkaður stimpill teldist með í fingrafarinu án þess að nokkur hefði
    ákveðið það. Sé hann af klukkunni gefa tvær byggingar sitt hvora summu um
    leið og sekúnda skilur þær að — villan í #47 aftur.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.mappa = Path(self._tmp.name)

    def _byggja(self, migrations: Path | None) -> sqlite3.Connection:
        samband = opna(self.mappa / "grunnur.sqlite")
        self.addCleanup(samband.close)
        keyra(samband, migrations)
        return samband

    def test_sagnalistarnir_skarast_ekki(self) -> None:
        self.assertFalse(KEYRSLUSAGNIR & GAGNASAGNIR)

    def test_allir_stimplar_verkefnisins_eru_flokkadir(self) -> None:
        samband = self._byggja(MIGRATIONS_MAPPA)
        oflokkadir = oflokkadir_stimplar(samband)
        self.assertEqual(
            oflokkadir,
            [],
            "Þessir tímastimplar eru hvorki keyrslu- né gagnastimplar: "
            + ", ".join(f"{t}.{d}" for t, d in oflokkadir)
            + ". Ákveddu fyrir hvern hvort gildið komi af klukkunni við keyrslu "
            "(sögnin í KEYRSLUSAGNIR — telur ekki með) eða úr hrágögnunum/"
            "provenance (sögnin í GAGNASAGNIR — telur með). Sjá REGLAN í "
            "src/python/gagnagrunnur/fingrafar.py.",
        )

    def test_profid_ser_raunverulega_stimplana(self) -> None:
        """Án þessa gæti prófið á undan staðist af því að engir dálkar fundust."""
        samband = self._byggja(MIGRATIONS_MAPPA)
        toflur = [r["name"] for r in samband.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )]
        stimplar = {
            rad["name"]
            for tafla in toflur
            for rad in samband.execute(f"PRAGMA table_info({_oruggt_nafn(tafla)})")
            if er_timastimpill(rad["name"])
        }
        self.assertLessEqual(THEKKTIR_KEYRSLUSTIMPLAR | THEKKTIR_GAGNASTIMPLAR, stimplar)
        for dalkur in THEKKTIR_KEYRSLUSTIMPLAR:
            with self.subTest(dalkur=dalkur):
                self.assertTrue(er_keyrslustimpill(dalkur))
                self.assertFalse(er_gagnastimpill(dalkur))
        for dalkur in THEKKTIR_GAGNASTIMPLAR:
            with self.subTest(dalkur=dalkur):
                self.assertTrue(er_gagnastimpill(dalkur))
                self.assertFalse(er_keyrslustimpill(dalkur))

    def test_oflokkadur_stimpill_fellir_profid(self) -> None:
        """Mörkin: ný migration með created_at o.fl. verður að gripast."""
        migrations = self.mappa / "migrations"
        migrations.mkdir()
        dalkar = ", ".join(f'"{d}" TEXT' for d in OFLOKKADIR)
        skrifa_migration(
            migrations,
            1,
            "morg",
            "CREATE TABLE records (id INTEGER PRIMARY KEY, "
            "first_loaded_at TEXT, fetched_at TEXT, occurred_at TEXT, "
            f"utc_day TEXT, format TEXT, {dalkar});",
        )
        samband = self._byggja(migrations)
        self.assertEqual(
            oflokkadir_stimplar(samband),
            [("records", d) for d in OFLOKKADIR],
        )

    def test_oflokkadur_stimpill_telur_med(self) -> None:
        """Óflokkaður dálkur er ekki undanskilinn — þess vegna verður að grípa hann."""
        self.assertFalse(er_keyrslustimpill("created_at"))
        self.assertFalse(er_keyrslustimpill("Loaded_At"))
        self.assertTrue(er_timastimpill("Loaded_At"))
        self.assertFalse(er_timastimpill("format"))


if __name__ == "__main__":
    unittest.main()
