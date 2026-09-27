"""Próf fyrir hleðslu mbl-niðurstaðna í SQL-grunninn (issue #9).

Það sem þarf að standast, og er prófað hér:

* Allar fimm spurningarnar eru svaranlegar með **einni SQL-fyrirspurn** á
  töflunum úr ``005_mbl_regex.sql``.
* Hvert svar er rekjanlegt í **mynstrið** sem framkallaði það OG **eintakið**
  sem það var lesið úr (regla 8).
* Mynstrin sjálf liggja í grunninum með niðurstöðunum — án mynstursins er
  ekki hægt að sjá hvers vegna talan varð þessi.
* Finnist mynstur ekki kemur skýr villa og **ekkert** er skrifað; hálft svar
  er ekki niðurstaða (regla 6).
* Fleiri en eitt eintak mega liggja í töflunni samtímis, aðgreind eftir
  sóknartíma.

Allar fyrirspurnir eru með breytum (regla 5). Prófin eru netlaus: þau lesa
frosna eintakið og smíða gervieintök, en skrifa aldrei í ``data/raw/``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import logging
import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.keyrari import MIGRATIONS_MAPPA, keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from mbl_gervigogn import GERVI_HTML, GERVI_SVOR, skrifa_eintak  # noqa: E402
from vinnsla.mbl_eintak import finna_eintok, lesa_eintak  # noqa: E402
from vinnsla.mbl_hledsla import HledsluVilla, hlada_eintak, hlada_ollu  # noqa: E402
from vinnsla.mbl_mynstur import MYNSTUR_FRETTASLOD, UtdrattarVilla  # noqa: E402

# Keyrarinn varar við götum í migration-númerum (002–004 eru á greinum hinna
# agentanna) og hleðslan skráir hvert eintak. Hvorugt er villa og hvorugt er
# það sem þessi próf mæla — þögnin er aðeins hér, ekki í keyrslunni sjálfri.
for heiti in ("gagnagrunnur.keyrari", "vinnsla.mbl_hledsla"):
    logging.getLogger(heiti).setLevel(logging.ERROR)

# Ein fyrirspurn sem svarar öllum fimm spurningunum og sýnir um leið hvaðan
# hvert svar kemur: mynstrið, eintakið og sóknartíminn fylgja hverri línu.
SVOR_SQL = """
SELECT e.question_number AS nr,
       e.question_key    AS lykill,
       e.question_is     AS spurning,
       e.value_number    AS gildi,
       e.value_text      AS svar,
       e.unit            AS eining,
       e.pattern_name    AS mynsturheiti,
       e.pattern         AS mynstur,
       e.match_count     AS tilvik,
       e.distinct_count  AS einstok,
       e.sample_match    AS synishorn,
       e.notes           AS takmarkanir,
       s.raw_file        AS eintak,
       s.fetched_at      AS sott,
       s.source_url      AS upprunaslod
  FROM mbl_extractions e
  JOIN mbl_snapshots   s ON s.id = e.snapshot_id
 WHERE s.fetched_at = ?
 ORDER BY e.question_number
"""

FROSNA_EINTAKID = "mbl-20260916T120851Z"

# Viðmiðstölurnar fyrir frosna eintakið; sami samanburður og í
# test_mbl_utdrattur, hér gerður á því sem raunverulega liggur í grunninum.
from test_mbl_utdrattur import vidmidstolur  # noqa: E402


class GrunnProf(unittest.TestCase):
    """Sameiginleg umgjörð: tómur grunnur með raunverulegu migration-unum."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.samband = opna(self.mappa / "prof.sqlite")
        self.addCleanup(self.samband.close)
        keyra(self.samband, MIGRATIONS_MAPPA)

    def svor(self, sott: str) -> list[sqlite3.Row]:
        """Keyrir SVOR_SQL fyrir eitt eintak — alltaf með breytu, aldrei f-streng."""
        return self.samband.execute(SVOR_SQL, (sott,)).fetchall()

    def frosna_eintakid(self):
        """Frosna eintakið úr ``data/raw/mbl/`` — lesið, aldrei skrifað."""
        eintok = [e for e in finna_eintok() if e.skraarheiti.startswith(FROSNA_EINTAKID)]
        self.assertTrue(eintok, f"{FROSNA_EINTAKID}.html finnst ekki í data/raw/mbl/.")
        return eintok[0]


