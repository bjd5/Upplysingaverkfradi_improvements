"""Próf fyrir handritsleitina á byggðu gömlu síðunni — ákvörðun (b) í issue #3.

Línurnar úr þætti 0101 sem gamla síðan birtir sem dæmi um þáttarann standa sem
stutt tilvitnun. Undanþágan er fryst lína fyrir línu (`VEFUNDANTEKNINGAR`).
Prófin sanna þrennt, hvert þar sem það á að bresta (docs/agenta-verkefni.md,
kafli 6):

1. Undanþágurnar ná **nákvæmlega** yfir línurnar sem finnast — engin umfram,
   engin vantar, og aðeins í skránum tveimur.
2. **Ný** handritslína hvar sem er í `docs/vidmid/vefur/` fellir leitina.
3. Undanþegin lína sem breytist um **eitt orð** fellir leitina.

Gervilínurnar eru heimatilbúnar. Prófin breyta raunlínum án þess að afrita þær:
orð er valið úr skránni sjálfri við keyrslu, svo enginn handritstexti er hér.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vidmid import vefleit  # noqa: E402
from vidmid.handritsreitir import VEFMAPPA, VEFUNDANTEKNINGAR  # noqa: E402

ROT = Path(__file__).resolve().parents[1]
STAT = "docs/vidmid/vefur/friends/phoebe-statistics.html"
LEIT = "docs/vidmid/vefur/search.json"
LINUR_I_SKRA = 9  # átta úr <pre>-dæminu + hóplínan

GERVILINA = "Gunther: I told you the blue notebook was left behind."


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
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "s.html"
            slod.write_text(
                f'<p>Dæmi: <code>{GERVILINA}</code> og meira.</p>'
                f'<pre><code>[Sena]\n{GERVILINA}</code></pre>'
                f'<img alt="{GERVILINA}" src="x.webp">', encoding="utf-8")
            fundin = [t for e in vefleit.einingar(slod) for t in vefleit.tilsvor(e)]
        self.assertEqual(fundin, [GERVILINA] * 3)


class RaunsidanProf(unittest.TestCase):
    """(i) Undanþágurnar ná nákvæmlega yfir línurnar sem finnast."""

    def test_undanthagur_eru_nakvaemlega_fundnu_linurnar(self) -> None:
        fundin, _, _ = vefleit.fundin_tilsvor(ROT, VEFMAPPA)
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
        fravik, _ = vefleit.leita(ROT, VEFMAPPA, {})
        self.assertEqual(len(fravik), 2 * LINUR_I_SKRA)
        self.assertEqual({slod for slod, _, _ in fravik}, {STAT, LEIT})

    def test_undanthaga_bundin_vid_skra(self) -> None:
        """Sama lína í annarri skrá er ekki undanþegin."""
        lykill = next(k for k in VEFUNDANTEKNINGAR if k[0] == STAT)
        fravik, _ = vefleit.leita(ROT, VEFMAPPA, {("annad.html", lykill[1]): (1, "x")})
        self.assertIn(STAT, {slod for slod, _, _ in fravik})


class AfritProf(unittest.TestCase):
    """(ii) og (iii) á afriti af skránum tveimur í bráðabirgðamöppu."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        for slod in (STAT, LEIT):
            (self.rot / slod).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROT / slod, self.rot / slod)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _leita(self) -> list[tuple[str, str, str]]:
        fravik, _ = vefleit.leita(self.rot, VEFMAPPA, VEFUNDANTEKNINGAR)
        return fravik

    def test_afritid_er_hreint(self) -> None:
        self.assertEqual(self._leita(), [])

    def test_ny_lina_i_nyrri_skra_fellir(self) -> None:
        (self.rot / VEFMAPPA / "ny.html").write_text(
            f"<pre>{GERVILINA}</pre>", encoding="utf-8")
        fravik = self._leita()
        self.assertEqual(len(fravik), 1)
        self.assertIn("ny.html", fravik[0][0])

    def test_ny_lina_i_undanthegna_skra_fellir(self) -> None:
        slod = self.rot / STAT
        slod.write_text(slod.read_text(encoding="utf-8").replace(
            "</pre>", f"\n{GERVILINA}</pre>", 1), encoding="utf-8")
        fravik = self._leita()
        self.assertEqual(len(fravik), 1)
        self.assertIn("ekkert undanþegið", fravik[0][2])

    def test_eitt_ord_breytt_i_undanthegna_linu_fellir(self) -> None:
        slod = self.rot / STAT
        texti = slod.read_text(encoding="utf-8")
        lina = next(t for e in vefleit.einingar(slod) for t in vefleit.tilsvor(e))
        sidasta = lina.split()[-1]
        breytt = lina[: -len(sidasta)] + "Xyz"
        # Línan er skráð með stöðluðum bilum; í <pre> eru þau þegar stöðluð.
        self.assertIn(lina, texti)
        slod.write_text(texti.replace(lina, breytt, 1), encoding="utf-8")
        skyringar = [s for _, _, s in self._leita()]
        self.assertEqual(len(skyringar), 2, skyringar)
        self.assertTrue(any("ekkert undanþegið" in s for s in skyringar))
        self.assertTrue(any("finnst ekki" in s for s in skyringar))

    def test_frava_prentar_ekki_linuna(self) -> None:
        fravik, _ = vefleit.leita(self.rot, VEFMAPPA, {})
        linur = [t for e in vefleit.einingar(self.rot / STAT) for t in vefleit.tilsvor(e)]
        for eitt in fravik:
            for lina in linur:
                self.assertNotIn(lina, " ".join(eitt))

    def test_tvitekin_undanthegin_lina_fellir(self) -> None:
        """Undanþága gildir fyrir skráðan fjölda tilvika, ekki ótakmarkað."""
        slod = self.rot / STAT
        texti = slod.read_text(encoding="utf-8")
        lina = next(t for e in vefleit.einingar(slod) for t in vefleit.tilsvor(e))
        slod.write_text(texti.replace("</pre>", f"\n{lina}</pre>", 1), encoding="utf-8")
        fravik = self._leita()
        self.assertEqual(len(fravik), 1)
        self.assertIn("2 sinnum", fravik[0][2])

    def test_horfin_mappa_er_fravik(self) -> None:
        fravik, _ = vefleit.leita(self.rot, "ekki-til", {})
        self.assertEqual(len(fravik), 1)


if __name__ == "__main__":
    unittest.main()
