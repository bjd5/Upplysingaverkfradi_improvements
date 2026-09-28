"""Útfluttu gildin borin við tölur gömlu síðunnar (issue #15, #16).

Það sem síðan birtir er það sem stendur í ``web/gogn/`` — þess vegna er
samanburðurinn gerður á **útfluttu, námunduðu gildunum**, ekki á SQL-svörunum
(það gera ``test_fyrirspurnir_*``). Viðmiðið er lesið úr
``docs/vidmid/vidmid.json`` og hver uppfletting krefst **nákvæmlega einnar
samsvörunar**: samanburður við enga línu stenst alltaf og sannar ekkert (#47).

Uppflettingarnar eru endurnýttar úr prófum hvers safns (fluttar inn sem
einingar, svo unittest keyri ekki prófin þeirra tvisvar).

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
import utflutningur_grunnur as ug
from friends_grunnur import vidmid_gildi
from hjalp import ROT
from mbl_vidmid import FROSNA_EINTAKID, SULKA_EFTIR_LYKLI, VIDMIDSKAFLI, VIDMIDSSIDA

import test_hagstofan_vidmid as hagvidmid  # noqa: E402
import test_jardskjalftar_vidmid as skjvidmid  # noqa: E402
import test_vedurstodvar_mat_vidmid as vedvidmid  # noqa: E402

from vinnsla.vedurstodvar_samanburdur import lesa_vidmid_siur  # noqa: E402

VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
PHOEBE_SKRAR = ROT / "docs" / "vidmid" / "phoebe-stats"


def _vidmidsrader() -> list[dict]:
    return json.loads(VIDMID_JSON.read_text(encoding="utf-8"))["gogn"]


def _ein(rader: list[dict], hvad: str) -> dict:
    if len(rader) != 1:
        raise AssertionError(f"'{hvad}' fann {len(rader)} línur í viðmiðinu, á að finna eina.")
    return rader[0]


def _csv(heiti: str) -> list[dict[str, str]]:
    with (PHOEBE_SKRAR / heiti).open(encoding="utf-8", newline="") as skra:
        return list(csv.DictReader(skra))


class Skjalftar(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gogn = ug.lesa("skjalftar.json")["gogn"]

    def test_yfirlitstolurnar(self) -> None:
        s = self.gogn["samantekt"]
        yfir = skjvidmid._yfirlitsgildi
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

    def test_staerdartaflan(self) -> None:
        (mlw,) = self.gogn["staerd_eftir_kvarda"]
        for reitur, sulka in (("fjoldi", "Fjöldi"), ("lagmark", "Lágmark"),
                              ("hamark", "Hámark"), ("midgildi", "Miðgildi")):
            with self.subTest(sulka=sulka):
                self.assertEqual(mlw[reitur], skjvidmid._kvardagildi(mlw["kvardi"], sulka)["gildi"])

    def test_dagar_og_manudir(self) -> None:
        dagar, manudir = skjvidmid._dagatolur_vidmids()
        self.assertEqual({d["dagur"]: d["fjoldi"] for d in self.gogn["dagar"]}, dagar)
        self.assertEqual({m["manudur"]: (m["dagar"], m["atburdir"]) for m in self.gogn["manudir"]},
                         manudir)


class Hagstofan(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gogn = ug.lesa("hagstofan.json")["gogn"]
        cls.rader = [r for r in _vidmidsrader()
                     if r.get("sida") == hagvidmid.SIDA and r.get("flokkur") == "tafla"
                     and r.get("tegund") == hagvidmid.TEGUND_HLUTFALLS]

    def test_oll_36_hlutfollin(self) -> None:
        self.assertEqual(len(self.gogn["hlutfoll"]), 36)
        for rad in self.gogn["hlutfoll"]:
            lykill = (rad["svid"], rad["kyn"], rad["stada"])
            with self.subTest(lykill=lykill):
                vaent = _ein([r for r in self.rader if hagvidmid._lykill(r) == lykill], str(lykill))
                self.assertEqual(rad["hlutfall"], vaent["gildi"])

    def test_mismunirnir_thrir(self) -> None:
        self.assertEqual({m["prosentustig"] for m in self.gogn["mismunir"]},
                         hagvidmid.lesa_prosentustig())

    def test_summurnar_eru_innan_namundunar(self) -> None:
        self.assertLessEqual({s["summa"] for s in self.gogn["summur"]}, hagvidmid.LEYFDAR_SUMMUR)


class Vedurstodvar(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gogn = ug.lesa("vedurstodvar.json")["gogn"]
        cls.svor = cls.gogn["svor"]

    def test_beidnirnar_fimm(self) -> None:
        vidmid = lesa_vidmid_siur()
        self.assertEqual(len(vidmid), len(self.gogn["beidnir"]))
        for beidni in self.gogn["beidnir"]:
            sia = "engin sía" if beidni["sia"] == "engin sía" else " + ".join(
                f"`{hluti}`" for hluti in beidni["sia"].split(" + "))
            with self.subTest(sia=sia):
                self.assertEqual(beidni["fjoldi"], vidmid[sia])

    def test_svorin(self) -> None:
        s, tolur = self.svor, vedvidmid._tolur_i_svari
        self.assertEqual(tolur(vedvidmid.KAFLI_NIDURSTADA),
                         (s["naesta_virka"]["station_id"], s["naesta_virka"]["metrar"]))
        self.assertEqual(tolur(vedvidmid.KAFLI_SVOR, "Hver er næsta veðurstöð"),
                         (s["naesta"]["station_id"], s["naesta"]["metrar"]))
        self.assertEqual(
            tolur(vedvidmid.KAFLI_SVOR, "Hver er næsta virka stöðin"),
            (s["naesta_virka"]["station_id"], s["naesta_virka"]["metrar"],
             s["naesta_aflogd"]["station_id"], s["naesta_aflogd"]["metrar"],
             s["naesta_aflogd"]["lokaar"], s["munur_metrar"]))
        self.assertEqual(tolur(vedvidmid.KAFLI_SVOR, "Hversu margar af stöðvunum"),
                         (s["fjoldi_virkra"], s["fjoldi_allra"], s["hlutfall_virkra_prosent"]))
        self.assertFalse(s["naesta_virka_naer_aftur"])
        self.assertEqual(
            tolur(vedvidmid.KAFLI_SVOR, "Dygði sama stöð"),
            (s["ar_aftur_i_timann"], s["naesta_virka"]["station_id"],
             s["naesta_virka"]["fyrsta_ar"], s["vidmidunarar"], s["langtimastod"]["station_id"],
             s["langtimastod"]["metrar"], s["langtimastod"]["fyrsta_ar"]))

    def test_sulurnar_eru_thaer_somu_og_a_gomlu_myndinni(self) -> None:
        texti = vedvidmid.VIDMID_SVG.read_text(encoding="utf-8")
        nofn = [(m["nafn"], int(m["audkenni"])) for m in vedvidmid.SVG_NAFN.finditer(texti)]
        gildi = [(int(m["metrar"]), int(m["start"]), int(m["lok"]) if m["lok"] else None)
                 for m in vedvidmid.SVG_GILDI.finditer(texti)]
        self.assertEqual(len(nofn), vedvidmid.LINUR_A_MYND)
        self.assertEqual(
            list(zip(nofn, gildi)),
            [((st["nafn"], st["station_id"]), (st["metrar"], st["fyrsta_ar"], st["lokaar"]))
             for st in self.gogn["stodvar_i_kassa"][: vedvidmid.LINUR_A_MYND]])


class Mbl(unittest.TestCase):
    def test_svorin_fimm(self) -> None:
        skjal = ug.lesa("mbl.json")["gogn"]
        self.assertTrue(skjal["uppruni"]["hragogn"].endswith(FROSNA_EINTAKID + ".html"))
        rader = [r for r in _vidmidsrader()
                 if r.get("sida") == VIDMIDSSIDA and r.get("lina") == FROSNA_EINTAKID
                 and VIDMIDSKAFLI in (r.get("kafli") or []) and r.get("visst")]
        self.assertEqual(len(skjal["svor"]), len(SULKA_EFTIR_LYKLI))
        for svar in skjal["svor"]:
            sulka = SULKA_EFTIR_LYKLI[svar["lykill"]]
            with self.subTest(sulka=sulka):
                vaent = _ein([r for r in rader if r["sulka"] == sulka], sulka)
                self.assertEqual(svar["gildi"], vaent["gildi"])
                self.assertTrue(svar["mynstur"])


class Phoebe(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gogn = ug.lesa("phoebe-tolfraedi.json")["gogn"]

    def test_umfang_og_thattunargaedi(self) -> None:
        u = self.gogn["umfang"]
        self.assertEqual(u["handritsskrar"], vidmid_gildi("handritsskrár"))
        self.assertEqual(u["thaettir"], vidmid_gildi("þættir"))
        g = u["thattunargaedi"]
        for reitur, heiti in (("textablokkir", "textablokkir alls"), ("tilsvor", "tilsvör"),
                              ("svidsfyrirsagnir", "sviðsfyrirsagnir"),
                              ("svidsleidbeiningar", "sviðsleiðbeiningar"),
                              ("oflokkad", "óflokkað"), ("oflokkad_prosent", "óflokkað hlutfall")):
            with self.subTest(heiti=heiti):
                self.assertEqual(g[reitur], vidmid_gildi(heiti))

    def test_linur_hvers_vinar(self) -> None:
        for rad in self.gogn["plass"]["alls"]:
            with self.subTest(persona=rad["persona"]):
                self.assertEqual(rad["linur"], vidmid_gildi(f"línur {rad['persona']}"))

    def test_plass_eftir_thattarod(self) -> None:
        ut = {(r["thattarod"], r["persona"]): r for r in self.gogn["plass"]["eftir_thattarod"]}
        skra = _csv("phoebe-screentime-by-season.csv")
        self.assertEqual(len(ut), len(skra))
        for v in skra:
            r = ut[(int(v["season"]), v["character"].title())]
            self.assertEqual((r["linur"], r["ord"], r["hlutdeild_prosent"], r["saeti"]),
                             (int(v["lines"]), int(v["words"]), float(v["line_share_pct"]),
                              int(v["rank_by_lines"])))

    def test_tengsl(self) -> None:
        self.assertEqual(
            [(r["persona"].lower(), r["lift"], r["saeti"]) for r in self.gogn["tengsl"]],
            [(v["character"], float(v["interaction_lift"]), int(v["rank"]))
             for v in _csv("phoebe-top-talkers.csv")])

    def test_naervera_med_helmingstilvikinu(self) -> None:
        ut = {r["thattarod"]: r for r in self.gogn["naervera"]}
        for v in _csv("phoebe-mentions-by-season.csv"):
            with self.subTest(thattarod=v["season"]):
                self.assertEqual(ut[int(v["season"])]["i_tali_a_thatt"],
                                 float(v["dialogue_mentions_per_episode"]))
        self.assertEqual(ut[1]["i_tali_a_thatt"], 4.12)  # 99/24 = 4,125 — ekki 4,13


if __name__ == "__main__":
    unittest.main()
