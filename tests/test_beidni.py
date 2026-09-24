"""Próf fyrir beiðnalýsingu: samhæfi við frosna sniðið og hula á leyndarmálum."""

from __future__ import annotations

import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from sofnun.beidni import Beidni, HULID, fingrafar, full_slod, lysing  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
