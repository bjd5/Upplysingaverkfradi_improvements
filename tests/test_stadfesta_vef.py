"""Próf fyrir ``utflutningur.stadfesta_vef`` — staðfestinguna á undan birtingu (#28).

Hvert próf afritar ``web/`` í tímabundna möppu og spillir afritinu; raunverulega
``web/`` er aldrei snert (regla 10). Síðasta prófið keyrir sömu skipun og
birtingin, ``scripts/stadfesta-vef.sh``, og les útgangskóðann.

    python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from utflutningur import stadfesta_vef  # noqa: E402

SKRIFTA = hjalp.ROT / "scripts" / "stadfesta-vef.sh"
PROFSIDA = """<!DOCTYPE html>
<html lang="is"><body>
  <section data-gogn="ekki-til.json"></section>
  <section data-gogn="../index.html"></section>
  <a href="../gogn/vantar-lika.json">gagnaskráin</a>
  <p data-stada-gagna></p>
</body></html>
"""


class StadfestaVefProf(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.vefur = Path(tmp.name) / "web"
        shutil.copytree(stadfesta_vef.VEFUR, self.vefur)
        self.gogn = self.vefur / "gogn"

    def _villur(self) -> str:
        return "\n".join(stadfesta_vef.stadfesta(self.vefur))

    def _breyta(self, heiti: str, **reitir: object) -> None:
        skra = self.gogn / heiti
        umslag = json.loads(skra.read_text(encoding="utf-8"))
        umslag.update(reitir)
        skra.write_text(json.dumps(umslag, ensure_ascii=False), encoding="utf-8")

    def test_vefurinn_eins_og_hann_er_stenst(self) -> None:
        self.assertEqual([], stadfesta_vef.stadfesta(stadfesta_vef.VEFUR))

    def test_skra_sem_utflutningurinn_skrifar_ma_ekki_vanta(self) -> None:
        (self.gogn / "hagstofan.json").unlink()
        self.assertIn("web/gogn/hagstofan.json vantar", self._villur())

    def test_ogilt_json_stodvar(self) -> None:
        (self.gogn / "mbl.json").write_text('{"uppfaert": ', encoding="utf-8")
        self.assertIn("web/gogn/mbl.json er ekki gilt JSON (lína 1", self._villur())

    def test_ekki_utf8_stodvar(self) -> None:
        (self.gogn / "mbl.json").write_bytes(b'{"heimild": "\xe9"}')
        self.assertIn("web/gogn/mbl.json er ekki UTF-8", self._villur())

    def test_umslag_utan_snids_utflutningsins_stodvar(self) -> None:
        gallar = {
            "uppfaert ekki ISO": {"uppfaert": "í gær"},
            "uppfaert án tímabeltis": {"uppfaert": "2026-09-10T09:02:26"},
            "gogn ekki listi": {"gogn": {"a": 1}},
            "gogn tómur": {"gogn": []},
            "heimild auð": {"heimild": " "},
            "óþekktur reitur": {"aukalega": 1},
            "NaN": {"gogn": [float("nan")]},
        }
        for lysing, reitir in gallar.items():
            with self.subTest(lysing):
                shutil.copy2(stadfesta_vef.VEFGOGN / "skjalftar.json", self.gogn)
                self._breyta("skjalftar.json", **reitir)
                self.assertIn("web/gogn/skjalftar.json stenst ekki snið", self._villur())

    def test_gagnaskra_sem_sida_visar_i_verdur_ad_vera_til(self) -> None:
        (self.vefur / "sidur" / "prof.html").write_text(PROFSIDA, encoding="utf-8")
        (self.gogn / "yfirlit.json").unlink()
        villur = self._villur()
        self.assertIn("sidur/prof.html vísar í gogn/ekki-til.json", villur)
        self.assertIn("sidur/prof.html vísar í gogn/vantar-lika.json", villur)
        self.assertIn("sidur/prof.html vísar í gogn/yfirlit.json", villur)
        self.assertIn("sidur/prof.html nefnir gagnaskrána '../index.html'", villur)

    def test_main_telur_upp_allar_villur_og_skilar_einum(self) -> None:
        (self.gogn / "phoebe-tolfraedi.json").unlink()
        (self.gogn / "vedurstodvar.json").write_text("[]", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()) as villur:
            self.assertEqual(1, stadfesta_vef.main(["--vefur", str(self.vefur)]))
        self.assertIn("Birting stöðvuð", villur.getvalue())
        self.assertIn("phoebe-tolfraedi.json vantar", villur.getvalue())
        self.assertIn("vedurstodvar.json stenst ekki snið", villur.getvalue())

    def test_skriftan_stodvar_med_utgangskoda(self) -> None:
        umhverfi = {**os.environ, "PYTHON": sys.executable}
        for spilla, vaentur_kodi in ((False, 0), (True, 1)):
            with self.subTest(spillt=spilla):
                if spilla:
                    (self.gogn / "skjalftar.json").unlink()
                keyrsla = subprocess.run(
                    [str(SKRIFTA), "--vefur", str(self.vefur)],
                    capture_output=True, text=True, env=umhverfi, check=False,
                )
                self.assertEqual(vaentur_kodi, keyrsla.returncode, keyrsla.stderr)


if __name__ == "__main__":
    unittest.main()
