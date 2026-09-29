"""Próf fyrir beiðnalýsingu og stillingar söfnunarinnar (regla 4).

* **Beiðnir:** samhæfi við frosna provenance-sniðið og hula á leyndarmálum.
* **Stillingar:** forgangur umhverfis fram yfir ``.env``, lestur hennar og
  lekavörn — lykill má hvergi birtast í villuboðum.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun.beidni import Beidni, HULID, fingrafar, full_slod, lysing  # noqa: E402
from sofnun import stillingar  # noqa: E402
from sofnun.stillingar import (  # noqa: E402
    StillingaVilla,
    krefjast,
    lesa_env_skra,
    tala,
    texti,
)


# --- Beiðnir -------------------------------------------------------------------

LYKILL = "ENGINN-RAUNVERULEGUR-LYKILL-123"

# Reitir úr data/raw/vedur-quakes/provenance.json eins og skráin var fryst í
# upprunaverkefninu. Þeir eru hér til að sanna að nýja lagið skrifi SAMA snið og
# þekki beiðnina sem þegar hefur verið gerð (regla 4).
FROSNIR_BREYTUR = {
    "start_time": "2023-11-01T00:00:00+00:00",
    "end_time": "2024-01-01T00:00:00+00:00",
    "depth_min": 0,
    "depth_max": 50,
    "size_min": 3,
    "size_max": 7,
    "polygon": "POLYGON((-23 64.1,-23 63.7,-21.5 63.7,-21.5 64.1,-23 64.1))",
    "type": "earthquake",
    "evaluation_mode": "manual",
    "format": "json",
    "system": "sil",
}
FROSID = {
    "provider": "Veðurstofa Íslands",
    "endpoint": "https://api.vedur.is/quakes/events",
    "documentation": "https://api.vedur.is/quakes/openapi.json",
    "method": "GET",
    "parameters": FROSNIR_BREYTUR,
    "fetched_at_utc": "2026-09-10T11:46:23Z",
    "sha256": "a535359ea84346426d5ce7fccf4ce8e5158b712e4fc66378dae4b291f771fa9a",
    "response_bytes": 93233,
    "license": "CC BY 4.0",
}


def skjalftabeidni(**breytingar) -> Beidni:
    """Beiðnin sem frosna skráin lýsir."""
    rok = {
        "thjonusta": "vedur-quakes",
        "veitandi": "Veðurstofa Íslands",
        "slod": "https://api.vedur.is/quakes/events",
        "heiti": "events",
        "breytur": FROSNIR_BREYTUR,
        "skjolun": "https://api.vedur.is/quakes/openapi.json",
    }
    return Beidni(**{**rok, **breytingar})


class FingrafarProf(unittest.TestCase):
    def test_thekkir_frosnu_skrana(self) -> None:
        """Beiðni sem þegar er til í data/raw/ á ekki að vera send aftur."""
        self.assertEqual(fingrafar(lysing(skjalftabeidni())), fingrafar(FROSID))

    def test_breytt_faeribreyta_er_onnur_beidni(self) -> None:
        onnur = skjalftabeidni(breytur={**FROSNIR_BREYTUR, "size_min": 4})
        self.assertNotEqual(fingrafar(lysing(onnur)), fingrafar(FROSID))

    def test_tala_og_texti_eru_sama_beidnin(self) -> None:
        """``3`` og ``"3"`` verða eins í slóðinni og mega ekki sækja gögnin tvisvar."""
        sem_texti = {nafn: str(gildi) for nafn, gildi in FROSNIR_BREYTUR.items()}
        self.assertEqual(
            fingrafar(lysing(skjalftabeidni(breytur=sem_texti))), fingrafar(FROSID)
        )

    def test_gagnastofn_telur_med(self) -> None:
        """Hagstofan sækir með POST: sami endapunktur, ólíkar fyrirspurnir."""
        grunnur = Beidni(thjonusta="hagstofan", veitandi="Hagstofa Íslands",
                         slod="https://px.hagstofa.is/api", adferd="POST")
        fyrri = fingrafar(lysing(Beidni(**{**vars(grunnur), "gagnastofn": b'{"a":1}'})))
        seinni = fingrafar(lysing(Beidni(**{**vars(grunnur), "gagnastofn": b'{"a":2}'})))
        self.assertNotEqual(fyrri, seinni)

    def test_ahrif_hausa_engin(self) -> None:
        """Hausar lýsa ekki því hvaða gögn voru sótt og mega ekki ráða fingrafari."""
        med_haus = skjalftabeidni(hausar={"Accept": "application/json"})
        self.assertEqual(fingrafar(lysing(med_haus)), fingrafar(FROSID))


class HuluProf(unittest.TestCase):
    def test_lykill_i_haus_kemst_ekki_i_provenance(self) -> None:
        skjal = lysing(skjalftabeidni(hausar={"Authorization": f"Bearer {LYKILL}"}))
        self.assertEqual(skjal["request_headers"]["Authorization"], HULID)
        self.assertNotIn(LYKILL, str(skjal))

    def test_lykill_i_faeribreytu_kemst_hvorki_i_breytur_ne_slod(self) -> None:
        skjal = lysing(skjalftabeidni(breytur={"api_key": LYKILL, "format": "json"}))
        self.assertEqual(skjal["parameters"]["api_key"], HULID)
        self.assertNotIn(LYKILL, skjal["request_url"])
        self.assertNotIn(LYKILL, str(skjal))

    def test_venjuleg_gildi_haldast(self) -> None:
        skjal = lysing(skjalftabeidni())
        self.assertEqual(skjal["parameters"]["system"], "sil")


class SlodaProf(unittest.TestCase):
    def test_listi_verdur_ad_endurteknu_nafni(self) -> None:
        self.assertEqual(
            full_slod("https://api.vedur.is/weather/stations", {"station_id": [1, 2]}),
            "https://api.vedur.is/weather/stations?station_id=1&station_id=2",
        )

    def test_engar_breytur_gefa_hreina_slod(self) -> None:
        self.assertEqual(full_slod("https://www.mbl.is/", {}), "https://www.mbl.is/")



# --- Stillingar ----------------------------------------------------------------

class EnvSkraProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.slod = Path(self._tmp.name) / ".env"
        lesa_env_skra.cache_clear()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        lesa_env_skra.cache_clear()

    def test_les_gildi_og_hunsar_athugasemdir(self) -> None:
        self.slod.write_text(
            "# athugasemd\n\nNOTANDA_AUDKENNI=nafn@skoli.is\nBID_MILLI_KALLA=2.5\n",
            encoding="utf-8",
        )
        self.assertEqual(
            lesa_env_skra(self.slod),
            {"NOTANDA_AUDKENNI": "nafn@skoli.is", "BID_MILLI_KALLA": "2.5"},
        )

    def test_gaesalappir_eru_fjarlaegdar(self) -> None:
        self.slod.write_text('NOTANDA_AUDKENNI="nafn@skoli.is"\n', encoding="utf-8")
        self.assertEqual(lesa_env_skra(self.slod)["NOTANDA_AUDKENNI"], "nafn@skoli.is")

    def test_engin_skra_er_ekki_villa(self) -> None:
        self.assertEqual(lesa_env_skra(self.slod), {})

    def test_onyt_lina_nefnir_linunumer_en_ekki_innihald(self) -> None:
        """Línan gæti geymt lykil og má því ekki rata í villuboð (regla 4)."""
        self.slod.write_text(f"GILT=1\n{LYKILL}\n", encoding="utf-8")
        with self.assertRaises(StillingaVilla) as samhengi:
            lesa_env_skra(self.slod)
        self.assertIn("Lína 2", str(samhengi.exception))
        self.assertNotIn(LYKILL, str(samhengi.exception))


class ForgangurProf(unittest.TestCase):
    def setUp(self) -> None:
        lesa_env_skra.cache_clear()

    def test_umhverfi_gengur_fyrir_env_skra(self) -> None:
        ur_skra = {"PROF_BREYTA": "ur-skra"}
        with mock.patch.object(stillingar, "lesa_env_skra", lambda: ur_skra):
            with mock.patch.dict(os.environ, {"PROF_BREYTA": "ur-umhverfi"}):
                self.assertEqual(texti("PROF_BREYTA"), "ur-umhverfi")
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(texti("PROF_BREYTA"), "ur-skra")

    def test_sjalfgefid_thegar_ekkert_finnst(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(texti("PROF_BREYTA_SEM_ER_EKKI_TIL", "sjalfgefid"), "sjalfgefid")

    def test_tomt_gildi_telst_vanta(self) -> None:
        with mock.patch.dict(os.environ, {"PROF_BREYTA": "   "}):
            self.assertIsNone(texti("PROF_BREYTA"))


class KrafaProf(unittest.TestCase):
    def setUp(self) -> None:
        lesa_env_skra.cache_clear()

    def test_villa_nefnir_breytuna_en_ekki_gildid(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(StillingaVilla) as samhengi:
                krefjast("API_LYKILL", "hún geymir lykilinn")
            skilabod = str(samhengi.exception)
        self.assertIn("API_LYKILL", skilabod)
        self.assertIn(".env", skilabod)

    def test_tala_fellur_an_thess_ad_birta_gildid(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": LYKILL}):
            with self.assertRaises(StillingaVilla) as samhengi:
                tala("BID_MILLI_KALLA", 1.0)
        self.assertNotIn(LYKILL, str(samhengi.exception))

    def test_tala_les_gildi(self) -> None:
        with mock.patch.dict(os.environ, {"BID_MILLI_KALLA": "2.5"}):
            self.assertEqual(tala("BID_MILLI_KALLA", 1.0), 2.5)


if __name__ == "__main__":
    unittest.main()
