"""Frávik stöðva Friends-hleðsluna — þau laumast ekki í grunninn (issue #10).

Hvert varnarlag er prófað þar sem það á að **bresta**, ekki þar sem það er
líklegt til að halda (lærdómurinn úr #47): breytt skrá, tvítekinn lykill,
gildi utan marka, ósamræmi milli skráa, skorður skemans sjálfs og
strengjasamsetning í SQL. Gallarnir eru settir í afrit (``friends_grunnur.
Afrit``); frumritin eru aldrei snert (regla 10). Til að prófa lögin á eftir
SHA-staðfestingunni er afritið „endurundirritað“ í provenance-afritinu.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
import sql_samsetning
from friends_grunnur import Afrit, opna_med_toflum, vidmid_gildi
from hjalp import PYTHON_ROT

from gagnagrunnur.tenging import tenging  # noqa: E402
from vinnsla import friends_hledsla as hledsla  # noqa: E402
from vinnsla.friends_skrar import HledsluVilla  # noqa: E402

PER_EPISODE = "phoebe-per-episode.csv"
TELJA_SKRAR = "SELECT COUNT(*) FROM friends_transcript_files"
HLEDSLUEININGAR = ("friends_skrar", "friends_faerslur", "friends_phoebe_faerslur",
                   "friends_samraemi", "friends_hledsla")


class GallarProf(unittest.TestCase):
    """Gallað afrit er hlaðið í tóman grunn; hleðslan verður að stöðvast."""

    def setUp(self) -> None:
        self.afrit = Afrit()
        self.samband = opna_med_toflum(self.afrit.rot)

    def tearDown(self) -> None:
        self.samband.close()
        self.afrit.loka()

    def hlada(self) -> dict[str, int]:
        return hledsla.hlada(self.samband, self.afrit.mappa, self.afrit.provenance)

    def bresta(self, *brot: str) -> None:
        with self.assertRaises(HledsluVilla) as samhengi:
            self.hlada()
        for texti in brot:
            self.assertIn(texti, str(samhengi.exception))

    def skipta(self, heiti: str, gamalt: str, nytt: str, undirrita: bool = True) -> None:
        texti = self.afrit.lesa(heiti)
        self.assertEqual(texti.count(gamalt), 1, f"{gamalt!r} ekki einkvæmt í {heiti}")
        self.afrit.skrifa(heiti, texti.replace(gamalt, nytt), undirrita)

    def test_oskemmt_afrit_hledst(self) -> None:
        """Viðmið hinna prófanna: óbreytt afrit hleðst án athugasemda."""
        self.assertEqual(self.hlada()["friends_transcript_files"],
                         vidmid_gildi("handritsskrár"))

    # --- SHA-256 og skráalistinn -------------------------------------------

    def test_breytt_skra_stodvar_hledslu(self) -> None:
        self.skipta("interaction-matrix.csv", "Phoebe,Rachel,1367", "Phoebe,Rachel,1368",
                    undirrita=False)
        self.bresta("interaction-matrix.csv", "provenance")
        self.assertEqual(self.samband.execute(TELJA_SKRAR).fetchone()[0], 0)

    def test_eitt_baeti_nog(self) -> None:
        """Línuskil einnar línu breytt — summan sér það, tölurnar ekki."""
        self.skipta(PER_EPISODE, "\r\n0102,", "\n0102,", undirrita=False)
        self.bresta(PER_EPISODE, "SHA-256")

    def test_skra_sem_vantar_stodvar_hledslu(self) -> None:
        (self.afrit.mappa / "signature-phrases.csv").unlink()
        self.bresta("vantar", "signature-phrases.csv")

    def test_skra_umfram_stodvar_hledslu(self) -> None:
        (self.afrit.mappa / "aukaskra.csv").write_text("a\n1\n", encoding="utf-8")
        self.bresta("umfram", "aukaskra.csv")

    # --- einstakar færslur -------------------------------------------------

    def test_tvitekinn_lykill_stodvar_hledslu(self) -> None:
        lina = "0102,1,The One With The Sonogram at the End,"
        texti = self.afrit.lesa(PER_EPISODE)
        heil = next(r for r in texti.split("\r\n") if r.startswith(lina))
        self.afrit.skrifa(PER_EPISODE, texti.replace(heil, heil + "\r\n" + heil))
        self.bresta("tvítekinn", "0102")

    def test_tvitekin_samskipti_stodva_hledslu(self) -> None:
        self.skipta("interaction-matrix.csv", "Phoebe,Rachel,1367\r\n",
                    "Phoebe,Rachel,1367\r\nPhoebe,Rachel,1367\r\n")
        self.bresta("tvítekinn", "Phoebe")

    def test_thattarod_utan_marka_stodvar_hledslu(self) -> None:
        self.skipta(PER_EPISODE, "\r\n0102,1,", "\r\n0102,11,")
        self.bresta("utan marka", "season")

    def test_neikvaedur_fjoldi_stodvar_hledslu(self) -> None:
        self.skipta("signature-phrases.csv", "ooh,220,", "ooh,-220,")
        self.bresta("ekki heiltala", "count")

    def test_texti_i_talnareit_stodvar_hledslu(self) -> None:
        self.skipta("speaks-with-phoebe.csv", "Mike,190,", "Mike,nítján,")
        self.bresta("ekki heiltala", "lines_to_phoebe")

    def test_gestur_sem_vinur_stodvar_hledslu(self) -> None:
        self.skipta("interaction-matrix.csv", "Joey,Ross,1258", "Joey,Mike,1258")
        self.bresta("ekki einn vinanna sex")

    def test_rangur_dalkur_stodvar_hledslu(self) -> None:
        self.skipta("signature-phrases.csv", "phrase,count,", "phrase,fjoldi,")
        self.bresta("dálkarnir")

    # --- samræmi milli skráa -----------------------------------------------

    def test_osamraemi_vid_meta_stodvar_hledslu(self) -> None:
        self.skipta("_meta.json", '"phoebe": 7483', '"phoebe": 7484')
        self.bresta("Ósamræmi", "phoebe")

    def test_oflokkad_hlutfall_sem_stemmir_ekki_stodvar_hledslu(self) -> None:
        self.skipta("_meta.json", '"unclassified_pct": 2.95', '"unclassified_pct": 2.94')
        self.bresta("Ósamræmi", "óflokkaðra")

    def test_summa_skrar_sem_stemmir_ekki_stodvar_hledslu(self) -> None:
        self.skipta(PER_EPISODE, "\r\n0102,1,The One With The Sonogram at the End,1,167,",
                    "\r\n0102,1,The One With The Sonogram at the End,1,168,")
        self.bresta("friends_lines_total")

    def test_skemaskordur_na_thvi_sem_python_hleypir(self) -> None:
        """Síðasta varnarlagið: gildi sem Python-sannreyningin hleypir í gegn en
        skemað hafnar — nafntilvik í tali verða að skiptast í formleg og gælunöfn.
        """
        self.skipta("phoebe-mentions-by-season.csv", "\r\n1,24,24,94,5,99,187,286,56,43,",
                    "\r\n1,24,24,94,5,99,187,286,55,43,")
        self.bresta("phoebe_mentions_by_season", "CHECK")


class FaerslaProf(unittest.TestCase):
    """Misheppnuð hleðsla skilur fyrri grunn eftir ósnertan."""

    def test_gallad_endurhledsla_rullar_til_baka(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "friends.sqlite"
            opna_med_toflum(Path(mappa)).close()
            with tenging(slod) as samband:
                hledsla.hlada(samband)

            afrit = Afrit()
            try:
                texti = afrit.lesa("_meta.json")
                afrit.skrifa("_meta.json", texti.replace('"joey": 8183', '"joey": 8184'))
                with self.assertRaises(HledsluVilla), tenging(slod) as samband:
                    hledsla.hlada(samband, afrit.mappa, afrit.provenance)
            finally:
                afrit.loka()

            with tenging(slod) as samband:
                self.assertEqual(samband.execute(TELJA_SKRAR).fetchone()[0],
                                 vidmid_gildi("handritsskrár"))


class SkemaProf(unittest.TestCase):
    """CHECK-skorður og framandi lyklar migration 006, beint í SQL."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna_med_toflum(Path(self._tmp.name))
        hledsla.hlada(self.samband)

    def tearDown(self) -> None:
        self.samband.rollback()
        self.samband.close()
        self._tmp.cleanup()

    def hafnad(self, fyrirspurn: str, breytur: tuple) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(fyrirspurn, breytur)

    def test_thattarod_utan_marka(self) -> None:
        self.hafnad("INSERT INTO friends_seasons (season, aired_episodes) VALUES (?, ?)",
                    (11, 24))

    def test_thattakodi_og_thattarod_verda_ad_stemma(self) -> None:
        self.hafnad("INSERT INTO friends_transcript_files VALUES (?, ?, ?, ?)",
                    ("0301", 2, "Titill", 1))

    def test_tvitekinn_frumlykill(self) -> None:
        self.hafnad("INSERT INTO friends_episode_lines (episode_code, character_name, "
                    "lines, words) VALUES (?, ?, ?, ?)", ("0101", "Phoebe", 1, 1))

    def test_gestur_kemst_ekki_i_vinatoflu(self) -> None:
        self.hafnad("INSERT INTO friends_interactions (speaker, addressee, lines) "
                    "VALUES (?, ?, ?)", ("Phoebe", "Mike", 3))

    def test_neikvaedur_fjoldi(self) -> None:
        self.hafnad("UPDATE friends_parse_blocks SET blocks = ? WHERE block_kind = ?",
                    (-1, "unclassified"))

    def test_uppruninn_er_ein_lina(self) -> None:
        self.hafnad("UPDATE friends_sources SET id = ?", (2,))


