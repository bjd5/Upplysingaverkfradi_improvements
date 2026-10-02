"""Sönnun þess að nýja síðan sýni sömu tölur og sú gamla (issue #29).

Prófið les ``docs/vidmid/vidmid.json`` (frosið viðmið) og ``web/gogn/*.json``
(útfluttu gögnin), ber hverja efnislega tölu saman og ber niðurstöðuna við
``docs/samanburdur.md``. Skjalið og kóðinn geta því ekki sundrast: breytist tala,
frávik eða ástæða í öðru þeirra fellur prófið. Ekkert net; aðeins staðalsafnið.

    python3 -m unittest discover -s tests -p "test_vidmid_samanburdur.py"
"""

from __future__ import annotations

import collections
import json
import re
import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from vidmid_hjalp import EKKI_BORID, EKKI_VID, STEMMIR, VIKUR, lesa_gogn, lesa_vidmid, snida  # noqa: E402
from vidmid_reglur import allar_nidurstodur  # noqa: E402

SKJAL = ROT / "docs" / "samanburdur.md"
META = ROT / "data" / "processed" / "phoebe-stats" / "_meta.json"
MBL_MAPPA = ROT / "data" / "raw" / "mbl"
SIDUR_MAPPA = ROT / "web" / "sidur"
TALA_ORD = {"níu": 9, "sex": 6, "Fjórar": 4}
RODIN = re.compile(r"^\|(.+)\|\s*$")


def _toflur() -> dict[str, list[list[str]]]:
    """Skiptir skjalinu í töflur eftir fyrirsögn; hver röð er listi af reitum."""
    toflur: dict[str, list[list[str]]] = collections.defaultdict(list)
    kafli = ""
    for lina in SKJAL.read_text(encoding="utf-8").splitlines():
        if lina.startswith("#"):
            kafli = lina.lstrip("# ").strip()
        elif (m := RODIN.match(lina)) and not set(m[1]) <= set("-| :"):
            toflur[kafli].append([c.strip().strip("`") for c in m[1].split("|")])
    return toflur


def _tala(texti: str) -> int:
    return int(texti.replace(".", ""))


