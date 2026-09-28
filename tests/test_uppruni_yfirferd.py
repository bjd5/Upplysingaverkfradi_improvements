"""Próf fyrir ``uppruni.saga``, ``uppruni.skyrsla`` og ``uppruni.yfirfara``.

Gervi-upprunarepo er búið til með git í tímabundinni möppu; ekkert net.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from uppruni.flokkun import Regla, Stilling  # noqa: E402
from uppruni.saga import Breyting, SoguVilla, lesa_breytingar  # noqa: E402
from uppruni.skyrsla import Lidur, Yfirferd, skrifa  # noqa: E402
from uppruni.yfirfara import skrifa_stodu, yfirfara  # noqa: E402

STILLING = Stilling(
    repo="daemi/uppruni",
    grein="main",
    reglur=(
        Regla(("src/earthquakes.py",), "kodi", "skjalftavaktin", "src/python/vinnsla/"),
        Regla(("notes/*",), "utan"),
    ),
)


class LesaBreytingarProf(unittest.TestCase):
    def test_thattar_venjulegar_og_faerdar_skrar(self) -> None:
        uttak = "M\0src/a.py\0R095\0gamalt.md\0nýtt.md\0A\0b.json\0".encode()
        self.assertEqual(
            lesa_breytingar(uttak),
            [Breyting("M", "src/a.py"), Breyting("R", "nýtt.md", "gamalt.md"), Breyting("A", "b.json")],
        )

    def test_tomt_uttak(self) -> None:
        self.assertEqual(lesa_breytingar(b""), [])

    def test_lysing_faerdrar_skrar(self) -> None:
        self.assertEqual(Breyting("R", "b", "a").lysing, "fært frá `a`")


class SkyrslaProf(unittest.TestCase):
    def yfirferd(self, *lidir: Lidur) -> Yfirferd:
        return Yfirferd("a/b", "1" * 40, "2" * 40, "2026-09-28", 3, lidir,
                        {"skjalftavaktin": "Skjálftavaktin"})

    def test_flokkar_eftir_rannsokn_og_sleppir_tomum_koflum(self) -> None:
        texti = skrifa(self.yfirferd(
            Lidur(Breyting("M", "src/earthquakes.py"), STILLING.reglur[0], ("754 línur",)),
            Lidur(Breyting("A", "notes/x.md"), STILLING.reglur[1]),
        ))
        self.assertIn("### Skjálftavaktin — `web/sidur/skjalftavaktin.html`", texti)
        self.assertIn("754 línur", texti)
        self.assertIn("`notes/x.md`", texti)
        self.assertNotIn("## Óflokkað", texti)
        self.assertNotIn("## Þarf ákvörðun", texti)

    def test_oflokkud_skra_faer_eigin_kafla(self) -> None:
        texti = skrifa(self.yfirferd(Lidur(Breyting("A", "nytt/a|b.txt"), None)))
        self.assertIn("## Óflokkað", texti)
        self.assertIn("`nytt/a\\|b.txt`", texti)  # | brýtur ekki töfluna


@unittest.skipUnless(shutil.which("git"), "git er ekki uppsett")
class YfirfaraProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.klon = Path(self._tmp.name) / "uppruni"
        self.klon.mkdir()
        self.git("init", "-q", "-b", "main")
        self.fra = self.commit({"src/earthquakes.py": "import json\n"})

    def git(self, *rok: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.klon), "-c", "user.name=p", "-c", "user.email=p@p", *rok],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def commit(self, skrar: dict[str, str]) -> str:
        for slod, texti in skrar.items():
            (self.klon / slod).parent.mkdir(parents=True, exist_ok=True)
            (self.klon / slod).write_text(texti, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "breyting")
        return self.git("rev-parse", "HEAD")

    def test_flokkar_og_athugar_nyjar_skrar(self) -> None:
        til = self.commit({
            "src/earthquakes.py": "import requests\n",
            "notes/dagbok.md": "x\n",
            "nytt.txt": "x\n",
        })
        y = yfirfara(self.klon, STILLING, self.fra, til, "2026-09-28")
        flokkar = {l.breyting.slod: (l.flokkur, l.athugasemdir) for l in y.lidir}
        self.assertEqual(y.fjoldi_commita, 1)
        self.assertEqual(flokkar["src/earthquakes.py"][0], "kodi")
        self.assertIn("requests", flokkar["src/earthquakes.py"][1][0])
        self.assertEqual(flokkar["notes/dagbok.md"], ("utan", ()))
        self.assertEqual(flokkar["nytt.txt"][0], "oflokkad")

    def test_endurskrifud_saga_er_villa(self) -> None:
        self.git("checkout", "-q", "--orphan", "ny")
        til = self.commit({"a.txt": "x\n"})
        with self.assertRaises(SoguVilla):
            yfirfara(self.klon, STILLING, self.fra, til, "2026-09-28")

    def test_skrifa_stodu_faerir_fram_og_visar_i_skyrslu(self) -> None:
        stada = Path(self._tmp.name) / "stada.json"
        stada.write_text(json.dumps({"_lysing": "x", "yfirfarid_til": self.fra}))
        skrifa_stodu("abc", "2026-09-28", stada.parent / "2026-09-28-abc.md", stada)
        self.assertEqual(
            json.loads(stada.read_text()),
            {"_lysing": "x", "yfirfarid_til": "abc", "dagsetning": "2026-09-28",
             "skyrsla": "2026-09-28-abc.md"},
        )


if __name__ == "__main__":
    unittest.main()
