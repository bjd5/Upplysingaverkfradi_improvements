"""Próf fyrir úttak Phoebe-greiningarinnar (issue #14, pakki P2.5).

Tvennt er prófað:

1. **Úttakið á gervihandritum** — skrifar sömu 17 skrár og viðmiðið, er hrein
   afleiða (sömu bæti í tveimur keyrslum, engir tímastimplar) og neitar að
   skrifa í ``web/gogn/``. Netlaust, keyrir alltaf.
2. **Samanburður við frosna viðmiðið á raunhandritunum** — bæti fyrir bæti.
   Handritin eru aldrei í repo-inu (issue #3), svo prófið keyrir aðeins sé
   ``FRIENDS_HANDRIT_MAPPA`` stillt á ``season/`` í delvinso-safninu
   (commit a4641fe). Annars er því **sleppt með skýringu**, aldrei þagað.

Samanburðartólið sjálft er prófað þar sem það á að BRESTA (kafli 6): ein
breytt tala, tímastimpill sem laumast aftur inn, skrá sem vantar.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from friends_gervihandrit import skrifa_gervihandrit  # noqa: E402
from hjalp import ROT  # noqa: E402
from phoebe_vidmid import (  # noqa: E402
    munur_vid_vidmid, skrifa_vaent, vidmidsmeta, vidmidsskrar,
)

from vinnsla.friends_handrit import (  # noqa: E402
    DOUBLE_EPISODE_FILES, EXCLUDED_FILES, TRANSCRIPT_DIR_ENV,
)
from vinnsla.phoebe_greining import analyse  # noqa: E402
from vinnsla.phoebe_uttak import run, write_outputs  # noqa: E402

TIMASTIMPLAR = ("generated_utc", "generated_at")


class UttakGervihandrita(unittest.TestCase):
    """Úttakið keyrt frá enda til enda á gervihandritunum."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._rot = tempfile.TemporaryDirectory()
        rot = Path(cls._rot.name)
        handrit = skrifa_gervihandrit(rot / "handrit")
        cls.fyrra = rot / "fyrra"
        cls.seinna = rot / "seinna"
        run(handrit, cls.fyrra)
        run(handrit, cls.seinna)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._rot.cleanup()

    def test_sama_skrasafn_og_vidmidid(self) -> None:
        self.assertEqual(sorted(p.name for p in self.fyrra.iterdir()), vidmidsskrar())

    def test_hrein_afleida_sama_baeti_i_tveimur_keyrslum(self) -> None:
        for heiti in vidmidsskrar():
            with self.subTest(skra=heiti):
                self.assertEqual((self.fyrra / heiti).read_bytes(),
                                 (self.seinna / heiti).read_bytes())

    def test_engir_timastimplar(self) -> None:
        for heiti in ("_meta.json", "summary.json"):
            gogn = json.loads((self.fyrra / heiti).read_text(encoding="utf-8"))
            for stimpill in TIMASTIMPLAR:
                self.assertNotIn(stimpill, gogn, heiti)

    def test_csv_med_crlf_eins_og_vidmidid(self) -> None:
        texti = (self.fyrra / "mentions-by-season.csv").read_bytes()
        self.assertTrue(texti.startswith(b"season,mentions,episodes,mentions_per_episode\r\n"))
        self.assertNotIn(b"\n", texti.replace(b"\r\n", b""))

    def test_tom_ordatafla_faer_haus(self) -> None:
        texti = (self.fyrra / "phoebe-distinctive-words.csv").read_text(encoding="utf-8")
        self.assertEqual(texti.splitlines(), [
            "word,z_score,phoebe_count,others_count,phoebe_per_10k,others_per_10k"])

    def test_meta_telur_gervihandritin(self) -> None:
        meta = json.loads((self.fyrra / "_meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["transcript_files_used"], 2)
        self.assertEqual(meta["aired_episodes_covered"], 3)
        self.assertEqual(meta["parse_quality"]["unclassified"], 3)


class SkrifarEkkiIVefinn(unittest.TestCase):
    """Varnaglinn gegn web/gogn/ prófaður þar sem hann á að stöðva."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._rot = tempfile.TemporaryDirectory()
        cls.greining = analyse(skrifa_gervihandrit(Path(cls._rot.name)))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._rot.cleanup()

    def test_neitar_web_gogn_og_undirmoppu(self) -> None:
        for mappa in (ROT / "web" / "gogn", ROT / "web" / "gogn" / "phoebe"):
            with self.subTest(mappa=mappa):
                with self.assertRaisesRegex(ValueError, "skrifar ekki"):
                    write_outputs(self.greining, mappa)
        self.assertFalse((ROT / "web" / "gogn" / "phoebe").exists())


class FastarStemmaVidVidmid(unittest.TestCase):
    """Afmörkun úrtaksins er lesin úr viðmiðinu, ekki afrituð."""

    def test_undanskildar_og_tvofaldar_skrar(self) -> None:
        meta = vidmidsmeta()
        self.assertEqual(sorted(EXCLUDED_FILES), meta["transcript_files_excluded"])
        self.assertEqual(sorted(DOUBLE_EPISODE_FILES),
                         meta["conventions"]["double_episode_files"])


class Samanburdartolid(unittest.TestCase):
    """Samanburðurinn verður að finna frávik — annars sannar hann ekkert."""

    def setUp(self) -> None:
        self._rot = tempfile.TemporaryDirectory()
        self.mappa = skrifa_vaent(Path(self._rot.name))

    def tearDown(self) -> None:
        self._rot.cleanup()

    def test_vaent_uttak_stenst(self) -> None:
        self.assertEqual(munur_vid_vidmid(self.mappa), [])

    def test_ein_breytt_tala_finnst(self) -> None:
        slod = self.mappa / "screentime-by-season.csv"
        slod.write_bytes(slod.read_bytes().replace(b"\r\n1,Phoebe,", b"\r\n1,Phoebe,9", 1))
        self.assertEqual(munur_vid_vidmid(self.mappa), ["screentime-by-season.csv: önnur bæti"])

    def test_timastimpill_sem_laumast_inn_finnst(self) -> None:
        slod = self.mappa / "_meta.json"
        gogn = json.loads(slod.read_text(encoding="utf-8"))
        slod.write_text(json.dumps({"generated_utc": "2026-09-28T00:00:00Z", **gogn},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(munur_vid_vidmid(self.mappa), ["_meta.json: önnur bæti"])

    def test_skra_sem_vantar_og_aukaskra_finnast(self) -> None:
        (self.mappa / "summary.json").unlink()
        (self.mappa / "presentation.json").write_text("{}", encoding="utf-8")
        self.assertEqual(munur_vid_vidmid(self.mappa),
                         ["summary.json: vantar", "presentation.json: umfram viðmiðið"])


HANDRIT = os.environ.get(TRANSCRIPT_DIR_ENV, "")


@unittest.skipUnless(HANDRIT and Path(HANDRIT).is_dir(),
                     f"{TRANSCRIPT_DIR_ENV} er ekki stillt — raunhandritin eru utan repo-sins "
                     "(issue #3); samanburðinum við viðmiðið er sleppt.")
class RaunhandritVidVidmid(unittest.TestCase):
    """Bæti fyrir bæti við docs/vidmid/phoebe-stats/ á raunhandritunum."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._rot = tempfile.TemporaryDirectory()
        cls.mappa = Path(cls._rot.name)
        run(HANDRIT, cls.mappa)
        cls.meta = json.loads((cls.mappa / "_meta.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._rot.cleanup()

    def test_allar_skrar_eins_og_vidmidid(self) -> None:
        self.assertEqual(munur_vid_vidmid(self.mappa), [])

    def test_stadfestar_tolur(self) -> None:
        vaent = vidmidsmeta()
        for lykill in ("transcript_files_used", "aired_episodes_covered",
                       "episodes_per_season", "parse_quality",
                       "friends_line_totals", "friends_word_totals"):
            with self.subTest(lykill=lykill):
                self.assertEqual(self.meta[lykill], vaent[lykill])


if __name__ == "__main__":
    unittest.main()
