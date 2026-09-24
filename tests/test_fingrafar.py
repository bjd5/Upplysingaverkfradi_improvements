"""Próf fyrir fingrafarið — mælitækið á að grunnurinn sé afleiða (regla 5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import skrifa_migration  # noqa: E402

from gagnagrunnur.fingrafar import _oruggt_nafn, fingrafar, lysing  # noqa: E402
from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402

MIGRATION = "CREATE TABLE maelingar (id INTEGER PRIMARY KEY, stadur TEXT);"


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


if __name__ == "__main__":
    unittest.main()
