"""Central Perk-útflutningurinn borinn við viðmiðið (issue #15, #24).

Samanburðurinn er á **útfluttu, námunduðu gildunum** í
``phoebe-central-perk.json``. Tölurnar eru lesnar úr ``docs/vidmid/vidmid.json``
með uppflettingum ``central_perk_grunnur`` (nákvæmlega ein samsvörun) og
handritastigið úr SVG-mynd gömlu síðunnar (``central_perk_hjalp.svg_points``).

Útflutningurinn skrifar í tímabundna möppu, aldrei í ``web/gogn/``.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import utflutningur_grunnur as ug
from central_perk_grunnur import inngangstala, songhandrit, vidmidstala
from central_perk_hjalp import svg_points

from gagnagrunnur.tenging import opna  # noqa: E402
from utflutningur import central_perk_json  # noqa: E402
from utflutningur.flytja_ut import flytja_ut  # noqa: E402
from utflutningur.json_skrif import UtflutningsVilla  # noqa: E402

HANDRIT, MIDGILDI, HLUTFALL = ("Handrit", "Miðgildi hlutdeildar Phoebe",
                               "Hinir fimm á móti Phoebe")


def setUpModule() -> None:
    global _TMP, GRUNNUR, UMSLAG
    _TMP = tempfile.TemporaryDirectory()
    mappa = Path(_TMP.name)
    GRUNNUR = ug.byggja_grunn(mappa / "rannsokn.sqlite")
    (mappa / "ut").mkdir()
    flytja_ut(mappa / "ut", GRUNNUR)
    UMSLAG = ug.lesa_json(mappa / "ut" / central_perk_json.SKRAARHEITI)


def tearDownModule() -> None:
    _TMP.cleanup()


class VidmidProf(unittest.TestCase):
    def setUp(self) -> None:
        self.lysi = UMSLAG["lysigogn"]

    def test_umslagid(self) -> None:
        self.assertEqual(list(UMSLAG), ["uppfaert", "heimild", "gogn", "lysigogn"])
        # breytt_utc frosnu skránna í docs/vidmid/provenance.json — ekki loaded_at.
        self.assertEqual(UMSLAG["uppfaert"], "2026-09-17T09:47:17+00:00")

    def test_227_19_24_og_munurinn(self) -> None:
        s = self.lysi["samantekt"]
        self.assertEqual(s["handritsskrar"], inngangstala("227"))
        self.assertEqual(s["songhandrit"], inngangstala("19"))
        self.assertEqual(s["songsenur"], inngangstala("24"))
        self.assertEqual(s["munur_midgilda_prosentustig"], inngangstala("4,2"))

    def test_hoparnir(self) -> None:
        """33/175/19 handrit, miðgildi 13,1/14,4/18,6 %, hlutföll 6,7/5,9/4,4."""
        self.assertEqual([h["hopur"] for h in self.lysi["hopar"]],
                         list(central_perk_json.HOPAHEITI))
        for hopur in self.lysi["hopar"]:
            with self.subTest(hopur=hopur["hopur"]):
                self.assertEqual(hopur["handrit"], vidmidstala(hopur["heiti"], HANDRIT))
                self.assertEqual(hopur["midgildi_prosent"], vidmidstala(hopur["heiti"], MIDGILDI))
                self.assertEqual(hopur["hinir_fimm_a_moti_phoebe"],
                                 vidmidstala(hopur["heiti"], HLUTFALL))

    def test_songhandritin_eru_listi_sidunnar(self) -> None:
        self.assertEqual(self.lysi["songhandrit"], songhandrit())

    def test_handritastigid_er_punktar_myndarinnar(self) -> None:
        self.assertEqual(
            {r["handrit"]: (r["hopur"], f"{r['hlutdeild_prosent']:.1f}") for r in UMSLAG["gogn"]},
            svg_points())
        for rad in UMSLAG["gogn"]:
            self.assertEqual(rad["hlutdeild_prosent"], round(rad["hlutdeild_prosent"], 1))

    def test_segdirnar_eru_ordrettar(self) -> None:
        self.assertTrue(self.lysi["segdir"])
        self.assertTrue(all(s["mynstur"] and s["gripur"] and s["sleppur"]
                            for s in self.lysi["segdir"]))


class UppfaertBrestaProf(unittest.TestCase):
    """Bresta: finnist summa frosinnar skráar ekki í provenance er stöðvað."""

    def test_summa_sem_finnst_ekki_stodvar_utflutning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            afrit = Path(tmp) / "afrit.sqlite"
            shutil.copyfile(GRUNNUR, afrit)
            with sqlite3.connect(afrit) as samband:
                samband.execute("UPDATE central_perk_source_files SET sha256 = ? "
                                "WHERE file_name = 'phoebe-central-perk.svg'", ("0" * 64,))
            samband = opna(afrit)
            try:
                with self.assertRaisesRegex(UtflutningsVilla, "phoebe-central-perk.svg"):
                    central_perk_json.byggja(samband)
            finally:
                samband.close()


if __name__ == "__main__":
    unittest.main()
