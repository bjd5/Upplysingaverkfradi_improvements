"""Endurhleðsla ofan á fyrirliggjandi grunn gefur sama grunn og hrein bygging.

Regla 5: grunnurinn er afleiða af hrágögnum og migrations — ekki af því hversu
oft var hlaðið. ``main.py --skref hlada`` tvisvar á sama grunn á því að gefa
sama fingrafar og hrein bygging úr ``scripts/endurbyggja-grunn.sh``.

Villan sem þetta festir (fannst í #39, PR #60): Hagstofuhleðslan eyddi línu
sinni í ``fetch_log`` og setti hana inn aftur. ``fetch_log.id`` er
AUTOINCREMENT (migration 001), svo auðkennið fór úr 1 í 3 og fingrafarið
breyttist — sama tegund villu og PR #42 lagaði fyrir veðurstöðvarnar.

Kafli 15 (``docs/agenta-verkefni.md``): staðfesting sem getur stemmt af
tilviljun er ekki staðfesting. Því er líka sannað hér að seinni hleðslan
**skrifaði í raun** (keyrslustimpill Hagstofunnar er síðar en í þeirri fyrri)
og að fingrafarið **sér** einmitt þessa villu (auðkenni fært → önnur summa).

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ENDURBYGGINGARSKRIFTA, ROT  # noqa: E402

from gagnagrunnur.fingrafar import fingrafar  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from test_endurbygging import bida_yfir_sekundumork  # noqa: E402
from test_heildarhledsla import keyra_hledslu  # noqa: E402
from vinnsla import hagstofan, vedurstodvar_hledsla  # noqa: E402

BIDTIMI_SEK = 120

SKRANINGAR_SQL = "SELECT service, id FROM fetch_log ORDER BY service"
HLEDSLUSTIMPILL_SQL = "SELECT loaded_at FROM hagstofan_datasets"


def reikna_fingrafar(grunnur: Path) -> str:
    samband = opna(grunnur)
    try:
        return fingrafar(samband)
    finally:
        samband.close()


def lesa(grunnur: Path, sql: str) -> list[tuple]:
    samband = sqlite3.connect(grunnur)
    try:
        return [tuple(rad) for rad in samband.execute(sql)]
    finally:
        samband.close()


def keyra_endurbyggingu(grunnur: Path) -> subprocess.CompletedProcess[str]:
    """``scripts/endurbyggja-grunn.sh`` á ``grunnur`` — hrein bygging frá grunni."""
    umhverfi = {"PYTHON": sys.executable, **os.environ, "RANNSOKN_GRUNNUR": str(grunnur)}
    return subprocess.run(
        ["bash", str(ENDURBYGGINGARSKRIFTA)],
        capture_output=True,
        text=True,
        env=umhverfi,
        cwd=ROT,
        timeout=BIDTIMI_SEK,
    )


class EndurhledslaProf(unittest.TestCase):
    """Tómur grunnur hlaðinn, sami grunnur hlaðinn aftur, borið saman."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        mappa = Path(cls._tmp.name)
        cls.grunnur = mappa / "rannsokn.sqlite"

        cls.fyrri = keyra_hledslu(cls.grunnur)
        cls.fingrafar_a = reikna_fingrafar(cls.grunnur)
        cls.skraningar_a = lesa(cls.grunnur, SKRANINGAR_SQL)
        cls.stimplar_a = lesa(cls.grunnur, HLEDSLUSTIMPILL_SQL)

        # Án sekúndumarka gæti keyrslustimpillinn stemmt af tilviljun og
        # sönnunin fyrir því að seinni hleðslan skrifaði væri engin (kafli 15).
        bida_yfir_sekundumork(time.time())
        cls.seinni = keyra_hledslu(cls.grunnur)
        cls.fingrafar_b = reikna_fingrafar(cls.grunnur)
        cls.skraningar_b = lesa(cls.grunnur, SKRANINGAR_SQL)
        cls.stimplar_b = lesa(cls.grunnur, HLEDSLUSTIMPILL_SQL)

        cls.hrein = keyra_endurbyggingu(mappa / "hrein.sqlite")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_badar_hledslur_takast(self) -> None:
        self.assertEqual(self.fyrri.returncode, 0, self.fyrri.stderr)
        self.assertEqual(self.seinni.returncode, 0, self.seinni.stderr)
        self.assertEqual(self.hrein.returncode, 0, self.hrein.stderr)

    def test_seinni_hledslan_skrifadi_i_raun(self) -> None:
        """Sama fingrafar sannar ekkert ef seinni hleðslan gerði ekkert."""
        self.assertEqual(len(self.stimplar_a), 1)
        self.assertEqual(len(self.stimplar_b), 1)
        self.assertLess(self.stimplar_a[0][0], self.stimplar_b[0][0])

    def test_endurhledsla_gefur_sama_fingrafar(self) -> None:
        self.assertEqual(
            self.fingrafar_b,
            self.fingrafar_a,
            "Endurhleðsla ofan á grunn breytti fingrafarinu — grunnurinn mælir "
            "þá hversu oft var hlaðið, ekki hvað var hlaðið (regla 5).",
        )

    def test_endurhledsla_gefur_sama_fingrafar_og_hrein_bygging(self) -> None:
        self.assertEqual(self.hrein.stdout.strip(), self.fingrafar_a)
        self.assertEqual(self.fingrafar_b, self.hrein.stdout.strip())

    def test_audkenni_i_fetch_log_haldast(self) -> None:
        """Bein athugun á rót vandans — ekki aðeins summan."""
        self.assertEqual(
            self.skraningar_a,
            sorted([(hagstofan.THJONUSTA, 1), (vedurstodvar_hledsla.THJONUSTA, 2)]),
        )
        self.assertEqual(self.skraningar_b, self.skraningar_a)


