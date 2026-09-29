"""Próf fyrir ``utflutningur.flytja_ut`` — útflutning allra safna í einu (issue #15).

Þrennt er sannað:

* úttaksmappan er breyta og prófin skrifa aldrei í ``web/gogn/``,
* tvær keyrslur á sama grunni gefa sömu bæti (ekkert klukkuháð),
* bregðist eitt safn er **engin** skrá skrifuð — ekki heldur þær sem tókust —
  og eldri skrár standa óbreyttar.

    python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import utflutningur_grunnur as ug

from hjalp import ROT  # noqa: E402
from utflutningur import flytja_ut as eining  # noqa: E402
from utflutningur.flytja_ut import SKRAR, UTFLUTNINGAR, flytja_ut  # noqa: E402
from utflutningur.json_skrif import HAMARKS_BAETI, UtflutningsVilla  # noqa: E402

ELDRA = b'{"eldri": true}\n'
# Þak reglu 3.4 á alla fyrstu hleðslu síðu; gagnaskrá síðu má ekki éta það upp.
SIDUTHAK_BAETI = 500_000


def setUpModule() -> None:
    global _TMP, GRUNNUR
    _TMP = tempfile.TemporaryDirectory()
    GRUNNUR = ug.byggja_grunn(Path(_TMP.name) / "rannsokn.sqlite")


def tearDownModule() -> None:
    _TMP.cleanup()


class FlytjaUtProf(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.mappa = Path(tmp.name)

    def test_sjalfgefin_uttaksmappa_er_web_gogn(self) -> None:
        sjalfgefid = inspect.signature(flytja_ut).parameters["uttaksmappa"].default
        self.assertEqual(sjalfgefid, ROT / "web" / "gogn")

    def test_skrifar_eina_skra_a_hvert_safn(self) -> None:
        skrifadar = flytja_ut(self.mappa, GRUNNUR)
        self.assertEqual([slod.name for slod in skrifadar], list(SKRAR))
        self.assertEqual(sorted(p.name for p in self.mappa.iterdir()), sorted(SKRAR))

    def test_skrarnar_eru_litlar(self) -> None:
        for slod in flytja_ut(self.mappa, GRUNNUR):
            with self.subTest(skra=slod.name):
                self.assertLess(slod.stat().st_size, HAMARKS_BAETI)
                self.assertLess(slod.stat().st_size, SIDUTHAK_BAETI // 5)

    def test_tvaer_keyrslur_gefa_somu_baeti(self) -> None:
        fyrri = {s.name: s.read_bytes() for s in flytja_ut(self.mappa, GRUNNUR)}
        seinni = {s.name: s.read_bytes() for s in flytja_ut(self.mappa, GRUNNUR)}
        self.assertEqual(fyrri, seinni)

    def test_eitt_safn_bregst_og_ekkert_er_skrifad(self) -> None:
        for heiti in UTFLUTNINGAR:
            (self.mappa / heiti).write_bytes(ELDRA)

        def bregst(_samband: object) -> dict:
            raise UtflutningsVilla("prófvilla")

        sidasta = list(UTFLUTNINGAR)[-1]
        with mock.patch.dict(eining.UTFLUTNINGAR, {sidasta: bregst}):
            with self.assertRaises(UtflutningsVilla):
                flytja_ut(self.mappa, GRUNNUR)
        for heiti in UTFLUTNINGAR:
            with self.subTest(skra=heiti):
                self.assertEqual((self.mappa / heiti).read_bytes(), ELDRA)
        self.assertEqual(sorted(p.name for p in self.mappa.iterdir()), sorted(UTFLUTNINGAR))

    def test_vistudu_skrarnar_i_web_gogn_eru_i_takt_vid_grunninn(self) -> None:
        """Skrárnar í git eru afleiddar: ný útflutningskeyrsla á að gefa sömu bæti.

        Prófið les ``web/gogn/`` en skrifar aldrei þangað. Falli það hefur
        grunnurinn eða útflutningurinn breyst án þess að skrárnar væru fluttar út
        á ný — eða einhver hefur handbreytt þeim (regla 5.4).
        """
        for slod in flytja_ut(self.mappa, GRUNNUR):
            with self.subTest(skra=slod.name):
                self.assertEqual((eining.VEFGOGN / slod.name).read_bytes(), slod.read_bytes())

    def test_grunnur_sem_er_ekki_til_er_villa_og_ekki_buinn_til(self) -> None:
        vantar = self.mappa / "ekki-til.sqlite"
        with self.assertRaises(UtflutningsVilla):
            flytja_ut(self.mappa, vantar)
        self.assertFalse(vantar.exists())
        self.assertEqual(list(self.mappa.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
