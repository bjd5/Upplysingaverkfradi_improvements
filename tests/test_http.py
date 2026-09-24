"""Próf fyrir HTTP-lagið. Engin netsamskipti: opnari og bið eru gefin inn."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun import http, stillingar  # noqa: E402
from sofnun.http import HttpVilla, notandaaudkenni, saekja  # noqa: E402
from sofnun.stillingar import StillingaVilla  # noqa: E402
from test_beidni import skjalftabeidni  # noqa: E402

TENGILIDUR = "nafn@skoli.is"
LYKILL = "ENGINN-RAUNVERULEGUR-LYKILL-123"
SVAR = b'{"type": "FeatureCollection", "features": []}'


class Gervisvar:
    """Svar sem hegðar sér eins og hlutur frá ``urlopen`` í ``with``-setningu."""

    def __init__(self, baeti: bytes = SVAR, stada: int = 200,
                 efnistegund: str | None = "application/json") -> None:
        self.baeti = baeti
        self.status = stada
        self.headers = {"Content-Type": efnistegund}

    def read(self, hamark: int | None = None) -> bytes:
        return self.baeti if hamark is None else self.baeti[:hamark]

    def __enter__(self) -> Gervisvar:
        return self

    def __exit__(self, *_) -> bool:
        return False


class Gervitengill:
    """Skráir hverja beiðni og skilar (eða kastar) því sem raðað var upp."""

    def __init__(self, *svor: object) -> None:
        self.svor = list(svor)
        self.beidnir: list[object] = []

    def __call__(self, beidni: object, timeout: float | None = None) -> object:
        self.beidnir.append(beidni)
        naest = self.svor.pop(0) if self.svor else Gervisvar()
        if isinstance(naest, Exception):
            raise naest
        return naest


def http_villa(kodi: int, hausar: dict | None = None) -> HTTPError:
    return HTTPError("https://api.vedur.is/quakes/events", kodi, "villa", hausar or {}, None)


class AudkennisProf(unittest.TestCase):
    def setUp(self) -> None:
        stillingar.lesa_env_skra.cache_clear()

    def test_audkenni_nefnir_verkefnid_og_tengilid(self) -> None:
        with mock.patch.dict(os.environ, {"NOTANDA_AUDKENNI": TENGILIDUR}):
            audkenni = notandaaudkenni()
        self.assertIn("Upplysingaverkfraedi", audkenni)
        self.assertIn(TENGILIDUR, audkenni)

    def test_tengilidur_er_ekki_hardkodadur(self) -> None:
        with mock.patch.dict(os.environ, {"NOTANDA_AUDKENNI": "GitHub: einhver"}):
            self.assertIn("GitHub: einhver", notandaaudkenni())

    def test_vantandi_tengilidur_stodvar_beidnina(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(stillingar, "lesa_env_skra", dict):
                with self.assertRaises(StillingaVilla):
                    notandaaudkenni()

    def test_styristafur_i_tengilid_er_hafnad(self) -> None:
        """Nýlína í haus er höfuðlínuinnspýting, ekki tengiliður."""
        with self.assertRaises(HttpVilla):
            notandaaudkenni("nafn@skoli.is\r\nX-Annad: gildi")


class SaekjaProf(unittest.TestCase):
    """Sameiginleg umgjörð: eigið data/raw/, engin bið og þekktur tengiliður."""

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

    def saekja(self, tengill: Gervitengill, **rok) -> object:
        return saekja(rok.pop("beidni", skjalftabeidni()), rot=self.rot,
                      opnari=tengill, sofa=self.svefn.append, **rok)

    def skrar_i_safni(self) -> list[str]:
        mappa = self.rot / "vedur-quakes"
        return sorted(skra.name for skra in mappa.iterdir()) if mappa.is_dir() else []


class VistunProf(SaekjaProf):
    def test_hragognin_fara_a_disk_obreytt(self) -> None:
        svar = self.saekja(Gervitengill(Gervisvar()))
        self.assertEqual(svar.baeti, SVAR)
        self.assertEqual(svar.slod_skrar.read_bytes(), SVAR)
        self.assertFalse(svar.ur_safni)

    def test_audkenni_fylgir_beidninni(self) -> None:
        tengill = Gervitengill(Gervisvar())
        self.saekja(tengill)
        haus = tengill.beidnir[0].get_header("User-agent")
        self.assertIn(TENGILIDUR, haus)

    def test_stodugildi_annad_en_200_vistar_ekkert(self) -> None:
        with self.assertRaises(HttpVilla):
            self.saekja(Gervitengill(Gervisvar(stada=204)))
        self.assertEqual(self.skrar_i_safni(), [])

    def test_tomt_svar_vistar_ekkert(self) -> None:
        with self.assertRaises(HttpVilla):
            self.saekja(Gervitengill(Gervisvar(baeti=b"")))
        self.assertEqual(self.skrar_i_safni(), [])

    def test_of_stort_svar_vistar_ekkert(self) -> None:
        with self.assertRaises(HttpVilla):
            self.saekja(Gervitengill(Gervisvar(baeti=b"x" * 50)), hamark_baeta=10)
        self.assertEqual(self.skrar_i_safni(), [])


class HradatakmorkunProf(SaekjaProf):
    def test_bid_milli_kalla_a_somu_thjonustu(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": "5"}):
            self.saekja(Gervitengill(Gervisvar()))
            self.saekja(Gervitengill(Gervisvar()), thvinga=True)
        self.assertEqual(len(self.svefn), 1)
        self.assertGreater(self.svefn[0], 4.0)

    def test_fyrsta_kall_bidur_ekki(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": "5"}):
            self.saekja(Gervitengill(Gervisvar()))
        self.assertEqual(self.svefn, [])

    def test_adrar_thjonustur_bida_ekki_hver_eftir_annarri(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": "5"}):
            self.saekja(Gervitengill(Gervisvar()))
            self.saekja(Gervitengill(Gervisvar()),
                        beidni=skjalftabeidni(thjonusta="hagstofan"))
        self.assertEqual(self.svefn, [])


class EndurtilraunaProf(SaekjaProf):
    def test_timabundin_villa_er_reynd_aftur(self) -> None:
        tengill = Gervitengill(http_villa(503), URLError("timeout"), Gervisvar())
        svar = self.saekja(tengill)
        self.assertEqual(svar.baeti, SVAR)
        self.assertEqual(len(tengill.beidnir), 3)

    def test_bidin_vex_milli_tilrauna(self) -> None:
        self.saekja(Gervitengill(http_villa(503), http_villa(503), Gervisvar()))
        self.assertEqual(self.svefn, [http.BID_GRUNNUR, http.BID_GRUNNUR * 2])

    def test_endurtilraunir_stodvast_a_thakinu(self) -> None:
        tengill = Gervitengill(*[URLError("niðri")] * (http.TILRAUNIR + 2))
        with self.assertRaises(HttpVilla) as samhengi:
            self.saekja(tengill)
        self.assertEqual(len(tengill.beidnir), http.TILRAUNIR)
        self.assertIn("Veðurstofa", str(samhengi.exception))
        self.assertEqual(self.skrar_i_safni(), [])

    def test_villa_sem_lagast_ekki_er_ekki_endurtekin(self) -> None:
        tengill = Gervitengill(http_villa(404), Gervisvar())
        with self.assertRaises(HttpVilla):
            self.saekja(tengill)
        self.assertEqual(len(tengill.beidnir), 1)
        self.assertEqual(self.svefn, [])

    def test_farid_er_eftir_retry_after(self) -> None:
        self.saekja(Gervitengill(http_villa(429, {"Retry-After": "7"}), Gervisvar()))
        self.assertEqual(self.svefn, [7.0])

    def test_retry_after_yfir_thaki_er_takmarkad(self) -> None:
        self.saekja(Gervitengill(http_villa(429, {"Retry-After": "99999"}), Gervisvar()))
        self.assertEqual(self.svefn, [http.BID_HAMARK])


class LeyndarmalaProf(SaekjaProf):
    """Lykill fer í beiðnina og hvergi annað (regla 4)."""

    def provenance_texti(self) -> str:
        mappa = self.rot / "vedur-quakes"
        return "".join(
            skra.read_text(encoding="utf-8")
            for skra in mappa.iterdir() if skra.name.endswith("provenance.json")
        )

    def test_lykill_i_haus_fer_i_beidnina_en_ekki_i_provenance(self) -> None:
        tengill = Gervitengill(Gervisvar())
        self.saekja(tengill, leynihausar={"Authorization": f"Bearer {LYKILL}"})
        self.assertIn(LYKILL, tengill.beidnir[0].get_header("Authorization"))
        self.assertNotIn(LYKILL, self.provenance_texti())

    def test_lykill_i_faeribreytu_fer_i_slodina_en_ekki_i_provenance(self) -> None:
        tengill = Gervitengill(Gervisvar())
        self.saekja(tengill, leynibreytur={"api_key": LYKILL})
        self.assertIn(LYKILL, tengill.beidnir[0].full_url)
        self.assertNotIn(LYKILL, self.provenance_texti())

    def test_lykill_kemst_ekki_i_villubod(self) -> None:
        with self.assertRaises(HttpVilla) as samhengi:
            self.saekja(Gervitengill(*[http_villa(500)] * http.TILRAUNIR),
                        leynibreytur={"api_key": LYKILL})
        self.assertNotIn(LYKILL, str(samhengi.exception))

    def test_lykill_kemst_ekki_i_logg(self) -> None:
        with self.assertLogs("sofnun.http", level="INFO") as logg:
            self.saekja(Gervitengill(Gervisvar()), leynibreytur={"api_key": LYKILL})
        self.assertNotIn(LYKILL, "\n".join(logg.output))


class SkyndiminnisProf(SaekjaProf):
    """Sömu gögn eru ekki sótt tvisvar að óþörfu (regla 4)."""

    def test_onnur_sokn_sendir_ekkert_kall(self) -> None:
        self.saekja(Gervitengill(Gervisvar()))
        tengill = Gervitengill(Gervisvar(baeti=b"nyrra svar"))
        svar = self.saekja(tengill)
        self.assertEqual(tengill.beidnir, [])
        self.assertTrue(svar.ur_safni)
        self.assertEqual(svar.baeti, SVAR)

    def test_thvingud_sokn_saekir_samt(self) -> None:
        self.saekja(Gervitengill(Gervisvar()))
        tengill = Gervitengill(Gervisvar(baeti=b'{"nytt": true}'))
        svar = self.saekja(tengill, thvinga=True)
        self.assertEqual(len(tengill.beidnir), 1)
        self.assertFalse(svar.ur_safni)
        self.assertEqual(len(self.skrar_i_safni()), 4)

    def test_onnur_beidni_er_sott(self) -> None:
        self.saekja(Gervitengill(Gervisvar()))
        onnur = skjalftabeidni(breytur={"size_min": 4})
        tengill = Gervitengill(Gervisvar())
        self.saekja(tengill, beidni=onnur)
        self.assertEqual(len(tengill.beidnir), 1)

    def test_provenance_ur_safni_stemmir_vid_gognin(self) -> None:
        fyrsta = self.saekja(Gervitengill(Gervisvar()))
        endurnotad = self.saekja(Gervitengill())
        self.assertEqual(endurnotad.provenance["sha256"], fyrsta.provenance["sha256"])
        skjal = json.loads(
            fyrsta.slod_skrar.with_suffix("").with_suffix(".provenance.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(skjal, endurnotad.provenance)


if __name__ == "__main__":
    unittest.main()
