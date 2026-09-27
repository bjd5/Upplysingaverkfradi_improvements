"""Próf fyrir sannreyningu jarðskjálftagagnanna (issue #6).

Kjarninn: frávik stöðva keyrsluna. Færsla sem stenst ekki afmörkun beiðninnar
má aldrei hverfa hljóðlega úr úrtakinu (regla 6), og afleiddu lyklarnir tveir
verða að vera dregnir út með sömu regex-mynstrum og í upprunaverkefninu.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from vinnsla.jardskjalftar import (  # noqa: E402
    AUDKENNISMYNSTUR,
    DAGSMYNSTUR,
    lesa_skjalfta,
    talning_eftir_degi,
)
from vinnsla.jardskjalftar_afmorkun import (  # noqa: E402
    SkjalftaVilla,
    dagar,
    lesa_afmorkun,
    reitur_ur_marghyrningi,
)

HRAGOGN = ROT / "data" / "raw" / "vedur-quakes" / "events.json"
PROVENANCE = ROT / "data" / "raw" / "vedur-quakes" / "provenance.json"

VAENTIR_ATBURDIR = 334
VAENTIR_DAGAR = 61

GILD_FAERSLA = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-22.52034, 63.86282]},
    "properties": {
        "time": "2023-11-01T00:56:41.645Z",
        "type": "earthquake",
        "depth": 5.126,
        "event_id": "SIL1235710",
        "magnitude": 3.74,
        "magnitude_type": "Mlw",
        "evaluation_mode": "manual",
    },
}


class AfmorkunProf(unittest.TestCase):
    """Afmörkunin er LESIN úr provenance.json, ekki slegin inn."""

    def setUp(self) -> None:
        self.afmorkun = lesa_afmorkun(PROVENANCE)

    def test_timabilid_telur_61_utc_dag(self) -> None:
        listi = dagar(self.afmorkun)

        self.assertEqual(len(listi), VAENTIR_DAGAR)
        self.assertEqual(listi[0], "2023-11-01")
        self.assertEqual(listi[-1], "2023-12-31", "endirinn er undanskilinn")
        self.assertEqual(len(set(listi)), len(listi), "enginn dagur tvítekinn")

    def test_siurnar_koma_ur_provenance(self) -> None:
        self.assertEqual((self.afmorkun.staerd_min, self.afmorkun.staerd_max), (3.0, 7.0))
        self.assertEqual((self.afmorkun.dypt_min, self.afmorkun.dypt_max), (0.0, 50.0))
        self.assertEqual(self.afmorkun.atburdategund, "earthquake")
        self.assertEqual(self.afmorkun.matsadferd, "manual")
        self.assertEqual(self.afmorkun.kerfi, "sil")
        self.assertEqual(self.afmorkun.leyfi, "CC BY 4.0")

    def test_marghyrningurinn_verdur_ad_reit(self) -> None:
        reitur = reitur_ur_marghyrningi("POLYGON((-23 64.1,-23 63.7,-21.5 63.7,-21.5 64.1,-23 64.1))")

        self.assertEqual(reitur, (-23.0, -21.5, 63.7, 64.1))

    def test_ekki_rethyrndur_marghyrningur_stodvar(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            reitur_ur_marghyrningi("POLYGON((-23 64.1,-22 63.9,-21.5 63.7,-23 64.1))")

    def test_ologrun_provenance_stodvar(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "provenance.json"
            skjal = json.loads(PROVENANCE.read_text(encoding="utf-8"))
            del skjal["parameters"]["size_min"]
            slod.write_text(json.dumps(skjal), encoding="utf-8")

            with self.assertRaises(SkjalftaVilla) as samhengi:
                lesa_afmorkun(slod)
        self.assertIn("size_min", str(samhengi.exception))

    def test_timabil_sem_byrjar_inni_i_degi_stodvar(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "provenance.json"
            skjal = json.loads(PROVENANCE.read_text(encoding="utf-8"))
            skjal["parameters"]["start_time"] = "2023-11-01T06:00:00+00:00"
            slod.write_text(json.dumps(skjal), encoding="utf-8")

            with self.assertRaises(SkjalftaVilla):
                lesa_afmorkun(slod)


class RegexProf(unittest.TestCase):
    """Sömu tvö mynstur og í upprunaverkefninu, bæði með fullmatch."""

    def test_dagsmynstur_dregur_ut_utc_dag(self) -> None:
        samsvorun = DAGSMYNSTUR.fullmatch("2023-11-02T20:35:42.458Z")

        self.assertIsNotNone(samsvorun)
        assert samsvorun is not None
        self.assertEqual(samsvorun.group("utc_day"), "2023-11-02")

    def test_dagsmynstur_hafnar_odru_snidi(self) -> None:
        for stimpill in (
            "2023-11-02 20:35:42Z",
            "2023-11-02T20:35:42+00:00",
            "2023-11-02T20:35:42.458Z ",
        ):
            with self.subTest(stimpill=stimpill):
                self.assertIsNone(DAGSMYNSTUR.fullmatch(stimpill))

    def test_audkennismynstur_klyfur_sil(self) -> None:
        samsvorun = AUDKENNISMYNSTUR.fullmatch("SIL1235710")

        self.assertIsNotNone(samsvorun)
        assert samsvorun is not None
        self.assertEqual(samsvorun.group("source_system"), "SIL")
        self.assertEqual(samsvorun.group("event_number"), "1235710")

    def test_audkennismynstur_hafnar_odru(self) -> None:
        for audkenni in ("SIL0123", "sil1235710", "SIL", "SIL1235710x", "IMO1235710"):
            with self.subTest(audkenni=audkenni):
                self.assertIsNone(AUDKENNISMYNSTUR.fullmatch(audkenni))


class FrosnuGognProf(unittest.TestCase):
    """Frosna svarið sjálft — 334 atburðir sem allir standast beiðnina."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.afmorkun = lesa_afmorkun(PROVENANCE)
        cls.skjalftar = lesa_skjalfta(HRAGOGN, cls.afmorkun)

    def test_allir_atburdir_lesast(self) -> None:
        self.assertEqual(len(self.skjalftar), VAENTIR_ATBURDIR)

    def test_audkenni_eru_einkvaem(self) -> None:
        audkenni = [s.event_id for s in self.skjalftar]

        self.assertEqual(len(set(audkenni)), VAENTIR_ATBURDIR)

    def test_afleiddu_lyklarnir_stemma_vid_frumgildin(self) -> None:
        for skjalfti in self.skjalftar:
            with self.subTest(event_id=skjalfti.event_id):
                self.assertEqual(
                    skjalfti.source_system + skjalfti.event_number, skjalfti.event_id
                )
                self.assertTrue(skjalfti.occurred_at.startswith(skjalfti.utc_day + "T"))

    def test_kvardi_er_alltaf_skradur(self) -> None:
        for skjalfti in self.skjalftar:
            with self.subTest(event_id=skjalfti.event_id):
                self.assertTrue(skjalfti.magnitude_type.strip())

    def test_talning_telur_thogla_daga_med(self) -> None:
        talning = talning_eftir_degi(self.skjalftar, dagar(self.afmorkun))

        self.assertEqual(len(talning), VAENTIR_DAGAR)
        self.assertEqual(sum(talning.values()), VAENTIR_ATBURDIR)
        self.assertEqual(sum(1 for fjoldi in talning.values() if fjoldi == 0), 43)
        self.assertEqual(max(talning.values()), 187)
        self.assertEqual(talning["2023-11-10"], 187)


