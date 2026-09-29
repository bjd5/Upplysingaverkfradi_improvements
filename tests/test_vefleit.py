"""Próf fyrir handritsleitina á HTML og JSON — ákvörðun (b) í issue #3.

Línurnar úr þætti 0101 sem gamla síðan birtir sem dæmi um þáttarann standa sem
stutt tilvitnun. Síðan var tekin úr trénu 28.9.2026 og er aðeins í frosna
commit-inu (`FROSID_COMMIT`, git-tagið `vidmid-frosid`). Undanþágan er fryst
lína fyrir línu (`VEFUNDANTEKNINGAR`) og gildir aðeins þar. Prófin sanna
þrennt, hvert þar sem það á að bresta (docs/agenta-verkefni.md, kafli 6):

1. Undanþágurnar ná **nákvæmlega** yfir línurnar sem finnast í frosnu
   skránum — engin umfram, engin vantar, aðeins í skránum tveimur.
2. **Ný** handritslína fellir leitina — í trénu, og í frosnu skránum.
3. Undanþegin lína sem breytist um **eitt orð** fellir leitina.

Gervilínurnar eru heimatilbúnar. Prófin breyta raunlínum án þess að afrita þær:
orð er valið úr skránni sjálfri við keyrslu, svo enginn handritstexti er hér.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vidmid import vefleit  # noqa: E402
from vidmid.handritsreitir import (  # noqa: E402
    FROSID_COMMIT,
    VEFMOPPUR,
    VEFUNDANTEKNINGAR,
)

ROT = Path(__file__).resolve().parents[1]
STAT = "docs/vidmid/vefur/friends/phoebe-statistics.html"
LEIT = "docs/vidmid/vefur/search.json"
LINUR_I_SKRA = 9  # átta úr <pre>-dæminu + hóplínan

GERVILINA = "Gunther: I told you the blue notebook was left behind."

FROSNAR = vefleit.ur_commiti(ROT, FROSID_COMMIT, [STAT, LEIT])
AN_FROSNA = "frosna commit-ið er ekki í klóninu (grunnt klón)"


def _tilsvor(heimild: vefleit.Heimild) -> list[str]:
    return [t for e in vefleit.einingar_texta(heimild[2], heimild[1])
            for t in vefleit.tilsvor(e)]


class GreiningProf(unittest.TestCase):
    """Greinir `tilsvor` enskt tilsvar frá íslenskri merkingu?"""

    def test_enskt_tilsvar_finnst(self) -> None:
        self.assertEqual(vefleit.tilsvor(GERVILINA), [GERVILINA])

    def test_hopraedumadur_finnst(self) -> None:
        self.assertEqual(len(vefleit.tilsvor("Ross and Rachel: We were on a break")), 1)

    def test_islenskar_merkingar_standast(self) -> None:
        for eining in ("Heimild: Veðurstofa Íslands", "Nafn: texti",
                       "Endapunktur: https://api.vedur.is/quakes/events.",
                       "Margfaldari: fNum2", "Phoebe: (singing), (sings)"):
            with self.subTest(eining=eining):
                self.assertEqual(vefleit.tilsvor(eining), [])

    def test_islenskur_texti_eftir_tilvitnun_er_skorinn_af(self) -> None:
        """Í search.json rennur <code> saman við málsgreinina á eftir."""
        eining = f"{GERVILINA} og þetta er íslenskur texti."
        self.assertEqual(vefleit.tilsvor(eining), [f"{GERVILINA} og"])

    def test_tilsvar_i_html_kodabloki_og_eigind(self) -> None:
        html = (f'<p>Dæmi: <code>{GERVILINA}</code> og meira.</p>'
                f'<pre><code>[Sena]\n{GERVILINA}</code></pre>'
                f'<img alt="{GERVILINA}" src="x.webp">')
        self.assertEqual(_tilsvor(("s.html", ".html", html)), [GERVILINA] * 3)


class TreProf(unittest.TestCase):
    """(ii) Í trénu er ekkert undanþegið: ný lína í web/ eða docs/ fellir leitina."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        for mappa in VEFMOPPUR:
            (self.rot / mappa).mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _tre(self) -> list[vefleit.Frava]:
        heimildir, vantar = vefleit.ur_trenu(self.rot, VEFMOPPUR)
        self.assertEqual(vantar, [])
        return vefleit.bera_saman(heimildir, {})[0]

    def test_ny_lina_i_vefsidu_fellir(self) -> None:
        (self.rot / "web" / "sida.html").write_text(f"<pre>{GERVILINA}</pre>", encoding="utf-8")
        fravik = self._tre()
        self.assertEqual(len(fravik), 1)
        self.assertEqual(fravik[0][0], "web/sida.html")

    def test_ny_lina_i_json_i_docs_fellir(self) -> None:
        (self.rot / "docs" / "d.json").write_text(
            '{"gogn": ["%s"]}' % GERVILINA, encoding="utf-8")
        self.assertEqual(len(self._tre()), 1)

    def test_undanthaga_frosna_commitsins_gildir_ekki_i_trenu(self) -> None:
        """Síðan endurvakin í trénu er ný — undanþágan er bundin frosna commit-inu."""
        if FROSNAR is None:
            self.skipTest(AN_FROSNA)
        for slod, _, texti in FROSNAR:
            (self.rot / slod).parent.mkdir(parents=True, exist_ok=True)
            (self.rot / slod).write_text(texti, encoding="utf-8")
        self.assertEqual(len(self._tre()), 2 * LINUR_I_SKRA)

    def test_raunverulega_treid_er_hreint(self) -> None:
        heimildir, vantar = vefleit.ur_trenu(ROT, VEFMOPPUR)
        self.assertEqual(vantar, [])
        self.assertEqual(vefleit.bera_saman(heimildir, {}), ([], 0))


