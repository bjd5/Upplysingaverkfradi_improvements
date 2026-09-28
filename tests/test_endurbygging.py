"""Próf fyrir scripts/endurbyggja-grunn.sh.

Regla 5: grunnurinn er afleiða, ekki frumgagn. Það þýðir tvennt sem er
prófað hér — hann verður alltaf eins úr sömu heimildum, og hann fer ekki
í git.

Frá #39 hleður skriftan öllum fimm söfnunum, og þau bera keyrslustimpla
(``loaded_at``, ``extracted_at``) á sekúndunákvæmni. Tvær hraðar byggingar
innan sömu sekúndu stemma því af tilviljun (#47, kafli 6), svo prófið bíður
yfir sekúndumörk á milli þeirra og **sannar** að það hafi tekist: allir
keyrslustimplar seinni byggingarinnar eru síðar en þeir fyrri.
"""

from __future__ import annotations

import math
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ENDURBYGGINGARSKRIFTA, ROT  # noqa: E402

from gagnagrunnur.fingrafar import _oruggt_nafn, er_gagnastimpill, er_timastimpill  # noqa: E402

BIDTIMI_SEK = 120

# Aðaltafla hvers safns: fingrafarið sannar lítið ef eitthvert þeirra er tómt.
ADALTOFLUR = (
    "earthquakes",
    "hagstofan_observations",
    "weather_stations",
    "mbl_extractions",
    "friends_transcript_files",
)


def bida_yfir_sekundumork(eftir: float) -> None:
    """Bíður þar til klukkan er komin inn í sekúndu sem hefst eftir ``eftir``."""
    naesta = math.floor(eftir) + 1
    while time.time() < naesta:
        time.sleep(naesta - time.time())


def _dalkar(samband: sqlite3.Connection, tafla: str) -> list[str]:
    return [
        r["name"]
        for r in samband.execute("SELECT name FROM pragma_table_info(?)", (tafla,))
    ]


def keyrslustimplar(grunnur: Path) -> dict[tuple[str, str], list[str]]:
    """Gildi allra keyrslustimpla, eftir (tafla, dálkur).

    Keyrslustimpill hér er hver ``*_at``-dálkur sem er ekki gagnastimpill úr
    provenance. Vísvitandi **ekki** ``sleppt_dalkar``: sönnunin má ekki velta á
    flokkuninni sem hún á að prófa.
    """
    samband = sqlite3.connect(grunnur)
    samband.row_factory = sqlite3.Row
    try:
        toflur = [
            r[0]
            for r in samband.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {
            (tafla, dalkur): [
                r[0]
                for r in samband.execute(
                    f"SELECT {_oruggt_nafn(dalkur)} FROM {_oruggt_nafn(tafla)}"
                )
            ]
            for tafla in toflur
            for dalkur in _dalkar(samband, tafla)
            if er_timastimpill(dalkur) and not er_gagnastimpill(dalkur)
        }
    finally:
        samband.close()


class EndurbyggingProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.grunnur = Path(self._tmp.name) / "rannsokn.sqlite"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _keyra(self, grunnur: Path | None = None) -> subprocess.CompletedProcess[str]:
        # PYTHON úr umhverfinu ræður; annars sami túlkur og prófin (3.12+),
        # því sjálfgefið python3 skriftunnar getur verið of gamalt (#14).
        umhverfi = {
            "PYTHON": sys.executable,
            **os.environ,
            "RANNSOKN_GRUNNUR": str(grunnur or self.grunnur),
        }
        return subprocess.run(
            ["bash", str(ENDURBYGGINGARSKRIFTA)],
            capture_output=True,
            text=True,
            env=umhverfi,
            cwd=ROT,
            timeout=BIDTIMI_SEK,
        )

    def test_gefur_sama_grunn_tvisvar_i_rod(self) -> None:
        """Tvær hreinar byggingar með öllum söfnum, sekúndumörk á milli, eitt fingrafar."""
        grunnur_a = Path(self._tmp.name) / "a.sqlite"
        grunnur_b = Path(self._tmp.name) / "b.sqlite"

        fyrri = self._keyra(grunnur_a)
        self.assertEqual(fyrri.returncode, 0, fyrri.stderr)
        bida_yfir_sekundumork(time.time())
        seinni = self._keyra(grunnur_b)
        self.assertEqual(seinni.returncode, 0, seinni.stderr)

        for grunnur in (grunnur_a, grunnur_b):
            samband = sqlite3.connect(grunnur)
            self.addCleanup(samband.close)
            for tafla in ADALTOFLUR:
                with self.subTest(grunnur=grunnur.name, tafla=tafla):
                    fjoldi = samband.execute(
                        f"SELECT COUNT(*) FROM {_oruggt_nafn(tafla)}"
                    ).fetchone()[0]
                    self.assertGreater(fjoldi, 0, "Safn vantar í bygginguna.")

        # Sönnunin fyrir því að sekúndumörkin voru raunverulega yfirstigin:
        # án hennar gæti prófið staðist af tilviljun (kafli 6).
        stimplar_a, stimplar_b = keyrslustimplar(grunnur_a), keyrslustimplar(grunnur_b)
        self.assertIn(("friends_sources", "loaded_at"), stimplar_a)
        self.assertIn(("mbl_extractions", "extracted_at"), stimplar_a)
        for lykill, gildi_a in stimplar_a.items():
            with self.subTest(stimpill=lykill):
                self.assertLess(max(gildi_a), min(stimplar_b[lykill]))

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
