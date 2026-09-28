"""Próf fyrir hleðslu Friends-talnanna í grunninn (issue #10).

Netlaus: talnaskrárnar í ``data/processed/phoebe-stats/`` eru hlaðnar í
tímabundinn grunn og **grunnurinn spurður**. Væntu tölurnar eru lesnar úr
``docs/vidmid/vidmid.json`` (``stadfestar``), ekki handskrifaðar hér — sjá
``friends_grunnur.vidmid_gildi``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from friends_grunnur import opna_med_toflum, vidmid_gildi

from gagnagrunnur.fingrafar import _oruggt_nafn, fingrafar, lysing  # noqa: E402
from vinnsla import friends_hledsla as hledsla  # noqa: E402
from vinnsla.friends_faerslur import BLOKKAFLOKKAR  # noqa: E402
from vinnsla.friends_handrit import SOURCE_COMMIT  # noqa: E402
from vinnsla.friends_skrar import STATS_MAPPA, lesa_summur  # noqa: E402

VINIR = ("Phoebe", "Rachel", "Ross", "Chandler", "Monica", "Joey")

# (heiti í vidmid.json, fyrirspurn sem á að skila þeirri tölu)
FJOLDATOLUR = (
    ("handritsskrár", "SELECT COUNT(*) FROM friends_transcript_files"),
    ("þættir", "SELECT SUM(aired_episodes) FROM friends_transcript_files"),
    ("þættir", "SELECT SUM(aired_episodes) FROM friends_seasons"),
    ("textablokkir alls", "SELECT total_blocks FROM friends_parse_quality"),
    ("tilsvör", "SELECT speaker_lines FROM friends_parse_quality"),
    ("sviðsfyrirsagnir", "SELECT scene_headings FROM friends_parse_quality"),
    ("sviðsleiðbeiningar", "SELECT stage_directions FROM friends_parse_quality"),
    ("óflokkað", "SELECT unclassified FROM friends_parse_quality"),
    ("óflokkað hlutfall", "SELECT unclassified_pct FROM friends_parse_quality"),
)
LINUR_VINAR = "SELECT lines FROM friends_character_totals WHERE character_name = ?"

# PLÁSS á þáttaröð, með röðun (sama og screentime-skráin).
PLASS_A_ROD = """
SELECT t.season, l.character_name, SUM(l.lines) AS lines, SUM(l.words) AS words,
       ROUND(100.0 * SUM(l.lines) / SUM(SUM(l.lines)) OVER (PARTITION BY t.season), 2)
           AS line_share_pct,
       RANK() OVER (PARTITION BY t.season ORDER BY SUM(l.lines) DESC) AS rank_by_lines
FROM friends_episode_lines AS l
JOIN friends_transcript_files AS t USING (episode_code)
GROUP BY t.season, l.character_name
"""
# NÆRVERA á þáttaröð: nafntilvik í tali á hvern sýndan þátt, ónámundað. SQLite
# námundar hálfa frá núlli (99/24 = 4,125 -> 4,13) en greiningin notaði round()
# Python, sem námundar að sléttri tölu (-> 4,12). Borið er saman innan hálfs
# síðasta aukastafs svo prófið mæli gögnin, ekki námundunarvenjuna.
NAERVERA_A_ROD = """
SELECT m.season, m.in_dialogue_by_others + m.in_own_dialogue AS in_dialogue,
       1.0 * (m.in_dialogue_by_others + m.in_own_dialogue) / s.aired_episodes
           AS per_episode
