"""Próf fyrir migration-keyrarann.

Kjarninn: migration er keyrð einu sinni, aldrei breytt eftir á, og hver
keyrsla er annaðhvort heil eða engin (reglur 5 og 6).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import skrifa_migration  # noqa: E402

from gagnagrunnur.keyrari import (  # noqa: E402
    MigrationVilla,
    finna_migrations,
    keyra,
    lesa_skradar,
)
from gagnagrunnur.tenging import opna  # noqa: E402

TAFLA_SQL = "CREATE TABLE {heiti} (id INTEGER PRIMARY KEY, gildi TEXT);"


class KeyrariProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        self.migrations = self.mappa / "migrations"
        self.migrations.mkdir()
        self.samband = opna(self.mappa / "prof.sqlite")

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def _grunnmigration(self) -> Path:
        return skrifa_migration(
            self.migrations, 1, "gagnasofnun", TAFLA_SQL.format(heiti="maelingar")
        )

    # --- eðlileg keyrsla -------------------------------------------------

    def test_keyrir_i_numerarod(self) -> None:
        skrifa_migration(self.migrations, 2, "seinni", TAFLA_SQL.format(heiti="b"))
        skrifa_migration(self.migrations, 1, "fyrri", TAFLA_SQL.format(heiti="a"))

        keyrdar = keyra(self.samband, self.migrations)

        self.assertEqual([m.numer for m in keyrdar], [1, 2])
        self.assertEqual([m.heiti for m in keyrdar], ["fyrri", "seinni"])

    def test_skrair_summu_og_timastimpil(self) -> None:
        slod = self._grunnmigration()
        keyra(self.samband, self.migrations)

        skrad = lesa_skradar(self.samband)[1]
        self.assertEqual(skrad["name"], "gagnasofnun")
        self.assertEqual(skrad["checksum"], finna_migrations(self.migrations)[0].summa)
        self.assertTrue(skrad["applied_at"].startswith("20"), skrad["applied_at"])
        self.assertTrue(slod.exists())

    def test_sama_migration_tvisvar_breytir_engu(self) -> None:
        self._grunnmigration()

        fyrri = keyra(self.samband, self.migrations)
        skrad_eftir_fyrri = lesa_skradar(self.samband)
        seinni = keyra(self.samband, self.migrations)

        self.assertEqual(len(fyrri), 1)
        self.assertEqual(seinni, [], "Seinni keyrsla á ekki að beita neinu")
        self.assertEqual(lesa_skradar(self.samband), skrad_eftir_fyrri)

    # --- sagan verður að stemma ------------------------------------------

    def test_breytt_migration_stodvar_keyrslu(self) -> None:
        slod = self._grunnmigration()
        keyra(self.samband, self.migrations)

        slod.write_text(
            TAFLA_SQL.format(heiti="maelingar") + "\n-- viðbót eftir á\n",
            encoding="utf-8",
        )

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("hefur breyst", str(samhengi.exception))

    def test_skrad_migration_sem_vantar_a_diski_stodvar(self) -> None:
        slod = self._grunnmigration()
        keyra(self.samband, self.migrations)
        slod.unlink()

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("finnst ekki", str(samhengi.exception))

    def test_endurnefnd_migration_stodvar(self) -> None:
        slod = self._grunnmigration()
        keyra(self.samband, self.migrations)
        slod.rename(self.migrations / "001_nytt-heiti.sql")

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("Endurnefndu", str(samhengi.exception))

    def test_obeitt_migration_ur_rod_stodvar(self) -> None:
        """Migration sem birtist undir hæsta keyrða númeri gæfi annan grunn."""
        skrifa_migration(self.migrations, 2, "seinni", TAFLA_SQL.format(heiti="b"))
        keyra(self.samband, self.migrations)

        skrifa_migration(self.migrations, 1, "eftira", TAFLA_SQL.format(heiti="a"))

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("endurbyggja-grunn.sh", str(samhengi.exception))

    # --- skráarheiti og mappa --------------------------------------------

    def test_tvitekid_numer_stodvar(self) -> None:
        skrifa_migration(self.migrations, 1, "fyrri", TAFLA_SQL.format(heiti="a"))
        skrifa_migration(self.migrations, 1, "seinni", TAFLA_SQL.format(heiti="b"))

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("einkvæm", str(samhengi.exception))

    def test_ogilt_skraarheiti_stodvar(self) -> None:
        """Skrá sem passar ekki við mynstrið má ekki hverfa þegjandi (regla 6)."""
        (self.migrations / "Mælingar Útgáfa 2.sql").write_text("SELECT 1;", "utf-8")

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("passar ekki", str(samhengi.exception))

    def test_mappa_sem_vantar_stodvar(self) -> None:
        with self.assertRaises(MigrationVilla):
            keyra(self.samband, self.mappa / "engin-mappa")

    # --- heilindi einnar keyrslu -----------------------------------------

    def test_fallin_migration_rullar_ollu_til_baka(self) -> None:
        """Migration sem fellur í miðju kafi skilur ekkert eftir sig."""
        self._grunnmigration()
        keyra(self.samband, self.migrations)

        skrifa_migration(
            self.migrations,
            2,
            "gallaed",
            TAFLA_SQL.format(heiti="gott") + TAFLA_SQL.format(heiti="gott"),
        )

        with self.assertRaises(MigrationVilla):
            keyra(self.samband, self.migrations)

        toflur = {
            rad["name"]
            for rad in self.samband.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertNotIn("gott", toflur, "Taflan átti að rúllast til baka")
        self.assertNotIn(2, lesa_skradar(self.samband), "Færslan átti ekki að standa")

    def test_migration_med_commit_stodvar(self) -> None:
        """Eigin færslustýring myndi rjúfa heildina sem keyrarinn treystir á."""
        skrifa_migration(
            self.migrations, 1, "med-commit", TAFLA_SQL.format(heiti="a") + "\nCOMMIT;\n"
        )

        with self.assertRaises(MigrationVilla) as samhengi:
            keyra(self.samband, self.migrations)
        self.assertIn("COMMIT", str(samhengi.exception))

    def test_commit_i_athugasemd_er_i_lagi(self) -> None:
        """Orðið COMMIT í athugasemd er texti, ekki færslustýring."""
        skrifa_migration(
            self.migrations,
            1,
            "med-athugasemd",
            "-- COMMIT er ekki leyft hér\n" + TAFLA_SQL.format(heiti="a"),
        )

        self.assertEqual(len(keyra(self.samband, self.migrations)), 1)


if __name__ == "__main__":
    unittest.main()