class FlokkunStenst(unittest.TestCase):
    """Hver efnisleg tala fær einn flokk og skjalið segir það sama og kóðinn."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.vidmid = lesa_vidmid()
        cls.nidurstodur = allar_nidurstodur()
        cls.toflur = _toflur()

    def test_allar_efnislegar_tolur_flokkadar_einu_sinni(self) -> None:
        radir = [r["id"] for r in self.vidmid["gogn"] if r["visst"]]
        self.assertEqual(sorted(n.id for n in self.nidurstodur), sorted(radir))
        self.assertEqual(len(radir), self.vidmid["samantekt"]["efnislegar"])

    def test_tafla_sida_fyrir_sidu(self) -> None:
        eftir_sidu: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for n in self.nidurstodur:
            eftir_sidu[n.sida][n.flokkur] += 1
        skjal = {r[0]: r for r in self.toflur["Síða fyrir síðu"] if r[0].endswith(".html")}
        self.assertEqual(set(skjal), {s["sida"] for s in self.vidmid["sidur"]})
        for sida, r in skjal.items():
            c = eftir_sidu[sida]
            with self.subTest(sida=sida):
                vaentanlegt = [sum(c.values()), c[STEMMIR] + c[VIKUR], c[STEMMIR], c[VIKUR],
                               c[EKKI_VID], c[EKKI_BORID]]
                self.assertEqual([_tala(x) for x in r[2:8]], vaentanlegt)
        samtals = next(r for r in self.toflur["Síða fyrir síðu"] if r[0] == "Samtals")
        self.assertEqual(_tala(samtals[2]), len(self.nidurstodur))
        self.assertEqual(_tala(samtals[4]), sum(n.flokkur == STEMMIR for n in self.nidurstodur))
        self.assertEqual(_tala(samtals[5]), sum(n.flokkur == VIKUR for n in self.nidurstodur))

    def test_fravik_i_skjalinu_eru_eins_og_kodinn_reiknar_thau(self) -> None:
        kodinn = sorted((n.id, n.maeling, n.gamalt, n.nytt, n.astaeda)
                        for n in self.nidurstodur if n.flokkur == VIKUR)
        skjal = sorted(tuple(r[:5]) for r in self.toflur["Öll frávik"] if "#" in r[0])
        self.assertTrue(kodinn, "samanburðurinn á að finna frávik (mbl-eintakið)")
        self.assertEqual(skjal, kodinn)

    def test_ekki_borid_saman_og_a_ekki_vid_eru_eins_og_kodinn(self) -> None:
        kodinn = collections.Counter(
            (n.sida, n.flokkur, n.astaeda) for n in self.nidurstodur
            if n.flokkur in (EKKI_BORID, EKKI_VID))
        skjal = collections.Counter()
        for kafli in ("Ekki borið saman", "Á ekki við lengur"):
            for r in self.toflur[kafli]:
                if r[0].endswith(".html"):
                    skjal[(r[0], r[1], r[3])] += _tala(r[2])
        self.assertEqual(skjal, kodinn)

    def test_stemmir_er_aldrei_skrifad_inn_med_hendi(self) -> None:
        for n in self.nidurstodur:
            if n.flokkur == STEMMIR:
                self.assertEqual(n.astaeda, "", n.id)
                self.assertNotEqual(n.nytt, "", f"{n.id}: ber saman við ekkert")
            if n.flokkur == VIKUR:
                self.assertNotEqual(n.gamalt, n.nytt, n.id)


class StadfestarTolur(unittest.TestCase):
    """Tölurnar í `stadfestar` koma úr nýju gögnunum og stemma."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.vidmid = lesa_vidmid()
        cls.skjalftar = lesa_gogn("skjalftar")["gogn"]["samantekt"]
        ly = lesa_gogn("phoebe-tolfraedi")["lysigogn"]
        cls.umfang, cls.gaedi = ly["umfang"], ly["umfang"]["thattunargaedi"]
        cls.linur = {x["persona"]: x["linur"] for x in ly["plass_alls"]}

    def _nytt(self, heiti: str) -> float:
        beint = {
            "jarðskjálftar": self.skjalftar["atburdir"], "dagar í glugganum": self.skjalftar["dagar"],
            "handritsskrár": self.umfang["handritsskrar"], "þættir": self.umfang["thaettir"],
            "textablokkir alls": self.gaedi["textablokkir"], "tilsvör": self.gaedi["tilsvor"],
            "sviðsfyrirsagnir": self.gaedi["svidsfyrirsagnir"],
            "sviðsleiðbeiningar": self.gaedi["svidsleidbeiningar"],
            "óflokkað": self.gaedi["oflokkad"], "óflokkað hlutfall": self.gaedi["oflokkad_prosent"],
        }
        return beint[heiti] if heiti in beint else self.linur[heiti.removeprefix("línur ")]

    def test_hver_stadfest_tala_stemmir(self) -> None:
        stadfestar = self.vidmid["stadfestar"]
        self.assertEqual(len(stadfestar), 16)
        for s in stadfestar:
            with self.subTest(heiti=s["heiti"]):
                self.assertEqual(self._nytt(s["heiti"]), s["gildi"])
                if s["ur_gagnaskra"] is not None:
                    self.assertEqual(self._nytt(s["heiti"]), s["ur_gagnaskra"])
                self.assertTrue(s["stemmir"])

    def test_skjalid_telur_stadfestu_tolurnar(self) -> None:
        radir = {r[0]: r for r in _toflur()["Staðfestu tölurnar"] if len(r) == 4 and r[0] != "Heiti"}
        stadfestar = {s["heiti"]: s["gildi"] for s in self.vidmid["stadfestar"]}
        self.assertEqual(set(radir), set(stadfestar))
        for heiti, r in radir.items():
            self.assertEqual(r[1], snida(stadfestar[heiti]), heiti)
            self.assertEqual(r[3], "já", heiti)


