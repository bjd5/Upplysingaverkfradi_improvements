"""Próf fyrir talningar Phoebe-greiningarinnar (issue #14, pakki P2.5).

Netlaus og á gervihandritum einum (``friends_gervihandrit``). Væntu tölurnar
eru **handtaldar** úr gervihandritunum — ekki lesnar úr úttaki kóðans, svo
prófið geti ekki lagað sig að villu. Samanburður við raunhandritin er í
``test_phoebe_uttak``.

Skilyrðin eru líka prófuð þar sem þau eiga að BRESTA (kafli 6): engin
ræðuskipti, ósamræmd mynsturflögg, óþekkt talningarsvið, tóm talnaröð.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from friends_gervihandrit import skrifa_gervihandrit  # noqa: E402

from vinnsla.friends_thattari import parse_episode  # noqa: E402
from vinnsla.phoebe_greining import analyse  # noqa: E402
from vinnsla.phoebe_ordafordi import (  # noqa: E402
    Vocabulary, distinctive_words, log_odds_z, upper_median,
)
from vinnsla.phoebe_tengsl import Interactions, talker_rows  # noqa: E402
from vinnsla.phoebe_thema import corpus_counts  # noqa: E402


class Gervigreining(unittest.TestCase):
    """Heildargreiningin keyrð á gervihandritunum tveimur."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._mappa = tempfile.TemporaryDirectory()
        cls.a = analyse(skrifa_gervihandrit(Path(cls._mappa.name)))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._mappa.cleanup()

    # ------------------------------------------------------------ þáttun
    def test_gaedamat(self) -> None:
        self.assertEqual(len(self.a.episodes), 2)
        self.assertEqual(self.a.kind_counts,
                         Counter(scene=4, action=1, person=15, other=3))
        self.assertEqual(self.a.unclassified_pct, 13.04)

    # ------------------------------------------------------------- plássið
    def test_linur_og_ord_vinanna(self) -> None:
        st = self.a.screentime
        self.assertEqual(dict(st.total_lines), dict(
            phoebe=5, rachel=1, ross=1, chandler=1, monica=2, joey=2))
        # „C'mon Mon“ er tvö orð; „(smiles)“ er ekki talað; Ursula og
        # Phoebe Sr. eru ekki Phoebe.
        self.assertEqual(dict(st.total_words), dict(
            phoebe=10, rachel=2, ross=2, chandler=3, monica=4, joey=7))

    def test_tvofaldur_thattur_telst_tveir(self) -> None:
        st = self.a.screentime
        self.assertEqual(dict(st.counts.aired), {1: 1, 2: 2})
        self.assertEqual(dict(st.counts.files), {1: 1, 2: 1})

    def test_hlutdeild_og_rod(self) -> None:
        heild = {r["character"]: r for r in self.a.screentime.overall_rows}
        self.assertEqual(heild["phoebe"]["line_share_pct"], 41.67)
        self.assertEqual(heild["phoebe"]["rank_by_lines"], 1)
        # Jafntefli (monica, joey: 2 línur) halda röð FRIENDS.
        self.assertEqual([r["character"] for r in self.a.screentime.overall_rows],
                         ["phoebe", "monica", "joey", "rachel", "ross", "chandler"])

    def test_senur(self) -> None:
        heild = {r["character"]: r["speaking_scenes"] for r in self.a.screentime.overall_rows}
        self.assertEqual(heild, dict(phoebe=3, rachel=1, ross=1, chandler=1, monica=2, joey=2))

    # --------------------------------------------------------- nafntilvik
    def test_nafntilvik_eftir_thattarod(self) -> None:
        fyrsta, onnur = self.a.mentions.season_rows
        self.assertEqual(fyrsta["mentions_in_dialogue_by_others"], 3)
        self.assertEqual(fyrsta["mentions_in_own_dialogue"], 0)
        self.assertEqual(fyrsta["mentions_in_stage_directions"], 1)
        self.assertEqual(fyrsta["mentions_nickname_pheebs"], 1)
        self.assertEqual(fyrsta["mentions_formal_phoebe"], 2)
        self.assertIsNone(fyrsta["change_vs_prev_season_pct"])
        # Jafntefli í efsta sæti: fyrst til að nefna hana vinnur.
        self.assertEqual(fyrsta["top_mentioner"], "rachel")
        self.assertEqual(onnur["dialogue_mentions_per_episode"], 0.5)
        self.assertEqual(onnur["change_vs_prev_season_pct"], -83.33)

    def test_cmon_er_ekki_mon(self) -> None:
        self.assertEqual(self.a.mentions.name_totals["monica"], 1)
        self.assertEqual(self.a.mentions.name_totals["joey"], 1)
        self.assertEqual(self.a.mentions.name_totals["phoebe"], 4)

    # -------------------------------------------------------------- tengsl
    def test_raeduskipti_og_lift(self) -> None:
        rodud = [(r["character"], r["adjacent_turns"]) for r in self.a.talkers]
        self.assertEqual(rodud, [("rachel", 2), ("ross", 1), ("joey", 1),
                                 ("chandler", 0), ("monica", 0)])
        rachel = self.a.talkers[0]
        # Mæld hlutdeild 2/4, vænt 1/7 → 3,5.
        self.assertEqual(rachel["interaction_lift"], 3.5)
        self.assertEqual(rachel["expected_share_pct"], 14.29)

    def test_tvieykissena_og_avorp(self) -> None:
        joey = next(r for r in self.a.talkers if r["character"] == "joey")
        self.assertEqual(joey["two_person_scene_lines"], 2)
        self.assertEqual(joey["lines_naming_phoebe_at_edge"], 1)
        monica = next(r for r in self.a.talkers if r["character"] == "monica")
        self.assertEqual(monica["lines_mentioning_phoebe"], 1)

    def test_gestir_eru_ekki_phoebe(self) -> None:
        self.assertEqual([(g["character"], g["adjacent_turns"]) for g in self.a.guests],
                         [("ursula", 2), ("phoebe sr", 1)])

    def test_samskiptafylki(self) -> None:
        self.assertEqual(dict(self.a.pairs), {
            ("rachel", "phoebe"): 1, ("phoebe", "rachel"): 1, ("ross", "phoebe"): 1,
            ("joey", "monica"): 1, ("chandler", "joey"): 1, ("phoebe", "joey"): 1,
        })

    # ----------------------------------------------------------- orðaforði
    def test_talhattur_phoebe(self) -> None:
        v = self.a.vocabulary
        self.assertEqual(v.phoebe_line_lengths, [3, 1, 1, 3, 2])
        self.assertEqual((v.questions, v.exclamations), (1, 0))
        # Ekkert orð nær 40 tilvikum í svo litlu úrtaki.
        self.assertEqual(self.a.distinctive, [])


