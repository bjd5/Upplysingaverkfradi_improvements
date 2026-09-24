"""Próf fyrir tengilagið: foreign_keys, breytufyrirspurnir og færslustýring."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.tenging import (  # noqa: E402
    SJALFGEFIN_SLOD,
    UMHVERFISBREYTA,
    opna,
    slod_grunns,
    tenging,
)


class SlodProf(unittest.TestCase):
    """Forgangsröðin: viðfang > umhverfisbreyta > sjálfgefin slóð."""

    def test_vidfang_gengur_fyrir(self) -> None:
        with mock.patch.dict(os.environ, {UMHVERFISBREYTA: "/annar/stadur.sqlite"}):
            self.assertEqual(slod_grunns("/minn/grunnur.sqlite"),
                             Path("/minn/grunnur.sqlite"))

    def test_umhverfisbreyta_gengur_fyrir_sjalfgefnu(self) -> None:
        with mock.patch.dict(os.environ, {UMHVERFISBREYTA: "/ur/umhverfi.sqlite"}):
            self.assertEqual(slod_grunns(), Path("/ur/umhverfi.sqlite"))

    def test_sjalfgefid_thegar_ekkert_er_gefid(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(slod_grunns(), SJALFGEFIN_SLOD)


class TengingProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.grunnur = Path(self._tmp.name) / "prof.sqlite"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_foreign_keys_er_kveikt(self) -> None:
        with tenging(self.grunnur) as samband:
            self.assertEqual(samband.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_foreign_key_er_i_raun_thvingud(self) -> None:
        """Ekki nóg að pragman segist vera á — hún verður að stöðva brot."""
        with tenging(self.grunnur) as samband:
            samband.executescript(
                "CREATE TABLE foreldri (id INTEGER PRIMARY KEY);"
                "CREATE TABLE barn ("
                "  id INTEGER PRIMARY KEY,"
                "  foreldri_id INTEGER NOT NULL REFERENCES foreldri (id)"
                ");"
            )

        with self.assertRaises(sqlite3.IntegrityError):
            with tenging(self.grunnur) as samband:
                samband.execute("INSERT INTO barn (id, foreldri_id) VALUES (?, ?)",
                                (1, 99))

    def test_breytufyrirspurn_kemst_oskemmd_i_gegn(self) -> None:
        """Gildi með SQL-setningafræði á að lenda í dálki, ekki í keyrslu (regla 5)."""
        illkvittid = "Reykjanes'); DROP TABLE maelingar; --"
        with tenging(self.grunnur) as samband:
            samband.execute("CREATE TABLE maelingar (id INTEGER PRIMARY KEY, stadur TEXT)")
            samband.execute("INSERT INTO maelingar (stadur) VALUES (?)", (illkvittid,))

        with tenging(self.grunnur) as samband:
            geymt = samband.execute(
                "SELECT stadur FROM maelingar WHERE stadur = ?", (illkvittid,)
            ).fetchone()
            self.assertIsNotNone(geymt, "Taflan á enn að vera til og geyma gildið")
            self.assertEqual(geymt["stadur"], illkvittid)

    def test_commit_vid_edlileg_lok(self) -> None:
        with tenging(self.grunnur) as samband:
            samband.execute("CREATE TABLE t (a INTEGER)")
            samband.execute("INSERT INTO t (a) VALUES (?)", (1,))

        with tenging(self.grunnur) as samband:
            self.assertEqual(samband.execute("SELECT count(*) FROM t").fetchone()[0], 1)

    def test_rollback_vid_villu_og_villan_heldur_afram(self) -> None:
        """Regla 6: villan er ekki þögguð, og ekkert situr eftir hálfklárað."""
        with tenging(self.grunnur) as samband:
            samband.execute("CREATE TABLE t (a INTEGER)")

        with self.assertRaises(ValueError):
            with tenging(self.grunnur) as samband:
                samband.execute("INSERT INTO t (a) VALUES (?)", (1,))
                raise ValueError("eitthvað fór úrskeiðis í miðri vinnslu")

        with tenging(self.grunnur) as samband:
            self.assertEqual(samband.execute("SELECT count(*) FROM t").fetchone()[0], 0)

    def test_opna_byr_til_moppuna_ef_hana_vantar(self) -> None:
        djupt = Path(self._tmp.name) / "ny" / "mappa" / "grunnur.sqlite"
        samband = opna(djupt)
        samband.close()
        self.assertTrue(djupt.exists())


if __name__ == "__main__":
    unittest.main()
