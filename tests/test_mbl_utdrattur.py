"""Próf fyrir regex-útdráttinn á mbl.is-eintakinu (issue #9).

Tvennt er prófað hér:

* **Viðmiðið.** Öll fimm mynstrin eiga að skila sömu tölu og gamla síðan birti
  fyrir NÁKVÆMLEGA sama eintak. Væntingarnar eru ekki handskrifaðar hér heldur
  lesnar úr ``docs/vidmid/vidmid.json`` — breytist viðmiðið fellur prófið.
* **Jaðartilvikin.** Finnist mynstur ekki, eða gefi það tvíræða niðurstöðu, á
  að koma skýr villa en ekki þögult núll eða tómur listi (regla 6).

Prófin eru netlaus og lesa frosna eintakið í ``data/raw/mbl/`` án þess að
skrifa í það (regla 10). Jaðartilvikin nota gervieintök úr ``mbl_gervigogn``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from mbl_vidmid import (  # noqa: E402
    ELDRA_EINTAKID,
    FROSNA_EINTAKID,
    FROSNA_MD5,
    FROSNA_UPPRUNASLOD,
    vidmidstolur,
)
from vinnsla.mbl_eintak import finna_eintok  # noqa: E402
from vinnsla.mbl_mynstur import SPURNINGAR, UtdrattarVilla  # noqa: E402
from vinnsla.mbl_ord import synileg_ord, synilegur_texti  # noqa: E402
from vinnsla.mbl_utdrattur import (  # noqa: E402
    draga_ut_allt,
    draga_ut_gengi_usd,
    draga_ut_hitastig,
    draga_ut_synileg_ord,
)


class VidmidProf(unittest.TestCase):
    """Skila mynstrin fimm sömu tölum og gamla síðan birti?"""

    @classmethod
    def setUpClass(cls) -> None:
        eintok = [e for e in finna_eintok() if e.skraarheiti.startswith(FROSNA_EINTAKID)]
        if not eintok:
            raise AssertionError(
                f"{FROSNA_EINTAKID}.html finnst ekki í data/raw/mbl/. "
                "Það er eina eintakið sem til er — sjá data/raw/README.md."
            )
        cls.eintak = eintok[0]
        cls.utdraettir = draga_ut_allt(cls.eintak.lesa_html())
        cls.svor = {u.spurning.lykill: u.gildi for u in cls.utdraettir}

    def test_eintakid_er_thad_sem_vidmidid_lysir(self) -> None:
        """Samanburður er marklaus nema skráin sé sannarlega sú sama."""
        self.assertEqual(self.eintak.md5, FROSNA_MD5)
        self.assertEqual(self.eintak.upprunaslod, FROSNA_UPPRUNASLOD)

    def test_oll_fimm_mynstrin_skila_vidmidinu(self) -> None:
        """Kjarninn: fimm mynstur, fimm tölur, engin þeirra víkur."""
        self.assertEqual(self.svor, vidmidstolur(FROSNA_EINTAKID))

    def test_hver_spurning_fyrir_sig(self) -> None:
        """Sama og að ofan, en fellur á einni spurningu í einu — læsilegri villa."""
        vaent = vidmidstolur(FROSNA_EINTAKID)
        for spurning in SPURNINGAR:
            with self.subTest(spurning=spurning.numer, lykill=spurning.lykill):
                self.assertEqual(self.svor[spurning.lykill], vaent[spurning.lykill])

    def test_frettatilvik_eru_fleiri_en_einstakar_frettir(self) -> None:
        """Gamla síðan skráði 99 tilvik sem urðu 43 fréttir eftir afritahreinsun."""
        frettir = next(u for u in self.utdraettir if u.spurning.numer == 1)
        self.assertEqual(frettir.tilvik, 99)
        self.assertEqual(frettir.einstok, 43)

    def test_vidmidid_greinir_eintokin_ad(self) -> None:
        """Eldra eintakið hefur aðrar tölur — annars væri samanburðurinn tómur.

        Gamla síðan las tvö eintök með níu daga millibili. Fjórar af fimm
        tölum breyttust milli þeirra; hitinn einn stóð í stað.
        """
        eldra = vidmidstolur(ELDRA_EINTAKID)
        nyrra = vidmidstolur(FROSNA_EINTAKID)
        breyttust = [lykill for lykill in nyrra if eldra[lykill] != nyrra[lykill]]
        self.assertEqual(
            sorted(breyttust),
            ["auglysingareitir", "einstakar-frettir", "gengi-usd", "synileg-ord"],
        )
        self.assertEqual(eldra["hitastig-reykjavik"], nyrra["hitastig-reykjavik"])

    def test_hvert_svar_ber_mynstrid_sitt(self) -> None:
        """Talan er órekjanleg án mynstursins sem framkallaði hana (regla 8)."""
        for utdrattur in self.utdraettir:
            with self.subTest(lykill=utdrattur.spurning.lykill):
                self.assertTrue(utdrattur.mynstur)
                self.assertTrue(utdrattur.mynsturheiti)
                self.assertTrue(utdrattur.synishorn)
                self.assertGreater(utdrattur.tilvik, 0)


class TyntMynsturProf(unittest.TestCase):
    """Finnist mynstur ekki á að koma skýr villa, ekki tóm niðurstaða (regla 6)."""

    def _stadfesta_villu(self, html_texti: str, vaent_ord: str) -> None:
        with self.assertRaises(UtdrattarVilla) as samhengi:
            draga_ut_allt(html_texti)
        self.assertIn(vaent_ord, str(samhengi.exception))

    def test_engin_frettaslod(self) -> None:
        self._stadfesta_villu(
            '<html><body><a href="/frettir/innlent/">Innlent</a></body></html>',
            "MYNSTUR_FRETTASLOD",
        )

    def test_ekkert_hitastig(self) -> None:
        self._stadfesta_villu(
            '<html><body><a href="/frettir/innlent/2026/09/16/frett/">F</a>'
            "</body></html>",
            "MYNSTUR_HITI_REYKJAVIK",
        )

    def test_ekkert_gengi(self) -> None:
        html_texti = (
            '<html><body><a href="/frettir/innlent/2026/09/16/frett/">F</a>'
            "<select><option selected>Reykjavík</option></select>"
            '<span class="value">11</span><span class="unit">&deg;</span>'
            "</body></html>"
        )
        self._stadfesta_villu(html_texti, "MYNSTUR_USD_GENGI")

    def test_engin_synileg_ord(self) -> None:
        """Tómur orðalisti er villa, ekki núll — fréttasíða án orða er ómöguleg."""
        with self.assertRaises(UtdrattarVilla) as samhengi:
            draga_ut_synileg_ord("<html><head><title>x</title></head><body>"
                                 "<script>var a = 1;</script></body></html>")
        self.assertIn("Ekkert sýnilegt orð", str(samhengi.exception))

    def test_enginn_auglysingareitur(self) -> None:
        self._stadfesta_villu(
            '<html><body><a href="/frettir/innlent/2026/09/16/frett/">F</a>'
            "<select><option selected>Reykjavík</option></select>"
            '<span class="value">11</span><span class="unit">&deg;</span>'
            '<script>arrCurrency[1] = new MakeItem("USD", "121.33");</script>'
            "</body></html>",
            "MYNSTUR_AUGLYSINGAREITUR",
        )

    def test_villan_nefnir_mynstrid_sem_brast(self) -> None:
        """Skilaboðin segja hvað brast, svo hægt sé að laga rétt mynstur."""
        with self.assertRaises(UtdrattarVilla) as samhengi:
            draga_ut_hitastig("<html><body>ekkert veður</body></html>")
        skilabod = str(samhengi.exception)
        self.assertIn("Hitastig Reykjavíkur fannst ekki", skilabod)
        self.assertIn("MYNSTUR_HITI_REYKJAVIK", skilabod)


class TviraedniProf(unittest.TestCase):
    """Tvíræð niðurstaða er villa — útdrátturinn velur ekki milli gilda."""

    def test_tvo_hitastig_gefa_villu(self) -> None:
        html_texti = (
            "<select><option selected>Reykjavík</option></select>"
            '<span class="value">11</span><span class="unit">&deg;</span>'
            "<select><option selected>Reykjavík</option></select>"
            '<span class="value">3</span><span class="unit">&deg;</span>'
        )
        with self.assertRaises(UtdrattarVilla) as samhengi:
            draga_ut_hitastig(html_texti)
        self.assertIn("Fleiri en eitt hitastig", str(samhengi.exception))

    def test_tvo_gengi_gefa_villu(self) -> None:
        html_texti = (
            '<script>arrCurrency[1] = new MakeItem("USD", "121.33");</script>'
            '<script>arrCurrency[2] = new MakeItem("USD", "99.00");</script>'
        )
        with self.assertRaises(UtdrattarVilla) as samhengi:
            draga_ut_gengi_usd(html_texti)
        self.assertIn("Ósamræmd USD-gengi", str(samhengi.exception))

    def test_endurtekid_sama_gengi_er_leyft(self) -> None:
        """Sama gildi tvisvar er ekki tvíræðni — aðeins ólík gildi eru það."""
        html_texti = (
            '<script>arrCurrency[1] = new MakeItem("USD", "121.33");</script>'
            '<script>arrCurrency[2] = new MakeItem("USD", "121.33");</script>'
        )
        utdrattur = draga_ut_gengi_usd(html_texti)
        self.assertEqual(utdrattur.gildi, 121.33)
        self.assertEqual(utdrattur.tilvik, 2)
        self.assertEqual(utdrattur.einstok, 1)


class OrdahreinsunProf(unittest.TestCase):
    """Röð hreinsunarþrepanna ræður orðatölunni og er því prófuð sérstaklega."""

    def test_script_og_style_teljast_ekki(self) -> None:
        texti = synilegur_texti(
            "<body><script>leyniord</script><style>faliord</style>synilegt</body>"
        )
        self.assertNotIn("leyniord", texti)
        self.assertNotIn("faliord", texti)
        self.assertIn("synilegt", texti)

    def test_tagg_verdur_ad_bili(self) -> None:
        """Annars límdust orð sitt hvorum megin við tagg saman í eitt."""
        self.assertEqual(synileg_ord("<p>eitt</p><p>tvo</p>"), ["eitt", "tvo"])

    def test_html_takn_eru_afkodud(self) -> None:
        self.assertEqual(synileg_ord("<p>eitt&nbsp;tvo</p>"), ["eitt", "tvo"])

    def test_tolur_teljast_ekki_ord(self) -> None:
        self.assertEqual(synileg_ord("<p>orð 42 orð</p>"), ["orð", "orð"])

    def test_bandstrikad_ord_er_eitt_ord(self) -> None:
        self.assertEqual(synileg_ord("<p>ferða-lög</p>"), ["ferða-lög"])

    def test_olokid_script_naer_til_enda(self) -> None:
        """Ólokið tagg mætti ekki hleypa forritskóða inn í talninguna."""
        self.assertEqual(synileg_ord("<body>synilegt<script>leyniord"), ["synilegt"])


if __name__ == "__main__":
    unittest.main()