@unittest.skipIf(FROSNAR is None, AN_FROSNA)
class FrosidProf(unittest.TestCase):
    """(i)–(iii) á frosnu skránum eins og þær eru í FROSID_COMMIT."""

    def _saman(self, heimildir: list[vefleit.Heimild]) -> list[vefleit.Frava]:
        return vefleit.bera_saman(heimildir, VEFUNDANTEKNINGAR)[0]

    def _breytt(self, slod: str, breyta) -> list[vefleit.Heimild]:
        return [(s, v, breyta(t) if s == slod else t) for s, v, t in FROSNAR]

    def test_frosnu_skrarnar_eru_hreinar(self) -> None:
        self.assertEqual(self._saman(FROSNAR), [])

    def test_undanthagur_eru_nakvaemlega_fundnu_linurnar(self) -> None:
        fundin, _ = vefleit.fundin_tilsvor(FROSNAR)
        self.assertEqual(set(fundin), set(VEFUNDANTEKNINGAR))
        for lykill, fjoldi in fundin.items():
            with self.subTest(lykill=lykill):
                self.assertEqual(fjoldi, VEFUNDANTEKNINGAR[lykill][0])

    def test_adeins_tvaer_skrar_niu_linur_hvor(self) -> None:
        skrar = [slod for slod, _ in VEFUNDANTEKNINGAR]
        self.assertEqual(sorted(set(skrar)), [STAT, LEIT])
        self.assertEqual(skrar.count(STAT), LINUR_I_SKRA)
        self.assertEqual(skrar.count(LEIT), LINUR_I_SKRA)

    def test_an_undanthagna_fellur_leitin_a_theim_einum(self) -> None:
        fravik, fjoldi = vefleit.bera_saman(FROSNAR, {})
        self.assertEqual((len(fravik), fjoldi), (2 * LINUR_I_SKRA, 2 * LINUR_I_SKRA))

    def test_ny_lina_i_frosinni_skra_fellir(self) -> None:
        fravik = self._saman(self._breytt(
            STAT, lambda t: t.replace("</pre>", f"\n{GERVILINA}</pre>", 1)))
        self.assertEqual(len(fravik), 1)
        self.assertIn("ekkert undanþegið", fravik[0][2])

    def test_eitt_ord_breytt_i_undanthegna_linu_fellir(self) -> None:
        lina = _tilsvor(next(h for h in FROSNAR if h[0] == STAT))[0]
        breytt = lina[: -len(lina.split()[-1])] + "Xyz"
        texti = next(t for s, _, t in FROSNAR if s == STAT)
        self.assertIn(lina, texti)  # í <pre> eru bilin þegar stöðluð
        skyringar = [s for _, _, s in self._saman(
            self._breytt(STAT, lambda t: t.replace(lina, breytt, 1)))]
        self.assertEqual(len(skyringar), 2, skyringar)
        self.assertTrue(any("ekkert undanþegið" in s for s in skyringar))
        self.assertTrue(any("finnst ekki" in s for s in skyringar))

    def test_tvitekin_undanthegin_lina_fellir(self) -> None:
        """Undanþága gildir fyrir skráðan fjölda tilvika, ekki ótakmarkað."""
        lina = _tilsvor(next(h for h in FROSNAR if h[0] == STAT))[0]
        fravik = self._saman(self._breytt(
            STAT, lambda t: t.replace("</pre>", f"\n{lina}</pre>", 1)))
        self.assertEqual(len(fravik), 1)
        self.assertIn("2 sinnum", fravik[0][2])

    def test_undanthaga_bundin_vid_skra(self) -> None:
        """Sama lína undir annarri slóð er ekki undanþegin."""
        endurnefnt = [("annad.html" if s == STAT else s, v, t) for s, v, t in FROSNAR]
        self.assertIn("annad.html", {s for s, _, _ in self._saman(endurnefnt)})

    def test_fravik_prenta_ekki_linuna(self) -> None:
        fravik, _ = vefleit.bera_saman(FROSNAR, {})
        linur = [t for h in FROSNAR for t in _tilsvor(h)]
        for eitt in fravik:
            for lina in linur:
                self.assertNotIn(lina, " ".join(eitt))


class TiltaekniProf(unittest.TestCase):

    def test_ovidkomandi_commit_er_ekki_tiltaekt(self) -> None:
        self.assertIsNone(vefleit.ur_commiti(ROT, "0" * 40, [STAT]))

    def test_horfin_mappa_er_fravik(self) -> None:
        fravik, _ = vefleit.leita(ROT, ("ekki-til",), FROSID_COMMIT, {})
        self.assertIn("ekki til", fravik[0][2])


if __name__ == "__main__":
    unittest.main()
