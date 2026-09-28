"""Próf fyrir ``uppruni.flokkun`` og ``uppruni.athuganir``.

Engin netsamskipti og ekkert git: aðeins hrein gögn og config/uppruni.json.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from uppruni.athuganir import athuga  # noqa: E402
from uppruni.flokkun import (  # noqa: E402
    FLOKKAR,
    FLYTJA,
    Regla,
    StillingarVilla,
    finna_reglu,
    lesa_stillingu,
)

ROT = hjalp.ROT
JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijklmnop"


class ReglurProf(unittest.TestCase):
    def test_fyrsta_regla_sem_passar_raedur(self) -> None:
        reglur = (
            Regla(("src/mbl_*.py",), "kodi", "mbl-regex", "src/"),
            Regla(("src/*",), "utan"),
        )
        self.assertEqual(finna_reglu("src/mbl_regex.py", reglur).flokkur, "kodi")
        self.assertEqual(finna_reglu("src/annad.py", reglur).flokkur, "utan")

    def test_stjarna_naer_yfir_undirmoppur(self) -> None:
        regla = Regla(("site/lotur/*",), "utan")
        self.assertTrue(regla.passar("site/lotur/regex/index.qmd"))

    def test_engin_regla_skilar_none(self) -> None:
        self.assertIsNone(finna_reglu("nytt/skra.txt", (Regla(("src/*",), "utan"),)))


class StillingProf(unittest.TestCase):
    """config/uppruni.json verður að vísa á staði sem eru til í þessu repo."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.stilling = lesa_stillingu()

    def test_markmid_eru_til(self) -> None:
        for regla in self.stilling.reglur:
            if regla.flokkur in FLYTJA:
                with self.subTest(markmid=regla.markmid):
                    self.assertTrue(list(ROT.glob(regla.markmid)), f"{regla.markmid} er ekki til")

    def test_hver_rannsokn_a_sidu(self) -> None:
        for regla in self.stilling.reglur:
            if regla.rannsokn:
                with self.subTest(rannsokn=regla.rannsokn):
                    self.assertTrue((ROT / "web" / "sidur" / f"{regla.rannsokn}.html").is_file())

    def test_thekktar_upprunaskrar_eru_flokkadar(self) -> None:
        for slod, flokkur in {
            "src/earthquakes.py": "kodi",
            "data/raw/hagstofan/response.json": "hragogn",
            "site/lotur/regex/mbl.qmd": "sida",
            "site/lotur/regex/index.qmd": "utan",
            "data/fangj-friends": "bannad",
            "src/volcano_population.py": "akvordun",
        }.items():
            with self.subTest(slod=slod):
                self.assertEqual(finna_reglu(slod, self.stilling.reglur).flokkur, flokkur)

    def _rong_stilling(self, reglur: list[dict]) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "uppruni.json"
            slod.write_text(json.dumps({"repo": "a/b", "grein": "main", "reglur": reglur}))
            with self.assertRaises(StillingarVilla):
                lesa_stillingu(slod)

    def test_othekktur_flokkur_er_villa(self) -> None:
        self._rong_stilling([{"mynstur": ["*"], "flokkur": "eitthvad"}])

    def test_flutningur_an_markmids_er_villa(self) -> None:
        self._rong_stilling([{"mynstur": ["*"], "flokkur": "kodi", "rannsokn": "x"}])

    def test_flokkarnir_hafa_islensk_heiti(self) -> None:
        self.assertTrue(set(FLYTJA) <= set(FLOKKAR))


class AthuganirProf(unittest.TestCase):
    def py(self, texti: str, stadbundnar: frozenset[str] = frozenset()) -> list[str]:
        return athuga("src/x.py", texti.encode(), "kodi", stadbundnar)

    def test_hrein_skra_faer_engar_athugasemdir(self) -> None:
        self.assertEqual(self.py("import json\n\nprint(json.dumps(1))\n"), [])

    def test_leyndarmal_er_merkt_en_ekki_endurtekid(self) -> None:
        athugasemdir = self.py(f'TOKEN = "{JWT}"\n')
        self.assertTrue(any("leyndarmál" in a for a in athugasemdir))
        self.assertNotIn(JWT, " ".join(athugasemdir))

    def test_heiti_umhverfisbreytu_er_ekki_leyndarmal(self) -> None:
        self.assertEqual(self.py('token = "TMDB_READ_ACCESS_TOKEN_NAME"\n'), [])

    def test_sql_ur_f_streng_er_merkt(self) -> None:
        texti = 'def f(c, i):\n    c.execute(f"SELECT * FROM t WHERE id = {i}")\n'
        self.assertTrue(any("regla 5" in a for a in self.py(texti)))

    def test_sql_med_breytum_er_i_lagi(self) -> None:
        texti = 'def f(c, i):\n    c.execute("SELECT * FROM t WHERE id = ?", (i,))\n'
        self.assertEqual(self.py(texti), [])

    def test_thoggud_villa_er_merkt(self) -> None:
        texti = "try:\n    x = 1\nexcept ValueError:\n    pass\n"
        self.assertTrue(any("þögguð" in a for a in self.py(texti)))

    def test_of_long_skra_er_merkt(self) -> None:
        self.assertTrue(any("301 línur" in a for a in self.py("x = 1\n" * 301)))

    def test_utanadkomandi_pakki_en_ekki_stadbundinn(self) -> None:
        texti = "import requests\nimport hagstofan\nfrom src import earthquakes\n"
        athugasemdir = self.py(texti, frozenset({"hagstofan", "src"}))
        self.assertEqual(athugasemdir, ["Pakkar utan staðalsafns: requests (regla 10 — spyrja)"])

    def test_inline_still_i_sidu(self) -> None:
        texti = b'<p style="color: red">x</p>'
        self.assertIn("Inline CSS/JS — aðskilja (regla 2)", athuga("site/a.qmd", texti, "sida"))

    def test_script_med_src_er_i_lagi(self) -> None:
        self.assertEqual(athuga("site/a.html", b'<script src="a.js" defer></script>', "sida"), [])

    def test_hragogn_med_hastofum_i_heiti(self) -> None:
        athugasemdir = athuga("data/raw/x/Svar.json", b"{}", "hragogn")
        self.assertTrue(any("regla 1.2" in a for a in athugasemdir))

    def test_tviundaskra_faer_adeins_staerd(self) -> None:
        self.assertEqual(athuga("data/raw/x/mynd.png", b"\x89PNG\xff\xfe", "hragogn"), [])


if __name__ == "__main__":
    unittest.main()
