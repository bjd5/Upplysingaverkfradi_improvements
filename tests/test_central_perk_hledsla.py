"""Próf fyrir hleðslu Central Perk-niðurstaðnanna í grunninn (issue #10).

Netlaus: frosnu skrárnar í ``data/processed/central-perk-frosid/`` eru hlaðnar í
tímabundinn grunn og **grunnurinn spurður** með fyrirspurnum síðunnar. Væntu
tölurnar eru lesnar úr ``docs/vidmid/vidmid.json`` (tölurnar sem gamla síðan
birti), aldrei handskrifaðar; SQL skilar óafrúnnuðu og prófið námundar eins og
birtingin (Python ``round``, docs/adferdafraedi.md 4.1).

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from central_perk_grunnur import (  # noqa: E402
    inngangstala, songhandrit, vidmidstala,
)
from central_perk_vidmid import VIDMIDSMAPPA, svg_points  # noqa: E402
from friends_grunnur import opna_med_toflum  # noqa: E402

from gagnagrunnur import fyrirspurnir  # noqa: E402
from gagnagrunnur.fingrafar import (  # noqa: E402
    _oruggt_nafn, fingrafar, lysing, oflokkadir_stimplar, sleppt_dalkar,
)
from gagnagrunnur.tenging import UMHVERFISBREYTA, tenging  # noqa: E402
from vinnsla import central_perk_hledsla as hledsla  # noqa: E402
from vinnsla import friends_hledsla  # noqa: E402
from vinnsla.central_perk_adfang import ADFANGSMAPPA, SKRAR  # noqa: E402
from vinnsla.friends_handrit import SOURCE_COMMIT  # noqa: E402
from vinnsla.friends_skrar import STATS_MAPPA  # noqa: E402

# Töflulínur samanburðartöflunnar á gömlu síðunni, eftir hópi.
LINUR = {
    "no_central_perk": "Engin Central Perk-sena",
    "central_perk": "Central Perk, enginn Phoebe-söngur",
    "phoebe_sings": "Phoebe syngur í Central Perk",
}
HANDRIT, MIDGILDI, HLUTFALL = "Handrit", "Miðgildi hlutdeildar Phoebe", "Hinir fimm á móti Phoebe"
STIMPILL_A = "2026-01-01T00:00:00+00:00"
STIMPILL_B = "2026-01-01T00:00:01+00:00"
TOFLUR_SQL = "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'central\\_perk\\_%' ESCAPE '\\'"


def prosent(hlutdeild: float) -> float:
    """Hlutdeild 0–1 → prósenta með einum aukastaf, eins og síðan birti."""
    return round(100 * hlutdeild, 1)


class HladidProf(unittest.TestCase):
    """Frosnu skrárnar hlaðnar einu sinni og grunnurinn spurður."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.samband = opna_med_toflum(Path(cls._tmp.name))
        cls.fjoldi = hledsla.hlada(cls.samband)
        cls.samband.commit()
        cls.samantekt = fyrirspurnir.keyra(cls.samband, "central-perk-samantekt")
        cls.hopar = {r["group_key"]: r for r in fyrirspurnir.keyra(cls.samband, "central-perk-hopar")}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()

    # --- tölurnar úr SQL, bornar við viðmiðið -----------------------------

    def test_samantektin_er_ein_lina(self) -> None:
        self.assertEqual(len(self.samantekt), 1)

    def test_handritsskrar_songhandrit_og_songsenur(self) -> None:
        rad = self.samantekt[0]
        self.assertEqual(rad["transcript_files"], inngangstala("227"))
        self.assertEqual(rad["singing_files"], inngangstala("19"))
        self.assertEqual(rad["singing_scenes"], inngangstala("24"))

    def test_hoparnir_33_175_19(self) -> None:
        for hopur, lina in LINUR.items():
            with self.subTest(hopur=hopur):
                self.assertEqual(self.hopar[hopur]["transcript_files"], vidmidstala(lina, HANDRIT))

    def test_midgildi_hlutdeildar_13_1_14_4_18_6(self) -> None:
        for hopur, lina in LINUR.items():
            with self.subTest(hopur=hopur):
                self.assertEqual(prosent(self.hopar[hopur]["median_phoebe_share"]),
                                 vidmidstala(lina, MIDGILDI))
        self.assertEqual(prosent(self.hopar["phoebe_sings"]["median_phoebe_share"]),
                         inngangstala("18,6%"))
        self.assertEqual(prosent(self.hopar["central_perk"]["median_phoebe_share"]),
                         inngangstala("14,4%"))

    def test_munurinn_4_2_prosentustig(self) -> None:
        self.assertEqual(round(self.samantekt[0]["median_difference_pp"], 1), inngangstala("4,2"))

    def test_hinir_fimm_a_moti_phoebe(self) -> None:
        for hopur, lina in LINUR.items():
            with self.subTest(hopur=hopur):
                self.assertEqual(round(self.hopar[hopur]["median_friends_to_phoebe_ratio"], 1),
                                 vidmidstala(lina, HLUTFALL))

    def test_songhandritin_eru_listi_sidunnar(self) -> None:
        ur_sql = [r["episode_code"] for r in fyrirspurnir.keyra(self.samband, "central-perk-songhandrit")]
        self.assertEqual(len(ur_sql), inngangstala("19"))
        self.assertEqual(ur_sql, songhandrit())

    # --- handritastigið ----------------------------------------------------

    def test_handritastig_endurgerir_punkta_myndarinnar(self) -> None:
        """Borið við óháðan SVG-lestur P2.6 (tests/central_perk_vidmid.py)."""
        ur_sql = {r["episode_code"]: (r["group_key"], f"{r['phoebe_share_pct']:.1f}")
                  for r in fyrirspurnir.keyra(self.samband, "central-perk-handrit")}
        self.assertEqual(ur_sql, svg_points())

    def test_handritskodarnir_eru_their_somu_og_i_friends(self) -> None:
        with (STATS_MAPPA / "phoebe-per-episode.csv").open(encoding="utf-8", newline="") as skra:
            friends = {r["episode_code"] for r in csv.DictReader(skra)}
        ur_sql = {r[0] for r in self.samband.execute(
            "SELECT episode_code FROM central_perk_transcript_files")}
        self.assertEqual(ur_sql, friends)

    def test_segdirnar_sex_i_rod(self) -> None:
        nofn = [r["pattern_name"] for r in fyrirspurnir.keyra(self.samband, "central-perk-segdir")]
        texti = (ADFANGSMAPPA / "phoebe-central-perk-regex.md").read_text(encoding="utf-8")
        self.assertEqual(nofn, re.findall(r"^#### `([A-Z_]+)`$", texti, re.MULTILINE))

    # --- uppruni, höfundaréttur, fingrafar ---------------------------------

    def test_uppruni(self) -> None:
        rad = self.samband.execute("SELECT * FROM central_perk_sources").fetchone()
        self.assertEqual(rad["transcript_repository"], "delvinso/friends-tv-show-analysis")
        self.assertEqual(rad["transcript_commit"], SOURCE_COMMIT)
        self.assertEqual(rad["analysis_commit"], "2865ed6")
        self.assertEqual(rad["input_directory"], "data/processed/central-perk-frosid")
        skrar = [r[0] for r in self.samband.execute(
            "SELECT file_name FROM central_perk_source_files ORDER BY file_name")]
        self.assertEqual(skrar, sorted(SKRAR))

    def test_afritid_er_baetaeins_vidmidinu(self) -> None:
        """Vinnugagnið og sönnunargagnið eru eins (data/processed/README.md, kafli 2)."""
        self.assertEqual(sorted(p.name for p in ADFANGSMAPPA.iterdir()), sorted(SKRAR))
        for heiti in SKRAR:
            with self.subTest(skra=heiti):
                self.assertEqual((ADFANGSMAPPA / heiti).read_bytes(),
                                 (VIDMIDSMAPPA / heiti).read_bytes())

    def test_ekkert_textagildi_er_nytt(self) -> None:
        """Enginn handritstexti: hvert textagildi gagnataflnanna stendur orðrétt í aðfanginu."""
        adfang = "".join((ADFANGSMAPPA / heiti).read_text(encoding="utf-8") for heiti in SKRAR)
        for tafla in ("central_perk_groups", "central_perk_transcript_files", "central_perk_patterns"):
            for rad in self.samband.execute(f"SELECT * FROM {_oruggt_nafn(tafla)}"):
                for gildi in rad:
                    if isinstance(gildi, str):
                        with self.subTest(tafla=tafla, gildi=gildi[:40]):
                            self.assertIn(gildi, adfang)

    def test_loaded_at_er_eini_keyrslustimpillinn(self) -> None:
        self.assertEqual(oflokkadir_stimplar(self.samband), [])
        for (tafla,) in self.samband.execute(TOFLUR_SQL):
            with self.subTest(tafla=tafla):
                vaent = ["loaded_at"] if tafla == "central_perk_sources" else []
                self.assertEqual(sleppt_dalkar(self.samband, tafla), vaent)


