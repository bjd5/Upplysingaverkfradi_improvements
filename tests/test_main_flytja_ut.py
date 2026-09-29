"""``main.py --skref flytja-ut``: skrifar web/gogn/, bregst með útgangskóða 1 (#15).

Grunnur og úttaksmappa eru tímabundnar (``main.GAGNAGRUNNUR`` og
``main.VEFGOGN`` eru plástraðar) — prófið skrifar aldrei í raunverulega
``web/gogn/``.

    PATH=<python3.12>:$PATH python3 -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import utflutningur_grunnur as ug

import main  # noqa: E402
from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import tenging  # noqa: E402
from utflutningur.flytja_ut import AN_UTFLUTNINGS, SKRAR, UTFLUTNINGAR  # noqa: E402

ELDRA = b'{"eldri": true}\n'


class MainFlytjaUtProf(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.mappa = Path(tmp.name)
        self.vefgogn = self.mappa / "gogn"
        self.vefgogn.mkdir()

    def _main(self, grunnur: Path) -> int:
        with (
            mock.patch.object(main, "GAGNAGRUNNUR", grunnur),
            mock.patch.object(main, "VEFGOGN", self.vefgogn),
        ):
            return main.main(["--skref", "flytja-ut"])

    def test_skrifar_skrarnar_og_nefnir_sofn_an_utflutnings(self) -> None:
        grunnur = ug.byggja_grunn(self.mappa / "rannsokn.sqlite")
        with self.assertLogs("utflutningur.flytja_ut", "WARNING") as skra:
            self.assertEqual(self._main(grunnur), 0)
        self.assertEqual(sorted(p.name for p in self.vefgogn.iterdir()), sorted(SKRAR))
        vidvorun = "\n".join(skra.output)
        for safn in AN_UTFLUTNINGS:
            with self.subTest(safn=safn):
                self.assertIn(safn, vidvorun)

    def test_ohladinn_grunnur_gefur_villu_og_snertir_engar_skrar(self) -> None:
        grunnur = self.mappa / "tomur.sqlite"
        with tenging(grunnur) as samband:
            keyra(samband)
        for heiti in UTFLUTNINGAR:
            (self.vefgogn / heiti).write_bytes(ELDRA)
        with self.assertLogs("rannsokn", "ERROR") as skra:
            self.assertEqual(self._main(grunnur), 1)
        self.assertIn("Útflutningur", "\n".join(skra.output))
        for heiti in UTFLUTNINGAR:
            with self.subTest(skra=heiti):
                self.assertEqual((self.vefgogn / heiti).read_bytes(), ELDRA)

    def test_grunnur_sem_vantar_gefur_villu(self) -> None:
        with self.assertLogs("rannsokn", "ERROR"):
            self.assertEqual(self._main(self.mappa / "vantar.sqlite"), 1)
        self.assertEqual(list(self.vefgogn.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
