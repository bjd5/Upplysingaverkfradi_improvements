"""Central Perk-greiningin borin við frosna viðmiðið (issue #14, pakki P2.6).

Tveir hlutar:

1. **Viðmiðið og samanburðartólið** — keyrir alltaf. Viðmiðsskrárnar verða
   að vera innbyrðis samkvæmar (punktar SVG-myndarinnar = hóparnir í
   ``summary.json``), og samanburðurinn verður að finna frávik þar sem þau
   eru (kafli 6) — annars sannar hann ekkert.
2. **Raunhandritin** — handritin eru aldrei í repo-inu (issue #3), svo þessi
   hluti keyrir aðeins sé ``FRIENDS_HANDRIT_MAPPA`` stillt á ``season/`` í
   ``delvinso/friends-tv-show-analysis`` @ ``a4641fe``. Annars er honum
   **sleppt með skýringu**. Föstu gildin um söngtilvikin eru niðurstaða
   handvirku yfirferðarinnar í gömlu ``tests/test_phoebe_central_perk.py``.

    FRIENDS_HANDRIT_MAPPA=/slóð/á/season python3 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from central_perk_hjalp import (  # noqa: E402
    VIDMID_SUMMARY, VIDMID_SVG, csv_points, regex_markdown, svg_points,
)
from hjalp import ROT  # noqa: E402

from vinnsla.central_perk_greining import analyse  # noqa: E402
from vinnsla.central_perk_uttak import (  # noqa: E402
    EPISODES_FILE, PATTERNS_FILE, SUMMARY_FILE, run,
)
from vinnsla.friends_handrit import TRANSCRIPT_DIR_ENV  # noqa: E402

VIDMID_REGEX = ROT / "docs" / "vidmid" / "generated" / "phoebe-central-perk-regex.md"

# Handritin þar sem yfirferðin staðfesti skýrt merkt söngatriði Phoebe í
# Central Perk: nítján skrár, 24 senur alls.
YFIRFARIN_SONGHANDRIT = {
    "0101", "0110", "0111", "0208", "0212-0213", "0217", "0218", "0314", "0315",
    "0323", "0401", "0402", "0405", "0410", "0418", "0603", "0615-0616", "0810",
    "1017-1018",
}
# Umtal um söng er ekki söngur (0107: einn hljómur áður en rafmagnið fer).
EKKI_SONGUR = ("0107", "0307", "0715", "0913")


class VidmidOgSamanburdur(unittest.TestCase):
    """Viðmiðið sjálft og tólið sem ber saman við það."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(VIDMID_SUMMARY.read_text(encoding="utf-8"))
        cls.punktar = svg_points()

    def test_punktar_myndarinnar_eru_hoparnir(self) -> None:
        self.assertEqual(len(self.punktar), self.summary["transcript_files"])
        for hopur, gildi in self.summary["groups"].items():
            with self.subTest(hopur=hopur):
                self.assertEqual(sum(1 for h, _ in self.punktar.values() if h == hopur),
                                 gildi["n"])
        self.assertEqual(sorted(e for e, (h, _) in self.punktar.items() if h == "phoebe_sings"),
                         self.summary["singing_episode_ids"])

    def test_breyttur_punktur_finnst(self) -> None:
        svg = VIDMID_SVG.read_text(encoding="utf-8")
        breytt = svg.replace("<title>0101: ", "<title>0101: 1", 1)
        self.assertNotEqual(svg_points(breytt)["0101"], self.punktar["0101"])

    def test_csv_points_rundar_eins_og_myndin(self) -> None:
        radir = [{"episode_id": "0101", "group": "central_perk", "phoebe_share": "0.08905"}]
        self.assertEqual(csv_points(radir), {"0101": ("central_perk", "8.9")})

    def test_mynd_an_punkta_er_villa(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Engir punktar"):
            svg_points("<svg></svg>")


HANDRIT = os.environ.get(TRANSCRIPT_DIR_ENV, "")


@unittest.skipUnless(HANDRIT and Path(HANDRIT).is_dir(),
                     f"{TRANSCRIPT_DIR_ENV} er ekki stillt — raunhandritin eru utan repo-sins "
                     "(issue #3); samanburðinum við viðmiðið er sleppt.")
class RaunhandritVidVidmid(unittest.TestCase):
    """Nýju einingarnar á raunhandritunum, bornar við viðmiðið."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._rot = tempfile.TemporaryDirectory()
        cls.mappa = Path(cls._rot.name)
        run(HANDRIT, cls.mappa)
        cls.nidurstodur = analyse(HANDRIT)
        cls.eftir_id = {r.episode_id: r for r in cls.nidurstodur}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._rot.cleanup()

    def test_summary_baeti_fyrir_baeti(self) -> None:
        self.assertEqual((self.mappa / SUMMARY_FILE).read_bytes(), VIDMID_SUMMARY.read_bytes())

    def test_hver_skra_eins_og_punktur_myndarinnar(self) -> None:
        with (self.mappa / EPISODES_FILE).open(encoding="utf-8", newline="") as f:
            self.assertEqual(csv_points(list(csv.DictReader(f))), svg_points())

    def test_segdirnar_eins_og_regex_md(self) -> None:
        radir = json.loads((self.mappa / PATTERNS_FILE).read_text(encoding="utf-8"))["patterns"]
        self.assertEqual(regex_markdown(radir), VIDMID_REGEX.read_text(encoding="utf-8"))

    def test_227_skrar_an_undanskildra(self) -> None:
        self.assertEqual(len(self.nidurstodur), 227)
        self.assertNotIn("0423uncut", self.eftir_id)
        self.assertNotIn("07outtakes", self.eftir_id)

    def test_yfirfarin_songhandrit(self) -> None:
        self.assertEqual({r.episode_id for r in self.nidurstodur if r.group == "phoebe_sings"},
                         YFIRFARIN_SONGHANDRIT)
        self.assertEqual(sum(r.singing_scenes for r in self.nidurstodur), 24)

    def test_umtal_um_song_er_ekki_songur(self) -> None:
        for episode_id in EKKI_SONGUR:
            with self.subTest(handrit=episode_id):
                self.assertNotEqual(self.eftir_id[episode_id].group, "phoebe_sings")

    def test_fjorar_songsenur_i_0405(self) -> None:
        self.assertEqual(self.eftir_id["0405"].singing_scenes, 4)


if __name__ == "__main__":
    unittest.main()
