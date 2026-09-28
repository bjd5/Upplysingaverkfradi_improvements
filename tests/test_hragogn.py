"""Próf fyrir hrágagnageymsluna: vistun, provenance og frosin eintök.

* ``sofnun.hragogn`` — vistun nýrra svara, provenance og endurnýting.
* ``sofnun.frosid`` — frosin eintök á eldri provenance-sniðum.

Öll gögn eru skrifuð í tímabundna möppu (``tempfile``); ``data/raw/`` í repo-inu
er aldrei skrifuð í. Engin netsamskipti.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun.hragogn import (  # noqa: E402
    HragagnaVilla,
    finna_fyrra_svar,
    mappa_safns,
    vista_svar,
)
from test_beidni import FROSID, skjalftabeidni  # noqa: E402
from sofnun.frosid import FrosidVilla, frosid_svar, frosin_eintok  # noqa: E402


# --- Hrágagnageymslan ----------------------------------------------------------

# Lyklarnir sem frosna skráin data/raw/vedur-quakes/provenance.json notar og
# lýsa beiðninni sjálfri. Nýja lagið verður að skrifa þá alla — annars er þetta
# nýtt snið en ekki það sama.
FROSNIR_LYKLAR = {
    "provider", "endpoint", "documentation", "method", "parameters",
    "request_url", "fetched_at_utc", "sha256", "response_bytes",
    "license", "license_url",
}

SVAR = b'{"type": "FeatureCollection", "features": []}'


class VistunProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def vista(self, **breytingar) -> object:
        beidni = skjalftabeidni(leyfi="CC BY 4.0",
                                leyfisslod="https://creativecommons.org/licenses/by/4.0/",
                                **breytingar)
        return vista_svar(beidni, SVAR, stada=200,
                          efnistegund="application/json", rot=self.rot)

    def test_svarid_er_vistad_obreytt(self) -> None:
        svar = self.vista()
        self.assertEqual(svar.slod_skrar.read_bytes(), SVAR)
        self.assertFalse(svar.ur_safni)

    def test_provenance_hefur_alla_frosnu_lyklana(self) -> None:
        svar = self.vista()
        self.assertLessEqual(FROSNIR_LYKLAR, set(svar.provenance))
        for lykill in ("provider", "endpoint", "documentation", "method", "parameters"):
            self.assertEqual(svar.provenance[lykill], FROSID[lykill])

    def test_provenance_skrair_summu_og_staerd(self) -> None:
        svar = self.vista()
        self.assertEqual(svar.provenance["sha256"], hashlib.sha256(SVAR).hexdigest())
        self.assertEqual(svar.provenance["response_bytes"], len(SVAR))
        self.assertEqual(svar.provenance["status_code"], 200)

    def test_provenance_skra_liggur_vid_hlid_gagnanna(self) -> None:
        svar = self.vista()
        provenance = svar.slod_skrar.with_suffix("").with_suffix(".provenance.json")
        skjal = json.loads(provenance.read_text(encoding="utf-8"))
        self.assertEqual(skjal["raw_file"], svar.slod_skrar.name)

    def test_tvaer_soknir_yfirskrifa_ekki_hvor_adra(self) -> None:
        """Hrágögnum er aldrei breytt eftir á — ekki heldur af næstu sókn (regla 4)."""
        fyrri = self.vista()
        seinni = self.vista()
        self.assertNotEqual(fyrri.slod_skrar, seinni.slod_skrar)
        self.assertTrue(fyrri.slod_skrar.is_file())

    def test_efnistegund_raedur_endingu(self) -> None:
        beidni = skjalftabeidni(thjonusta="mbl", heiti="mbl")
        svar = vista_svar(beidni, b"<html></html>", stada=200,
                          efnistegund="text/html; charset=UTF-8", rot=self.rot)
        self.assertEqual(svar.slod_skrar.suffix, ".html")

    def test_engar_timabundnar_skrar_skildar_eftir(self) -> None:
        self.vista()
        eftirlegukindur = [
            skra.name for skra in mappa_safns("vedur-quakes", self.rot).iterdir()
            if not skra.name.startswith("events-")
        ]
        self.assertEqual(eftirlegukindur, [])


class HeitaProf(unittest.TestCase):
    def test_thjonustuheiti_med_slod_er_hafnad(self) -> None:
        """Heitið kemur frá kallanda og ræður slóð undir data/raw/."""
        with self.assertRaises(HragagnaVilla):
            mappa_safns("../../etc")

    def test_islenskir_stafir_i_heiti_eru_hafnad(self) -> None:
        with self.assertRaises(HragagnaVilla):
            mappa_safns("veðurstöðvar")


class FyrraSvarProf(unittest.TestCase):
    """Frosnu skrárnar úr upprunaverkefninu eiga að þekkjast óbreyttar."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.mappa = self.rot / "vedur-quakes"
        self.mappa.mkdir(parents=True)
        (self.mappa / "events.json").write_bytes(SVAR)
        self.skrifa_provenance(hashlib.sha256(SVAR).hexdigest())

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def skrifa_provenance(self, summa: str) -> None:
        skjal = {**FROSID, "sha256": summa}
        (self.mappa / "provenance.json").write_text(
            json.dumps(skjal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def test_sama_beidni_finnst_i_frosnu_sniði(self) -> None:
        svar = finna_fyrra_svar(skjalftabeidni(), self.rot)
        self.assertIsNotNone(svar)
        self.assertTrue(svar.ur_safni)
        self.assertEqual(svar.baeti, SVAR)

    def test_onnur_beidni_finnst_ekki(self) -> None:
        onnur = skjalftabeidni(breytur={**FROSID["parameters"], "size_min": 4})
        self.assertIsNone(finna_fyrra_svar(onnur, self.rot))

    def test_tom_mappa_gefur_ekkert(self) -> None:
        self.assertIsNone(finna_fyrra_svar(skjalftabeidni(thjonusta="hagstofan"), self.rot))

    def test_breytt_hragogn_stodva_keyrslu(self) -> None:
        """Skemmd hrágögn mega ekki fara þegjandi inn í rannsóknina (regla 6)."""
        (self.mappa / "events.json").write_bytes(b"{}")
        with self.assertRaises(HragagnaVilla):
            finna_fyrra_svar(skjalftabeidni(), self.rot)

    def test_onyt_provenance_skra_stodvar_ekki_leitina(self) -> None:
        """Nýjasta skráin er ónýt; leitin heldur áfram í þá eldri og segir frá."""
        (self.mappa / "events-20990101T000000Z.provenance.json").write_text(
            "{ekki json", encoding="utf-8"
        )
        with self.assertLogs("sofnun.hragogn", level="WARNING"):
            svar = finna_fyrra_svar(skjalftabeidni(), self.rot)
        self.assertIsNotNone(svar)



# --- Frosin eintök -------------------------------------------------------------

INNIHALD = b'{"gogn": [1, 2, 3]}'
ONNUR_SUMMA = "0" * 64


class FrosidProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def mappa(self, thjonusta: str = "hagstofan") -> Path:
        mappa = self.rot / thjonusta
        mappa.mkdir(parents=True, exist_ok=True)
        return mappa

    def skra(self, heiti: str, innihald: bytes = INNIHALD, thjonusta: str = "hagstofan") -> Path:
        slod = self.mappa(thjonusta) / heiti
        slod.write_bytes(innihald)
        return slod

    def arfur(self, kort: dict[str, str], thjonusta: str = "hagstofan") -> None:
        """Skrifar provenance á sniði Hagstofunnar: summur í korti."""
        (self.mappa(thjonusta) / "provenance.json").write_text(
            json.dumps({"methods": ["GET", "POST"], "sha256": kort}), encoding="utf-8"
        )

    def fylgiskra(self, stofn: str, skjal: dict, thjonusta: str = "mbl") -> None:
        """Skrifar lýsigögn á sniði mbl-skriftunnar: ein skrá, eitt skjal."""
        (self.mappa(thjonusta) / f"{stofn}.json").write_text(
            json.dumps(skjal), encoding="utf-8"
        )


class EkkertEintakProf(FrosidProf):
    def test_tom_mappa_gefur_none(self) -> None:
        self.assertIsNone(frosid_svar("hagstofan", "response.json", self.rot))

    def test_safn_sem_er_ekki_til_gefur_none(self) -> None:
        self.assertIsNone(frosid_svar("hagstofan", "response.json", self.rot))
        self.assertEqual(frosin_eintok("hagstofan", "*.json", self.rot), [])


class KortasnidProf(FrosidProf):
    """Sniðið hjá Hagstofunni: ``provenance.json`` með summur í korti."""

    def test_sannreynt_eintak_er_skilad(self) -> None:
        self.skra("response.json")
        self.arfur({"response.json": hashlib.sha256(INNIHALD).hexdigest()})
        svar = frosid_svar("hagstofan", "response.json", self.rot)
        self.assertIsNotNone(svar)
        self.assertEqual(svar.baeti, INNIHALD)
        self.assertTrue(svar.ur_safni)
        self.assertEqual(svar.provenance["methods"], ["GET", "POST"])

    def test_ostemmandi_summa_stodvar_keyrsluna(self) -> None:
        """Hrágagn sem hefur breyst er ekki notað — og ekki þaggað (regla 6)."""
        self.skra("response.json")
        self.arfur({"response.json": ONNUR_SUMMA})
        with self.assertRaises(FrosidVilla) as gripid:
            frosid_svar("hagstofan", "response.json", self.rot)
        self.assertIn("response.json", str(gripid.exception))
        self.assertIn("SHA256", str(gripid.exception))


class FylgiskraProf(FrosidProf):
    """Sniðið hjá mbl: lýsigagnaskrá með sama stofni og MD5-summu."""

    def test_md5_eintak_er_sannreynt_og_skilad(self) -> None:
        self.skra("mbl-20260916T120851Z.html", thjonusta="mbl")
        self.fylgiskra(
            "mbl-20260916T120851Z",
            {"source_url": "https://www.mbl.is/frettir/", "md5": hashlib.md5(INNIHALD).hexdigest()},
        )
        svar = frosid_svar("mbl", "mbl-*.html", self.rot)
        self.assertIsNotNone(svar)
        self.assertEqual(svar.baeti, INNIHALD)
        self.assertEqual(svar.provenance["source_url"], "https://www.mbl.is/frettir/")

    def test_ostemmandi_md5_stodvar_keyrsluna(self) -> None:
        self.skra("mbl-20260916T120851Z.html", thjonusta="mbl")
        self.fylgiskra("mbl-20260916T120851Z", {"md5": "0" * 32})
        with self.assertRaises(FrosidVilla) as gripid:
            frosid_svar("mbl", "mbl-*.html", self.rot)
        self.assertIn("MD5", str(gripid.exception))


class OsannreynanlegtProf(FrosidProf):
    """Eintak án skráðrar summu er ekki notað. Þögul notkun væri verri en stopp."""

    def test_engin_summa_stodvar_keyrsluna(self) -> None:
        self.skra("response.json")
        with self.assertRaises(FrosidVilla) as gripid:
            frosid_svar("hagstofan", "response.json", self.rot)
        bod = str(gripid.exception)
        self.assertIn("engin skráð summa", bod)
        self.assertIn("regla 6", bod)

    def test_provenance_an_summu_fyrir_skrana(self) -> None:
        """Summa fyrir aðra skrá í möppunni gildir ekki fyrir þessa."""
        self.skra("response.json")
        self.arfur({"metadata.json": hashlib.sha256(b"annad").hexdigest()})
        with self.assertRaises(FrosidVilla):
            frosid_svar("hagstofan", "response.json", self.rot)

    def test_onyt_provenance_er_ekki_thoggud(self) -> None:
        """Ónýtt JSON er skráð í logg og eintakið er ekki notað."""
        self.skra("response.json")
        (self.mappa() / "provenance.json").write_text("{ekki json", encoding="utf-8")
        with self.assertLogs("sofnun.frosid", level="WARNING") as logg:
            with self.assertRaises(FrosidVilla):
                frosid_svar("hagstofan", "response.json", self.rot)
        self.assertIn("provenance.json", "\n".join(logg.output))


class TviraettEintakProf(FrosidProf):
    """Tvö eintök í sömu möppu gera óljóst hvoru tölurnar tilheyra."""

    def test_tvo_eintok_stodva_keyrsluna(self) -> None:
        self.skra("mbl-20260916T120851Z.html", thjonusta="mbl")
        self.skra("mbl-20260917T120851Z.html", thjonusta="mbl")
        with self.assertRaises(FrosidVilla) as gripid:
            frosid_svar("mbl", "mbl-*.html", self.rot)
        bod = str(gripid.exception)
        self.assertIn("2 eintök", bod)
        self.assertIn("mbl-20260916T120851Z.html", bod)
        self.assertIn("mbl-20260917T120851Z.html", bod)


if __name__ == "__main__":
    unittest.main()