class SqlSvorProf(GrunnProf):
    """Eru spurningarnar fimm svaranlegar með SQL — og með réttu svari?"""

    def setUp(self) -> None:
        super().setUp()
        self.eintak = self.frosna_eintakid()
        self.hledsla = hlada_eintak(self.samband, self.eintak)

    def test_fimm_svor_i_grunninum(self) -> None:
        radir = self.svor(self.eintak.sotta_stund)
        self.assertEqual(len(radir), 5)
        self.assertEqual([r["nr"] for r in radir], [1, 2, 3, 4, 5])

    def test_svorin_eru_vidmidid(self) -> None:
        """Kjarninn: talan sem SQL skilar er talan sem gamla síðan birti."""
        radir = self.svor(self.eintak.sotta_stund)
        ur_grunni = {r["lykill"]: r["gildi"] for r in radir}
        self.assertEqual(ur_grunni, vidmidstolur(FROSNA_EINTAKID))

    def test_hver_spurning_hefur_texta_og_einingu(self) -> None:
        """Svar án spurningar er ekki svar — báðar hliðar liggja í grunninum."""
        for rad in self.svor(self.eintak.sotta_stund):
            with self.subTest(lykill=rad["lykill"]):
                self.assertTrue(rad["spurning"].endswith("?"))
                self.assertTrue(rad["svar"])
                self.assertTrue(rad["eining"])
                self.assertTrue(rad["takmarkanir"])

    def test_spurning_fletts_upp_eftir_lykli(self) -> None:
        """Ein spurning, ein fyrirspurn — með breytu."""
        rad = self.samband.execute(
            "SELECT value_number, value_text FROM mbl_extractions "
            "WHERE question_key = ?",
            ("gengi-usd",),
        ).fetchone()
        self.assertEqual(rad["value_number"], 121.33)
        self.assertEqual(rad["value_text"], "121,33 ISK fyrir 1 USD")


class RekjanleikiProf(GrunnProf):
    """Er hvert svar rekjanlegt í mynstrið OG eintakið? (regla 8)"""

    def setUp(self) -> None:
        super().setUp()
        self.eintak = self.frosna_eintakid()
        hlada_eintak(self.samband, self.eintak)
        self.radir = self.svor(self.eintak.sotta_stund)

    def test_hvert_svar_bendir_a_eintakid_sitt(self) -> None:
        for rad in self.radir:
            with self.subTest(lykill=rad["lykill"]):
                self.assertEqual(rad["eintak"], self.eintak.skraarheiti)
                self.assertEqual(rad["sott"], self.eintak.sotta_stund)
                self.assertEqual(rad["upprunaslod"], self.eintak.upprunaslod)

    def test_mynstrid_sjalft_liggur_i_grunninum(self) -> None:
        """Án mynstursins er ekki hægt að sjá hvers vegna talan varð þessi."""
        for rad in self.radir:
            with self.subTest(lykill=rad["lykill"]):
                self.assertTrue(rad["mynstur"].strip())
                self.assertTrue(rad["mynsturheiti"].startswith("MYNSTUR_"))
                self.assertTrue(rad["synishorn"].strip())

    def test_mynstrid_er_geymt_ordrett(self) -> None:
        """Geymt mynstur verður að vera þýðanlegt aftur — annars er það ólæsilegt."""
        rad = self.samband.execute(
            "SELECT pattern, pattern_flags FROM mbl_extractions WHERE question_key = ?",
            ("einstakar-frettir",),
        ).fetchone()
        self.assertEqual(rad["pattern"], MYNSTUR_FRETTASLOD.pattern)
        self.assertIn("VERBOSE", rad["pattern_flags"])

    def test_eintakid_ber_sannreynd_lysigogn(self) -> None:
        """Sóknartími, MD5 og stærð fylgja með svo talan sé rekjanleg í hrágagnið."""
        rad = self.samband.execute(
            "SELECT md5, sha256, content_length_bytes, status_code "
            "FROM mbl_snapshots WHERE fetched_at = ?",
            (self.eintak.sotta_stund,),
        ).fetchone()
        self.assertEqual(rad["md5"], self.eintak.md5)
        self.assertEqual(rad["sha256"], self.eintak.sha256)
        self.assertEqual(rad["content_length_bytes"], self.eintak.staerd)
        self.assertEqual(rad["status_code"], 200)

    def test_afmorkun_fylgir_thegar_leitin_var_afmorkud(self) -> None:
        """USD fannst aðeins innan script-blokka; sú afmörkun er hluti aðferðarinnar."""
        rad = self.samband.execute(
            "SELECT scope_name, scope_pattern FROM mbl_extractions "
            "WHERE question_key = ?",
            ("gengi-usd",),
        ).fetchone()
        self.assertEqual(rad["scope_name"], "MYNSTUR_SCRIPT_BLOKK")
        self.assertIn("script", rad["scope_pattern"])


