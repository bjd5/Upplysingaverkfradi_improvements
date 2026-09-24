"""Próf fyrir viðmiðið sjálft: síðulesturinn og tölurnar sem hann skilar.

Þetta er varðstaða um kröfu verkefnisins: nýja síðan á að sýna sömu tölur og sú
gamla (docs/endurbygging.md, kafli 2). Falli próf hér er annað tveggja rétt —
viðmiðið breyttist (sem má ekki gerast, docs/vidmid/ er fryst) eða lesarinn
hætti að finna tölu sem hann fann áður. Hvort tveggja verður að stöðva.

Keyrsla::

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
PYTHON_ROT = ROT / "src" / "python"
if str(PYTHON_ROT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROT))

from vidmid.sidulestur import Sidulesari  # noqa: E402
from vidmid.stadfestar import STADFESTAR  # noqa: E402
from vidmid.tolugreining import finna_tolur  # noqa: E402

VEFUR = ROT / "docs" / "vidmid" / "vefur"
META = VEFUR / "friends" / "phoebe-stats" / "_meta.json"
VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"

HTML_DAEMI = """<html><body>
<nav><ol class="breadcrumb"><li>Brauðmylsna 99</li></ol></nav>
<main class="content" id="quarto-document-content">
  <h1 class="title">Titill</h1>
  <section class="level2"><h2>Niðurstöður</h2>
    <p>Úrtakið er <strong>334</strong> skjálftar á 61 degi.</p>
    <div class="sourceCode"><pre class="sourceCode python"><code>
      <span class="dv">4055</span></code></pre></div>
    <p>Tafla um stöðvar.</p>
    <table><thead><tr><th>Svið</th><th>Kyn</th><th>Hlutfall</th></tr></thead>
      <tbody><tr><td>Alls</td><td>Karlar</td><td>70,3</td></tr></tbody></table>
  </section>