class FravikStodvaProf(unittest.TestCase):
    """Hvert frávik á að falla með SkjalftaVillu, ekki sleppa þegjandi."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        self.afmorkun = lesa_afmorkun(PROVENANCE)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _skrifa(self, *faerslur: dict) -> Path:
        slod = self.mappa / "events.json"
        slod.write_text(
            json.dumps({"type": "FeatureCollection", "features": list(faerslur)}),
            encoding="utf-8",
        )
        return slod

    def _breytt(self, **eiginleikar: object) -> dict:
        faersla = copy.deepcopy(GILD_FAERSLA)
        faersla["properties"].update(eiginleikar)
        return faersla

    def _stodvast(self, *faerslur: dict) -> str:
        slod = self._skrifa(*faerslur)
        with self.assertRaises(SkjalftaVilla) as samhengi:
            lesa_skjalfta(slod, self.afmorkun)
        return str(samhengi.exception)

    def test_gild_faersla_kemst_i_gegn(self) -> None:
        skjalftar = lesa_skjalfta(self._skrifa(copy.deepcopy(GILD_FAERSLA)), self.afmorkun)

        self.assertEqual(len(skjalftar), 1)
        self.assertEqual(skjalftar[0].event_id, "SIL1235710")
        self.assertEqual(skjalftar[0].utc_day, "2023-11-01")

    def test_of_stor_skjalfti_stodvar(self) -> None:
        self.assertIn("magnitude", self._stodvast(self._breytt(magnitude=7.4)))

    def test_of_djupur_skjalfti_stodvar(self) -> None:
        self.assertIn("depth", self._stodvast(self._breytt(depth=64.0)))

    def test_atburdur_utan_timabils_stodvar(self) -> None:
        villa = self._stodvast(self._breytt(time="2024-01-01T00:00:00.000Z"))

        self.assertIn("utan tímabils", villa)

    def test_ogildur_timastimpill_stodvar(self) -> None:
        self.assertIn("2023-11-01", self._stodvast(self._breytt(time="2023-11-01 00:56:41Z")))

    def test_dagur_sem_er_ekki_til_stodvar(self) -> None:
        self._stodvast(self._breytt(time="2023-11-31T00:56:41.645Z"))

    def test_sjalfvirkt_mat_stodvar(self) -> None:
        self.assertIn("evaluation_mode", self._stodvast(self._breytt(evaluation_mode="automatic")))

    def test_onnur_atburdategund_stodvar(self) -> None:
        self.assertIn("type", self._stodvast(self._breytt(type="explosion")))

    def test_tomur_kvardi_stodvar(self) -> None:
        self.assertIn("magnitude_type", self._stodvast(self._breytt(magnitude_type="  ")))

    def test_kvardi_sem_vantar_stodvar(self) -> None:
        faersla = copy.deepcopy(GILD_FAERSLA)
        del faersla["properties"]["magnitude_type"]

        self.assertIn("magnitude_type", self._stodvast(faersla))

    def test_rangt_audkenni_stodvar(self) -> None:
        self.assertIn("SIL", self._stodvast(self._breytt(event_id="IMO1235710")))

    def test_tvitekid_audkenni_stodvar(self) -> None:
        villa = self._stodvast(
            copy.deepcopy(GILD_FAERSLA), self._breytt(time="2023-11-02T01:00:00.000Z")
        )

        self.assertIn("einkvæm", villa)

    def test_hnit_utan_reits_stodvar(self) -> None:
        faersla = copy.deepcopy(GILD_FAERSLA)
        faersla["geometry"]["coordinates"] = [-18.0, 65.5]

        self.assertIn("utan marka", self._stodvast(faersla))

    def test_onnur_rumfraedi_en_punktur_stodvar(self) -> None:
        faersla = copy.deepcopy(GILD_FAERSLA)
        faersla["geometry"] = {"type": "LineString", "coordinates": [-22.5, 63.8]}

        self.assertIn("Point", self._stodvast(faersla))

    def test_oskradur_eiginleiki_stodvar(self) -> None:
        """Nýr lykill þýðir að svarið er ekki það snið sem sannreyningin þekkir."""
        self.assertIn("Óvæntir", self._stodvast(self._breytt(nytt_svid=1)))

    def test_tala_sem_er_texti_stodvar(self) -> None:
        self.assertIn("tölu", self._stodvast(self._breytt(magnitude="3.74")))

    def test_skra_sem_er_ekki_featurecollection_stodvar(self) -> None:
        slod = self.mappa / "events.json"
        slod.write_text(json.dumps({"type": "Feature"}), encoding="utf-8")

        with self.assertRaises(SkjalftaVilla) as samhengi:
            lesa_skjalfta(slod, self.afmorkun)
        self.assertIn("FeatureCollection", str(samhengi.exception))

    def test_skra_sem_vantar_stodvar(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            lesa_skjalfta(self.mappa / "er-ekki-til.json", self.afmorkun)


if __name__ == "__main__":
    unittest.main()
