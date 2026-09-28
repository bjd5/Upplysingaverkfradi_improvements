"""``main.py --skref hlada`` frá tómum grunni: öll fimm söfnin, talin úr SQL (#39).

Væntu tölurnar eru **ekki handskrifaðar hér**. Þær eru lesnar úr prófum
pakkanna sem byggðu hverja hleðslu (#6–#10) eða úr ``docs/vidmid/vidmid.json``
gegnum hjálpareiningar þeirra — svo ein tala á sér eina heimild.

Hleðslan er keyrð sem undirferli, eins og notandi keyrir hana, á grunn í
tímabundinni möppu (``RANNSOKN_GRUNNUR``). ``data/`` er aðeins lesið.

Bresta-prófin (kafli 6) keyra ``main()`` í sama ferli með einu safni beint á
aðfang sem vantar eða er skemmt, og krefjast rc ≠ 0 og villu sem nefnir safnið.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import logging
import math
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import PYTHON_ROT, ROT  # noqa: E402

import main  # noqa: E402
from friends_grunnur import vidmid_gildi  # noqa: E402
from gagnagrunnur.fingrafar import _oruggt_nafn  # noqa: E402
from keyrsla import hledsla  # noqa: E402
from mbl_grunnur import SVOR_SQL  # noqa: E402
from mbl_vidmid import FROSNA_EINTAKID, vidmidstolur  # noqa: E402
from test_friends_hledsla import FJOLDATOLUR  # noqa: E402
from test_hagstofan_hledsla import AUDKENNI, VAENT_STAERDIR, VAENTAR_MAELINGAR  # noqa: E402
from test_jardskjalftar_hledsla import VAENTIR_ATBURDIR, VAENTIR_DAGAR  # noqa: E402
from test_vedurstodvar_hledsla import FJOLDI_STODVA, FJOLDI_VIRKRA  # noqa: E402
from vinnsla.mbl_eintak import finna_eintok  # noqa: E402

BIDTIMI_SEK = 120
MAIN = PYTHON_ROT / "main.py"

# Hleðslurnar skrá hvert safn; það er ekki það sem bresta-prófin mæla (þau
# grípa villuna á "rannsokn" með assertLogs). Þögnin er aðeins í prófunum.
for _heiti in ("gagnagrunnur", "keyrsla", "vinnsla"):
    logging.getLogger(_heiti).setLevel(logging.ERROR)

# Aðaltafla hvers safns — sú sem verður tóm ef safnið dettur úr hleðslunni.
ADALTOFLUR = {
    "Jarðskjálftar": "earthquakes",
    "Hagstofan": "hagstofan_observations",
    "Veðurstöðvar": "weather_stations",
    "mbl.is": "mbl_extractions",
    "Friends": "friends_transcript_files",
}


def keyra_hledslu(grunnur: Path) -> subprocess.CompletedProcess[str]:
    """``python main.py --skref hlada`` á ``grunnur``, eins og notandi keyrir það."""
    return subprocess.run(
        [sys.executable, str(MAIN), "--skref", "hlada"],
        capture_output=True,
        text=True,
        env={**os.environ, "RANNSOKN_GRUNNUR": str(grunnur)},
        cwd=ROT,
        timeout=BIDTIMI_SEK,
    )


class HeildarhledslaProf(unittest.TestCase):
    """Einn tómur grunnur, ein keyrsla, allar fjöldatölur úr SQL."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.grunnur = Path(cls._tmp.name) / "rannsokn.sqlite"
        cls.keyrsla = keyra_hledslu(cls.grunnur)
        cls.samband = sqlite3.connect(cls.grunnur)
        cls.samband.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()

    def eitt(self, sql: str, breytur: tuple = ()) -> object:
        return self.samband.execute(sql, breytur).fetchone()[0]

    def test_keyrslan_tekst(self) -> None:
        self.assertEqual(self.keyrsla.returncode, 0, self.keyrsla.stderr)
        self.assertIn("Hlóð 5 gagnasöfnum", self.keyrsla.stderr)

    def test_oll_sofnin_eru_skrad_i_hledslunni(self) -> None:
        """Safn sem dettur úr ``SOFN`` fellur hér, ekki aðeins í fjöldaprófunum."""
        self.assertEqual([s.heiti for s in hledsla.SOFN], list(ADALTOFLUR))

    def test_engin_tafla_er_tom(self) -> None:
        """Tafla úr migration sem engin hleðsla fyllir er gat í flæðinu.

        Nær líka til safna sem bætast við síðar: ný migration án hleðslu fellur hér.
        """
        toflur = [
            rad[0]
            for rad in self.samband.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        self.assertGreater(len(toflur), len(ADALTOFLUR))
        for tafla in toflur:
            with self.subTest(tafla=tafla):
                # SQLite tekur ekki töfluheiti sem breytu; heitið fer því gegnum
                # hvítlistann í fingrafar.py (regla 5).
                fjoldi = self.eitt(f"SELECT COUNT(*) FROM {_oruggt_nafn(tafla)}")
                self.assertGreater(fjoldi, 0, f"{tafla} er tóm eftir heildarhleðslu.")

    def test_jardskjalftar(self) -> None:
        self.assertEqual(self.eitt("SELECT COUNT(*) FROM earthquakes"), VAENTIR_ATBURDIR)
        self.assertEqual(self.eitt("SELECT COUNT(*) FROM earthquake_days"), VAENTIR_DAGAR)

    def test_hagstofan_er_margfeldi_viddastaerda(self) -> None:
        fjoldi = self.eitt(
            "SELECT COUNT(*) FROM hagstofan_observations WHERE dataset_id = ?", (AUDKENNI,)
        )
        self.assertEqual(fjoldi, math.prod(VAENT_STAERDIR))
        self.assertEqual(fjoldi, VAENTAR_MAELINGAR)

    def test_vedurstodvar(self) -> None:
        self.assertEqual(self.eitt("SELECT COUNT(*) FROM weather_stations"), FJOLDI_STODVA)
        self.assertEqual(
            self.eitt("SELECT COUNT(*) FROM weather_stations WHERE end_year IS NULL"),
            FJOLDI_VIRKRA,
        )

    def test_mbl_svorin_fimm_eru_vidmidid(self) -> None:
        eintak = next(e for e in finna_eintok() if e.skraarheiti.startswith(FROSNA_EINTAKID))
        radir = self.samband.execute(SVOR_SQL, (eintak.sotta_stund, None, None)).fetchall()
        self.assertEqual([r["nr"] for r in radir], [1, 2, 3, 4, 5])
        self.assertEqual(
            {r["lykill"]: r["gildi"] for r in radir}, vidmidstolur(FROSNA_EINTAKID)
        )

    def test_friends(self) -> None:
        """227 handritsskrár, 61.161 tilsvör o.s.frv. — allt úr vidmid.json."""
        for heiti, fyrirspurn in FJOLDATOLUR:
            with self.subTest(heiti=heiti):
                vaent = vidmid_gildi(heiti)
                if isinstance(vaent, float):
                    self.assertAlmostEqual(self.eitt(fyrirspurn), vaent, delta=0.01)
                else:
                    self.assertEqual(self.eitt(fyrirspurn), vaent)


class BrestaProf(unittest.TestCase):
    """Það sem á að stöðva hleðsluna gerir það — með rc ≠ 0 og safnið nefnt."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.mappa = Path(self._tmp.name)
        self.grunnur = self.mappa / "rannsokn.sqlite"

    def _main_med(self, heiti: str, adfang: Path) -> tuple[int, str]:
        """Keyrir ``main --skref hlada`` með aðfangi eins safns beint á ``adfang``."""
        sofn = tuple(
            replace(s, frosid=adfang) if s.heiti == heiti else s for s in hledsla.SOFN
        )
        self.assertNotEqual(sofn, hledsla.SOFN, f"Ekkert safn heitir {heiti!r}.")
        with (
            mock.patch.object(hledsla, "SOFN", sofn),
            mock.patch.object(main, "GAGNAGRUNNUR", self.grunnur),
            self.assertLogs("rannsokn", "ERROR") as skra,
        ):
            rc = main.main(["--skref", "hlada"])
        return rc, "\n".join(skra.output)

    def _toflur(self) -> set[str]:
        if not self.grunnur.exists():
            return set()
        with sqlite3.connect(self.grunnur) as samband:
            return {r[0] for r in samband.execute("SELECT name FROM sqlite_master")}

    def test_frosid_safn_vantar(self) -> None:
        for safn in hledsla.SOFN:
            with self.subTest(safn=safn.heiti):
                rc, skilabod = self._main_med(safn.heiti, self.mappa / "vantar")
                self.assertEqual(rc, 1)
                self.assertIn(f"{safn.heiti} (#{safn.issue})", skilabod)
                self.assertIn("vantar", skilabod)
                # Stöðvað áður en grunnurinn var snertur.
                self.assertEqual(self._toflur(), set())

    def test_tom_mappa_telst_vanta(self) -> None:
        tom = self.mappa / "tom"
        tom.mkdir()
        rc, skilabod = self._main_med("Friends", tom)
        self.assertEqual(rc, 1)
        self.assertIn("Friends (#10)", skilabod)

    def test_skemmt_adfang_nefnir_safnid_og_ruller_ollu_til_baka(self) -> None:
        """Friends er síðast: fyrri söfnin fjögur mega ekki sitja eftir í grunninum."""
        skemmt = self.mappa / "phoebe-stats"
        skemmt.mkdir()
        (skemmt / "summary.json").write_text("{", encoding="utf-8")
        rc, skilabod = self._main_med("Friends", skemmt)
        self.assertEqual(rc, 1)
        self.assertIn("Hleðsla Friends (#10)", skilabod)
        with sqlite3.connect(self.grunnur) as samband:
            for heiti, tafla in ADALTOFLUR.items():
                with self.subTest(safn=heiti):
                    sql = f"SELECT COUNT(*) FROM {_oruggt_nafn(tafla)}"
                    fjoldi = samband.execute(sql).fetchone()[0]
                    self.assertEqual(fjoldi, 0, f"{tafla} hélt línum eftir rollback.")


if __name__ == "__main__":
    unittest.main()