class MorgEintokProf(GrunnProf):
    """Mega tvö eintök liggja í töflunni samtímis, aðgreind eftir sóknartíma?"""

    def setUp(self) -> None:
        super().setUp()
        self.hra = self.mappa / "hra"
        self.fyrra = skrifa_eintak(self.hra, "20260907T103959Z")
        # Seinna eintakið hefur eitt auglýsingaauðkenni til viðbótar.
        seinna_html = GERVI_HTML.replace(
            'Ads.renderSlot("9999-1", {});',
            'Ads.renderSlot("9999-1", {});\nAds.renderSlot("9999-2", {});',
        )
        self.seinna = skrifa_eintak(self.hra, "20260916T120851Z", seinna_html)
        self.hledslur = hlada_ollu(self.samband, self.hra)

    def test_baedi_eintokin_liggja_i_grunninum(self) -> None:
        fjoldi = self.samband.execute(
            "SELECT COUNT(*) AS n FROM mbl_snapshots"
        ).fetchone()["n"]
        self.assertEqual(fjoldi, 2)

    def test_eintokin_eru_adgreind_eftir_sottum_tima(self) -> None:
        radir = self.samband.execute(
            "SELECT fetched_at, raw_file FROM mbl_snapshots ORDER BY fetched_at"
        ).fetchall()
        self.assertEqual(
            [r["fetched_at"] for r in radir],
            ["2026-09-07T10:39:59Z", "2026-09-16T12:08:51Z"],
        )
        self.assertEqual(len({r["raw_file"] for r in radir}), 2)

    def test_hvort_eintak_hefur_sin_fimm_svor(self) -> None:
        for hledsla in self.hledslur:
            with self.subTest(eintak=hledsla.eintak.skraarheiti):
                radir = self.svor(hledsla.eintak.sotta_stund)
                self.assertEqual(len(radir), 5)

    def test_eldra_eintakid_glatast_ekki_vid_nyrra(self) -> None:
        """Talan úr eldri sókn stendur óbreytt þótt nýrri sókn bætist við."""
        eldra = {r["lykill"]: r["gildi"] for r in self.svor("2026-09-07T10:39:59Z")}
        nyrra = {r["lykill"]: r["gildi"] for r in self.svor("2026-09-16T12:08:51Z")}
        self.assertEqual(eldra, GERVI_SVOR)
        self.assertEqual(nyrra["auglysingareitir"], 3.0)
        self.assertEqual(eldra["auglysingareitir"], 2.0)

    def test_sama_spurning_tvisvar_er_leyfd_thvert_a_eintok(self) -> None:
        """UNIQUE-skilyrðið bindur spurninguna við eintak, ekki við töfluna alla."""
        fjoldi = self.samband.execute(
            "SELECT COUNT(*) AS n FROM mbl_extractions WHERE question_key = ?",
            ("gengi-usd",),
        ).fetchone()["n"]
        self.assertEqual(fjoldi, 2)


