"""``main.py --skref vinna``: hvað keyrir, hvað ekki, og hvað er sagt um það (#39).

Netlausu vinnslurnar (P2.3, P2.4) keyra alltaf. Handritavinnslurnar (P2.5,
P2.6) keyra aðeins sé ``FRIENDS_HANDRIT_MAPPA`` stillt, og annars er það sagt
í viðvörun — aldrei þagað (regla 6). Frosnu Friends-tölurnar í
``data/processed/phoebe-stats/`` eru aldrei yfirskrifaðar.

Allt úttak fer í tímabundna möppu; ``data/`` er aðeins lesið. Raunhandritin
eru utan repo-sins (#3), svo prófið sem notar þau keyrir aðeins sé breytan
stillt og er annars sleppt með skýringu.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

import main  # noqa: E402
from keyrsla import urvinnsla  # noqa: E402
from keyrsla.villa import SkrefVilla  # noqa: E402
from vinnsla import central_perk_uttak, phoebe_uttak  # noqa: E402
from vinnsla.friends_handrit import TRANSCRIPT_DIR_ENV  # noqa: E402
from vinnsla.friends_skrar import STATS_MAPPA  # noqa: E402

NETLAUST_UTTAK = (
    "earthquakes/events.csv",
    "earthquakes/daily.csv",
    "earthquakes/samantekt.json",
    "vedurstodvar/mat.json",
)
HANDRITAMOPPUR = (urvinnsla.PHOEBE_ENDURREIKNAD, central_perk_uttak.OUTPUT_DIR.name)

for _heiti in ("gagnagrunnur", "keyrsla", "vinnsla"):
    logging.getLogger(_heiti).setLevel(logging.ERROR)


def _summa_moppu(mappa: Path) -> str:
    """SHA-256 yfir heiti og bæti allra skráa möppunnar."""
    summa = hashlib.sha256()
    for slod in sorted(mappa.iterdir()):
        summa.update(slod.name.encode())
        summa.update(slod.read_bytes())
    return summa.hexdigest()


class VinnslaProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.unnid = Path(self._tmp.name) / "processed"

    def _main(self, umhverfi: dict[str, str]) -> int:
        """``main --skref vinna`` með úttakið í tímabundnu möppunni."""
        umhverfi = {k: v for k, v in os.environ.items() if k != TRANSCRIPT_DIR_ENV} | umhverfi
        with (
            mock.patch.dict(os.environ, umhverfi, clear=True),
            mock.patch.object(main, "GOGN_UNNIN", self.unnid),
        ):
            return main.main(["--skref", "vinna"])

    def test_an_handrita_keyra_netlausar_og_vidvorun_nefnir_hinar(self) -> None:
        with self.assertLogs("keyrsla.urvinnsla", "WARNING") as skra:
            self.assertEqual(self._main({}), 0)

        for skra_heiti in NETLAUST_UTTAK:
            with self.subTest(skra=skra_heiti):
                self.assertTrue((self.unnid / skra_heiti).is_file())
        for mappa in HANDRITAMOPPUR:
            self.assertFalse((self.unnid / mappa).exists(), f"{mappa} varð til án handrita")

        vidvorun = "\n".join(skra.output)
        for heiti in ("phoebe_uttak", "central_perk_uttak", TRANSCRIPT_DIR_ENV, "Ekki keyrt"):
            self.assertIn(heiti, vidvorun)

    def test_tom_breyta_telst_ekki_beidni(self) -> None:
        with mock.patch.dict(os.environ, {TRANSCRIPT_DIR_ENV: "  "}):
            self.assertIsNone(urvinnsla.handritamappa())
        with mock.patch.dict(os.environ, {TRANSCRIPT_DIR_ENV: "/a/b"}):
            self.assertEqual(urvinnsla.handritamappa(), Path("/a/b"))

    def test_breyta_a_moppu_sem_vantar_stodvar_adur_en_nokkud_er_skrifad(self) -> None:
        vantar = str(Path(self._tmp.name) / "ekki-til")
        with self.assertLogs("rannsokn", "ERROR") as skra:
            self.assertEqual(self._main({TRANSCRIPT_DIR_ENV: vantar}), 1)
        self.assertIn(TRANSCRIPT_DIR_ENV, "\n".join(skra.output))
        self.assertEqual(list(self.unnid.iterdir()), [], "Eitthvað var skrifað fyrir villuna.")

    def test_handritavinnslur_skrifa_utan_frosnu_moppunnar(self) -> None:
        handrit = Path(self._tmp.name) / "season"
        handrit.mkdir()
        with (
            mock.patch.object(phoebe_uttak, "run", return_value=[]) as phoebe,
            mock.patch.object(central_perk_uttak, "run", return_value=[]) as central,
        ):
            self.assertEqual(self._main({TRANSCRIPT_DIR_ENV: str(handrit)}), 0)
        phoebe.assert_called_once_with(handrit, self.unnid / urvinnsla.PHOEBE_ENDURREIKNAD)
        central.assert_called_once_with(handrit, self.unnid / HANDRITAMOPPUR[1])

    def test_neitar_ad_skrifa_i_frosnu_phoebe_tolurnar(self) -> None:
        with mock.patch.object(urvinnsla, "PHOEBE_ENDURREIKNAD", STATS_MAPPA.name):
            with self.assertRaises(SkrefVilla):
                urvinnsla.phoebe_mappa(STATS_MAPPA.parent)


@unittest.skipUnless(
    os.environ.get(TRANSCRIPT_DIR_ENV),
    f"{TRANSCRIPT_DIR_ENV} er ekki stillt — raunhandritin eru utan repo-sins (#3).",
)
class RaunhandritProf(unittest.TestCase):
    """Allar fjórar vinnslurnar á raunhandritunum; frosna mappan ósnert."""

    def test_allar_vinnslur_og_frosid_osnert(self) -> None:
        fyrir = _summa_moppu(STATS_MAPPA)
        with tempfile.TemporaryDirectory() as tmp:
            unnid = Path(tmp)
            yfirlit = urvinnsla.vinna_allt(unnid, urvinnsla.handritamappa())
            self.assertEqual(len(yfirlit), 4)
            self.assertEqual(
                len(list((unnid / urvinnsla.PHOEBE_ENDURREIKNAD).iterdir())),
                len(list(STATS_MAPPA.iterdir())),
            )
            self.assertEqual(
                sorted(p.name for p in (unnid / HANDRITAMOPPUR[1]).iterdir()),
                sorted(central_perk_uttak.OUTPUT_FILES),
            )
        self.assertEqual(_summa_moppu(STATS_MAPPA), fyrir)


if __name__ == "__main__":
    unittest.main()
