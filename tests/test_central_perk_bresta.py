"""Central Perk-hleðslan þar sem hún á að BRESTA (issue #10, kafli 6).

Hvert próf skemmir **afrit** af frosnu skránum (``central_perk_grunnur.Afrit``)
og krefst villu sem nefnir gallann. Þar sem gallinn á að komast framhjá
SHA-staðfestingunni er afritið endurundirritað, svo næsta varnarlag sé
prófað. Að lokum: skemaskorður 007 beint í SQL, og misheppnuð endurhleðsla
skilur fyrri grunn eftir ósnertan (rollback).

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from central_perk_grunnur import Afrit  # noqa: E402
from friends_grunnur import opna_med_toflum  # noqa: E402

from gagnagrunnur.fingrafar import fingrafar  # noqa: E402
from gagnagrunnur.tenging import tenging  # noqa: E402
from vinnsla import central_perk_hledsla as hledsla  # noqa: E402
from vinnsla.central_perk_adfang import REGEX, SUMMARY, SVG, CentralPerkVilla  # noqa: E402

PUNKTUR_0123 = 'cx="185.3" cy="303.4" r="4.2" fill="#64748B" fill-opacity="0.58"><title>0123: 17.4%'
PUNKTUR_0101 = 'cx="731.9" cy="382.5" r="4.2" fill="#7C3AED" fill-opacity="0.58"><title>0101: 8.9%'


class GallarProf(unittest.TestCase):
    """Hver galli í aðfanginu stöðvar hleðsluna með skýringu."""

    def setUp(self) -> None:
        self.afrit = Afrit()
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna_med_toflum(Path(self._tmp.name))

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()
        self.afrit.loka()

    def hlada(self) -> dict[str, int]:
        return hledsla.hlada(self.samband, self.afrit.mappa, self.afrit.provenance)

    def bresta(self, skyring: str) -> None:
        with self.assertRaisesRegex(CentralPerkVilla, skyring):
            self.hlada()

    def test_oskemmt_afrit_hledst(self) -> None:
        self.assertEqual(self.hlada()["central_perk_transcript_files"], 227)

    # --- SHA-staðfestingin --------------------------------------------------

    def test_breytt_skra_stodvar(self) -> None:
        self.afrit.skipta(SUMMARY, '"singing_scenes": 24', '"singing_scenes": 25', undirrita=False)
        self.bresta(f"{SUMMARY} stemmir ekki við provenance")

    def test_eitt_baeti_i_myndinni_nog(self) -> None:
        self.afrit.skipta(SVG, "17.4%", "17.5%", undirrita=False)
        self.bresta(f"{SVG} stemmir ekki við provenance")

    def test_skra_sem_vantar_stodvar(self) -> None:
        (self.afrit.mappa / REGEX).unlink()
        self.bresta("er ekki til")

    # --- sannreyning hvers reits (endurundirritað) ---------------------------

    def test_hlutdeild_utan_marka(self) -> None:
        self.afrit.skipta(SUMMARY, "0.13057199211045364", "1.3057199211045364")
        self.bresta("median_phoebe_share")

    def test_punktur_yfir_hundrad_prosentum(self) -> None:
        self.afrit.skipta(SVG, "0123: 17.4%", "0123: 174.0%")
        self.bresta("> 100%")

    def test_tala_sem_texti(self) -> None:
        self.afrit.skipta(SUMMARY, '"singing_scenes": 24', '"singing_scenes": "24"')
        self.bresta("singing_scenes")

    def test_tvitekinn_thattakodi(self) -> None:
        self.afrit.skipta(SVG, "<title>0203:", "<title>0123:")
        self.bresta("tvisvar")

    def test_tvitekid_songhandrit(self) -> None:
        self.afrit.skipta(SUMMARY, '"0110",', '"0101",')
        self.bresta("tvíteknir")

    def test_olesanlegur_punktur_sleppur_ekki(self) -> None:
        self.afrit.skipta(SVG, 'r="4.2" fill="#64748B"', 'r="4.3" fill="#64748B"')
        self.bresta("engum sleppt")

    def test_titill_og_stadsetning_stangast_a(self) -> None:
        self.afrit.skipta(SVG, "0123: 17.4%", "0123: 17.6%")
        self.bresta("teiknaður við")

    def test_punktur_i_rongum_dalki(self) -> None:
        self.afrit.skipta(SVG, PUNKTUR_0123, PUNKTUR_0123.replace("#64748B", "#7C3AED"))
        self.bresta("utan dálksins")

    def test_segdarskrain_a_rongu_snidi(self) -> None:
        self.afrit.skipta(REGEX, "**Sleppur:** ", "**Missir:** ")
        self.bresta("sniðinu")

    # --- samræmi milli skráa (endurundirritað) --------------------------------

    def test_n_stemmir_ekki_vid_punktana(self) -> None:
        self.afrit.skipta(SUMMARY, '"n": 33', '"n": 34')
        self.bresta("no_central_perk: 33 punktar")

    def test_midgildi_stemmir_ekki_vid_punktana(self) -> None:
        self.afrit.skipta(SUMMARY, "0.1442400774443369", "0.1452400774443369")
        self.bresta("median_phoebe_share punktanna")

    def test_munurinn_stemmir_ekki(self) -> None:
        self.afrit.skipta(SUMMARY, "4.203443235958468", "4.203443235958469")
        self.bresta("munurinn")

    def test_songhandrit_sem_myndin_synir_ekki(self) -> None:
        self.afrit.skipta(SUMMARY, '"0101",', '"0102",')
        self.bresta("sönghandritin")

    def test_segd_sem_kodinn_keyrir_ekki(self) -> None:
        self.afrit.skipta(REGEX, "[A-Za-z]+(?:['’][A-Za-z]+)?", "[A-Za-z]+")
        self.bresta("central_perk_mynstur")

    def test_songsenur_faerri_en_songhandrit(self) -> None:
        self.afrit.skipta(SUMMARY, '"singing_scenes": 24', '"singing_scenes": 18')
        self.bresta("færri söngsenur")


class SkemaProf(unittest.TestCase):
    """Skorður 007 ná því sem Python hleypti framhjá."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna_med_toflum(Path(self._tmp.name))
        self.samband.execute(
            "INSERT INTO central_perk_groups VALUES ('central_perk', 1, 0.14, 0.15, 5.9)")

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def bresta(self, sql: str, breytur: tuple) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(sql, breytur)

    def test_promill_utan_marka(self) -> None:
        self.bresta("INSERT INTO central_perk_transcript_files VALUES (?, ?, ?)",
                    ("0101", "central_perk", 1001))

    def test_promill_sem_rauntala(self) -> None:
        self.bresta("INSERT INTO central_perk_transcript_files VALUES (?, ?, ?)",
                    ("0101", "central_perk", 17.4))

    def test_othekktur_hopur(self) -> None:
        self.bresta("INSERT INTO central_perk_groups VALUES (?, ?, ?, ?, ?)",
                    ("sometimes_sings", 2, 0.1, 0.1, 1.0))

    def test_hopur_sem_er_ekki_til(self) -> None:
        self.bresta("INSERT INTO central_perk_transcript_files VALUES (?, ?, ?)",
                    ("0101", "phoebe_sings", 174))

    def test_tvitekinn_frumlykill(self) -> None:
        self.samband.execute("INSERT INTO central_perk_transcript_files VALUES ('0101', 'central_perk', 89)")
        self.bresta("INSERT INTO central_perk_transcript_files VALUES (?, ?, ?)",
                    ("0101", "central_perk", 90))

    def test_thattakodi_a_rongu_formi(self) -> None:
        self.bresta("INSERT INTO central_perk_transcript_files VALUES (?, ?, ?)",
                    ("1101", "central_perk", 90))

    def test_songsenurnar_eru_ein_lina(self) -> None:
        self.bresta("INSERT INTO central_perk_singing VALUES (?, ?)", (2, 24))


