"""Próf fyrir greiningu, samantekt og úttak Central Perk (issue #14, pakki P2.6).

Keyrt frá enda til enda á gervihandritunum í ``central_perk_gervihandrit``
(netlaust, án raunhandrita — issue #3). Væntu tölurnar eru handtaldar þar.
Skilyrðin eru líka prófuð þar sem þau eiga að BRESTA (kafli 15): mappa sem
vantar, hópur án handrita, skrif í ``web/gogn/``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from central_perk_gervihandrit import VAENT, skrifa_gervihandrit  # noqa: E402
from central_perk_vidmid import regex_markdown  # noqa: E402
from hjalp import ROT  # noqa: E402

from vinnsla.central_perk_greining import EpisodeResult, analyse  # noqa: E402
from vinnsla.central_perk_mynstur import DOCUMENTED_PATTERNS, MAIN_CAST  # noqa: E402
from vinnsla.central_perk_samantekt import pattern_rows, summarise  # noqa: E402
from vinnsla.central_perk_uttak import (  # noqa: E402
    EPISODES_FILE, META_FILE, OUTPUT_FILES, PATTERNS_FILE, SUMMARY_FILE, main, run,
    write_outputs,
)
from vinnsla.friends_handrit import SOURCE_COMMIT, TranscriptError  # noqa: E402

TIMASTIMPLAR = ("generated_utc", "generated_at", "uppfaert")
VIDMID_REGEX = ROT / "docs" / "vidmid" / "generated" / "phoebe-central-perk-regex.md"


class GreiningGervihandrita(unittest.TestCase):
    """Orð, hópar og söngsenur hvers gervihandrits — handtalið."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._rot = tempfile.TemporaryDirectory()
        cls.handrit = skrifa_gervihandrit(Path(cls._rot.name) / "handrit")
        cls.nidurstodur = analyse(cls.handrit)
        cls.eftir_id = {r.episode_id: r for r in cls.nidurstodur}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._rot.cleanup()

    def test_undanskildar_skrar_og_onnur_ending_lesast_ekki(self) -> None:
        self.assertEqual([r.episode_id for r in self.nidurstodur], sorted(VAENT))

    def test_handtalid(self) -> None:
        for episode_id, (hopur, songsenur, ord_) in VAENT.items():
            with self.subTest(handrit=episode_id):
                r = self.eftir_id[episode_id]
                self.assertEqual(r.group, hopur)
                self.assertEqual(r.singing_scenes, songsenur)
                self.assertEqual(r.words, dict(zip(MAIN_CAST, ord_)))

    def test_samantekt(self) -> None:
        s = summarise(self.nidurstodur)
        self.assertEqual((s["transcript_files"], s["singing_files"], s["singing_scenes"]),
                         (4, 1, 2))
        self.assertEqual(s["singing_episode_ids"], ["0101"])
        g = s["groups"]
        self.assertEqual([g[k]["n"] for k in g], [1, 2, 1])
        self.assertEqual(list(g), ["no_central_perk", "central_perk", "phoebe_sings"])
        self.assertAlmostEqual(g["no_central_perk"]["median_phoebe_share"], 3 / 4)
        self.assertAlmostEqual(g["central_perk"]["median_phoebe_share"], (3 / 9 + 1 / 5) / 2)
        self.assertAlmostEqual(g["central_perk"]["median_friends_to_phoebe_ratio"], (2 + 4) / 2)
        self.assertAlmostEqual(g["phoebe_sings"]["median_friends_to_phoebe_ratio"], 17 / 7)
        self.assertAlmostEqual(s["median_difference_percentage_points"],
                               100 * (7 / 24 - (3 / 9 + 1 / 5) / 2))


class SamantektBrestur(unittest.TestCase):
    """Óskilgreint miðgildi er villa með skýringu, ekki hljóð tala."""

    def _rod(self, hopur: str, phoebe: int) -> EpisodeResult:
        ord_ = {name: 1 for name in MAIN_CAST}
        ord_["Phoebe"] = phoebe
        return EpisodeResult("0101", hopur, hopur != "no_central_perk", 0, ord_)

    def test_tomur_hopur(self) -> None:
        with self.assertRaisesRegex(ValueError, "phoebe_sings"):
            summarise([self._rod("no_central_perk", 1), self._rod("central_perk", 1)])

    def test_phoebe_thegir_i_ollum_hopnum(self) -> None:
        with self.assertRaisesRegex(ValueError, "hlutfallið"):
            summarise([self._rod("no_central_perk", 0), self._rod("central_perk", 1),
                       self._rod("phoebe_sings", 1)])

    def test_thognin_gefur_hlutdeild_0_og_oendanlegt_hlutfall(self) -> None:
        r = EpisodeResult("0101", "central_perk", True, 0, {name: 0 for name in MAIN_CAST})
        self.assertEqual(r.phoebe_share, 0.0)
        self.assertEqual(r.friends_to_phoebe_ratio, float("inf"))


