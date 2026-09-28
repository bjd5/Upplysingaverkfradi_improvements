"""Próf fyrir úttak skjálftavinnslunnar í data/processed/ (issue #14, pakki P2.3).

Prófin eru netlaus og skrifa aðeins í tímabundnar möppur — hvorki
``data/processed/``, ``data/raw/`` né ``web/gogn/`` er hreyft (regla 10).

Þrennt er prófað sem gæti annars brostið hljóðlaust:

* **Dálkarnir stemma við gagnaklasana.** CSV-skrá sem missir dálk lítur rétt út
  en er annað gagnasafn.
* **Úttakið er hrein afleiða.** Tvær keyrslur á sömu gögnum gefa sömu bæti.
  Vegguklukkustimpill í afleiddri skrá lætur hana virðast nýja þótt gögnin séu
  óbreytt — sama gildran og í issue #47.
* **Vinnslan skrifar ekki í web/gogn/.** Flæðið í kafla 0 er einstefna og
  varnaglinn er prófaður þar sem hann á að stöðva, ekki þar sem hann sefur.

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

from vinnsla.jardskjalftar import Skjalfti  # noqa: E402
from vinnsla.jardskjalftar_afmorkun import SkjalftaVilla  # noqa: E402
from vinnsla.jardskjalftar_talning import DagsTalning  # noqa: E402
from vinnsla.jardskjalftar_uttak import (  # noqa: E402
    ATBURDASKRA,
    DAGASKRA,
    SAMANTEKTARSKRA,
    vinna_skjalfta,
)

VAENTIR_ATBURDIR = 334
VAENTIR_DAGAR = 61

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
