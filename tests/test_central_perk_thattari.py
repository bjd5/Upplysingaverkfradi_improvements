"""Próf fyrir lestur, þáttun og söngmerkingu Central Perk-greiningarinnar (#14, P2.6).

Netlaus og án handrita (issue #3): allur texti er saminn hér eða í
``central_perk_gervihandrit``. Hvert skilyrði er líka prófað þar sem það á að
BRESTA (kafli 15) — t.d. söngmerking utan Central Perk, tilsvar annarrar
persónu sem nefnir söng, og þröskuldurinn 19/20 málsgreinar.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from central_perk_gervihandrit import THATTUR_0306  # noqa: E402

from vinnsla.central_perk_lestur import (  # noqa: E402
    Block, blocks_from_html, clean_text, read_blocks,
)
from vinnsla.central_perk_mynstur import MIN_PARAGRAPHS_FOR_P_FORMAT  # noqa: E402
from vinnsla.central_perk_songur import (  # noqa: E402
    audit_candidates, marks_phoebe_singing, phoebe_singing_scenes,
)
from vinnsla.central_perk_thattari import (  # noqa: E402
    block_contexts, count_words, dialogue_from_blocks, is_central_perk_scene,
    is_scene_start, normalise_speaker,
)
from vinnsla.friends_handrit import TranscriptError  # noqa: E402


def blokkir(*textar: str) -> list[Block]:
    """Blokkir í röð úr textum."""
    return [Block(text, i) for i, text in enumerate(textar)]


def html_med(malsgreinar: int, fyrsta: str) -> str:
    """HTML með ``malsgreinar`` málsgreinum; sú fyrsta er ``fyrsta``."""
    aukalegar = "".join("<p>Joey: Ja.</p>" for _ in range(malsgreinar - 1))
    return f"<html><body><p>{fyrsta}</p>{aukalegar}</body></html>"


class Lestur(unittest.TestCase):
    """HTML → blokkir."""

    def test_clean_text_thjappar_og_afkodar(self) -> None:
        self.assertEqual(clean_text("  a&amp;b\xa0 &nbsp;c\n d "), "a&b c d")

    def test_texti_utan_p_er_hunsadur(self) -> None:
        texti = "<h1>Phoebe: titill</h1><p>Joey: Hi.</p><b>Kredit</b>"
        self.assertEqual([b.text for b in blocks_from_html(texti)], ["Joey: Hi."])

    def test_olokud_p_lokast_vid_naestu(self) -> None:
        texti = "<p>Joey: Hi.<p>Ross: Yo."
        self.assertEqual([b.text for b in blocks_from_html(texti)], ["Joey: Hi.", "Ross: Yo."])

    def test_throskuldurinn_20_malsgreinar(self) -> None:
        """Tvö ``<br>`` kljúfa blokk í ``<br>``-sniði (19) en ekki í ``<p>``-sniði (20).

        Tölurnar eru skrifaðar út, ekki lesnar úr fastanum: viðmiðið segir 20
        málsgreinar og breyttur fasti á að fella prófið.
        """
        self.assertEqual(MIN_PARAGRAPHS_FOR_P_FORMAT, 20)
        fyrsta = "Ross: Hi.<br><br>Joey: Yo.<br>there."
        undir = blocks_from_html(html_med(19, fyrsta))
        yfir = blocks_from_html(html_med(20, fyrsta))
        self.assertEqual([b.text for b in undir[:2]], ["Ross: Hi.", "Joey: Yo. there."])
        self.assertEqual(yfir[0].text, "Ross: Hi. Joey: Yo. there.")
        self.assertEqual((len(undir), len(yfir)), (20, 20))

    def test_br_snid_tolusetur_upp_a_nytt(self) -> None:
        texti = "<p>[Scene: X]<br><br>Ross: A.</p><p>Joey: B.</p>"
        self.assertEqual([(b.text, b.source_index) for b in blocks_from_html(texti)],
                         [("[Scene: X]", 0), ("Ross: A.", 1), ("Joey: B.", 2)])

    def test_afkodun_er_utf8_replace_ekki_cp1252(self) -> None:
        """0x92 verður U+FFFD — ekki ’ eins og ``friends_handrit.read_html`` gæfi."""
        with tempfile.TemporaryDirectory() as rot:
            slod = Path(rot) / "0306.html"
            slod.write_bytes(THATTUR_0306)
            texti = [b.text for b in read_blocks(slod)]
        self.assertIn("Joey: I don�t know.", texti)
        self.assertEqual(count_words("I don�t know."), 4)
        self.assertEqual(count_words("I don’t know."), 3)

    def test_skra_sem_vantar_er_villa(self) -> None:
        with self.assertRaises(TranscriptError):
            read_blocks(Path("/ekki/til/0101.html"))


class Thattun(unittest.TestCase):
    """Senur, ræðumenn og orð."""

    def test_svidsfyrirsagnir(self) -> None:
        for texti in ("[Scene: Central Perk]", "(Cut to the hallway)", "[Later, …]",
                      "[Time lapse]", "  [Opening Credits]"):
            with self.subTest(texti=texti):
                self.assertTrue(is_scene_start(texti))
        for texti in ("Joey: [Scene: grín]", "(laughs)", "Scene: nei"):
            with self.subTest(texti=texti):
                self.assertFalse(is_scene_start(texti))
        self.assertTrue(is_central_perk_scene("[Scene: CENTRAL PERK, kvöld]"))
        self.assertFalse(is_central_perk_scene("Joey: at Central Perk"))

    def test_normalise_speaker(self) -> None:
        tilvik = {
            "Phoebe": "Phoebe", "PHOEBE (singing)": "Phoebe", "Pheobe": "Phoebe",
            "Phoe": "Phoebe", "Mnca": "Monica", "Rach": "Rachel", "Chan": "Chandler",
            "Monica and Phoebe": None, "All": None, "Gunther": None, "Phoebes": None,
        }
        for label, vaent in tilvik.items():
            with self.subTest(label=label):
                self.assertEqual(normalise_speaker(label), vaent)

    def test_count_words(self) -> None:
        self.assertEqual(count_words("Don't (laughs) go [to Ross] {pause} now."), 3)
        self.assertEqual(count_words("Room 2 is well-known."), 4)
        # Óparaður svigi sleppur í gegn: orðin í honum teljast (þekkt takmörkun).
        self.assertEqual(count_words("(laughs so"), 2)

    def test_senurakning_og_tilsvor(self) -> None:
        b = blokkir("Joey: Fyrir senu.", "[Scene: Central Perk]", "Ross: Hi there.",
                    "Commercial Break", "[Scene: Íbúð]", "Monica and Phoebe: Hey.")
        samhengi = [(c.scene_index, c.in_central_perk) for c in block_contexts(b)]
        self.assertEqual(samhengi, [(0, False), (1, True), (1, True), (1, True),
                                    (2, False), (2, False)])
        tilsvor = dialogue_from_blocks("0101", b)
        self.assertEqual([(d.speaker, d.scene_index, d.in_central_perk, d.word_count)
                          for d in tilsvor],
                         [("Joey", 0, False, 2), ("Ross", 1, True, 2), (None, 2, False, 1)])
        self.assertEqual(tilsvor[2].speaker_label, "Monica and Phoebe")


class Songmerking(unittest.TestCase):
    """Söngsenur: þrjár leiðir sem telja og jaðartilvik sem mega ekki telja."""

    def test_thrjar_leidir_sem_telja(self) -> None:
        for texti in ("[Scene: Central Perk, Phoebe is singing.]",
                      "Phoebe: (singing) La la.", "Phoebe (sings): La.",
                      "Phoebe: [starts to play and sing] La.",
                      "Phoebe, with her guitar, is singing.",
                      "They both turn to Phoebe who is singing."):
            with self.subTest(texti=texti):
                self.assertTrue(marks_phoebe_singing(texti))

    def test_jadartilvik_sem_telja_ekki(self) -> None:
        for texti in ("Ross: (singing) La.", "Ross: Phoebe is singing tonight.",
                      "Phoebe: I love this song.", "Phoebe: (plays guitar) Hm.",
                      "Phoebe plays the guitar.", "Monica and Phoebe: (singing) La."):
            with self.subTest(texti=texti):
                self.assertFalse(marks_phoebe_singing(texti))

    def test_songur_telst_adeins_i_central_perk(self) -> None:
        b = blokkir("[Scene: Íbúð]", "Phoebe: (singing) La.",
                    "[Scene: Central Perk]", "Phoebe: (singing) La.", "Phoebe: (sings) Aftur.",
                    "[Scene: Gata]", "Phoebe is singing.",
                    "[Scene: Central Perk]", "Joey: Hæ.")
        # Sena 2 hefur tvær merkingar en telst einu sinni; senur 1, 3 og 4 ekki.
        self.assertEqual(phoebe_singing_scenes(b), {2})

    def test_yfirferdarlisti(self) -> None:
        b = blokkir("[Scene: Central Perk]", "Ross: Nice song.", "Joey: Hæ.",
                    "[Scene: Íbúð]", "Phoebe: My guitar!", "[Later, Central Perk]",
                    "Phoebe: (singing) La.")
        self.assertEqual([(h.source_index, blk.source_index) for h, blk in audit_candidates(b)],
                         [(0, 1), (5, 6)])


if __name__ == "__main__":
    unittest.main()
