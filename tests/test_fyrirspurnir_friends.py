"""Friends-fyrirspurnirnar bornar við viðmiðið (issue #11).

Tvær heimildir viðmiðs, báðar frosnar í ``docs/vidmid/``:

* ``vidmid.json`` — tölurnar sem stóðu á gömlu síðunni (fjöldatölur, línur
  hvers vinar). Flett upp með ``friends_grunnur.vidmid_gildi``: nákvæmlega ein
  samsvörun á uppflettingu.
* ``data/processed/phoebe-stats/*.csv|json`` — gagnaskrárnar sem gamla síðan
  teiknaði úr í vafranum (``gagnadrifnar_sidur`` í vidmid.json). Tölurnar
  standa þar en ekki í HTML-inu, svo þær eru viðmiðið fyrir allt á þáttaröð.

Námundunin er gerð hér með Python, eins og birtingin gerir. Tilvikið sem
ákvað venjuna — 99/24 = 4,125 — er fest í ``NamundunProf``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from fyrirspurnir_grunnur import hladinn_grunnur
from friends_grunnur import vidmid_gildi
from hjalp import ROT

from gagnagrunnur.fyrirspurnir import keyra  # noqa: E402
from utflutningur.islenskt_snid import islensk_tala  # noqa: E402

VIDMID_MAPPA = ROT / "data" / "processed" / "phoebe-stats"
VINIR = ("Phoebe", "Rachel", "Ross", "Chandler", "Monica", "Joey")
GAEDI = (("total_blocks", "textablokkir alls"), ("speaker_lines", "tilsvör"),
         ("scene_headings", "sviðsfyrirsagnir"), ("stage_directions", "sviðsleiðbeiningar"),
         ("unclassified", "óflokkað"), ("unclassified_pct", "óflokkað hlutfall"))
PROSENTUAUKASTAFIR = 2
FYRSTA_THATTAROD = 1
HELMINGSTILVIK = 4.125  # 99 nafntilvik / 24 þættir


def lesa_csv(heiti: str) -> list[dict[str, str]]:
    with (VIDMID_MAPPA / heiti).open(encoding="utf-8", newline="") as skra:
        return list(csv.DictReader(skra))


class FriendsUrSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.samband = hladinn_grunnur()

    def test_thattunargaedin_eru_tolur_gomlu_sidunnar(self) -> None:
        rad = keyra(self.samband, "friends-thattunargaedi")[0]
        for dalkur, heiti in GAEDI:
            with self.subTest(heiti=heiti):
                self.assertEqual(rad[dalkur], vidmid_gildi(heiti))

    def test_linur_hvers_vinar_og_saeti(self) -> None:
        radir = keyra(self.samband, "friends-plass-alls")
        self.assertEqual(sorted(r["character_name"] for r in radir), sorted(VINIR))
        for rad in radir:
            with self.subTest(vinur=rad["character_name"]):
                self.assertEqual(rad["lines"], vidmid_gildi(f"línur {rad['character_name']}"))
        # Sætið er röðin eftir línum í viðmiðinu, ekki ágiskun.
        eftir_linum = sorted(VINIR, key=lambda n: -vidmid_gildi(f"línur {n}"))
        self.assertEqual([r["character_name"] for r in radir], eftir_linum)
        self.assertEqual([r["rank_by_lines"] for r in radir], list(range(1, len(VINIR) + 1)))

    def test_plass_eftir_thattarod_er_skjatimaskrain(self) -> None:
        """RANK() OVER (PARTITION BY season): sæti innan hverrar þáttaraðar."""
        ur_sql = {(r["season"], r["character_name"]): r
                  for r in keyra(self.samband, "friends-plass-eftir-thattarod")}
        skra = lesa_csv("phoebe-screentime-by-season.csv")
        self.assertEqual(len(ur_sql), len(skra))
        for vaent in skra:
            lykill = (int(vaent["season"]), vaent["character"].title())
            rad = ur_sql[lykill]
            with self.subTest(lykill=lykill):
                self.assertEqual(
                    (rad["lines"], rad["words"],
                     round(rad["line_share_pct"], PROSENTUAUKASTAFIR), rad["rank_by_lines"]),
                    (int(vaent["lines"]), int(vaent["words"]),
                     float(vaent["line_share_pct"]), int(vaent["rank_by_lines"])),
                )

    def test_saeti_er_innan_thattarodar_ekki_yfir_allar(self) -> None:
        """Bresta: hver þáttaröð á sitt 1. sæti — röðun yfir allt gæfi aðeins eitt."""
        radir = keyra(self.samband, "friends-plass-eftir-thattarod")
        fyrstu = {r["season"] for r in radir if r["rank_by_lines"] == 1}
        self.assertEqual(fyrstu, {r["season"] for r in radir})

    def test_thattaradirnar_leggjast_saman_i_heildina(self) -> None:
        summa: dict[str, int] = {}
        for rad in keyra(self.samband, "friends-plass-eftir-thattarod"):
            summa[rad["character_name"]] = summa.get(rad["character_name"], 0) + rad["lines"]
        self.assertEqual(summa, {n: vidmid_gildi(f"línur {n}") for n in VINIR})

    def test_interaction_lift_er_top_talkers_skrain_nakvaemlega(self) -> None:
        radir = keyra(self.samband, "friends-interaction-lift")
        skra = lesa_csv("phoebe-top-talkers.csv")
        self.assertEqual(
            [(r["character_name"].lower(), r["adjacent_turns"], r["total_lines"],
              r["adjacency_share_pct"], r["expected_share_pct"], r["interaction_lift"],
              r["lift_rank"]) for r in radir],
            [(v["character"], int(v["adjacent_turns"]), int(v["total_lines_in_show"]),
              float(v["adjacency_share_pct"]), float(v["expected_share_pct"]),
              float(v["interaction_lift"]), int(v["rank"])) for v in skra],
        )

    def test_nafntilvik_eftir_thattarod(self) -> None:
        ur_sql = {r["season"]: r for r in keyra(self.samband, "friends-nafntilvik-eftir-thattarod")}
        skra = lesa_csv("phoebe-mentions-by-season.csv")
        self.assertEqual(sorted(ur_sql), [int(v["season"]) for v in skra])
        for vaent in skra:
            rad = ur_sql[int(vaent["season"])]
            with self.subTest(thattarod=vaent["season"]):
                self.assertEqual(
                    (rad["episodes"], rad["in_dialogue"], rad["in_stage_directions"],
                     rad["mentions_total"], rad["formal_phoebe"], rad["nickname_pheebs"],
                     round(rad["dialogue_mentions_per_episode"], PROSENTUAUKASTAFIR),
                     rad["top_mentioner"].lower(), rad["top_mentioner_count"]),
                    (int(vaent["episodes"]), int(vaent["mentions_in_dialogue_total"]),
                     int(vaent["mentions_in_stage_directions"]), int(vaent["mentions_total"]),
                     int(vaent["mentions_formal_phoebe"]), int(vaent["mentions_nickname_pheebs"]),
                     float(vaent["dialogue_mentions_per_episode"]),
                     vaent["top_mentioner"], int(vaent["top_mentioner_count"])),
                )


class NamundunProf(unittest.TestCase):
    """Venjan: SQL skilar óafrúnnuðu, birtingin (Python) námundar.

    PR #59 skildi þetta eftir opið: SQLite ``ROUND`` námundar helming frá núlli,
    Python að sléttri tölu. Þáttaröð 1 hefur nákvæmlega 99/24 = 4,125 nafntilvik
    á þátt og gamla síðan sýndi 4,12.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.samband = hladinn_grunnur()
        radir = keyra(cls.samband, "friends-nafntilvik-eftir-thattarod")
        cls.fyrsta = next(r for r in radir if r["season"] == FYRSTA_THATTAROD)

    def test_sql_skilar_helmingstilvikinu_oafrunnudu(self) -> None:
        self.assertEqual(self.fyrsta["dialogue_mentions_per_episode"], HELMINGSTILVIK)

    def test_birtingin_gefur_tolu_gomlu_sidunnar(self) -> None:
        skjal = json.loads((VIDMID_MAPPA / "phoebe-mentions-by-season.json")
                           .read_text(encoding="utf-8"))
        vaent = skjal["headline"]["lowest_per_episode"]
        gildi = self.fyrsta["dialogue_mentions_per_episode"]
        self.assertEqual(round(gildi, PROSENTUAUKASTAFIR), vaent)
        self.assertEqual(islensk_tala(gildi, PROSENTUAUKASTAFIR), "4,12")

    def test_namundun_i_sql_hefdi_gefid_ranga_tolu(self) -> None:
        """Bresta: væri námundað í SQL stæði 4,13 á síðunni, ekki 4,12."""
        sqlite_gildi = self.samband.execute(
            "SELECT ROUND(?, ?)", (HELMINGSTILVIK, PROSENTUAUKASTAFIR)).fetchone()[0]
        self.assertEqual(sqlite_gildi, 4.13)
        self.assertNotEqual(sqlite_gildi, round(HELMINGSTILVIK, PROSENTUAUKASTAFIR))

    def test_undantekningin_i_thattunargaedum_rekst_ekki_a(self) -> None:
        """Sýnin í 006 námundar unclassified_pct í SQL. Það má aðeins standa
        meðan það gefur sömu tölu og Python-námundun óafrúnnaða gildisins.
        (Hin undantekningin, interaction_lift, er borin nákvæmlega við
        Python-námundaða skrá í ``test_interaction_lift_er_top_talkers_skrain_nakvaemlega``.)"""
        gaedi = keyra(self.samband, "friends-thattunargaedi")[0]
        oafrunnad = 100.0 * gaedi["unclassified"] / gaedi["total_blocks"]
        self.assertEqual(gaedi["unclassified_pct"], round(oafrunnad, PROSENTUAUKASTAFIR))


if __name__ == "__main__":
    unittest.main()
