"""Skjálftafyrirspurnirnar bornar við viðmiðið (issue #11).

Hver fyrirspurn í ``src/sql/queries/skjalftar-*.sql`` er keyrð á grunni sem er
hlaðinn úr frosna eintakinu, og **talan sem hún skilar er borin við töluna
sem gamla síðan birti** (``docs/vidmid/vidmid.json``). Uppflettingin í
viðmiðinu er sú sama og ``test_jardskjalftar_vidmid.py`` notar og krefst
nákvæmlega einnar samsvörunar.

Námundunin fer fram HÉR, í birtingarnákvæmni gömlu síðunnar, ekki í SQL —
sjá venjuna í ``gagnagrunnur/fyrirspurnir.py``.

Prófin sem **bresta**: sama spurning, spurð án dagatalsins (aðeins raðir í
``earthquakes``), er keyrð og sýnt að samanburðurinn fellur hana. Samanburður
sem stenst hvaða fyrirspurn sem er sannar ekkert (kafli 15).

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import unittest
from statistics import mean

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from fyrirspurnir_grunnur import hladinn_grunnur

# Eining, ekki föll úr henni — annars keyrði unittest prófin hennar tvisvar.
import test_jardskjalftar_vidmid as vidmid  # noqa: E402

from gagnagrunnur.fyrirspurnir import keyra  # noqa: E402
from vinnsla.jardskjalftar import lesa_skjalfta  # noqa: E402
from vinnsla.jardskjalftar_afmorkun import lesa_afmorkun  # noqa: E402
from vinnsla.jardskjalftar_samantekt import draga_saman  # noqa: E402
from vinnsla.jardskjalftar_talning import dagleg_talning  # noqa: E402

GLUGGI = 7
DAGLEGT_UPPHAF = "Daglegur fjöldi:"
DYPT_UPPHAF = "Dýpt:"
YFIRLIT_UPPHAF = "Úrtakið inniheldur"

# Röng útgáfa daglegu talningarinnar: telur aðeins daga sem eiga atburð.
AN_DAGATALS = (
    "SELECT utc_day, COUNT(*) AS event_count FROM earthquakes "
    "GROUP BY utc_day ORDER BY utc_day"
)
AN_DAGATALS_HLAUPANDI = (
    "SELECT utc_day, AVG(n) OVER (ORDER BY utc_day ROWS BETWEEN 6 PRECEDING "
    "AND CURRENT ROW) AS rolling_avg_7d FROM (SELECT utc_day, COUNT(*) AS n "
    "FROM earthquakes GROUP BY utc_day) ORDER BY utc_day"
)


def namunda(gildi: float) -> float:
    """Birtingarnámundun gömlu síðunnar: Python ``round``, tveir aukastafir."""
    return round(float(gildi), vidmid.AUKASTAFIR)


def dagatal_stemmir(radir: list) -> bool:
    """Ber daglega talningu við hvern dag í mánaðartöflum gömlu síðunnar."""
    vaent, _ = vidmid._dagatolur_vidmids()
    return {r["utc_day"]: r["event_count"] for r in radir} == vaent


class SkjalftarUrSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.samband = hladinn_grunnur()

    def eitt(self, heiti: str):
        radir = keyra(self.samband, heiti)
        self.assertEqual(len(radir), 1, heiti)
        return radir[0]

    # --- dagleg talning með núll-dögum -------------------------------------

    def test_dagleg_talning_er_hver_dagur_vidmidsins(self) -> None:
        radir = keyra(self.samband, "skjalftar-dagleg-talning")
        self.assertEqual(len(radir), vidmid._yfirlitsgildi("61", "heiltala", YFIRLIT_UPPHAF)["gildi"])
        self.assertTrue(dagatal_stemmir(radir))

    def test_talning_an_dagatals_fellur_a_sama_samanburdi(self) -> None:
        """Bresta: án LEFT JOIN vantar 43 daga og samanburðurinn verður að fella það."""
        radir = self.samband.execute(AN_DAGATALS).fetchall()
        self.assertLess(len(radir), 61)
        self.assertFalse(dagatal_stemmir(radir))

    def test_dagleg_samantekt(self) -> None:
        rad = self.eitt("skjalftar-dagleg-samantekt")
        gildi = lambda texti, tegund, upphaf=DAGLEGT_UPPHAF: vidmid._yfirlitsgildi(  # noqa: E731
            texti, tegund, upphaf)["gildi"]
        self.assertEqual(rad["day_count"], gildi("61", "heiltala", YFIRLIT_UPPHAF))
        self.assertEqual(rad["event_count"], gildi("334", "heiltala", YFIRLIT_UPPHAF))
        self.assertEqual(rad["days_without_events"], gildi("43", "heiltala"))
        self.assertEqual(rad["min_daily"], gildi("0", "heiltala"))
        self.assertEqual(rad["max_daily"], gildi("187", "heiltala"))
        self.assertEqual(namunda(rad["median_daily"]), gildi("0,00", "desimal"))

    def test_manadartalning_er_fyrirsagnir_manadartaflnanna(self) -> None:
        _, vaent = vidmid._dagatolur_vidmids()
        radir = keyra(self.samband, "skjalftar-manadartalning")
        self.assertEqual({r["month"]: (r["day_count"], r["event_count"]) for r in radir}, vaent)

    # --- stærð innan kvarða og dýpt ------------------------------------------

    def test_staerd_innan_hvers_kvarda(self) -> None:
        radir = keyra(self.samband, "skjalftar-staerd-eftir-kvarda")
        self.assertEqual([r["magnitude_type"] for r in radir], ["Mlw"])
        mlw = radir[0]
        self.assertEqual(mlw["event_count"], vidmid._kvardagildi("Mlw", "Fjöldi")["gildi"])
        self.assertEqual(namunda(mlw["min_magnitude"]), vidmid._kvardagildi("Mlw", "Lágmark")["gildi"])
        self.assertEqual(namunda(mlw["max_magnitude"]), vidmid._kvardagildi("Mlw", "Hámark")["gildi"])
        self.assertEqual(namunda(mlw["median_magnitude"]),
                         vidmid._kvardagildi("Mlw", "Miðgildi")["gildi"])

    def test_dypt(self) -> None:
        rad = self.eitt("skjalftar-dypt")
        bil = vidmid._yfirlitsgildi("0,07–11,26", "bil", DYPT_UPPHAF)["bil"]
        self.assertEqual([namunda(rad["min_depth_km"]), namunda(rad["max_depth_km"])], bil)
        self.assertEqual(namunda(rad["median_depth_km"]),
                         vidmid._yfirlitsgildi("4,67", "desimal", DYPT_UPPHAF)["gildi"])

    def test_sql_og_python_samantektin_segja_somu_sogu(self) -> None:
        """Tvær heimkynni sömu tölfræði (#14, P2.3 liður 3): SQL er heimild
        birtingarinnar, Python-samantektin eftirlit — óafrúnnað skulu þær stemma."""
        afmorkun = lesa_afmorkun()
        skjalftar = lesa_skjalfta(None, afmorkun)
        samantekt = draga_saman(skjalftar, dagleg_talning(skjalftar, afmorkun))
        mlw = keyra(self.samband, "skjalftar-staerd-eftir-kvarda")[0]
        python = {k.magnitude_type: k.dreifing for k in samantekt.staerdir}["Mlw"]
        self.assertEqual(
            (mlw["event_count"], mlw["min_magnitude"], mlw["max_magnitude"], mlw["median_magnitude"]),
            (python.fjoldi, python.lagmark, python.hamark, python.midgildi),
        )
        dypt = self.eitt("skjalftar-dypt")
        self.assertEqual(
            (dypt["min_depth_km"], dypt["max_depth_km"], dypt["median_depth_km"]),
            (samantekt.dypt_km.lagmark, samantekt.dypt_km.hamark, samantekt.dypt_km.midgildi),
        )
        dagleg = self.eitt("skjalftar-dagleg-samantekt")
        self.assertEqual(dagleg["days_without_events"], samantekt.dagar_an_atburda)
        self.assertEqual(dagleg["median_daily"], samantekt.dagleg_dreifing.midgildi)

    # --- hlaupandi 7 daga meðaltal (engin viðmiðstala) ----------------------

    def test_hlaupandi_medaltal_er_medaltal_sidustu_sjo_almanaksdaga(self) -> None:
        dagar = keyra(self.samband, "skjalftar-dagleg-talning")
        radir = keyra(self.samband, "skjalftar-hlaupandi-medaltal")
        self.assertEqual([r["utc_day"] for r in radir], [d["utc_day"] for d in dagar])
        self.assertEqual([r["event_count"] for r in radir], [d["event_count"] for d in dagar])
        fjoldi = [d["event_count"] for d in dagar]
        for i, rad in enumerate(radir):
            gluggi = fjoldi[max(0, i - GLUGGI + 1): i + 1]
            with self.subTest(dagur=rad["utc_day"]):
                self.assertEqual(rad["days_in_window"], len(gluggi))
                self.assertAlmostEqual(rad["rolling_avg_7d"], mean(gluggi), places=12)

    def test_hlaupandi_medaltal_an_nulldaga_er_annad(self) -> None:
        """Bresta: sami gluggi yfir röð án núll-daga nær yfir fleiri en 7 almanaksdaga."""
        rett = {r["utc_day"]: r["rolling_avg_7d"]
                for r in keyra(self.samband, "skjalftar-hlaupandi-medaltal")}
        rangt = {r["utc_day"]: r["rolling_avg_7d"]
                 for r in self.samband.execute(AN_DAGATALS_HLAUPANDI)}
        self.assertTrue(any(rett[dagur] != gildi for dagur, gildi in rangt.items()))

    def test_hlaupandi_medaltal_varpar_heildinni(self) -> None:
        """Summa daganna í fullum gluggum = 7 × meðaltal — engin tvítalning."""
        radir = keyra(self.samband, "skjalftar-hlaupandi-medaltal")
        for i in range(GLUGGI - 1, len(radir)):
            summa = sum(r["event_count"] for r in radir[i - GLUGGI + 1: i + 1])
            self.assertAlmostEqual(radir[i]["rolling_avg_7d"] * GLUGGI, summa, places=9)


if __name__ == "__main__":
    unittest.main()
