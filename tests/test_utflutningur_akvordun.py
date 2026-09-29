"""Útflutningurinn í heild: sömu bæti, allar skrár eða engin, stærð, yfirlit (#15).

Hvert skilyrði er prófað **þar sem það á að bresta** (docs/agenta-verkefni.md
kafli 15): ákvörðunin yfir *þvinguð* sekúndumörk og á grunni sem var
endurbyggður með annarri hleðsluklukku (``loaded_at``), samskrifin með diski
sem fyllist í miðju. Tvær hraðar keyrslur innan sömu sekúndu sanna ekkert (#47).

Allt úttak fer í tímabundnar möppur; ``web/gogn/`` er aðeins lesið.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import sqlite3
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import utflutningur_grunnur as ug

from hjalp import ROT  # noqa: E402
from utflutningur import json_skrif  # noqa: E402
from utflutningur.flytja_ut import SKRAR, UTFLUTNINGAR, flytja_ut  # noqa: E402
from utflutningur.yfirlit_json import SIDUR  # noqa: E402

VEFGOGN = ROT / "web" / "gogn"
ELDRA = b'{"eldri": true}\n'

# Þak á samtölu allra skráa í web/gogn/. Regla 3.4 leyfir 500 KB í fyrstu hleðslu
# síðu; síða les eina gagnaskrá (json_skrif.HAMARKS_BAETI = 100 KB á skrá) auk
# yfirlits, og HTML, CSS, letur og SVG-myndrit (#17) eiga að hafa meirihlutann.
# 150 KB fyrir ALLAR skrárnar saman heldur útflutningnum að samantektum þótt
# fleiri síður bætist við. Samtalan er nú um 49 KB.
HAMARK_SAMTALS = 150 * 1024


def _baeti(mappa: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(mappa.iterdir()) if p.is_file()}


def _bida_eftir_nyrri_sekundu() -> None:
    upphaf = int(time.time())
    while int(time.time()) == upphaf:
        time.sleep(0.02)


def setUpModule() -> None:
    global _TMP, TMP, GRUNNUR, UT
    _TMP = tempfile.TemporaryDirectory()
    TMP = Path(_TMP.name)
    GRUNNUR = ug.byggja_grunn(TMP / "fyrri.sqlite")
    UT = TMP / "ut"
    UT.mkdir()
    flytja_ut(UT, GRUNNUR)


def tearDownModule() -> None:
    _TMP.cleanup()


class AkvordunProf(unittest.TestCase):
    def _flytja(self, grunnur: Path, heiti: str) -> dict[str, bytes]:
        mappa = TMP / heiti
        mappa.mkdir()
        flytja_ut(mappa, grunnur)
        return _baeti(mappa)

    def test_endurkeyrsla_yfir_sekundumork_gefur_somu_baeti(self) -> None:
        _bida_eftir_nyrri_sekundu()
        self.assertEqual(self._flytja(GRUNNUR, "endurkeyrsla"), _baeti(UT))

    def test_endurbyggdur_grunnur_med_adra_hledsluklukku_gefur_somu_baeti(self) -> None:
        _bida_eftir_nyrri_sekundu()
        annar = ug.byggja_grunn(TMP / "seinni.sqlite")
        klukkur = [sqlite3.connect(g).execute("SELECT loaded_at FROM friends_sources").fetchone()[0]
                   for g in (GRUNNUR, annar)]
        self.assertNotEqual(klukkur[0], klukkur[1], "prófið þvingaði ekki sekúndumörk")
        self.assertEqual(self._flytja(annar, "annar-grunnur"), _baeti(UT))

    def test_uppfaert_er_ekki_i_dag(self) -> None:
        """Bresta: væri klukkan við útflutning notuð stæði dagurinn í dag í skránni."""
        i_dag = datetime.now().astimezone().date()
        for heiti in SKRAR:
            with self.subTest(skra=heiti):
                stund = datetime.fromisoformat(ug.lesa_json(UT / heiti)["uppfaert"])
                self.assertNotEqual(stund.date(), i_dag)


class SamskrifProf(unittest.TestCase):
    """Allar skrár leysa eldri af hólmi saman, eða engin."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.mappa = Path(tmp.name)
        for heiti in SKRAR:
            (self.mappa / heiti).write_bytes(ELDRA)

    def test_diskur_sem_fyllist_i_midjum_skrifum_breytir_engu(self) -> None:
        raunverulegt, kollin = json_skrif.os.fsync, []

        def fyllist(fd: int) -> None:
            kollin.append(fd)
            if len(kollin) == 3:
                raise OSError(28, "No space left on device")
            raunverulegt(fd)

        with mock.patch.object(json_skrif.os, "fsync", side_effect=fyllist):
            with self.assertRaises(OSError):
                flytja_ut(self.mappa, GRUNNUR)
        self.assertEqual(len(kollin), 3)
        self.assertEqual(_baeti(self.mappa), {heiti: ELDRA for heiti in SKRAR})
        self.assertEqual(sorted(p.name for p in self.mappa.iterdir()), sorted(SKRAR))

    def test_skraarheiti_med_moppu_er_hafnad(self) -> None:
        with self.assertRaises(json_skrif.UtflutningsVilla):
            json_skrif.skrifa_allar_atomiskt(self.mappa, {"../utan.json": b"{}"})
        self.assertEqual(_baeti(self.mappa), {heiti: ELDRA for heiti in SKRAR})


class StaerdProf(unittest.TestCase):
    def test_samtala_utflutningsins_er_undir_thakinu(self) -> None:
        staerdir = {h: len(b) for h, b in _baeti(UT).items()}
        self.assertLessEqual(sum(staerdir.values()), HAMARK_SAMTALS, staerdir)

    def test_samtala_web_gogn_i_git_er_undir_thakinu(self) -> None:
        samtals = sum(p.stat().st_size for p in VEFGOGN.iterdir() if p.is_file())
        self.assertLessEqual(samtals, HAMARK_SAMTALS)


class YfirlitProf(unittest.TestCase):
    """Snið sem óbreytt ``stada-gagna.js`` les á forsíðunni."""

    def test_yfirlit_er_a_snidinu_sem_stada_gagna_js_les(self) -> None:
        yfirlit = ug.lesa_json(UT / "yfirlit.json")
        self.assertIsInstance(yfirlit["heimild"], str)
        self.assertIsInstance(yfirlit["gogn"], list)
        self.assertEqual([f["skra"] for f in yfirlit["gogn"]], list(UTFLUTNINGAR))
        for faersla in yfirlit["gogn"]:
            with self.subTest(skra=faersla["skra"]):
                umslag = ug.lesa_json(UT / faersla["skra"])
                self.assertEqual(faersla["uppfaert"], umslag["uppfaert"])
                self.assertEqual(faersla["heimild"], umslag["heimild"])
                self.assertTrue((ROT / "web" / faersla["sida"]).is_file(), faersla["sida"])
        self.assertEqual(yfirlit["uppfaert"], max(f["uppfaert"] for f in yfirlit["gogn"]))

    def test_hver_utflutt_skra_a_sidu(self) -> None:
        self.assertEqual(set(SIDUR), set(UTFLUTNINGAR))


if __name__ == "__main__":
    unittest.main()