class EndurkeyrsluProf(unittest.TestCase):
    """Sama aðfang gefur sama grunn, hversu oft og í hvaða röð sem hlaðið er."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna_med_toflum(Path(self._tmp.name))

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def hlada_klukkan(self, stimpill: str) -> dict[str, int]:
        with mock.patch.object(hledsla, "_nuna", return_value=stimpill):
            return hledsla.hlada(self.samband)

    def test_tvofold_hledsla_breytir_engu(self) -> None:
        fyrri = self.hlada_klukkan(STIMPILL_A)
        fyrra = fingrafar(self.samband)
        self.assertEqual(self.hlada_klukkan(STIMPILL_A), fyrri)
        self.assertEqual(fingrafar(self.samband), fyrra)

    def test_eini_munurinn_yfir_sekundumork_er_loaded_at(self) -> None:
        """Klukkan þvinguð yfir sekúndumörk (#47): seinni hleðslan skrifaði í raun."""
        self.hlada_klukkan(STIMPILL_A)
        fyrra, fyrri_lysing = fingrafar(self.samband), lysing(self.samband)
        self.hlada_klukkan(STIMPILL_B)
        self.assertEqual(fingrafar(self.samband), fyrra)
        self.assertEqual(lysing(self.samband), fyrri_lysing)
        self.assertEqual(self.samband.execute(
            "SELECT loaded_at FROM central_perk_sources").fetchone()[0], STIMPILL_B)

    def test_endurhledsla_ofan_a_grunn_med_friends(self) -> None:
        """Hlaðið ofan á grunn með Friends, og Friends hlaðið aftur á eftir: sama fingrafar."""
        friends_hledsla.hlada(self.samband)
        self.hlada_klukkan(STIMPILL_A)
        fyrra = fingrafar(self.samband)
        self.hlada_klukkan(STIMPILL_B)
        friends_hledsla.hlada(self.samband)
        self.assertEqual(fingrafar(self.samband), fyrra)
        self.assertEqual(self.samband.execute(
            "SELECT COUNT(*) FROM central_perk_transcript_files").fetchone()[0], inngangstala("227"))


class InngangsProf(unittest.TestCase):
    """``python -m vinnsla.central_perk_hledsla`` á tómum grunni."""

    def test_main_hledur_og_skilar_0(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "rannsokn.sqlite"
            # basicConfig myndi bæta varanlegum handfangi á rótarskráninguna.
            with mock.patch.dict(os.environ, {UMHVERFISBREYTA: str(slod)}), \
                    mock.patch("logging.basicConfig"), \
                    self.assertLogs("vinnsla.central_perk_hledsla", "INFO") as skraning:
                self.assertEqual(hledsla.main([]), 0)
            self.assertIn("227 handritsskrár, 19 sönghandrit, 24 söngsenur", skraning.output[0])
            with tenging(slod) as samband:
                self.assertEqual(samband.execute(
                    "SELECT COUNT(*) FROM central_perk_groups").fetchone()[0], 3)

    def test_main_hafnar_roksemdum(self) -> None:
        with self.assertRaises(SystemExit):
            hledsla.main(["--eitthvad"])


if __name__ == "__main__":
    unittest.main()