class UttakGervihandrita(unittest.TestCase):
    """Skrárnar fjórar: hrein afleiða, engir stimplar, engin handrit, ekki í vefinn."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._rot = tempfile.TemporaryDirectory()
        rot = Path(cls._rot.name)
        handrit = skrifa_gervihandrit(rot / "handrit")
        cls.fyrra = rot / "fyrra"
        cls.seinna = rot / "seinna"
        run(handrit, cls.fyrra)
        run(handrit, cls.seinna)
        cls.nidurstodur = analyse(handrit)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._rot.cleanup()

    def test_skrarnar_fjorar_og_ekkert_annad(self) -> None:
        self.assertEqual(sorted(p.name for p in self.fyrra.iterdir()), sorted(OUTPUT_FILES))

    def test_hrein_afleida(self) -> None:
        for heiti in OUTPUT_FILES:
            with self.subTest(skra=heiti):
                self.assertEqual((self.fyrra / heiti).read_bytes(),
                                 (self.seinna / heiti).read_bytes())

    def test_engir_timastimplar_og_uppruni_skradur(self) -> None:
        for heiti in (SUMMARY_FILE, PATTERNS_FILE, META_FILE):
            texti = (self.fyrra / heiti).read_text(encoding="utf-8")
            for stimpill in TIMASTIMPLAR:
                self.assertNotIn(stimpill, texti, heiti)
        meta = json.loads((self.fyrra / META_FILE).read_text(encoding="utf-8"))
        self.assertEqual(meta["source_commit"], SOURCE_COMMIT)
        self.assertEqual(meta["transcript_files_used"], 4)

    def test_summary_er_samantektin(self) -> None:
        gogn = json.loads((self.fyrra / SUMMARY_FILE).read_text(encoding="utf-8"))
        self.assertEqual(gogn, summarise(self.nidurstodur))

    def test_thaettir_csv(self) -> None:
        with (self.fyrra / EPISODES_FILE).open(encoding="utf-8", newline="") as f:
            radir = list(csv.DictReader(f))
        self.assertEqual([r["episode_id"] for r in radir], sorted(VAENT))
        r = radir[0]
        self.assertEqual((r["group"], r["has_central_perk"], r["singing_scenes"],
                          r["words_phoebe"], r["main_cast_words"]),
                         ("phoebe_sings", "1", "2", "7", "24"))
        self.assertAlmostEqual(float(r["phoebe_share"]), 7 / 24)

    def test_enginn_handritstexti_i_uttaki(self) -> None:
        """Setningar úr gervihandritunum mega ekki birtast í úttakinu (issue #3)."""
        for heiti in OUTPUT_FILES:
            texti = (self.fyrra / heiti).read_text(encoding="utf-8")
            for brot in ("La la kisa", "Hello there friends", "Ignored words", "Scene:"):
                with self.subTest(skra=heiti, brot=brot):
                    self.assertNotIn(brot, texti)

    def test_neitar_web_gogn(self) -> None:
        for mappa in (ROT / "web" / "gogn", ROT / "web" / "gogn" / "central-perk"):
            with self.subTest(mappa=mappa):
                with self.assertRaisesRegex(ValueError, "skrifar ekki"):
                    write_outputs(self.nidurstodur, mappa)
        self.assertFalse((ROT / "web" / "gogn" / "central-perk").exists())


class Segdir(unittest.TestCase):
    """Segðirnar í úttakinu eru þær sem keyra — og þær sem viðmiðið sýndi."""

    def test_pattern_rows_eru_segdirnar_sjalfar(self) -> None:
        self.assertEqual([r["pattern"] for r in pattern_rows()],
                         [p.pattern for _, p, _, _ in DOCUMENTED_PATTERNS])

    def test_endurskapar_regex_md_vidmidsins(self) -> None:
        self.assertEqual(regex_markdown(pattern_rows()),
                         VIDMID_REGEX.read_text(encoding="utf-8"))

    def test_breytt_segd_finnst(self) -> None:
        radir = pattern_rows()
        radir[1] = {**radir[1], "pattern": radir[1]["pattern"].replace("100", "120")}
        self.assertNotEqual(regex_markdown(radir), VIDMID_REGEX.read_text(encoding="utf-8"))


class Inngangur(unittest.TestCase):
    """Týnd handritamappa er villa, ekki tóm greining."""

    def test_mappa_sem_vantar(self) -> None:
        with self.assertRaises(TranscriptError):
            analyse("/ekki/til/season")
        with self.assertLogs("vinnsla.central_perk_uttak", "ERROR"):
            self.assertEqual(main(["--handrit", "/ekki/til/season"]), 1)

    def test_mappa_an_handrita(self) -> None:
        with tempfile.TemporaryDirectory() as rot:
            with self.assertRaisesRegex(TranscriptError, "Engin handrit"):
                analyse(rot)


if __name__ == "__main__":
    unittest.main()