class FaerslaProf(unittest.TestCase):
    """Misheppnuð endurhleðsla skilur fyrri grunn eftir ósnertan."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.slod = Path(self._tmp.name) / "friends.sqlite"
        opna_med_toflum(Path(self._tmp.name)).close()
        with tenging(self.slod) as samband:
            hledsla.hlada(samband)
            self.fyrra = fingrafar(samband)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def fingrafar_nu(self) -> str:
        with tenging(self.slod) as samband:
            return fingrafar(samband)

    def test_gallad_adfang_rullar_til_baka(self) -> None:
        afrit = Afrit()
        try:
            afrit.skipta(SUMMARY, '"n": 175', '"n": 176')
            with self.assertRaises(CentralPerkVilla), tenging(self.slod) as samband:
                hledsla.hlada(samband, afrit.mappa, afrit.provenance)
        finally:
            afrit.loka()
        self.assertEqual(self.fingrafar_nu(), self.fyrra)

    def test_villa_eftir_innsetningu_rullar_til_baka(self) -> None:
        """Töflurnar voru tæmdar og fylltar áður en villan kom — rollback skilar þeim."""
        taldar: list[int] = []

        def falla(samband: sqlite3.Connection, _samantekt: dict) -> None:
            taldar.append(samband.execute(
                "SELECT COUNT(*) FROM central_perk_transcript_files").fetchone()[0])
            raise CentralPerkVilla("gervivilla eftir innsetningu")

        with mock.patch.object(hledsla, "_stadfesta_ur_sql", side_effect=falla):
            with self.assertRaises(CentralPerkVilla), tenging(self.slod) as samband:
                hledsla.hlada(samband)
        self.assertEqual(taldar, [227], "villan á að koma EFTIR innsetninguna")
        self.assertEqual(self.fingrafar_nu(), self.fyrra)

    def test_skemaskordur_vafnar_og_rullad_til_baka(self) -> None:
        upprunalegt = hledsla._radir

        def tvitekid(*rok: object) -> dict[str, list]:
            radir = upprunalegt(*rok)
            radir["central_perk_transcript_files"].append(radir["central_perk_transcript_files"][0])
            return radir

        with mock.patch.object(hledsla, "_radir", side_effect=tvitekid):
            with self.assertRaisesRegex(CentralPerkVilla, "hafnaði færslu"), \
                    tenging(self.slod) as samband:
                hledsla.hlada(samband)
        self.assertEqual(self.fingrafar_nu(), self.fyrra)


if __name__ == "__main__":
    unittest.main()
