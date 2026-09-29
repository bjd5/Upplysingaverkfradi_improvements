"""Próf fyrir söfnunareiningarnar. Engin netsamskipti og ekkert skrifað í repo-ið.

Tvær umgjörðir:

``FrosidRepoProf``
    Les raunverulegu möppuna ``data/raw/`` og staðfestir að söfnin sem þar
    liggja sendi ekkert netkall. Opnarinn fellur verði hann kallaður, svo
    prófið sannar bæði að kallinu sé sleppt og að ekkert sé skrifað.

``SofnunarProf``
    Allt sem skrifar fær sína eigin ``data/raw/`` úr ``tempfile``. Möppan í
    repo-inu er aldrei skrifuð í (regla 10).
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun import hagstofan, http, sofn, stillingar  # noqa: E402
from sofnun.frosid import frosid_svar  # noqa: E402
from sofnun.http import TILRAUNIR, HttpVilla  # noqa: E402
from sofnun.stillingar import StillingaVilla  # noqa: E402
from test_http import Gervisvar, Gervitengill, http_villa  # noqa: E402

TENGILIDUR = "nafn@skoli.is"

# Gervilykill. Ekkert raunverulegt leyndarmál kemur nálægt prófunum, og strengurinn
# er valinn svo hann sé auðþekkjanlegur finnist hann þar sem hann á ekki að vera.
LYKILL = "ENGINN-RAUNVERULEGUR-LYKILL-123"

RAUNVERULEG_RAW = Path(hjalp.ROT) / "data" / "raw"


def bannadur_opnari(*_rok, **_nefnd):
    """Opnari sem fellur strax. Sannar að ekkert netkall hafi verið sent."""
    raise AssertionError("Netkall var sent þótt gagnið liggi þegar í data/raw/.")


class FrosidRepoProf(unittest.TestCase):
    """Söfnin í ``data/raw/`` repo-sins mega ekki sækja neitt (regla 4).

    Þetta er skilyrðið fyrir verklokum issue #13: sjálfgefin keyrsla byggir
    síðuna úr frosnu gögnunum og talar ekki við netið.
    """

    def setUp(self) -> None:
        stillingar.lesa_env_skra.cache_clear()
        http.hreinsa_hradaminni()
        self.addCleanup(http.hreinsa_hradaminni)
        umhverfi = mock.patch.dict(os.environ, {"NOTANDA_AUDKENNI": TENGILIDUR})
        umhverfi.start()
        self.addCleanup(umhverfi.stop)

    def test_skjalftar_koma_ur_raw(self) -> None:
        svar = sofn.saekja_skjalfta(opnari=bannadur_opnari)
        self.assertTrue(svar.ur_safni)
        self.assertEqual(svar.slod_skrar.name, "events.json")

    def test_vedurstodvar_koma_ur_raw(self) -> None:
        svar = sofn.saekja_stodvar(opnari=bannadur_opnari)
        self.assertTrue(svar.ur_safni)
        self.assertTrue(svar.slod_skrar.name.startswith("stations-"))

    def test_hagstofan_kemur_ur_raw(self) -> None:
        """Bæði köllin eru fryst: lýsigögnin og svarið sjálft."""
        lysigogn, gogn = hagstofan.saekja_hagstofuna(opnari=bannadur_opnari)
        self.assertTrue(lysigogn.ur_safni)
        self.assertTrue(gogn.ur_safni)
        self.assertEqual(lysigogn.slod_skrar.name, "metadata.json")
        self.assertEqual(gogn.slod_skrar.name, "response.json")

    def test_mbl_kemur_ur_raw(self) -> None:
        svar = sofn.saekja_forsidu(opnari=bannadur_opnari)
        self.assertTrue(svar.ur_safni)
        self.assertTrue(svar.slod_skrar.name.endswith(".html"))

    def test_mbl_beidnin_visar_a_sott_slod(self) -> None:
        """Slóðin sem yrði sótt á að vera sú sem frosna eintakið kom af."""
        lysigogn = json.loads(
            next((RAUNVERULEG_RAW / "mbl").glob("mbl-*.json")).read_text(encoding="utf-8")
        )
        self.assertEqual(sofn.MBL_BEIDNI.slod, lysigogn["source_url"])

    def test_nominatim_er_ekki_lengur_sott(self) -> None:
        """Hnit VR-II eru frosin í vinnslulaginu, ekki flett upp í hverri keyrslu."""
        self.assertFalse(hasattr(sofn, "saekja_hnit_vr_ii"))
        self.assertFalse(hasattr(sofn, "NOMINATIM_BEIDNI"))


class TmdbLykilsProf(unittest.TestCase):
    """TMDB án lykils: skiljanleg villa, engin þögn og ekkert gildi í boðunum."""

    def setUp(self) -> None:
        stillingar.lesa_env_skra.cache_clear()

    def test_vantandi_lykill_fellur_med_skyringu(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(stillingar, "lesa_env_skra", dict):
                with self.assertRaises(StillingaVilla) as gripid:
                    sofn.saekja_tmdb(opnari=bannadur_opnari)
        bod = str(gripid.exception)
        self.assertIn("TMDB_TOKEN", bod)          # nefnir breytuna
        self.assertIn(".env", bod)                # segir hvar hún er sett
        self.assertIn("themoviedb.org", bod)      # og hvar lykillinn fæst

    def test_villan_er_ekki_thoggud(self) -> None:
        """Vantandi lykill skilar ekki tómu svari — hann kastar (regla 6)."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(stillingar, "lesa_env_skra", dict):
                with self.assertRaises(StillingaVilla):
                    sofn.leynihausar()


