"""Próf fyrir handritsleitina — skilyrðið sem gerir valkost A í issue #3 lögmætan.

Friends-tölurnar eru í git en handritin eru það ekki. Það stendur og fellur með
einni fullyrðingu: **engin talnaskrá geymir samfellda setningu úr þáttunum.**
Hér er hún prófuð, í báðar áttir. Hún nær til skránna sem leitin skannar, ekki
til alls repo-sins — afmörkunin er í docs/adferdafraedi.md, kafla 1.5.2.

Lærdómur úr docs/agenta-verkefni.md, kafla 15: *staðfesting sem getur stemmt af
tilviljun er ekki staðfesting.* Þess vegna er ekki nóg að leitin skili engu á
raunskránum — prófið keyrir hana líka á gervisetningu og fellur ef hún **finnur
hana ekki**. Leit sem finnur aldrei neitt væri annars græn að eilífu.

Gervigögnin hér eru heimatilbúin og eiga sér enga fyrirmynd í þáttunum.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vidmid import handritsleit  # noqa: E402
from vidmid.handritsreitir import SKJOLUN, TITILL, Undantekning  # noqa: E402

ROT = Path(__file__).resolve().parents[1]
AFRIT = ROT / "data" / "processed" / "phoebe-stats"

# Staðan 28.9.2026: 17 skrár í phoebe-stats og ein stök samantekt. Talan er
# hér svo leit sem hættir að finna skrárnar falli í stað þess að verða græn á
# tómu mengi.
SKANNADAR_SKRAR = 18
UNDANTEKNINGAR_FJOLDI = 18

# Heimatilbúin setning: sex orð og punktur. Hvorugt á hún sameiginlegt með
# þáttunum nema að vera ensk — það er nákvæmlega það sem leitin á að stöðva.
GERVISETNING = "The blue notebook was left behind."
GERVITALNAGILDI = ["2.95", "0212-0213", "10.16", "0.63", "1.31"]
GERVIHEITI = ["Phoebe", "Monica", "raeduskipti", "lines", "words"]


class SetningamerkiProf(unittest.TestCase):
    """Greinir tólið setningu frá talningu?"""

    def test_setning_telst_setning(self) -> None:
        self.assertGreater(handritsleit.setningamerki(GERVISETNING), 0)
        self.assertTrue(handritsleit.brotlegt(GERVISETNING))

    def test_talnagildi_telst_ekki_setning(self) -> None:
        """Tugabrot og þáttakóðar mega ekki reiknast sem setningar.

        Annars væri leitin ónothæf: hvert prósentugildi í skránum myndi falla,
        undanþágulistinn þyrfti að þekja öll gögnin og eftirlitið yrði að engu.
        """
        for gildi in GERVITALNAGILDI + GERVIHEITI:
            with self.subTest(gildi=gildi):
                self.assertEqual(handritsleit.setningamerki(gildi), 0)
                self.assertFalse(handritsleit.brotlegt(gildi))

    def test_ordathakid_er_undir_medaltilsvari(self) -> None:
        """Þakið verður að vera undir meðallengd tilsvars, annars sleppur lína.

        Meðaltilsvar er 11,2 orð (Phoebe) og 10,7 (hinir fimm) skv. summary.json.
        Prófið les þær tölur úr skránni í stað þess að trúa þessum texta.
        """
        samantekt = json.loads((AFRIT / "summary.json").read_text(encoding="utf-8"))
        stysta_medaltal = min(
            samantekt["words_per_line"], samantekt["words_per_line_others"]
        )
        self.assertLess(handritsleit.ORDATHAK_GAGNAREITS, stysta_medaltal / 2)


class GervimoppaProf(unittest.TestCase):
    """Keyrir leitina á tilbúnum skrám: hún verður að falla þar sem hún á að falla."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.mappa = self.rot / "gervi"
        self.mappa.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _leita(self, undantekningar: dict | None = None):
        with mock.patch.object(handritsleit, "MOPPUR", ("gervi",)), mock.patch.object(
            handritsleit, "STAKAR_SKRAR", ()
        ), mock.patch.object(
            handritsleit, "UNDANTEKNINGAR", undantekningar or {}
        ):
            return handritsleit.leita(self.rot)

    def _skrifa_json(self, nafn: str, gogn: object) -> None:
        (self.mappa / nafn).write_text(
            json.dumps(gogn, ensure_ascii=False), encoding="utf-8"
        )

    def test_finnur_setningu_i_json(self) -> None:
        self._skrifa_json("gervi.json", {"lines": 7483, "excerpt": GERVISETNING})
        fravik, _ = self._leita()
        self.assertEqual(len(fravik), 1)
        self.assertIn(".excerpt", str(fravik[0]))

    def test_finnur_setningu_djupt_i_lista(self) -> None:
        """Setning sem er grafin í hreiðruðum lista á að finnast líka."""
        self._skrifa_json(
            "gervi.json",
            {"seasons": [{"season": 1, "quotes": [{"text": GERVISETNING}]}]},
        )
        fravik, _ = self._leita()
        self.assertEqual(len(fravik), 1)
        self.assertIn("[].quotes[].text", str(fravik[0]))

    def test_finnur_setningu_i_csv(self) -> None:
        (self.mappa / "gervi.csv").write_text(
            f'character,lines,excerpt\nPhoebe,7483,"{GERVISETNING}"\n', encoding="utf-8"
        )
        fravik, _ = self._leita()
        self.assertEqual(len(fravik), 1)
        self.assertIn("excerpt", str(fravik[0]))

    def test_talningar_einar_gefa_engin_fravik(self) -> None:
        self._skrifa_json("gervi.json", {"lines": 7483, "character": "Phoebe"})
        fravik, talning = self._leita()
        self.assertEqual(fravik, [])
        self.assertEqual(talning["skrar"], 1)

    def test_fravikid_prentar_ekki_innihaldid(self) -> None:
        """Skýringin má ekki afrita strenginn — hún á að mæla hann, ekki birta.

        Annars myndi CI-úttakið geyma textann sem má ekki vera í repo-inu.
        """
        self._skrifa_json("gervi.json", {"excerpt": GERVISETNING})
        fravik, _ = self._leita()
        self.assertNotIn(GERVISETNING, str(fravik[0]))
        for ord_i_setningu in GERVISETNING.rstrip(".").split():
            self.assertNotIn(ord_i_setningu, str(fravik[0]))

    def test_undantekning_thaggar_en_pinnid_heldur(self) -> None:
        """Undanþeginn reitur sleppur — en aðeins með óbreyttu innihaldi."""
        self._skrifa_json("gervi.json", {"method": GERVISETNING})
        rett = hashlib.sha256(GERVISETNING.encode("utf-8")).hexdigest()
        lykill = ("gervi.json", ".method")

        fravik, _ = self._leita({lykill: Undantekning(SKJOLUN, "gervi", rett)})
        self.assertEqual(fravik, [], "óbreyttur undanþeginn reitur á að sleppa")

        rangt = "0" * 64
        fravik, _ = self._leita({lykill: Undantekning(TITILL, "gervi", rangt)})
        self.assertEqual(len(fravik), 1)
        self.assertIn("hefur breyst", str(fravik[0]))

    def test_daud_undantekning_er_fravik(self) -> None:
        """Undanþága sem á sér ekki stað má ekki liggja óáreitt í listanum."""
        self._skrifa_json("gervi.json", {"lines": 1})
        fravik, _ = self._leita(
            {("horfin.json", ".method"): Undantekning(SKJOLUN, "gervi", "0" * 64)}
        )
        self.assertEqual(len(fravik), 1)
        self.assertIn("dauð færsla", str(fravik[0]))

    def test_onaudsynleg_undantekning_er_fravik(self) -> None:
        """Undanþága fyrir reit sem stenst regluna víkkar listann að óþörfu."""
        self._skrifa_json("gervi.json", {"character": "Phoebe"})
        gildi = hashlib.sha256(b"Phoebe").hexdigest()
        fravik, _ = self._leita(
            {("gervi.json", ".character"): Undantekning(SKJOLUN, "gervi", gildi)}
        )
        self.assertEqual(len(fravik), 1)
        self.assertIn("ekki þörf", str(fravik[0]))

    def test_horfin_mappa_er_fravik(self) -> None:
        """Leit sem finnur ekki gögnin sín má ekki skila grænu."""
        with mock.patch.object(handritsleit, "MOPPUR", ("ekki-til",)), mock.patch.object(
            handritsleit, "STAKAR_SKRAR", ()
        ), mock.patch.object(handritsleit, "UNDANTEKNINGAR", {}):
            fravik, _ = handritsleit.leita(self.rot)
        self.assertEqual(len(fravik), 1)
        self.assertIn("ekki til", str(fravik[0]))


class RaunskrarProf(unittest.TestCase):
    """Fullyrðingin á skönnuðu skránum: engin geymir samfellda setningu.

    Afmörkunin er vísvitandi: leitin les JSON- og CSV-talnaskrárnar sem
    `handritsreitir.MOPPUR` og `STAKAR_SKRAR` telja upp — ekki allt repo-ið
    (docs/adferdafraedi.md, kafli 1.5.2).
    """

    def test_skannadar_talnaskrar_geyma_enga_samfellda_setningu(self) -> None:
        fravik, talning = handritsleit.leita()
        self.assertEqual([str(f) for f in fravik], [])
        self.assertEqual(talning["skrar"], SKANNADAR_SKRAR)
        self.assertEqual(talning["undantekningar"], UNDANTEKNINGAR_FJOLDI)

    def test_stadfesta_skilar_nulli(self) -> None:
        self.assertEqual(handritsleit.stadfesta(), 0)


if __name__ == "__main__":
    unittest.main()
