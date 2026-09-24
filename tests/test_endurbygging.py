"""Próf fyrir scripts/endurbyggja-grunn.sh.

Regla 5: grunnurinn er afleiða, ekki frumgagn. Það þýðir tvennt sem er
prófað hér — hann verður alltaf eins úr sömu heimildum, og hann fer ekki
í git.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ENDURBYGGINGARSKRIFTA, ROT  # noqa: E402

BIDTIMI_SEK = 120


class EndurbyggingProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.grunnur = Path(self._tmp.name) / "rannsokn.sqlite"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _keyra(self, grunnur: Path | None = None) -> subprocess.CompletedProcess[str]:
        umhverfi = {**os.environ, "RANNSOKN_GRUNNUR": str(grunnur or self.grunnur)}
        return subprocess.run(
            ["bash", str(ENDURBYGGINGARSKRIFTA)],
            capture_output=True,
            text=True,
            env=umhverfi,
            cwd=ROT,
            timeout=BIDTIMI_SEK,
        )

    def test_gefur_sama_grunn_tvisvar_i_rod(self) -> None:
        fyrri = self._keyra()
        self.assertEqual(fyrri.returncode, 0, fyrri.stderr)

        seinni = self._keyra()
        self.assertEqual(seinni.returncode, 0, seinni.stderr)

        self.assertTrue(fyrri.stdout.strip(), "Skriftan á að prenta fingrafar")
        self.assertEqual(
            fyrri.stdout.strip(),
            seinni.stdout.strip(),
            "Tvær hreinar endurbyggingar eiga að gefa sama fingrafar",
        )

    def test_byggir_fra_grunni_en_ofan_a_thad_sem_var(self) -> None:
        """Það sem átti sér enga heimild í migrations á að hverfa."""
        self.assertEqual(self._keyra().returncode, 0)

        import sqlite3

        samband = sqlite3.connect(self.grunnur)
        samband.execute("CREATE TABLE handvirk_tafla (a INTEGER)")
        samband.commit()
        samband.close()

        self.assertEqual(self._keyra().returncode, 0)

        samband = sqlite3.connect(self.grunnur)
        toflur = {
            nafn
            for (nafn,) in samband.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        samband.close()
        self.assertNotIn("handvirk_tafla", toflur)
        self.assertIn("schema_migrations", toflur)

    def test_neitar_slod_sem_er_ekki_sqlite(self) -> None:
        """Skriftan eyðir skrá — hún má ekki eyða hverju sem er."""
        nidurstada = self._keyra(Path(self._tmp.name) / "minnispunktar.txt")

        self.assertEqual(nidurstada.returncode, 1)
        self.assertIn("Neita", nidurstada.stderr)

    def test_gagnagrunnurinn_er_utan_git(self) -> None:
        """data/db/ er afleiða og fer aldrei í git (regla 5)."""
        for slod in ("data/db/", "data/db/rannsokn.sqlite"):
            with self.subTest(slod=slod):
                nidurstada = subprocess.run(
                    ["git", "check-ignore", "-q", slod],
                    cwd=ROT,
                    timeout=BIDTIMI_SEK,
                )
                self.assertEqual(
                    nidurstada.returncode, 0, f"{slod} er ekki útilokuð í .gitignore"
                )


if __name__ == "__main__":
    unittest.main()