class SofnunarProf(unittest.TestCase):
    """Sameiginleg umgjörð fyrir allt sem skrifar: eigin data/raw/ og engin bið."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.svefn: list[float] = []
        http.hreinsa_hradaminni()
        stillingar.lesa_env_skra.cache_clear()
        umhverfi = mock.patch.dict(
            os.environ, {"NOTANDA_AUDKENNI": TENGILIDUR, "BID_MILLI_KALLA": "0"}
        )
        umhverfi.start()
        self.addCleanup(umhverfi.stop)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(http.hreinsa_hradaminni)

    def skrar(self, thjonusta: str) -> list[str]:
        mappa = self.rot / thjonusta
        return sorted(skra.name for skra in mappa.iterdir()) if mappa.is_dir() else []


class EndurtilraunaProf(SofnunarProf):
    """Endurtilraunir stöðvast með þaki, og ekkert er vistað þegar þær þrýtur."""

    def test_endurtilraunir_stodvast_med_thaki(self) -> None:
        tengill = Gervitengill(*[http_villa(503)] * (TILRAUNIR + 5))
        with self.assertRaises(HttpVilla):
            sofn.saekja_skjalfta(
                rot=self.rot, opnari=tengill, sofa=self.svefn.append
            )
        self.assertEqual(len(tengill.beidnir), TILRAUNIR)
        self.assertEqual(self.skrar("vedur-quakes"), [])

    def test_villa_sem_lagast_ekki_er_ekki_endurtekin(self) -> None:
        """HTTP 404 lagast ekki við að spyrja aftur — ein tilraun og svo villa."""
        tengill = Gervitengill(http_villa(404))
        with self.assertRaises(HttpVilla):
            sofn.saekja_stodvar(
                rot=self.rot, opnari=tengill, sofa=self.svefn.append
            )
        self.assertEqual(len(tengill.beidnir), 1)

    def test_thogul_villa_er_omoguleg(self) -> None:
        """Bilun skilar ekki tómu svari og skrifar ekkert hálft í data/raw/."""
        tengill = Gervitengill(*[http_villa(500)] * TILRAUNIR)
        with self.assertRaises(HttpVilla) as gripid:
            sofn.saekja_stodvar(
                rot=self.rot, opnari=tengill, sofa=self.svefn.append
            )
        self.assertIn("ekkert var vistað", str(gripid.exception))
        self.assertEqual(self.skrar("vedurstodvar"), [])


class LykilsLekaProf(SofnunarProf):
    """Lykillinn fer í beiðnina og hvergi annað (regla 4)."""

    def saekja_tmdb(self, *svor: object) -> tuple[object, object]:
        tengill = Gervitengill(*svor)
        nidurstada = sofn.saekja_tmdb(
            lykill=LYKILL, rot=self.rot, opnari=tengill, sofa=self.svefn.append
        )
        return nidurstada, tengill

    def test_lykillinn_fylgir_beidninni(self) -> None:
        _, tengill = self.saekja_tmdb(Gervisvar(), Gervisvar())
        haus = tengill.beidnir[0].get_header("Authorization")
        self.assertEqual(haus, f"Bearer {LYKILL}")

    def test_lykillinn_kemst_ekki_i_provenance(self) -> None:
        (thattur, leikarar), _ = self.saekja_tmdb(Gervisvar(), Gervisvar())
        for svar in (thattur, leikarar):
            self.assertNotIn(LYKILL, json.dumps(svar.provenance, ensure_ascii=False))

    def test_lykillinn_kemst_ekki_a_disk(self) -> None:
        self.saekja_tmdb(Gervisvar(), Gervisvar())
        for skra in (self.rot / "tmdb").iterdir():
            self.assertNotIn(LYKILL, skra.read_text(encoding="utf-8", errors="replace"))

    def test_lykillinn_kemst_ekki_i_logg(self) -> None:
        with self.assertLogs("sofnun", level="DEBUG") as logg:
            self.saekja_tmdb(Gervisvar(), Gervisvar())
        self.assertNotIn(LYKILL, "\n".join(logg.output))

    def test_lykillinn_kemst_ekki_i_villuskilabod(self) -> None:
        with self.assertRaises(HttpVilla) as gripid:
            self.saekja_tmdb(http_villa(401))
        self.assertNotIn(LYKILL, str(gripid.exception))


class FrosidMblProf(SofnunarProf):
    """Nýtt mbl-eintak yfirskrifar ekki það sem greiningin byggir á."""

    def frysta_eintak(self, innihald: bytes = b"<html>frosid</html>") -> Path:
        """Skrifar frosið eintak á gamla sniðinu í tímabundnu möppuna."""
        import hashlib

        mappa = self.rot / "mbl"
        mappa.mkdir(parents=True)
        html = mappa / "mbl-20260916T120851Z.html"
        html.write_bytes(innihald)
        (mappa / "mbl-20260916T120851Z.json").write_text(
            json.dumps({
                "source_url": "https://www.mbl.is/frettir/",
                "md5": hashlib.md5(innihald).hexdigest(),
            }),
            encoding="utf-8",
        )
        return html

    def test_frosid_eintak_er_skilad_an_kalls(self) -> None:
        self.frysta_eintak()
        svar = sofn.saekja_forsidu(rot=self.rot, opnari=bannadur_opnari)
        self.assertTrue(svar.ur_safni)
        self.assertEqual(svar.baeti, b"<html>frosid</html>")

    def test_thvinga_saekir_nytt_an_ad_yfirskrifa(self) -> None:
        frosid = self.frysta_eintak()
        nytt = Gervisvar(baeti=b"<html>nytt</html>", efnistegund="text/html")
        svar = sofn.saekja_forsidu(
            thvinga=True, rot=self.rot, opnari=Gervitengill(nytt),
            sofa=self.svefn.append,
        )
        self.assertFalse(svar.ur_safni)
        self.assertEqual(frosid.read_bytes(), b"<html>frosid</html>")
        self.assertNotEqual(svar.slod_skrar, frosid)

    def test_frosna_eintakid_er_afram_vidmidid(self) -> None:
        """Eftir nýja sókn skilar sjálfgefin keyrsla samt frosna eintakinu."""
        self.frysta_eintak()
        sofn.saekja_forsidu(
            thvinga=True, rot=self.rot,
            opnari=Gervitengill(Gervisvar(baeti=b"<html>nytt</html>", efnistegund="text/html")),
            sofa=self.svefn.append,
        )
        svar = sofn.saekja_forsidu(rot=self.rot, opnari=bannadur_opnari)
        self.assertEqual(svar.baeti, b"<html>frosid</html>")


class HalfFrosidProf(SofnunarProf):
    """Hálft frosið Hagstofueintak er sagt upphátt, ekki notað í kyrrþey."""

    def test_vantandi_svar_er_skrad_og_sott_upp_a_nytt(self) -> None:
        import hashlib

        mappa = self.rot / "hagstofan"
        mappa.mkdir(parents=True)
        lysigogn = b'{"variables": []}'
        (mappa / "metadata.json").write_bytes(lysigogn)
        (mappa / "provenance.json").write_text(
            json.dumps({"sha256": {"metadata.json": hashlib.sha256(lysigogn).hexdigest()}}),
            encoding="utf-8",
        )
        with self.assertLogs("sofnun.hagstofan", level="WARNING") as logg:
            self.assertIsNone(hagstofan.frosin_hagstofa(self.rot))
        self.assertIn("response.json", "\n".join(logg.output))

    def test_tomt_safn_gefur_ekkert_frosid_svar(self) -> None:
        self.assertIsNone(frosid_svar("hagstofan", "response.json", self.rot))


if __name__ == "__main__":
    unittest.main()
