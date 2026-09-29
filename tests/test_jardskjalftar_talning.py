"""Próf fyrir talningu, samantekt og úttak skjálftaúrtaksins (issue #14, pakki P2.3).

Prófin eru **netlaus**: þau lesa frosna svarið í ``data/raw/vedur-quakes/``
(regla 4) og gervigögn í minni, og skrifa aðeins í tímabundnar möppur —
hvorki ``data/processed/``, ``data/raw/`` né ``web/gogn/`` er hreyft (regla 10).
Samanburðurinn við tölur gömlu síðunnar er í ``test_jardskjalftar_vidmid.py``.

Hegðunin er prófuð **þar sem hún á að bresta**, ekki bara þar sem hún á að
halda (lærdómurinn af issue #47). Í úttakinu gæti þrennt annars brostið
hljóðlaust:

* **Dálkarnir stemma við gagnaklasana.** CSV-skrá sem missir dálk lítur rétt út
  en er annað gagnasafn.
* **Úttakið er hrein afleiða.** Tvær keyrslur á sömu gögnum gefa sömu bæti.
* **Vinnslan skrifar ekki í web/gogn/.** Flæðið í kafla 0 er einstefna.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from vinnsla.jardskjalftar import Skjalfti, lesa_skjalfta  # noqa: E402
from vinnsla.jardskjalftar_afmorkun import SkjalftaVilla, lesa_afmorkun  # noqa: E402
from vinnsla.jardskjalftar_talning import (  # noqa: E402
    DagsTalning,
    dagar_an_atburda,
    dagleg_talning,
    draga_saman,
    dreifing,
    manadartalning,
    staerdir_eftir_kvarda,
)
from vinnsla.jardskjalftar_uttak import (  # noqa: E402
    ATBURDASKRA,
    DAGASKRA,
    SAMANTEKTARSKRA,
    vinna_skjalfta,
)


# --- Talning og samantekt ------------------------------------------------------

VAENTIR_ATBURDIR = 334
VAENTIR_DAGAR = 61


def gervi(
    event_id: str = "SIL1",
    dagur: str = "2023-11-01",
    staerd: float = 3.5,
    kvardi: str = "Mlw",
    dypt: float = 5.0,
) -> Skjalfti:
    """Býr til einn atburð í minni — engin skrá og ekkert netkall."""
    return Skjalfti(
        event_id=event_id,
        source_system="SIL",
        event_number=event_id.removeprefix("SIL"),
        occurred_at=f"{dagur}T00:00:00.000Z",
        utc_day=dagur,
        magnitude=staerd,
        magnitude_type=kvardi,
        depth_km=dypt,
        latitude=63.9,
        longitude=-22.5,
        event_type="earthquake",
        evaluation_mode="manual",
    )


class DaglegTalning(unittest.TestCase):
    """Hver UTC-dagur tímabilsins fær línu, líka dagar án atburðar."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.afmorkun = lesa_afmorkun()
        cls.skjalftar = lesa_skjalfta(None, cls.afmorkun)
        cls.dagatalning = dagleg_talning(cls.skjalftar, cls.afmorkun)

    def test_allir_dagar_tokna_med(self) -> None:
        self.assertEqual(len(self.dagatalning), VAENTIR_DAGAR)

    def test_talningin_telur_alla_atburdi(self) -> None:
        self.assertEqual(
            sum(dagur.event_count for dagur in self.dagatalning), VAENTIR_ATBURDIR
        )

    def test_dagarnir_eru_i_timarod_og_einkvaemir(self) -> None:
        lyklar = [dagur.utc_day for dagur in self.dagatalning]
        self.assertEqual(lyklar, sorted(lyklar))
        self.assertEqual(len(set(lyklar)), len(lyklar))

    def test_dagar_an_atburda_eru_taldir_en_ekki_slepptir(self) -> None:
        nullar = [d for d in self.dagatalning if d.event_count == 0]
        self.assertTrue(nullar, "Úrtakið hefur daga án atburðar; þeir verða að hafa línu.")
        self.assertEqual(dagar_an_atburda(self.dagatalning), len(nullar))

    def test_atburdur_utan_timabils_stodvar_talninguna(self) -> None:
        # Hér á talningin að bresta: dagur utan beiðninnar á sér enga línu.
        with self.assertRaises(SkjalftaVilla):
            dagleg_talning([gervi(dagur="2024-06-01")], self.afmorkun)


