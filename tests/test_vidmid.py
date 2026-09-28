"""Próf fyrir frosnu gögnin: hrágögnin, viðmiðið og vidmid.json.

Þetta er varðstaða um kröfu verkefnisins: nýja síðan á að sýna sömu tölur og sú
gamla (docs/endurbygging.md, kafli 2), og grunnurinn á að byggjast úr sömu
hrágögnum í hvert sinn (regla 5). Falli próf hér hefur frosið gagn breyst, og
það má ekki gerast.

Byggða gamla síðan og verkfærin sem lásu tölurnar úr henni eru í git-taginu
``vidmid-frosid``. vidmid.json er afurð þeirra og er hér fryst eins og hún var.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vidmid import provenance  # noqa: E402

VIDMID_JSON = hjalp.ROT / "docs" / "vidmid" / "vidmid.json"


class StadfestaProf(unittest.TestCase):
    """`stadfesta` á að finna breytta, horfna OG óskráða skrá."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.safnmappa = self.rot / "data" / "raw" / "prof"
        self.safnmappa.mkdir(parents=True)
        svar = self.safnmappa / "svar.json"
        svar.write_text("[1]", encoding="utf-8")
        self.skra = self.rot / "frysting.json"
        self.skra.write_text(json.dumps({"sofn": {"prof": {
            "heiti": "prof",
            "mappa": "data/raw/prof",
            "skrar": [{"slod": "svar.json", "staerd_baet": svar.stat().st_size,
                       "sha256": provenance.sha256_af(svar)}],
        }}}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _stadfesta(self) -> int:
        return provenance.stadfesta((self.skra,), self.rot)

    def test_osnert_safn_stemmir(self) -> None:
        self.assertEqual(self._stadfesta(), 0)

    def test_breytt_skra_finnst(self) -> None:
        (self.safnmappa / "svar.json").write_text("[2]", encoding="utf-8")
        self.assertEqual(self._stadfesta(), 1)

    def test_horfin_skra_finnst(self) -> None:
        (self.safnmappa / "svar.json").unlink()
        self.assertEqual(self._stadfesta(), 1)

    def test_oskrad_skra_finnst(self) -> None:
        (self.safnmappa / "auka.json").write_text("[3]", encoding="utf-8")
        self.assertEqual(self._stadfesta(), 1)

    def test_horfin_mappa_finnst(self) -> None:
        for skra in self.safnmappa.iterdir():
            skra.unlink()
        self.safnmappa.rmdir()
        self.assertEqual(self._stadfesta(), 1)


class FrosinGognProf(unittest.TestCase):
    """Gögnin sem ERU fryst í þessu repo-i eiga alltaf að stemma."""

    def test_stadfesta_skilar_nulli(self) -> None:
        self.assertEqual(provenance.stadfesta(), 0)

    def test_tmdb_er_skrad_ofryst(self) -> None:
        """Safn sem ekki tókst að frysta má ekki hverfa þegjandi (regla 6)."""
        skjal = json.loads(provenance.FRYSTING.read_text(encoding="utf-8"))
        self.assertIn("tmdb", {faersla["heiti"] for faersla in skjal["ofryst"]})

    def test_safn_i_tagi_er_ekki_i_trenu(self) -> None:
        """Safn sem var tekið úr trénu má ekki laumast aftur inn óskráð."""
        skjal = json.loads(provenance.PROVENANCE.read_text(encoding="utf-8"))
        for safn in skjal["geymt_i_tagi"]:
            self.assertEqual(safn["git_tag"], "vidmid-frosid")
            self.assertTrue(safn["git_commit"].startswith("f23035c"))
            for skra in safn["skrar"]:
                with self.subTest(safn=safn["heiti"], skra=skra["slod"]):
                    self.assertFalse((hjalp.ROT / safn["mappa"] / skra["slod"]).exists())


class VidmidSkraProf(unittest.TestCase):
    """vidmid.json á að vera í samræmi við sjálft sig."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.vidmid = json.loads(VIDMID_JSON.read_text(encoding="utf-8"))

    def test_snid_og_tolulausar_sidur(self) -> None:
        s = self.vidmid["samantekt"]
        self.assertEqual(s["sidur"], 24)
        self.assertEqual(sorted(s["sidur_tolulausar"]),
                         ["friends/uppahalds-video.html",
                          "reflections/sveinn.html"])

    def test_kodi_er_aldrei_efnisleg_nidurstada(self) -> None:
        self.assertFalse([t for t in self.vidmid["gogn"]
                          if t["flokkur"] == "kodi" and t["visst"]])

    def test_hver_tala_a_sida_og_samhengi(self) -> None:
        for t in self.vidmid["gogn"]:
            self.assertTrue(t["sida"] and t["texti"] and t["samhengi"])

    def test_skjalftatoflur_leggja_saman_i_334(self) -> None:
        # Mánaðartöflurnar hafa „Samtals" í fyrirsögninni; stærðartaflan á
        # sömu síðu hefur líka dálk sem heitir Fjöldi og má ekki fljóta með.
        dagl = [t for t in self.vidmid["gogn"]
                if t["sida"] == "capstone/earthquakes.html" and t["visst"]
                and t["sulka"] == "Fjöldi" and "Samtals" in (t["tafla"] or "")
                and t["lina"] not in (None, "Samtals")]
        self.assertEqual(len(dagl), 61, "61 dagur í glugganum")
        self.assertEqual(sum(t["gildi"] for t in dagl), 334)


if __name__ == "__main__":
    unittest.main()