FROM phoebe_mentions_by_season AS m
JOIN friends_seasons AS s USING (season)
"""
# Töflur sem geyma gildi úr talnaskránum (ekki uppruna hleðslunnar).
GAGNATOFLUR_SQL = (
    "SELECT name FROM sqlite_master WHERE type = 'table' "
    "AND (name LIKE 'friends\\_%' ESCAPE '\\' OR name LIKE 'phoebe\\_%' ESCAPE '\\') "
    "AND name NOT IN ('friends_sources', 'friends_source_files')"
)
HALFUR_AUKASTAFUR = 0.005 + 1e-9
STIMPILL_A = "2026-01-01T00:00:00+00:00"
STIMPILL_B = "2026-01-01T00:00:01+00:00"


def lesa_csv(heiti: str) -> list[dict[str, str]]:
    with (STATS_MAPPA / heiti).open(encoding="utf-8", newline="") as skra:
        return list(csv.DictReader(skra))


class HladidProf(unittest.TestCase):
    """Talnaskrárnar hlaðnar einu sinni og grunnurinn spurður."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.samband = opna_med_toflum(Path(cls._tmp.name))
        cls.fjoldi = hledsla.hlada(cls.samband)
        cls.samband.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()

    def eitt(self, fyrirspurn: str, breytur: tuple = ()) -> object:
        radir = self.samband.execute(fyrirspurn, breytur).fetchall()
        self.assertEqual(len(radir), 1, fyrirspurn)
        return radir[0][0]

    # --- fjöldatölurnar úr SQL, bornar við viðmiðið -----------------------

    def test_fjoldatolur_ur_sql_stemma_vid_vidmid(self) -> None:
        for heiti, fyrirspurn in FJOLDATOLUR:
            with self.subTest(heiti=heiti, fyrirspurn=fyrirspurn):
                self.assertEqual(self.eitt(fyrirspurn), vidmid_gildi(heiti))

    def test_oflokkad_hlutfall_innan_vikmarka_issue(self) -> None:
        """Issue #10: 2,95 % (±0,01) — reiknað í SQL úr fjöldanum, ekki lesið."""
        hlutfall = self.eitt(
            "SELECT 100.0 * unclassified / total_blocks FROM friends_parse_quality"
        )
        self.assertAlmostEqual(hlutfall, vidmid_gildi("óflokkað hlutfall"), delta=0.01)

    def test_linur_hvers_vinar_stemma_vid_vidmid(self) -> None:
        for nafn in VINIR:
            with self.subTest(vinur=nafn):
                self.assertEqual(self.eitt(LINUR_VINAR, (nafn,)),
                                 vidmid_gildi(f"línur {nafn}"))

    def test_blokkaflokkarnir_summast_i_heildina(self) -> None:
        self.assertEqual(self.eitt("SELECT SUM(blocks) FROM friends_parse_blocks"),
                         vidmid_gildi("textablokkir alls"))

    def test_undanskildu_skrarnar_eru_tvaer(self) -> None:
        radir = self.samband.execute(
            "SELECT file_name FROM friends_excluded_files ORDER BY file_name").fetchall()
        self.assertEqual([r[0] for r in radir], ["0423uncut.html", "07outtakes.html"])

    # --- mælitækin þrjú fást úr SQL ----------------------------------------

    def test_plass_a_thattarod_ur_sql_endurgerir_skrana(self) -> None:
        ur_sql = {(r["season"], r["character_name"]): tuple(r)[2:]
                  for r in self.samband.execute(PLASS_A_ROD)}
        skra = lesa_csv("phoebe-screentime-by-season.csv")
        self.assertEqual(len(ur_sql), len(skra))
        for rad in skra:
            lykill = (int(rad["season"]), rad["character"].title())
            with self.subTest(lykill=lykill):
                self.assertEqual(ur_sql[lykill], (
                    int(rad["lines"]), int(rad["words"]),
                    float(rad["line_share_pct"]), int(rad["rank_by_lines"])))

    def test_naervera_a_thattarod_ur_sql_endurgerir_skrana(self) -> None:
        ur_sql = {r["season"]: (r["in_dialogue"], r["per_episode"])
                  for r in self.samband.execute(NAERVERA_A_ROD)}
        for rad in lesa_csv("mentions-by-season.csv"):
            tal, a_thatt = ur_sql[int(rad["season"])]
            with self.subTest(thattarod=rad["season"]):
                self.assertEqual(tal, int(rad["mentions"]))
                self.assertLessEqual(abs(a_thatt - float(rad["mentions_per_episode"])),
                                     HALFUR_AUKASTAFUR)

    def test_interaction_lift_ur_sql_endurgerir_skrana(self) -> None:
        ur_sql = {r["character_name"]: r for r in self.samband.execute(
            "SELECT * FROM phoebe_interaction_lift")}
        skra = lesa_csv("phoebe-top-talkers.csv")
        self.assertEqual(len(ur_sql), len(skra))
        for rad in skra:
            fengid = ur_sql[rad["character"].title()]
            with self.subTest(persona=rad["character"]):
                self.assertEqual(fengid["adjacent_turns"], int(rad["adjacent_turns"]))
                self.assertEqual(fengid["adjacency_share_pct"], float(rad["adjacency_share_pct"]))
                self.assertEqual(fengid["expected_share_pct"], float(rad["expected_share_pct"]))
                self.assertEqual(fengid["interaction_lift"], float(rad["interaction_lift"]))

    def test_leidretting_fyrir_malgledi_faerir_rachel_ur_efsta_saeti(self) -> None:
        """Hrá talning sýnir Rachel efsta í línum; lift setur Monica efsta."""
        self.assertEqual(self.eitt(
            "SELECT character_name FROM friends_character_totals ORDER BY lines DESC LIMIT 1"),
            "Rachel")
        self.assertEqual(self.eitt(
            "SELECT character_name FROM phoebe_interaction_lift "
            "ORDER BY interaction_lift DESC LIMIT 1"), "Monica")

    # --- uppruni og höfundaréttur ------------------------------------------

    def test_uppruni_skrar_safn_og_commit(self) -> None:
        rad = self.samband.execute("SELECT * FROM friends_sources").fetchone()
        self.assertEqual(rad["transcript_repository"], "delvinso/friends")
        self.assertEqual(rad["transcript_commit"], SOURCE_COMMIT)
        self.assertEqual(rad["analysis_commit"], "2865ed6")

    def test_summur_skranna_eru_thaer_sem_provenance_skrair(self) -> None:
        radir = dict(self.samband.execute(
            "SELECT file_name, sha256 FROM friends_source_files").fetchall())
        self.assertEqual(radir, lesa_summur())

    def test_ekkert_textagildi_er_nytt_i_grunninum(self) -> None:
        """Enginn handritstexti: hvert textagildi stendur þegar í talnaskránum.

        Skrárnar sjálfar eru prófaðar fyrir samfelldum setningum í
        ``test_handritsleit``; hér er sannað að grunninn geymi ekkert umfram þær.
        """
        # Flokkaheitin í friends_parse_blocks eru orðaforði skemans (CHECK), ekki gögn.
        i_skranum = {g.lower() for g in _strengir_skranna()} | set(BLOKKAFLOKKAR.values())
        toflur = [r[0] for r in self.samband.execute(GAGNATOFLUR_SQL)]
        self.assertGreaterEqual(len(toflur), 14)
        for tafla in toflur:
            # Töfluheiti er ekki hægt að binda; hvítlisti fingrafarsins vitnar það.
            for rad in self.samband.execute(f"SELECT * FROM {_oruggt_nafn(tafla)}"):
                for gildi in rad:
                    if isinstance(gildi, str):
                        with self.subTest(tafla=tafla, gildi=gildi):
                            self.assertIn(gildi.lower(), i_skranum)