class ManadarTalning(unittest.TestCase):
    """Mánaðarsamtölur eru dregnar úr dagatalningunni, ekki reiknaðar upp á nýtt."""

    def test_telur_daga_og_atburdi_hvers_manadar(self) -> None:
        dagatalning = [
            DagsTalning("2023-11-29", 2),
            DagsTalning("2023-11-30", 0),
            DagsTalning("2023-12-01", 5),
        ]
        manudir = manadartalning(dagatalning)
        self.assertEqual([m.month for m in manudir], ["2023-11", "2023-12"])
        self.assertEqual([m.day_count for m in manudir], [2, 1])
        self.assertEqual([m.event_count for m in manudir], [2, 5])

    def test_manudur_an_atburda_fellur_ekki_ut(self) -> None:
        manudir = manadartalning([DagsTalning("2023-12-01", 0)])
        self.assertEqual([(m.month, m.event_count) for m in manudir], [("2023-12", 0)])

    def test_rangt_dagsnid_stodvar_talninguna(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            manadartalning([DagsTalning("2023/12/01", 1)])


class Dreifingar(unittest.TestCase):
    """Lýsandi tölfræði — og tómt úrtak sem á að falla, ekki skila núlli."""

    def test_reiknar_fjolda_bil_og_midgildi(self) -> None:
        nidurstada = dreifing([3.0, 1.0, 2.0])
        self.assertEqual(nidurstada.fjoldi, 3)
        self.assertEqual(nidurstada.lagmark, 1.0)
        self.assertEqual(nidurstada.hamark, 3.0)
        self.assertEqual(nidurstada.midgildi, 2.0)

    def test_tom_rod_er_villa_ekki_null(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            dreifing([])

    def test_kvardar_eru_aldrei_lagdir_saman(self) -> None:
        skjalftar = [
            gervi("SIL1", staerd=3.0, kvardi="Mlw"),
            gervi("SIL2", staerd=5.0, kvardi="Mlw"),
            gervi("SIL3", staerd=4.0, kvardi="Mw"),
        ]
        eftir_kvarda = {k.magnitude_type: k.dreifing for k in staerdir_eftir_kvarda(skjalftar)}
        self.assertEqual(sorted(eftir_kvarda), ["Mlw", "Mw"])
        self.assertEqual(eftir_kvarda["Mlw"].midgildi, 4.0)
        self.assertEqual(eftir_kvarda["Mw"].fjoldi, 1)


class Samantekt(unittest.TestCase):
    """Samantektin krefst þess að talningin og atburðirnir séu sama úrtakið."""

    def test_dregur_saman_frosna_urtakid(self) -> None:
        afmorkun = lesa_afmorkun()
        skjalftar = lesa_skjalfta(None, afmorkun)
        samantekt = draga_saman(skjalftar, dagleg_talning(skjalftar, afmorkun))

        self.assertEqual(samantekt.atburdir, VAENTIR_ATBURDIR)
        self.assertEqual(samantekt.dagar, VAENTIR_DAGAR)
        self.assertEqual(samantekt.fyrsti_dagur, "2023-11-01")
        self.assertEqual(samantekt.sidasti_dagur, "2023-12-31")
        self.assertEqual(samantekt.dypt_km.fjoldi, VAENTIR_ATBURDIR)
        self.assertEqual(
            sum(m.event_count for m in samantekt.manudir), VAENTIR_ATBURDIR
        )
        self.assertEqual(sum(m.day_count for m in samantekt.manudir), VAENTIR_DAGAR)

    def test_talning_ur_odru_urtaki_stodvar_samantektina(self) -> None:
        # Hér á samantektin að bresta: talningin og atburðirnir stemma ekki.
        with self.assertRaises(SkjalftaVilla):
            draga_saman([gervi()], [DagsTalning("2023-11-01", 7)])

    def test_tom_dagatalning_er_villa(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            draga_saman([], [])



# --- Úttak ---------------------------------------------------------------------

# Lyklar samantektarinnar. Enginn þeirra er tímastimpill keyrslunnar — og það
# er atriðið: listi sem er borinn saman grípur nýjan lykil sem enginn skoðaði.
SAMANTEKTARLYKLAR = {
    "atburdir",
    "dagar",
    "dagar_an_atburda",
    "dagleg_dreifing",
    "dypt_km",
    "fyrsti_dagur",
    "manudir",
    "sidasti_dagur",
    "staerdir",
}


class UttakFrosnaUrtaksins(unittest.TestCase):
    """Vinnslan keyrð frá enda til enda á frosna svarinu, án nets."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._mappa = tempfile.TemporaryDirectory()
        cls.mappa = Path(cls._mappa.name)
        cls.uttak = vinna_skjalfta(mappa=cls.mappa)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._mappa.cleanup()

    def test_skrifar_thrjar_skrar(self) -> None:
        for heiti in (ATBURDASKRA, DAGASKRA, SAMANTEKTARSKRA):
            self.assertTrue((self.mappa / heiti).is_file(), heiti)

    def test_atburdaskra_hefur_dalka_gagnaklasans(self) -> None:
        with (self.mappa / ATBURDASKRA).open(encoding="utf-8", newline="") as skra:
            rader = list(csv.DictReader(skra))
        self.assertEqual(
            list(rader[0]), [svid.name for svid in fields(Skjalfti)]
        )
        self.assertEqual(len(rader), VAENTIR_ATBURDIR)
        self.assertEqual(self.uttak.atburdir, VAENTIR_ATBURDIR)

    def test_dagaskra_hefur_alla_daga_og_telur_alla_atburdi(self) -> None:
        with (self.mappa / DAGASKRA).open(encoding="utf-8", newline="") as skra:
            rader = list(csv.DictReader(skra))
        self.assertEqual(list(rader[0]), [svid.name for svid in fields(DagsTalning)])
        self.assertEqual(len(rader), VAENTIR_DAGAR)
        self.assertEqual(
            sum(int(rod["event_count"]) for rod in rader), VAENTIR_ATBURDIR
        )

    def test_samantektin_hefur_engan_keyrslustimpil(self) -> None:
        samantekt = json.loads((self.mappa / SAMANTEKTARSKRA).read_text(encoding="utf-8"))
        self.assertEqual(set(samantekt), SAMANTEKTARLYKLAR)
        self.assertEqual(samantekt["atburdir"], VAENTIR_ATBURDIR)
        self.assertEqual(samantekt["dagar"], VAENTIR_DAGAR)

    def test_tvaer_keyrslur_gefa_somu_baeti(self) -> None:
        fyrri = {
            heiti: (self.mappa / heiti).read_bytes()
            for heiti in (ATBURDASKRA, DAGASKRA, SAMANTEKTARSKRA)
        }
        with tempfile.TemporaryDirectory() as onnur:
            vinna_skjalfta(mappa=onnur)
            for heiti, baeti in fyrri.items():
                self.assertEqual((Path(onnur) / heiti).read_bytes(), baeti, heiti)


class VarnagliVidVefgogn(unittest.TestCase):
    """Vinnslan á aldrei að skrifa í birtingarlagið (kafli 0)."""

    def test_skrif_i_vefgogn_eru_stodvud(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            vinna_skjalfta(mappa=ROT / "web" / "gogn")

    def test_skrif_i_undirmoppu_vefgagna_eru_stodvud(self) -> None:
        with self.assertRaises(SkjalftaVilla):
            vinna_skjalfta(mappa=ROT / "web" / "gogn" / "skjalftar")

    def test_vefgogn_eru_ohreyfd(self) -> None:
        # Varnaglinn á að falla áður en nokkuð verður til á disknum.
        for heiti in (ATBURDASKRA, DAGASKRA, SAMANTEKTARSKRA):
            self.assertFalse((ROT / "web" / "gogn" / heiti).exists(), heiti)


if __name__ == "__main__":
    unittest.main()