</main>
<footer><p>Byggt 2026-09-17</p></footer></body></html>"""


def _hlada_vidmid() -> dict:
    if not VIDMID_JSON.exists():
        raise unittest.SkipTest("vidmid.json vantar — keyrðu tolur.py skrifa")
    return json.loads(VIDMID_JSON.read_text(encoding="utf-8"))


class SidulesturProf(unittest.TestCase):
    """Lesarinn á að sjá efnið og ekkert annað."""

    def setUp(self) -> None:
        self.lesari = Sidulesari()
        self.blokkir = self.lesari.lesa(HTML_DAEMI)
        self.textar = [b.texti for b in self.blokkir]

    def test_titill_kemur_ur_h1(self) -> None:
        self.assertEqual(self.lesari.titill, "Titill")

    def test_brauðmylsna_og_fotur_komast_ekki_med(self) -> None:
        for utan in ("Brauðmylsna 99", "Byggt 2026-09-17"):
            self.assertNotIn(utan, " ".join(self.textar))

    def test_innlinumerki_klofna_ekki(self) -> None:
        self.assertIn("Úrtakið er 334 skjálftar á 61 degi.", self.textar)

    def test_fyrirsagnakedja(self) -> None:
        malsgrein = next(b for b in self.blokkir if b.texti.startswith("Úrtakið"))
        self.assertEqual(malsgrein.kafli, ("Titill", "Niðurstöður"))

    def test_toflusella_faer_rod_og_dalk(self) -> None:
        sella = next(b for b in self.blokkir if b.texti == "70,3")
        self.assertEqual((sella.tafla, sella.lina, sella.sulka),
                         ("Tafla um stöðvar.", "Alls · Karlar", "Hlutfall"))

    def test_kodi_er_merktur_kodi(self) -> None:
        kodi = next(b for b in self.blokkir if b.texti == "4055")
        self.assertEqual(kodi.flokkur, "kodi")


class StadfestarTolurProf(unittest.TestCase):
    """Tölurnar sem verklýsing P0.2 segir að VERÐI að koma fram."""

    @classmethod
    def setUpClass(cls) -> None:
        if not META.exists():
            raise unittest.SkipTest("docs/vidmid/ vantar — P0.1 er ekki í trénu")
        cls.meta = json.loads(META.read_text(encoding="utf-8"))

    def _ur_meta(self, leid: str):
        hluti = self.meta
        for lykill in leid.split("."):
            hluti = hluti[lykill]
        return hluti

    def test_allar_stemma_vid_gagnaskra(self) -> None:
        for s in STADFESTAR:
            if s.leid is None:
                continue
            with self.subTest(heiti=s.heiti):
                self.assertEqual(self._ur_meta(s.leid), s.gildi)

    def test_tolur_i_html_finnast(self) -> None:
        vidmid = _hlada_vidmid()
        efnislegar = {(t["sida"], t["gildi"]) for t in vidmid["gogn"]
                      if t["visst"]}
        for s in STADFESTAR:
            if not s.i_html:
                continue
            with self.subTest(heiti=s.heiti):
                self.assertIn((s.sida, s.gildi), efnislegar)

    def test_linur_a_personu_eru_hvergi_i_html(self) -> None:
        """Sex staðfestar tölur standa aðeins í gagnaskrá, ekki í HTML."""
        vidmid = _hlada_vidmid()
        i_html = {t["gildi"] for t in vidmid["gogn"] if t["visst"]}
        for gildi in (7483, 9259, 9058, 8446, 8395, 8183, 4055, 3259):
            with self.subTest(gildi=gildi):
                self.assertNotIn(gildi, i_html)


class OsamraemiProf(unittest.TestCase):
    """Röksemdirnar að baki ósamræminu í osamraemi.py — sannreyndar."""

    @classmethod
    def setUpClass(cls) -> None:
        if not META.exists():
            raise unittest.SkipTest("docs/vidmid/ vantar — P0.1 er ekki í trénu")
        cls.meta = json.loads(META.read_text(encoding="utf-8"))

    def test_niu_tvofaldar_skrar_loka_reikningnum(self) -> None:
        """227 + 9 = 236. Tölurnar 6 og 4 á öðrum síðum loka honum ekki."""
        tvofaldar = self.meta["conventions"]["double_episode_files"]
        self.assertEqual(len(tvofaldar), 9)
        self.assertEqual(
            self.meta["transcript_files_used"] + len(tvofaldar),
            self.meta["aired_episodes_covered"])

    def test_top_talkers_radast_olikt_i_eintokunum(self) -> None:
        """Jafntefli í adjacent_turns er brotið án fasts viðmiðs."""
        a = json.loads((VEFUR / "friends" / "phoebe-stats"
                        / "phoebe-top-talkers.json").read_text(encoding="utf-8"))
        b_skra = ROT / "docs" / "vidmid" / "phoebe-stats" / "phoebe-top-talkers.json"
        if not b_skra.exists():
            self.skipTest("phoebe-stats-eintakið vantar")
        b = json.loads(b_skra.read_text(encoding="utf-8"))
        rod_a = [x["character"] for x in a["non_friend_characters"]]
        rod_b = [x["character"] for x in b["non_friend_characters"]]
        self.assertNotEqual(rod_a, rod_b, "röðin ætti að vera ólík")
        self.assertEqual(sorted(rod_a), sorted(rod_b), "mengið ætti að vera eins")
        eftir_nafni = {x["character"]: x["adjacent_turns"]
                       for x in a["non_friend_characters"]}
        for x in b["non_friend_characters"]:
            self.assertEqual(eftir_nafni[x["character"]], x["adjacent_turns"])

    def test_skjalftatoflur_leggja_saman_i_334(self) -> None:
        vidmid = _hlada_vidmid()
        # Mánaðartöflurnar hafa „Samtals" í fyrirsögninni; stærðartaflan á
        # sömu síðu hefur líka dálk sem heitir Fjöldi og má ekki fljóta með.
        dagl = [t for t in vidmid["gogn"]
                if t["sida"] == "capstone/earthquakes.html" and t["visst"]
                and t["sulka"] == "Fjöldi" and "Samtals" in (t["tafla"] or "")
                and t["lina"] not in (None, "Samtals")]
        self.assertEqual(len(dagl), 61, "61 dagur í glugganum")
        self.assertEqual(sum(t["gildi"] for t in dagl), 334)


class VidmidSkraProf(unittest.TestCase):
    """vidmid.json á að vera í samræmi við síðurnar og sjálft sig."""

    def setUp(self) -> None:
        self.vidmid = _hlada_vidmid()

    def test_snid_og_tolulausar_sidur(self) -> None:
        s = self.vidmid["samantekt"]
        self.assertEqual(s["sidur"], 28)
        self.assertEqual(sorted(s["sidur_tolulausar"]),
                         ["friends/uppahalds-video.html",
                          "reflections/sveinn.html"])

    def test_kodi_er_aldrei_efnisleg_nidurstada(self) -> None:
        self.assertFalse([t for t in self.vidmid["gogn"]
                          if t["flokkur"] == "kodi" and t["visst"]])

    def test_hver_tala_a_sida_og_samhengi(self) -> None:
        for t in self.vidmid["gogn"]:
            self.assertTrue(t["sida"] and t["texti"] and t["samhengi"])

    def test_gogn_stemma_vid_sidurnar(self) -> None:
        """Endurlesið úr HTML-inu á að gefa sömu tölu á hverri síðu."""
        if not VEFUR.is_dir():
            self.skipTest("docs/vidmid/vefur/ vantar")
        for sida in self.vidmid["sidur"]:
            skra = VEFUR / sida["sida"]
            fjoldi = sum(len(finna_tolur(b.texti)) for b in
                         Sidulesari().lesa(skra.read_text(encoding="utf-8")))
            with self.subTest(sida=sida["sida"]):
                self.assertEqual(fjoldi, sida["tolur"])


if __name__ == "__main__":
    unittest.main()