class HledsluVilluProf(GrunnProf):
    """Villur stöðva hleðsluna — þær eru hvorki þaggaðar né skrifaðar hálfar."""

    def setUp(self) -> None:
        super().setUp()
        self.hra = self.mappa / "hra"

    def _fjoldi(self, tafla_svor: bool = False) -> int:
        sql = (
            "SELECT COUNT(*) AS n FROM mbl_extractions"
            if tafla_svor
            else "SELECT COUNT(*) AS n FROM mbl_snapshots"
        )
        return self.samband.execute(sql).fetchone()["n"]

    def test_tynt_mynstur_skrifar_ekkert(self) -> None:
        """Bregðist ein spurning af fimm er engin þeirra skrifuð."""
        an_auglysinga = GERVI_HTML.replace("Ads.renderSlot", "Auglysing.birta")
        slod = skrifa_eintak(self.hra, "20260916T120851Z", an_auglysinga)

        with self.assertRaises(UtdrattarVilla) as samhengi:
            hlada_eintak(self.samband, lesa_eintak(slod))

        self.assertIn("MYNSTUR_AUGLYSINGAREITUR", str(samhengi.exception))
        self.assertEqual(self._fjoldi(), 0)
        self.assertEqual(self._fjoldi(tafla_svor=True), 0)

    def test_endurhledsla_tvitelur_ekki(self) -> None:
        """Endurkeyrsla á sama eintaki er eðlileg og má ekki tvítelja."""
        slod = skrifa_eintak(self.hra, "20260916T120851Z")
        fyrri = hlada_eintak(self.samband, lesa_eintak(slod))
        seinni = hlada_eintak(self.samband, lesa_eintak(slod))

        self.assertFalse(fyrri.var_thegar_hladid)
        self.assertTrue(seinni.var_thegar_hladid)
        self.assertEqual(seinni.snapshot_id, fyrri.snapshot_id)
        self.assertEqual(self._fjoldi(), 1)
        self.assertEqual(self._fjoldi(tafla_svor=True), 5)

    def test_breytt_eintak_undir_sama_tima_stodvar(self) -> None:
        """Sami sóknartími en annað innihald þýðir að hrágagnið hefur breyst."""
        slod = skrifa_eintak(self.hra, "20260916T120851Z")
        hlada_eintak(self.samband, lesa_eintak(slod))

        breytt = GERVI_HTML.replace('"121.33"', '"999.99"')
        skrifa_eintak(self.hra, "20260916T120851Z", breytt)

        with self.assertRaises(HledsluVilla) as samhengi:
            hlada_eintak(self.samband, lesa_eintak(slod))
        self.assertIn("aðra SHA-256", str(samhengi.exception))

    def test_tom_nidurstada_kemst_ekki_i_grunninn(self) -> None:
        """Skilyrðin í 005 hafna línu sem mynstrið hitti aldrei á (regla 6)."""
        slod = skrifa_eintak(self.hra, "20260916T120851Z")
        hlada_eintak(self.samband, lesa_eintak(slod))

        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(
                "UPDATE mbl_extractions SET match_count = ? WHERE question_key = ?",
                (0, "gengi-usd"),
            )

    def test_svar_an_eintaks_kemst_ekki_i_grunninn(self) -> None:
        """Tilvísunarheilindi: útdráttur án eintaks væri órekjanleg tala."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.samband.execute(
                "INSERT INTO mbl_extractions ("
                "  snapshot_id, question_number, question_key, question_is,"
                "  pattern_name, pattern, pattern_flags,"
                "  value_number, value_text,"
                "  match_count, distinct_count, sample_match, extracted_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (999, 1, "einstakar-frettir", "Spurning?", "MYNSTUR_X", "x", "",
                 1.0, "1", 1, 1, "dæmi", "2026-09-24T00:00:00+00:00"),
            )

    def test_tom_mappa_er_villa_en_ekki_tomur_listi(self) -> None:
        """Útdráttur án eintaks er þögult núll — því er kastað villu (regla 6)."""
        tom = self.mappa / "tom"
        tom.mkdir()
        with self.assertRaises(RuntimeError) as samhengi:
            hlada_ollu(self.samband, tom)
        self.assertIn("Ekkert mbl-eintak", str(samhengi.exception))


if __name__ == "__main__":
    unittest.main()
