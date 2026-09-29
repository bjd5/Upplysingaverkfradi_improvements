"""Friends-handritin sem submodule — ákvörðun (a) í issue #3.

Git á að geyma **aðeins gitlink** (slóð + commit-SHA) fyrir handritasafnið,
aldrei skrá úr því. Og sama SHA á að standa alls staðar sem það er nefnt:
í gitlink, í kóðanum sem les handritin og í `frysting.json`. Prófið þarf
ekki handritin sjálf og stenst því eftir venjulegt `git clone`.
"""

from __future__ import annotations

import configparser
import json
import shutil
import subprocess
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vinnsla import friends_handrit  # noqa: E402

ROT = Path(__file__).resolve().parents[1]
SLOD = "data/raw/friends-handrit"
GITLINK_HAMUR = "160000"


def _git(*rok: str) -> str:
    return subprocess.run(
        ["git", *rok], cwd=ROT, check=True, capture_output=True, text=True
    ).stdout


@unittest.skipUnless(shutil.which("git") and (ROT / ".git").exists(), "ekki git-vinnumappa")
class SubmoduleProf(unittest.TestCase):

    def test_gitmodules_visar_a_delvinso(self) -> None:
        stilling = configparser.ConfigParser()
        stilling.read(ROT / ".gitmodules", encoding="utf-8")
        hluti = stilling[f'submodule "{SLOD}"']
        self.assertEqual(hluti["path"], SLOD)
        self.assertEqual(hluti["url"], friends_handrit.SOURCE_REPOSITORY)

    def test_adeins_gitlink_i_git(self) -> None:
        """Engin skrá undir submodule-slóðinni — aðeins ein færsla, hamur 160000."""
        faerslur = _git("ls-files", "-s", "--", SLOD).splitlines()
        self.assertEqual(len(faerslur), 1, "handritaskrár í git-vísinum")
        hamur, sha, _, slod = faerslur[0].replace("\t", " ").split(" ")
        self.assertEqual((hamur, slod), (GITLINK_HAMUR, SLOD))
        self.assertEqual(sha, friends_handrit.SOURCE_COMMIT)

    def test_sjalfgefna_mappan_er_i_submodule(self) -> None:
        self.assertEqual(friends_handrit.DEFAULT_TRANSCRIPT_DIR, ROT / SLOD / "season")

    def test_frysting_nefnir_sama_sha(self) -> None:
        skjal = json.loads((ROT / "data/raw/frysting.json").read_text(encoding="utf-8"))
        faersla = next(f for f in skjal["skrad_annars_stadar"] if f["mappa"] == SLOD)
        self.assertEqual(faersla["commit"], friends_handrit.SOURCE_COMMIT)
        self.assertEqual(faersla["upprunarepo"], friends_handrit.SOURCE_REPOSITORY)


if __name__ == "__main__":
    unittest.main()
