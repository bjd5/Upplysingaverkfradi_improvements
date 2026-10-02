"""Próf fyrir varnaglann: vinnslan skrifar aldrei í ``web/gogn/`` (kafli 0).

Einingarnar sem nota hann (skjálftar, veðurstöðvar, Phoebe, Central Perk) prófa
hver fyrir sig að úttak þeirra stöðvist við ``web/gogn/``. Hér er varnaglinn
sjálfur prófaður: hvaða möppur hann stöðvar, hverjar hann hleypir í gegn og
að hann falli með villuklasa kallandans. Ekkert er skrifað í ``web/gogn/``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from vinnsla.varnagli import VEFGOGN, krefjast_utan_vefs  # noqa: E402


class EiginVilla(RuntimeError):
    """Villuklasi kallanda, eins og ``MatVilla`` eða ``SkjalftaVilla``."""


class VarnagliProf(unittest.TestCase):
    def test_vefgogn_er_web_gogn_verkefnisins(self) -> None:
        self.assertEqual(VEFGOGN, ROT / "web" / "gogn")

    def test_vefgogn_og_undirmoppur_eru_stodvud(self) -> None:
        for mappa in (VEFGOGN, VEFGOGN / "skjalftar", VEFGOGN / "a" / "b", str(VEFGOGN)):
            with self.subTest(mappa=mappa), self.assertRaisesRegex(ValueError, "skrifar ekki"):
                krefjast_utan_vefs(mappa)

    def test_krokaleid_er_stodvud(self) -> None:
        # Borið saman eftir resolve(): data/../web/gogn er sama mappa.
        with self.assertRaises(ValueError):
            krefjast_utan_vefs(ROT / "data" / ".." / "web" / "gogn")

    def test_afstaed_slod_er_stodvud(self) -> None:
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(ROT)
        with self.assertRaises(ValueError):
            krefjast_utan_vefs(Path("web") / "gogn" / "skjalftar")

    def test_villuklasi_kallandans(self) -> None:
        with self.assertRaisesRegex(EiginVilla, "web"):
            krefjast_utan_vefs(VEFGOGN, EiginVilla)

    def test_systurmappa_og_onnur_web_gogn_eru_leyfd(self) -> None:
        # Varnaglinn ber saman möppur, ekki strengi: "gogn-annad" er ekki "gogn",
        # og web/gogn í annarri rót er ekki birtingarlag þessa verkefnis.
        krefjast_utan_vefs(VEFGOGN.with_name("gogn-annad"))
        krefjast_utan_vefs(ROT / "data" / "processed" / "earthquakes")
        with tempfile.TemporaryDirectory() as mappa:
            krefjast_utan_vefs(Path(mappa) / "web" / "gogn")

    def test_varnaglinn_byr_ekkert_til(self) -> None:
        ny = VEFGOGN / "varnagli-prof"
        with self.assertRaises(ValueError):
            krefjast_utan_vefs(ny)
        self.assertFalse(ny.exists())


if __name__ == "__main__":
    unittest.main()