class FingrafarNaemiProf(unittest.TestCase):
    """Fingrafarið sér villuna sem prófið að ofan á að grípa.

    Án þessa gæti ``A == B`` staðist af því að fingrafarið hunsaði
    ``fetch_log.id`` — og þá væri prófið að ofan staðfesting sem getur ekki
    fallið (kafli 15).
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.grunnur = Path(cls._tmp.name) / "rannsokn.sqlite"
        keyrsla = keyra_hledslu(cls.grunnur)
        if keyrsla.returncode != 0:
            raise AssertionError(keyrsla.stderr)
        cls.upphaflegt = reikna_fingrafar(cls.grunnur)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _breytt(self, sql: str, breytur: tuple) -> str:
        afrit = Path(self._tmp.name) / f"afrit-{self._testMethodName}.sqlite"
        shutil.copyfile(self.grunnur, afrit)
        samband = sqlite3.connect(afrit)
        try:
            with samband:
                self.assertEqual(samband.execute(sql, breytur).rowcount, 1)
        finally:
            samband.close()
        return reikna_fingrafar(afrit)

    def test_faert_audkenni_i_fetch_log_breytir_fingrafari(self) -> None:
        """Nákvæmlega villan: auðkenni Hagstofunnar fer úr 1 í 3."""
        breytt = self._breytt(
            "UPDATE fetch_log SET id = ? WHERE service = ?", (3, hagstofan.THJONUSTA)
        )
        self.assertNotEqual(breytt, self.upphaflegt)

    def test_breytt_gildi_breytir_fingrafari(self) -> None:
        breytt = self._breytt(
            "UPDATE hagstofan_observations SET value = value + 1 "
            "WHERE rowid = (SELECT MIN(rowid) FROM hagstofan_observations "
            "WHERE value IS NOT NULL)",
            (),
        )
        self.assertNotEqual(breytt, self.upphaflegt)


if __name__ == "__main__":
    unittest.main()