class StrengjasamsetningProf(unittest.TestCase):
    """Regla 5: engin SQL-fyrirspurn hleðslunnar er sett saman úr strengjum."""

    # Leitin sjálf er í sql_samsetning.py (#11) og nær þar yfir allt src/python.
    brot = staticmethod(sql_samsetning.brot)

    def test_hledslueiningarnar_setja_ekkert_saman(self) -> None:
        kollin = 0
        for eining in HLEDSLUEININGAR:
            kodi = (PYTHON_ROT / "vinnsla" / f"{eining}.py").read_text(encoding="utf-8")
            fundid, n = self.brot(kodi)
            kollin += n
            with self.subTest(eining=eining):
                self.assertEqual(fundid, [])
        self.assertGreaterEqual(kollin, 5, "Prófið fann engin keyrslukall — sannar ekkert.")

    def test_profid_ser_samsetningu(self) -> None:
        """Næmni: hver samsetningarleið er fundin í sýnidæmi."""
        for kodi in ('c.execute(f"SELECT * FROM t WHERE id = {x}")',
                     'c.execute("SELECT * FROM t WHERE id = " + x)',
                     'c.execute("SELECT * FROM t WHERE id = %s" % x)',
                     'c.execute("SELECT * FROM t WHERE id = {}".format(x))',
                     'c.execute(fyrirspurnir[x])'):
            with self.subTest(kodi=kodi):
                self.assertTrue(self.brot(kodi)[0])

    def test_breytur_eru_ekki_samsetning(self) -> None:
        self.assertEqual(self.brot('c.execute("SELECT 1 FROM t WHERE id = ?", (x,))')[0], [])


class VidmidsuppflettingProf(unittest.TestCase):
    """Uppflettingin í vidmid.json: nákvæmlega ein samsvörun, annars villa."""

    def test_engin_samsvorun_er_villa(self) -> None:
        with self.assertRaises(AssertionError):
            vidmid_gildi("ekki til", [{"heiti": "annað", "gildi": 1}])

    def test_tvaer_samsvaranir_eru_villa(self) -> None:
        with self.assertRaises(AssertionError):
            vidmid_gildi("x", [{"heiti": "x", "gildi": 1}, {"heiti": "x", "gildi": 2}])


if __name__ == "__main__":
    unittest.main()