class Tengslaskilyrdi(unittest.TestCase):
    """Þar sem tengslatalningin á að bresta."""

    def test_engin_raeduskipti_fellur(self) -> None:
        with self.assertRaisesRegex(ValueError, "Engin ræðuskipti"):
            talker_rows(Interactions(), Counter(rachel=3, ross=2))

    def test_engar_linur_hinna_fellur(self) -> None:
        samskipti = Interactions(after_phoebe=Counter(rachel=1))
        with self.assertRaises(ValueError):
            talker_rows(samskipti, Counter())


class Ordaforda(unittest.TestCase):
    """Log-odds og miðgildi."""

    def test_log_odds_samhverft_og_null_vid_jafna_tidni(self) -> None:
        self.assertEqual(log_odds_z(10, 10, 100, 100, 1.0), 0.0)
        self.assertAlmostEqual(log_odds_z(30, 10, 100, 100, 1.0),
                               -log_odds_z(10, 30, 100, 100, 1.0))
        self.assertGreater(log_odds_z(30, 10, 100, 100, 1.0), 0)

    def test_throskuldar_sia_ord(self) -> None:
        v = Vocabulary(phoebe_words=Counter(ooh=30, the=30, ok=40, sjaldan=5),
                       other_words=Counter(ooh=10, the=100, ok=40, sjaldan=5))
        ord = [r["word"] for r in distinctive_words(v)]
        # „the“ er stopporð, „ok“ of stutt, „sjaldan“ of sjaldgæft.
        self.assertEqual(ord, ["ooh"])

    def test_efra_midgildi_vid_slettan_fjolda(self) -> None:
        # Ekki meðaltal miðgildanna (2,5) — viðmiðið byggir á efra miðgildinu.
        self.assertEqual(upper_median([4, 1, 3, 2]), 3)
        self.assertEqual(upper_median([5, 1, 3]), 3)

    def test_midgildi_tomrar_radar_fellur(self) -> None:
        with self.assertRaises(ValueError):
            upper_median([])


class Themutalning(unittest.TestCase):
    """corpus_counts — forsíun má aldrei breyta talningu."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._mappa = tempfile.TemporaryDirectory()
        skrar = {"0301.html": "<p>[Scene: X]</p><p>Phoebe: My guitar and my guitars.</p>"
                              "<p>Ross: A guitar (guitar case)</p>"}
        mappa = skrifa_gervihandrit(Path(cls._mappa.name), skrar)
        cls.thaettir = [parse_episode(mappa / "0301.html")]

    @classmethod
    def tearDownClass(cls) -> None:
        cls._mappa.cleanup()

    def test_svid_phoebe_og_allt(self) -> None:
        mynstur = {"guitar": re.compile(r"\bguitar\w*\b"), "ekkert": re.compile(r"zzz")}
        self.assertEqual(corpus_counts(self.thaettir, mynstur, "phoebe"),
                         Counter(guitar=2, ekkert=0))
        # „all“ telur sviðsleiðbeiningar í svigum líka.
        self.assertEqual(corpus_counts(self.thaettir, mynstur, "all")["guitar"], 4)

    def test_osamraemd_flogg_fella(self) -> None:
        mynstur = {"a": re.compile("a"), "b": re.compile("b", re.I)}
        with self.assertRaises(ValueError):
            corpus_counts(self.thaettir, mynstur)

    def test_othekkt_svid_fellur(self) -> None:
        with self.assertRaisesRegex(ValueError, "Óþekkt svið"):
            corpus_counts(self.thaettir, {"a": re.compile("a")}, "rachel")


if __name__ == "__main__":
    unittest.main()