class OsamraemiStadfest(unittest.TestCase):
    """Fimm ósamræmi gömlu síðnanna: hvert er skráð eins og gögnin segja."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.vidmid = lesa_vidmid()
        cls.osamraemi = {o["heiti"]: o for o in cls.vidmid["osamraemi"]}
        cls.ly = lesa_gogn("phoebe-tolfraedi")["lysigogn"]
        cls.umfang = cls.ly["umfang"]

    def test_fimm_osamraemi_og_hvert_er_i_skjalinu(self) -> None:
        self.assertEqual(len(self.osamraemi), 5)
        skjal = SKJAL.read_text(encoding="utf-8")
        for heiti in self.osamraemi:
            self.assertIn(heiti, skjal)

    def test_tvofaldir_thaettir_niu_skrar(self) -> None:
        heiti = "Fjöldi skráa sem geyma tvöfalda þætti"
        sagt = {s["stadur"]: s["segir"] for s in self.osamraemi[heiti]["stadir"]}
        self.assertIn("níu", sagt["friends/phoebe-statistics.html"])
        self.assertIn("sex", sagt["friends/index.html"])
        self.assertIn("Fjórar", sagt["phoebe-central-perk.html"])
        nitt = self.umfang["skrar_med_tvo_thaetti"]
        self.assertEqual(nitt, TALA_ORD["níu"])
        self.assertEqual(self.umfang["handritsskrar"] + nitt, self.umfang["thaettir"])
        self.assertEqual(len(lesa_gogn_meta()["conventions"]["double_episode_files"]), nitt)
        stakar = self.umfang["handritsskrar"] - nitt
        self.assertEqual(stakar + 2 * nitt, self.umfang["thaettir"])
        gamlar_stakar = next(n for n in allar_nidurstodur() if n.id == "friends/index.html#0014")
        self.assertEqual(gamlar_stakar.gamalt, "223")
        self.assertNotEqual(223 + 2 * TALA_ORD["Fjórar"], self.umfang["thaettir"])

    def test_ordid_lina_merkir_thrennt(self) -> None:
        gaedi = self.umfang["thattunargaedi"]
        gildi = {r["id"]: r for r in self.vidmid["gogn"]}
        self.assertEqual(gildi["lotur/regex/index.html#0001"]["eining"], "línur")
        self.assertEqual(gildi["lotur/regex/index.html#0001"]["gildi"], gaedi["tilsvor"])
        self.assertEqual(gildi["friends/phoebe-statistics.html#0049"]["gildi"], gaedi["tilsvor"])
        delvinso = gildi["friends/index.html#0012"]["gildi"]
        self.assertNotIn(delvinso, (gaedi["tilsvor"], gaedi["textablokkir"]))

    def test_rod_topptalara_er_ekki_a_nyju_sidunum(self) -> None:
        for skra in ("phoebe-tolfraedi.json", "phoebe-tolfraedi.html"):
            slod = (SIDUR_MAPPA if skra.endswith("html") else ROT / "web" / "gogn") / skra
            texti = slod.read_text(encoding="utf-8").lower()
            for nafn in ("frank", "david", "grandmother"):
                self.assertNotIn(nafn, texti, f"{nafn} í {skra}")
        talkers = lesa_gogn_ut("phoebe-top-talkers.json")["non_friend_characters"]
        stig = collections.Counter(x["adjacent_turns"] for x in talkers)
        self.assertEqual({x["character"] for x in talkers if x["adjacent_turns"] == 174},
                         {"frank", "david"})
        self.assertEqual(stig[32], 2)

    def test_meta_eintokin_og_236(self) -> None:
        meta = lesa_gogn_meta()
        sagt = next(s["segir"] for s in self.osamraemi["_meta.json er í tveimur eintökum frá tveimur keyrslum"]["stadir"]
                    if s["stadur"].startswith("docs/vidmid/phoebe-stats"))
        self.assertIn(meta["generated_utc"], sagt)
        self.assertEqual(meta["aired_episodes_covered"], self.umfang["thaettir"])
        for sida in SIDUR_MAPPA.glob("*.html"):
            self.assertNotRegex(sida.read_text(encoding="utf-8"), r"236\s+(handrits)?skrár", sida.name)


class MblEintakid(unittest.TestCase):
    """Frávikið stóra: eintak 7.9.2026 er glatað, nýja síðan notar eintak 16.9.2026."""

    def test_eintakid_er_frá_16_september_og_hitt_er_glatad(self) -> None:
        ein = lesa_gogn("mbl")["lysigogn"]["eintak"]
        self.assertTrue(ein["sott"].startswith("2026-09-16"))
        self.assertFalse(list(MBL_MAPPA.glob("mbl-20260907*")), "glatað eintak má ekki vera til")
        self.assertTrue((ROT / ein["hraskra"]).exists())

    def test_nyja_eintakid_er_sa_dalkur_gomlu_sidunnar_sem_stemmir(self) -> None:
        nid = {n.id: n for n in allar_nidurstodur()}
        for nr in ("0084", "0085", "0086", "0087", "0088", "0089"):
            self.assertEqual(nid[f"lotur/regex/mbl.html#{nr}"].flokkur, STEMMIR, nr)
        for nr in ("0076", "0078", "0079", "0080"):
            self.assertEqual(nid[f"lotur/regex/mbl.html#{nr}"].flokkur, VIKUR, nr)


def lesa_gogn_meta() -> dict:
    """Tölur Friends-greiningarinnar (frosið vinnugagn, sama eintak og viðmiðið)."""
    return json.loads(META.read_text(encoding="utf-8"))


def lesa_gogn_ut(skra: str) -> dict:
    """Les skrá úr data/processed/phoebe-stats/."""
    return json.loads((META.parent / skra).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
