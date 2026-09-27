"""Próf á kröfu issue #9: fást öll fimm svörin úr SQL og eru þau rekjanleg?

Þetta er skilyrðið fyrir verklokum, orðað í issue #9:

* **Allar fimm spurningar æfingarinnar eru svaranlegar með SQL-fyrirspurn** á
  töflunum úr ``005_mbl_regex.sql``.
* **Hvert svar er rekjanlegt** í mynstrið sem framkallaði það og eintakið sem
  það var lesið úr (regla 8).

Talan sem SQL skilar er borin saman við ``docs/vidmid/vidmid.json`` — tölurnar
sem gamla síðan birti fyrir NÁKVÆMLEGA sama eintak. Væntingarnar eru því ekki
handskrifaðar hér; breytist viðmiðið fellur prófið.

Hegðun hleðslunnar sjálfrar — mörg eintök, endurkeyrsla, villur — er prófuð í
``test_mbl_hledsla.py``. Mynstrin án grunns eru prófuð í ``test_mbl_utdrattur.py``.

Prófin eru netlaus og lesa frosna eintakið án þess að skrifa í það (regla 10).

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from mbl_grunnur import GrunnProf  # noqa: E402
from mbl_vidmid import (  # noqa: E402
    FROSNA_EINTAKID,
    FROSNA_UPPRUNASLOD,
    vidmidstala,
    vidmidstolur,
)
from vinnsla.mbl_hledsla import hlada_eintak  # noqa: E402
from vinnsla.mbl_mynstur import MYNSTUR_FRETTASLOD  # noqa: E402


class HladidFrosidEintak(GrunnProf):
    """Frosna eintakið hlaðið í tóman grunn — undanfari allra prófa hér."""

    def setUp(self) -> None:
        super().setUp()
        self.eintak = self.frosna_eintakid()
        self.hledsla = hlada_eintak(self.samband, self.eintak)
        self.sott = self.eintak.sotta_stund


class SqlSvorProf(HladidFrosidEintak):
    """Eru spurningarnar fimm svaranlegar með SQL — og með réttu svari?"""

    def test_fimm_svor_i_grunninum(self) -> None:
        radir = self.svor(self.sott)
        self.assertEqual(len(radir), 5)
        self.assertEqual([r["nr"] for r in radir], [1, 2, 3, 4, 5])

    def test_svorin_eru_vidmidid(self) -> None:
        """Kjarninn: talan sem SQL skilar er talan sem gamla síðan birti."""
        ur_grunni = {r["lykill"]: r["gildi"] for r in self.svor(self.sott)}
        self.assertEqual(ur_grunni, vidmidstolur(FROSNA_EINTAKID))

    def test_hver_spurning_hefur_texta_og_einingu(self) -> None:
        """Svar án spurningar er ekki svar — báðar hliðar liggja í grunninum."""
        for rad in self.svor(self.sott):
            with self.subTest(lykill=rad["lykill"]):
                self.assertTrue(rad["spurning"].endswith("?"))
                self.assertTrue(rad["svar"])
                self.assertTrue(rad["eining"])
                self.assertTrue(rad["takmarkanir"])

    def test_spurning_fletts_upp_eftir_lykli(self) -> None:
        """Ein spurning, ein fyrirspurn — með breytu."""
        rad = self.samband.execute(
            "SELECT value_number, value_text FROM mbl_extractions "
            "WHERE question_key = ?",
            ("gengi-usd",),
        ).fetchone()
        self.assertEqual(rad["value_number"], 121.33)
        self.assertEqual(rad["value_text"], "121,33 ISK fyrir 1 USD")


class EittSvarIEinuProf(HladidFrosidEintak):
    """Eitt próf á hvert svar æfingarinnar — fimm spurningar, fimm próf.

    ``test_svorin_eru_vidmidid`` að ofan ber öll fimm saman í einu lagi og er
    það sem fellur ef eitthvað skeikar. Prófin hér svara annarri spurningu:
    **hvert** svaranna skeikaði. Villuskilaboðin nefna þá eina spurningu í
    stað þess að bera fram fimm talna kort til samanburðar.

    Væntu tölurnar eru lesnar úr ``docs/vidmid/vidmid.json``; textinn, einingin
    og mynsturheitið eru það sem þessi útfærsla lofar og er staðfest hér.
    """

    def _svar(self, lykill: str, mynsturheiti: str, vaentur_texti: str):
        """Les eitt svar úr SQL og staðfestir tölu, texta, einingu og mynstur.

        Talan er borin við viðmiðið; hitt er borið við það sem
        ``mbl_utdrattur`` lofar. Svarið verður að benda á sitt eigið eintak,
        annars er talan órekjanleg (regla 8).
        """
        rad = self.eitt_svar(self.sott, lykill)
        self.assertEqual(rad["gildi"], vidmidstala(FROSNA_EINTAKID, lykill))
        self.assertEqual(rad["svar"], vaentur_texti)
        self.assertEqual(rad["mynsturheiti"], mynsturheiti)
        self.assertEqual(rad["eintak"], self.eintak.skraarheiti)
        self.assertTrue(rad["mynstur"].strip())
        self.assertTrue(rad["synishorn"].strip())
        return rad

    def test_svar_1_einstakar_frettir(self) -> None:
        """1. „Hversu margar einstakar fréttir eru á síðunni?“ — 43 fréttir.

        Mynstrið fann 99 fréttahlekkjatilvik; sama grein tengist bæði úr mynd
        og fyrirsögn, svo afritahreinsun skilur 43 einstakar slóðir eftir.
        Báðar tölur liggja í grunninum svo hlutfallið sé rekjanlegt.
        """
        rad = self._svar(
            "einstakar-frettir", "MYNSTUR_FRETTASLOD", "43 einstakar fréttir"
        )
        self.assertEqual(rad["eining"], "fréttir")
        self.assertEqual(rad["tilvik"], 99)
        self.assertEqual(rad["einstok"], 43)

    def test_svar_2_hitastig_reykjavik(self) -> None:
        """2. „Hvert er hitastigið í Reykjavík?“ — 11 °C.

        Lesið úr veðurkassa síðunnar innan afmarkaðs glugga eftir valinni
        Reykjavík. Aðeins eitt hitastig má finnast: tvö væru tvíræðni og
        stöðvuðu útdráttinn.
        """
        rad = self._svar("hitastig-reykjavik", "MYNSTUR_HITI_REYKJAVIK", "11 °C")
        self.assertEqual(rad["eining"], "°C")
        self.assertEqual(rad["einstok"], 1)

    def test_svar_3_gengi_usd(self) -> None:
        """3. „Hvert er gengi Bandaríkjadals?“ — 121,33 ISK fyrir 1 USD.

        Sýnilegi innsláttarreiturinn er tómur í HTML-svarinu; gildið liggur
        neðar í JavaScript. Leitin er því afmörkuð við script-blokkir og sú
        afmörkun er hluti aðferðarinnar — hún fylgir svarinu í grunninn.
        """
        rad = self._svar("gengi-usd", "MYNSTUR_USD_GENGI", "121,33 ISK fyrir 1 USD")
        self.assertEqual(rad["eining"], "ISK á USD")
        self.assertEqual(rad["afmorkun"], "MYNSTUR_SCRIPT_BLOKK")

    def test_svar_4_synileg_ord(self) -> None:
        """4. „Hversu mörg sýnileg orð eru á síðunni?“ — 2.188 orð.

        Ósýnilegar blokkir (head, script, style, template, noscript og
        athugasemdir) eru fjarlægðar áður en talið er. Sú afmörkun ræður
        tölunni og fylgir henni því í grunninn.
        """
        rad = self._svar("synileg-ord", "MYNSTUR_ORD", "2.188 sýnileg orð")
        self.assertEqual(rad["eining"], "orð")
        self.assertEqual(rad["afmorkun"], "MYNSTUR_OSYNILEGT")
        # Einstök orð eru færri en tilvikin — annars væri ekkert orð endurtekið.
        self.assertLess(rad["einstok"], rad["tilvik"])

    def test_svar_5_auglysingareitir(self) -> None:
        """5. „Hversu margir auglýsingareitir eru skilgreindir?“ — 47 reitir.

        Talan er fjöldi einstakra ``Ads.renderSlot``-auðkenna, þ.e. skilgreindra
        reita, ekki staðfestur fjöldi birtra auglýsinga. Sú takmörkun er skráð
        með svarinu (regla 8) og er staðfest hér.
        """
        rad = self._svar(
            "auglysingareitir", "MYNSTUR_AUGLYSINGAREITUR", "47 auglýsingareitir"
        )
        self.assertEqual(rad["eining"], "reitir")
        self.assertIn("ekki staðfestur fjöldi", rad["takmarkanir"])


class RekjanleikiProf(HladidFrosidEintak):
    """Er hvert svar rekjanlegt í mynstrið OG eintakið? (regla 8)"""

    def setUp(self) -> None:
        super().setUp()
        self.radir = self.svor(self.sott)

    def test_hvert_svar_bendir_a_eintakid_sitt(self) -> None:
        for rad in self.radir:
            with self.subTest(lykill=rad["lykill"]):
                self.assertEqual(rad["eintak"], self.eintak.skraarheiti)
                self.assertEqual(rad["sott"], self.sott)
                self.assertEqual(rad["upprunaslod"], FROSNA_UPPRUNASLOD)

    def test_mynstrid_sjalft_liggur_i_grunninum(self) -> None:
        """Án mynstursins er ekki hægt að sjá hvers vegna talan varð þessi."""
        for rad in self.radir:
            with self.subTest(lykill=rad["lykill"]):
                self.assertTrue(rad["mynstur"].strip())
                self.assertTrue(rad["mynsturheiti"].startswith("MYNSTUR_"))
                self.assertTrue(rad["synishorn"].strip())

    def test_mynstrid_er_geymt_ordrett(self) -> None:
        """Geymt mynstur verður að vera þýðanlegt aftur — annars er það ólæsilegt."""
        rad = self.eitt_svar(self.sott, "einstakar-frettir")
        self.assertEqual(rad["mynstur"], MYNSTUR_FRETTASLOD.pattern)
        self.assertIn("VERBOSE", rad["mynsturflogg"])

    def test_eintakid_ber_sannreynd_lysigogn(self) -> None:
        """Sóknartími, MD5 og stærð fylgja með svo talan sé rekjanleg í hrágagnið."""
        rad = self.samband.execute(
            "SELECT md5, sha256, content_length_bytes, status_code "
            "FROM mbl_snapshots WHERE fetched_at = ?",
            (self.sott,),
        ).fetchone()
        self.assertEqual(rad["md5"], self.eintak.md5)
        self.assertEqual(rad["sha256"], self.eintak.sha256)
        self.assertEqual(rad["content_length_bytes"], self.eintak.staerd)
        self.assertEqual(rad["status_code"], 200)

    def test_afmorkun_fylgir_thegar_leitin_var_afmorkud(self) -> None:
        """USD fannst aðeins innan script-blokka; sú afmörkun er hluti aðferðarinnar."""
        rad = self.eitt_svar(self.sott, "gengi-usd")
        self.assertEqual(rad["afmorkun"], "MYNSTUR_SCRIPT_BLOKK")
        self.assertIn("script", rad["afmorkunarmynstur"])


if __name__ == "__main__":
    unittest.main()
