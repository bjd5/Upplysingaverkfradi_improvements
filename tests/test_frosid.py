"""Próf fyrir ``sofnun.frosid`` — frosin eintök á eldri sniðum.

Öll gögn eru skrifuð í tímabundna möppu (``tempfile``); ``data/raw/`` í repo-inu
er aldrei skrifuð í. Engin netsamskipti: einingin talar ekki við net.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun.frosid import FrosidVilla, frosid_svar, frosin_eintok  # noqa: E402

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