def _strengir_skranna() -> set[str]:
    """Öll strengjagildi talnaskránna: CSV-reitir og JSON-strengir og -lyklar."""
    strengir: set[str] = set()

    def ganga(hlutur: object) -> None:
        if isinstance(hlutur, str):
            strengir.add(hlutur)
        elif isinstance(hlutur, dict):
            strengir.update(hlutur)
            for gildi in hlutur.values():
                ganga(gildi)
        elif isinstance(hlutur, list):
            for gildi in hlutur:
                ganga(gildi)

    for slod in STATS_MAPPA.iterdir():
        if slod.suffix == ".csv":
            for rad in lesa_csv(slod.name):
                strengir.update(rad.values())
        elif slod.suffix == ".json":
            ganga(json.loads(slod.read_text(encoding="utf-8")))
    return strengir


class EndurkeyrsluProf(unittest.TestCase):
    """Sama aðfang gefur sama grunn, hversu oft sem hlaðið er."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna_med_toflum(Path(self._tmp.name))

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def hlada_klukkan(self, stimpill: str) -> dict[str, int]:
        with mock.patch.object(hledsla, "_nuna", return_value=stimpill):
            return hledsla.hlada(self.samband)

    def test_tvofold_hledsla_breytir_engu(self) -> None:
        """Sama klukka: grunnurinn allur (fingrafarið) er óbreyttur."""
        fyrri = self.hlada_klukkan(STIMPILL_A)
        fyrra_fingrafar = fingrafar(self.samband)
        seinni = self.hlada_klukkan(STIMPILL_A)

        self.assertEqual(fyrri, seinni)
        self.assertEqual(fingrafar(self.samband), fyrra_fingrafar)

    def test_eini_munurinn_yfir_sekundumork_er_loaded_at(self) -> None:
        """Önnur sekúnda: ekkert breytist nema keyrslustimpillinn sjálfur.

        Staðfesting sem stemmir af tilviljun er ekki staðfesting (#47), svo
        klukkan er þvinguð yfir sekúndumörk. Þar sem fingrafarið sleppir
        ``*_loaded_at`` (#47) er lýsingin eins; annars er stimpillinn eini
        munurinn — og ekkert annað í grunninum má hafa hreyfst.
        """
        self.hlada_klukkan(STIMPILL_A)
        fyrri = lysing(self.samband)
        self.hlada_klukkan(STIMPILL_B)
        seinni = lysing(self.samband)

        self.assertEqual(seinni.replace(STIMPILL_B, STIMPILL_A), fyrri)
        self.assertEqual(
            self.samband.execute("SELECT loaded_at FROM friends_sources").fetchone()[0],
            STIMPILL_B)

    def test_endurkeyrsla_tvofaldar_engar_radir(self) -> None:
        self.hlada_klukkan(STIMPILL_A)
        self.hlada_klukkan(STIMPILL_B)
        self.assertEqual(
            self.samband.execute("SELECT COUNT(*) FROM friends_transcript_files").fetchone()[0],
            vidmid_gildi("handritsskrár"))
        self.assertEqual(
            self.samband.execute("SELECT COUNT(*) FROM friends_sources").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
