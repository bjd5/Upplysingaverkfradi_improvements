"""Skjálfta-, mbl- og Phoebe-útflutningurinn borinn við viðmiðið (issue #15).

Það sem síðan birtir er það sem stendur í ``web/gogn/`` — samanburðurinn er því
á **útfluttu, námunduðu gildunum**, ekki á SQL-svörunum (það gera
``test_fyrirspurnir_*``). Viðmiðið er ``docs/vidmid/vidmid.json`` og hver
uppfletting krefst **nákvæmlega einnar samsvörunar**: samanburður við enga línu
stenst alltaf og sannar ekkert (#47). Uppflettingarnar eru endurnýttar úr
prófum hvers safns (fluttar inn sem einingar, svo unittest keyri ekki prófin
þeirra tvisvar). Hagstofan og veðurstöðvarnar eru bornar saman í
``test_utflutningur_hagstofan`` og ``test_utflutningur_vedurstodvar`` (#68).

Útflutningurinn skrifar í tímabundna möppu, aldrei í ``web/gogn/``.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import utflutningur_grunnur as ug
from friends_grunnur import vidmid_gildi
from hjalp import ROT
from mbl_hjalp import FROSNA_EINTAKID, SULKA_EFTIR_LYKLI, VIDMIDSKAFLI, VIDMIDSSIDA

import test_jardskjalftar_vidmid as skjvidmid  # noqa: E402

from utflutningur import central_perk_json, mbl_json, phoebe_json, skjalftar_json  # noqa: E402
from utflutningur.flytja_ut import flytja_ut  # noqa: E402

PHOEBE_SKRAR = ROT / "data" / "processed" / "phoebe-stats"


def setUpModule() -> None:
    global _TMP, GRUNNUR, UT
    _TMP = tempfile.TemporaryDirectory()
    mappa = Path(_TMP.name)
    GRUNNUR = ug.byggja_grunn(mappa / "rannsokn.sqlite")
    UT = mappa / "ut"
    UT.mkdir()
    flytja_ut(UT, GRUNNUR)


def tearDownModule() -> None:
    _TMP.cleanup()


def _lesa(heiti: str) -> dict:
    return ug.lesa_json(UT / heiti)


def _ein(rader: list[dict], hvad: str) -> dict:
    if len(rader) != 1:
        raise AssertionError(f"'{hvad}' fann {len(rader)} línur í viðmiðinu, á að finna eina.")
    return rader[0]


def _csv(heiti: str) -> list[dict[str, str]]:
    with (PHOEBE_SKRAR / heiti).open(encoding="utf-8", newline="") as skra:
        return list(csv.DictReader(skra))


def _grunngildi(sql: str) -> str:
    with sqlite3.connect(GRUNNUR) as samband:
        return samband.execute(sql).fetchone()[0]


class Umslog(unittest.TestCase):
    def test_reitir_og_uppfaert_ur_gognunum(self) -> None:
        vaent = {
            skjalftar_json.SKRAARHEITI: skjalftar_json.lesa_provenance()["fetched_at_utc"],
            mbl_json.SKRAARHEITI: _grunngildi("SELECT MAX(fetched_at) FROM mbl_snapshots"),
            phoebe_json.SKRAARHEITI: _grunngildi(
                "SELECT analysis_generated_utc FROM friends_sources"),
        }
        for heiti, stimpill in vaent.items():
            with self.subTest(skra=heiti):
                umslag = _lesa(heiti)
                self.assertEqual(list(umslag), ["uppfaert", "heimild", "gogn", "lysigogn"])
                self.assertEqual(datetime.fromisoformat(umslag["uppfaert"]),
                                 datetime.fromisoformat(stimpill).replace(microsecond=0))


class Skjalftar(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        umslag = _lesa(skjalftar_json.SKRAARHEITI)
        cls.dagar, cls.lysi = umslag["gogn"], umslag["lysigogn"]

    def test_yfirlitstolurnar(self) -> None:
        s, yfir = self.lysi["samantekt"], skjvidmid._yfirlitsgildi
        self.assertEqual(s["atburdir"], yfir("334", "heiltala", "Úrtakið inniheldur")["gildi"])
        self.assertEqual(s["dagar"], yfir("61", "heiltala", "Úrtakið inniheldur")["gildi"])
        d = s["daglegur_fjoldi"]
        self.assertEqual(d["midgildi"], yfir("0,00", "desimal", "Daglegur fjöldi:")["gildi"])
        self.assertEqual(d["lagmark"], yfir("0", "heiltala", "Daglegur fjöldi:")["gildi"])
        self.assertEqual(d["hamark"], yfir("187", "heiltala", "Daglegur fjöldi:")["gildi"])
        self.assertEqual(s["dagar_an_atburda"], yfir("43", "heiltala", "Daglegur fjöldi:")["gildi"])
        dypt = s["dypt_km"]
        self.assertEqual([dypt["lagmark"], dypt["hamark"]],
                         yfir("0,07–11,26", "bil", "Dýpt:")["bil"])
        self.assertEqual(dypt["midgildi"], yfir("4,67", "desimal", "Dýpt:")["gildi"])

    def test_hratt_syni_er_fyrstu_atburdirnir_obreyttir_ur_hragognunum(self) -> None:
        hra = json.loads((ROT / "data" / "raw" / "vedur-quakes" / "events.json")
                         .read_text("utf-8"))["features"]
        for syni, atburdur in zip(self.lysi["syni"], hra):
            with self.subTest(audkenni=syni["audkenni"]):
                eig = atburdur["properties"]
                self.assertEqual((syni["audkenni"], syni["timi"], syni["staerd"], syni["dypt_km"]),
                                 (eig["event_id"], eig["time"], eig["magnitude"], eig["depth"]))
                self.assertEqual((syni["lengd"], syni["breidd"]),
                                 tuple(atburdur["geometry"]["coordinates"]))
        self.assertEqual(len(self.lysi["syni"]), 8)

    def test_staerdartaflan(self) -> None:
        (mlw,) = self.lysi["staerd_eftir_kvarda"]
        for reitur, sulka in (("fjoldi", "Fjöldi"), ("lagmark", "Lágmark"),
                              ("hamark", "Hámark"), ("midgildi", "Miðgildi")):
            with self.subTest(sulka=sulka):
                self.assertEqual(mlw[reitur], skjvidmid._kvardagildi(mlw["kvardi"], sulka)["gildi"])

    def test_allir_dagar_og_manudir(self) -> None:
        dagar, manudir = skjvidmid._dagatolur_vidmids()
        self.assertEqual({d["dagur"]: d["fjoldi"] for d in self.dagar}, dagar)
        self.assertEqual({m["manudur"]: (m["dagar"], m["atburdir"]) for m in self.lysi["manudir"]},
                         manudir)

    def test_medaltalid_er_namundad_og_glugginn_skradur(self) -> None:
        self.assertEqual([d["dagar_i_glugga"] for d in self.dagar[:8]], [1, 2, 3, 4, 5, 6, 7, 7])
        for dagur in self.dagar:
            self.assertEqual(dagur["medaltal_7d"], round(dagur["medaltal_7d"], 2))


class Mbl(unittest.TestCase):
    def test_svorin_fimm_og_mynstrin(self) -> None:
        umslag = _lesa(mbl_json.SKRAARHEITI)
        self.assertTrue(umslag["lysigogn"]["eintak"]["hraskra"].endswith(FROSNA_EINTAKID + ".html"))
        rader = [r for r in ug.vidmidsradir(VIDMIDSSIDA)
                 if r.get("lina") == FROSNA_EINTAKID
                 and VIDMIDSKAFLI in (r.get("kafli") or []) and r.get("visst")]
        self.assertEqual(len(umslag["gogn"]), len(SULKA_EFTIR_LYKLI))
        for svar in umslag["gogn"]:
            sulka = SULKA_EFTIR_LYKLI[svar["lykill"]]
            with self.subTest(sulka=sulka):
                self.assertEqual(svar["gildi"], _ein([r for r in rader if r["sulka"] == sulka],
                                                     sulka)["gildi"])
                self.assertTrue(svar["mynstur"])


class Phoebe(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        umslag = _lesa(phoebe_json.SKRAARHEITI)
        cls.gogn, cls.lysi = umslag["gogn"], umslag["lysigogn"]

    def test_umfang_og_thattunargaedi(self) -> None:
        u = self.lysi["umfang"]
        self.assertEqual(u["handritsskrar"], vidmid_gildi("handritsskrár"))
        self.assertEqual(u["thaettir"], vidmid_gildi("þættir"))
        for reitur, heiti in (("textablokkir", "textablokkir alls"), ("tilsvor", "tilsvör"),
                              ("svidsfyrirsagnir", "sviðsfyrirsagnir"),
                              ("svidsleidbeiningar", "sviðsleiðbeiningar"),
                              ("oflokkad", "óflokkað"), ("oflokkad_prosent", "óflokkað hlutfall")):
            with self.subTest(heiti=heiti):
                self.assertEqual(u["thattunargaedi"][reitur], vidmid_gildi(heiti))

    def test_linur_hvers_vinar(self) -> None:
        for rad in self.lysi["plass_alls"]:
            with self.subTest(persona=rad["persona"]):
                self.assertEqual(rad["linur"], vidmid_gildi(f"línur {rad['persona']}"))

    def test_plass_eftir_thattarod(self) -> None:
        ut = {(r["thattarod"], r["persona"]): r for r in self.gogn}
        skra = _csv("phoebe-screentime-by-season.csv")
        self.assertEqual(len(ut), len(skra))
        for v in skra:
            r = ut[(int(v["season"]), v["character"].title())]
            self.assertEqual((r["linur"], r["ord"], r["hlutdeild_prosent"], r["saeti"]),
                             (int(v["lines"]), int(v["words"]), float(v["line_share_pct"]),
                              int(v["rank_by_lines"])))

    def test_tengsl(self) -> None:
        self.assertEqual(
            [(r["persona"].lower(), r["lift"], r["saeti"]) for r in self.lysi["tengsl"]],
            [(v["character"], float(v["interaction_lift"]), int(v["rank"]))
             for v in _csv("phoebe-top-talkers.csv")])

    def test_naervera_med_helmingstilvikinu(self) -> None:
        ut = {r["thattarod"]: r for r in self.lysi["naervera"]}
        for v in _csv("phoebe-mentions-by-season.csv"):
            with self.subTest(thattarod=v["season"]):
                self.assertEqual(ut[int(v["season"])]["i_tali_a_thatt"],
                                 float(v["dialogue_mentions_per_episode"]))
        self.assertEqual(ut[1]["i_tali_a_thatt"], 4.12)  # 99/24 = 4,125 — ekki 4,13

    def test_hlutdeild_alls_og_jafn_hlutur(self) -> None:
        plass = self.lysi["plass_alls"]
        self.assertAlmostEqual(sum(r["hlutdeild_prosent"] for r in plass), 100, delta=0.05)
        self.assertEqual(self.lysi["jafn_hlutur_prosent"], 16.67)  # 100/6


if __name__ == "__main__":
    unittest.main()
