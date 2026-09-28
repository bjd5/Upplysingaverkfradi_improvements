"""Próf fyrir keyrslupunkt gagnasöfnunar (``sofnun.saekja_allt``).

Prófin snerta hvorki net né ``data/raw/`` í repo-inu: söfnunaraðgerðunum er
skipt út fyrir gervi sem skila vistuðum svörum eða kasta þeim villum sem á að
prófa.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun import saekja_allt  # noqa: E402
from sofnun.frosid import FrosidVilla  # noqa: E402
from sofnun.hragogn import Svar  # noqa: E402
from sofnun.http import HttpVilla  # noqa: E402
from sofnun.saekja_allt import Nidurstada, SofnunVilla, keyra, safna  # noqa: E402
from sofnun.stillingar import StillingaVilla  # noqa: E402

LYKILS_BOD = "Umhverfisbreytuna TMDB_TOKEN vantar — hún geymir lykilinn."


def svar(*, ur_safni: bool, heiti: str = "svar.json") -> Svar:
    """Gervisvar; aðeins reitirnir sem keyrslupunkturinn skoðar eru raunverulegir."""
    return Svar(baeti=b"{}", slod_skrar=Path(heiti), provenance={}, ur_safni=ur_safni)


def ur_safni(**_rok) -> Svar:
    return svar(ur_safni=True)


def sott(**_rok) -> Svar:
    return svar(ur_safni=False)


def fellur(villa: Exception):
    """Aðgerð sem kastar tiltekinni villu."""
    def adgerd(**_rok):
        raise villa
    return adgerd


class KeyrsluProf(unittest.TestCase):
    """Sameiginleg umgjörð: söfnunum er skipt út fyrir gervi."""

    def sofn(self, **adgerdir) -> mock._patch:
        """Skiptir ``SOFN`` út fyrir gefnar aðgerðir og skilar patch-inu."""
        kort = {nafn: (adgerd, f"lýsing {nafn}") for nafn, adgerd in adgerdir.items()}
        return mock.patch.object(saekja_allt, "SOFN", kort)


class FlokkunProf(KeyrsluProf):
    """Fjórar niðurstöður eru greindar að: sótt, úr safni, óvirkt, brostið."""

    def test_safn_ur_geymslu_er_ekki_talid_sott(self) -> None:
        with self.sofn(skjalftar=ur_safni):
            nidurstada = keyra(["skjalftar"])
        self.assertEqual(nidurstada.ur_safni, ["skjalftar"])
        self.assertEqual(nidurstada.sott, [])
        self.assertTrue(nidurstada.netlaus)

    def test_sott_safn_er_talid_sott(self) -> None:
        with self.sofn(mbl=sott):
            nidurstada = keyra(["mbl"])
        self.assertEqual(nidurstada.sott, ["mbl"])
        self.assertFalse(nidurstada.netlaus)

    def test_vantandi_stilling_er_ovirkt_en_ekki_brostid(self) -> None:
        """TMDB án lykils er skjalfest staða verkefnisins, ekki keyrsluvilla."""
        with self.sofn(tmdb=fellur(StillingaVilla(LYKILS_BOD))):
            with self.assertLogs("sofnun", level="WARNING") as logg:
                nidurstada = keyra(["tmdb"])
        self.assertIn("tmdb", nidurstada.ovirk)
        self.assertEqual(nidurstada.brugdust, {})
        self.assertIn("TMDB_TOKEN", "\n".join(logg.output))

    def test_netvilla_er_brostid_safn(self) -> None:
        with self.sofn(skjalftar=fellur(HttpVilla("svaraði HTTP 503"))):
            with self.assertLogs("sofnun", level="ERROR"):
                nidurstada = keyra(["skjalftar"])
        self.assertIn("skjalftar", nidurstada.brugdust)

    def test_ostemmandi_frosid_eintak_er_brostid_safn(self) -> None:
        with self.sofn(mbl=fellur(FrosidVilla("summa stemmir ekki"))):
            with self.assertLogs("sofnun", level="ERROR"):
                nidurstada = keyra(["mbl"])
        self.assertIn("mbl", nidurstada.brugdust)


class SjalfstaediProf(KeyrsluProf):
    """Eitt safn sem bregst stöðvar ekki hin (regla 6 — villan er sögð, ekki kæfð)."""

    def test_tmdb_fellir_ekki_hin_sofnin(self) -> None:
        with self.sofn(
            skjalftar=ur_safni,
            hagstofan=ur_safni,
            vedurstodvar=ur_safni,
            mbl=ur_safni,
            tmdb=fellur(StillingaVilla(LYKILS_BOD)),
        ):
            with self.assertLogs("sofnun", level="WARNING"):
                nidurstada = keyra(list(saekja_allt.SOFN))
        self.assertEqual(
            nidurstada.ur_safni, ["skjalftar", "hagstofan", "vedurstodvar", "mbl"]
        )
        self.assertEqual(list(nidurstada.ovirk), ["tmdb"])
        self.assertTrue(nidurstada.netlaus)

    def test_brostid_safn_stodvar_ekki_thau_sem_a_eftir_koma(self) -> None:
        with self.sofn(skjalftar=fellur(HttpVilla("HTTP 503")), mbl=ur_safni):
            with self.assertLogs("sofnun", level="ERROR"):
                nidurstada = keyra(["skjalftar", "mbl"])
        self.assertEqual(nidurstada.ur_safni, ["mbl"])
        self.assertIn("skjalftar", nidurstada.brugdust)

    def test_ovaent_villa_fellur_obreytt_upp(self) -> None:
        """Villa sem lagið þekkir ekki er ekki flokkuð sem vænt niðurstaða."""
        with self.sofn(skjalftar=fellur(ZeroDivisionError("óvænt"))):
            with self.assertRaises(ZeroDivisionError):
                keyra(["skjalftar"])


class SafnaProf(KeyrsluProf):
    """``safna`` er inngangurinn sem ``main.py`` notar og ber villuna áfram."""

    def test_brostid_safn_fellur_med_sofnunarvillu(self) -> None:
        with self.sofn(skjalftar=fellur(HttpVilla("HTTP 503"))):
            with self.assertLogs("sofnun", level="ERROR"):
                with self.assertRaises(SofnunVilla) as gripid:
                    safna(["skjalftar"])
        self.assertIn("skjalftar", str(gripid.exception))

    def test_ovirkt_safn_fellir_ekki_keyrsluna(self) -> None:
        with self.sofn(skjalftar=ur_safni, tmdb=fellur(StillingaVilla(LYKILS_BOD))):
            with self.assertLogs("sofnun", level="WARNING"):
                nidurstada = safna(["skjalftar", "tmdb"])
        self.assertTrue(nidurstada.netlaus)
        self.assertEqual(nidurstada.brugdust, {})


class SkipanalinuProf(KeyrsluProf):
    """Skipanalínan: `listi` telur upp, skilagildið ber niðurstöðuna."""

    def test_listi_telur_upp_sofnin_an_ad_saekja(self) -> None:
        with mock.patch("builtins.print") as prentun:
            self.assertEqual(saekja_allt.main(["listi"]), 0)
        prentud = " ".join(str(kall.args[0]) for kall in prentun.call_args_list)
        for nafn in saekja_allt.SOFN:
            self.assertIn(nafn, prentud)

    def test_skilagildi_er_0_thegar_allt_er_i_lagi(self) -> None:
        with self.sofn(skjalftar=ur_safni):
            self.assertEqual(saekja_allt.main(["skjalftar"]), 0)

    def test_skilagildi_er_1_thegar_safn_brestur(self) -> None:
        with self.sofn(skjalftar=fellur(HttpVilla("HTTP 503"))):
            with self.assertLogs("sofnun", level="ERROR"):
                self.assertEqual(saekja_allt.main(["skjalftar"]), 1)

    def test_nominatim_er_ekki_i_sofnunum(self) -> None:
        """Hnit VR-II eru frosin í vinnslulaginu og ekki sótt í hverri keyrslu."""
        self.assertNotIn("nominatim", saekja_allt.SOFN)

    def test_oll_fjogur_frosnu_sofnin_eru_i_sofnunum(self) -> None:
        for nafn in ("skjalftar", "hagstofan", "vedurstodvar", "mbl"):
            self.assertIn(nafn, saekja_allt.SOFN)


class SamantektarProf(unittest.TestCase):
    def test_samantekt_nefnir_hvern_flokk(self) -> None:
        nidurstada = Nidurstada(
            sott=["mbl"], ur_safni=["skjalftar"],
            ovirk={"tmdb": LYKILS_BOD}, brugdust={"hagstofan": "HTTP 503"},
        )
        with self.assertLogs("sofnun", level="INFO") as logg:
            saekja_allt.samantekt(nidurstada)
        allt = "\n".join(logg.output)
        for nafn in ("mbl", "skjalftar", "tmdb", "hagstofan"):
            self.assertIn(nafn, allt)


if __name__ == "__main__":
    unittest.main()
