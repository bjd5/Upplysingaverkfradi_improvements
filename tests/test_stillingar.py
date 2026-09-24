"""Próf fyrir stillingar: forgangur umhverfis, .env-lestur og lekavörn."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun import stillingar  # noqa: E402
from sofnun.stillingar import (  # noqa: E402
    StillingaVilla,
    krefjast,
    lesa_env_skra,
    tala,
    texti,
)

LYKILL = "ENGINN-RAUNVERULEGUR-LYKILL-123"


class EnvSkraProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.slod = Path(self._tmp.name) / ".env"
        lesa_env_skra.cache_clear()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        lesa_env_skra.cache_clear()

    def test_les_gildi_og_hunsar_athugasemdir(self) -> None:
        self.slod.write_text(
            "# athugasemd\n\nNOTANDA_AUDKENNI=nafn@skoli.is\nBID_MILLI_KALLA=2.5\n",
            encoding="utf-8",
        )
        self.assertEqual(
            lesa_env_skra(self.slod),
            {"NOTANDA_AUDKENNI": "nafn@skoli.is", "BID_MILLI_KALLA": "2.5"},
        )

    def test_gaesalappir_eru_fjarlaegdar(self) -> None:
        self.slod.write_text('NOTANDA_AUDKENNI="nafn@skoli.is"\n', encoding="utf-8")
        self.assertEqual(lesa_env_skra(self.slod)["NOTANDA_AUDKENNI"], "nafn@skoli.is")

    def test_engin_skra_er_ekki_villa(self) -> None:
        self.assertEqual(lesa_env_skra(self.slod), {})

    def test_onyt_lina_nefnir_linunumer_en_ekki_innihald(self) -> None:
        """Línan gæti geymt lykil og má því ekki rata í villuboð (regla 4)."""
        self.slod.write_text(f"GILT=1\n{LYKILL}\n", encoding="utf-8")
        with self.assertRaises(StillingaVilla) as samhengi:
            lesa_env_skra(self.slod)
        self.assertIn("Lína 2", str(samhengi.exception))
        self.assertNotIn(LYKILL, str(samhengi.exception))


class ForgangurProf(unittest.TestCase):
    def setUp(self) -> None:
        lesa_env_skra.cache_clear()

    def test_umhverfi_gengur_fyrir_env_skra(self) -> None:
        ur_skra = {"PROF_BREYTA": "ur-skra"}
        with mock.patch.object(stillingar, "lesa_env_skra", lambda: ur_skra):
            with mock.patch.dict(os.environ, {"PROF_BREYTA": "ur-umhverfi"}):
                self.assertEqual(texti("PROF_BREYTA"), "ur-umhverfi")
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(texti("PROF_BREYTA"), "ur-skra")

    def test_sjalfgefid_thegar_ekkert_finnst(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(texti("PROF_BREYTA_SEM_ER_EKKI_TIL", "sjalfgefid"), "sjalfgefid")

    def test_tomt_gildi_telst_vanta(self) -> None:
        with mock.patch.dict(os.environ, {"PROF_BREYTA": "   "}):
            self.assertIsNone(texti("PROF_BREYTA"))


class KrafaProf(unittest.TestCase):
    def setUp(self) -> None:
        lesa_env_skra.cache_clear()

    def test_villa_nefnir_breytuna_en_ekki_gildid(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(StillingaVilla) as samhengi:
                krefjast("API_LYKILL", "hún geymir lykilinn")
            skilabod = str(samhengi.exception)
        self.assertIn("API_LYKILL", skilabod)
        self.assertIn(".env", skilabod)

    def test_tala_fellur_an_thess_ad_birta_gildid(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": LYKILL}):
            with self.assertRaises(StillingaVilla) as samhengi:
                tala("BID_MILLI_KALLA", 1.0)
        self.assertNotIn(LYKILL, str(samhengi.exception))

    def test_tala_les_gildi(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": "2.5"}):
            self.assertEqual(tala("BID_MILLI_KALLA", 1.0), 2.5)


if __name__ == "__main__":
    unittest.main()
