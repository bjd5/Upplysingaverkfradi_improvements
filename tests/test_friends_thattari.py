"""Próf fyrir sameiginlega Friends-þáttarann (issue #14, pakki P2.5).

Netlaus og á gervihandritum einum (``friends_gervihandrit``) — handritin sjálf
fara aldrei í repo-ið (issue #3). Hvert skilyrði er líka prófað þar sem það á
að BRESTA: mappa sem vantar, skráarheiti án þáttaraðar, undanskildar skrár,
merki sem líta út eins og ræðumenn en eru það ekki.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from friends_gervihandrit import skrifa_gervihandrit  # noqa: E402

from vinnsla.friends_handrit import (  # noqa: E402
    TRANSCRIPT_DIR_ENV, TranscriptError, aired_episodes, decode_transcript,
    episode_code, html_title, season_of, transcript_dir, transcript_paths,
)
from vinnsla.friends_thattari import (  # noqa: E402
    ACTION, OTHER, PERSON, SCENE, classify_blocks, html_to_blocks,
    normalise_speaker, parse_episode, speaker_lines, spoken_words,
)


class Skraalag(unittest.TestCase):
    """Hvaða skrár eru lesnar og hvað skráarheitið segir."""

    def setUp(self) -> None:
        self._mappa = tempfile.TemporaryDirectory()
        self.mappa = skrifa_gervihandrit(Path(self._mappa.name))

    def tearDown(self) -> None:
        self._mappa.cleanup()

    def test_undanskildar_skrar_og_onnur_ending_lesast_ekki(self) -> None:
        heiti = [p.name for p in transcript_paths(self.mappa)]
        self.assertEqual(heiti, ["0101.html", "0212-0213.html"])

    def test_mappa_ur_umhverfisbreytu(self) -> None:
        with mock.patch.dict(os.environ, {TRANSCRIPT_DIR_ENV: str(self.mappa)}):
            self.assertEqual(transcript_dir(), self.mappa)

    def test_mappa_sem_vantar_fellur_med_leidbeiningu(self) -> None:
        with self.assertRaisesRegex(TranscriptError, "delvinso.*a4641fe"):
            transcript_dir(self.mappa / "er-ekki-til")

    def test_mappa_an_handrita_fellur(self) -> None:
        with tempfile.TemporaryDirectory() as tom:
            with self.assertRaisesRegex(TranscriptError, "Engin handrit"):
                transcript_paths(tom)

    def test_thattarod_og_tvithaettir(self) -> None:
        self.assertEqual(season_of("0212-0213.html"), 2)
        self.assertEqual(season_of("1017-1018.html"), 10)
        self.assertEqual(aired_episodes("0212-0213.html"), 2)
        self.assertEqual(aired_episodes("0213.html"), 1)
        self.assertEqual(episode_code(self.mappa / "0212-0213.html"), "0212-0213")

    def test_skraarheiti_an_thattaradar_fellur(self) -> None:
        with self.assertRaises(TranscriptError):
            season_of("outtakes.html")

    def test_afkodun_reynir_cp1252_a_undan_latin1(self) -> None:
        # 0x92 er úrfellingarmerki í cp1252 en stýritákn í latin-1.
        self.assertEqual(decode_transcript(b"don\x92t"), "don’t")
        self.assertEqual(decode_transcript("þú".encode("utf-8")), "þú")
        # 0x81 er ekki til í cp1252 — þá tekur latin-1 við og bregst ekki.
        self.assertEqual(decode_transcript(b"a\x81b"), "a\x81b")

    def test_titill(self) -> None:
        self.assertEqual(html_title("<TITLE> A &amp;\n B </title>"), "A & B")
        self.assertEqual(html_title("<p>enginn titill</p>"), "")


class Blokkir(unittest.TestCase):
    """HTML → textablokkir."""

    def test_br_klyfur_eins_og_p(self) -> None:
        self.assertEqual(html_to_blocks("A: x<br>B: y<BR/>C: z"), ["A: x", "B: y", "C: z"])

    def test_haus_skriftur_og_athugasemdir_hverfa(self) -> None:
        texti = "<head><title>T</title></head><script>x</script><!-- y --><p>Z</p>"
        self.assertEqual(html_to_blocks(texti), ["Z"])

    def test_inline_tog_kljufa_ekki(self) -> None:
        self.assertEqual(html_to_blocks("<p>Joey: <b>Hey</b> <i>you</i></p>"), ["Joey: Hey you"])

    def test_cp1252_leifar_lagfaerdar(self) -> None:
        self.assertEqual(html_to_blocks("<p>it\x92s \x93so\x94\x97ok\x85</p>"),
                         ["it's \"so\"-ok..."])


class Raedumenn(unittest.TestCase):
    """normalise_speaker — hver er ræðumaður og hver ekki."""

    def test_styttingar_og_fullt_nafn(self) -> None:
        for merki, vaent in (("Phoe", "phoebe"), ("Mnca.", "monica"), ("Chan", "chandler"),
                             ("PHOEBE BUFFAY", "phoebe"), ("Phoebe (singing)", "phoebe")):
            with self.subTest(merki=merki):
                self.assertEqual(normalise_speaker(merki), (vaent, False))

    def test_skyldmenni_eru_ekki_phoebe(self) -> None:
        for merki in ("Phoebe Sr.", "Ursula", "Mrs. Buffay"):
            with self.subTest(merki=merki):
                nafn, hopur = normalise_speaker(merki)
                self.assertNotEqual(nafn, "phoebe")
                self.assertFalse(hopur)

    def test_skyldmenni_med_kommu_eru_ekki_hopur(self) -> None:
        # Án NOT_PHOEBE_LABELS teldist kommumerkið hópur og línan hyrfi.
        self.assertEqual(normalise_speaker("Buffay, the Vampire Layer"),
                         ("buffay, the vampire layer", False))

    def test_hopar(self) -> None:
        for merki in ("All", "Monica and Phoebe", "Ross, Joey", "Joey & Chandler", "Guys"):
            with self.subTest(merki=merki):
                self.assertTrue(normalise_speaker(merki)[1])

    def test_ekki_raedumenn(self) -> None:
        for merki in ("Transcribed by", "Written by", "Note", "a very long stage direction here"):
            with self.subTest(merki=merki):
                self.assertEqual(normalise_speaker(merki), ("", False))


class Flokkun(unittest.TestCase):
    """Flokkun blokka og senuteljarinn."""

    def test_fjorir_flokkar_og_senur(self) -> None:
        linur = classify_blocks(["Formáli", "[Scene: A]", "Ross: Hi (waves) there.",
                                 "(Ross leaves)", "(at the door)", "Joey: Ok.", "The End"])
        self.assertEqual([ln.kind for ln in linur],
                         [OTHER, SCENE, PERSON, ACTION, SCENE, PERSON, OTHER])
        self.assertEqual([ln.scene for ln in linur], [0, 1, 1, 1, 2, 2, 2])
        tilsvar = linur[2]
        self.assertEqual((tilsvar.speaker, tilsvar.text), ("ross", "Hi (waves) there."))
        self.assertEqual(tilsvar.spoken_lower, "hi   there.")

    def test_toluð_ord_an_sviga(self) -> None:
        self.assertEqual(spoken_words("Well-known (laughs) 2 guys, don't!"),
                         ["well-known", "guys", "don't"])


class GervithatturThattadur(unittest.TestCase):
    """parse_episode á gervihandritunum — handtaldar tölur."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._mappa = tempfile.TemporaryDirectory()
        mappa = skrifa_gervihandrit(Path(cls._mappa.name))
        cls.fyrsti = parse_episode(mappa / "0101.html")
        cls.tvofaldur = parse_episode(mappa / "0212-0213.html")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._mappa.cleanup()

    def test_lysigogn(self) -> None:
        self.assertEqual((self.fyrsti.code, self.fyrsti.season, self.fyrsti.n_episodes),
                         ("0101", 1, 1))
        self.assertEqual(self.fyrsti.title, "Gervi 0101: Fyrsti")
        self.assertEqual((self.tvofaldur.season, self.tvofaldur.n_episodes), (2, 2))

    def test_flokkafjoldi(self) -> None:
        def telja(thattur):
            return {k: sum(1 for ln in thattur.lines if ln.kind == k)
                    for k in (SCENE, ACTION, PERSON, OTHER)}
        # <h1>, „Transcribed by“ og „Commercial Break“ eru óflokkuð; skriftan í
        # <head> lendir hvergi.
        self.assertEqual(telja(self.fyrsti), {SCENE: 3, ACTION: 1, PERSON: 10, OTHER: 3})
        self.assertEqual(telja(self.tvofaldur), {SCENE: 1, ACTION: 0, PERSON: 5, OTHER: 0})

    def test_holinur_sleppa_ur_tilsvorum(self) -> None:
        med = speaker_lines(self.fyrsti, include_groups=True)
        an = speaker_lines(self.fyrsti)
        self.assertEqual(len(med) - len(an), 1)
        self.assertNotIn("all", [ln.speaker for ln in an])

    def test_br_snid_thattar_eins_og_p_snid(self) -> None:
        self.assertEqual([ln.speaker for ln in self.tvofaldur.lines if ln.kind == PERSON],
                         ["phoebe", "ursula", "phoebe", "phoebe sr", "monica"])


if __name__ == "__main__":
    unittest.main()
