"""Próf á hegðun mbl-hleðslunnar sjálfrar (issue #9).

Hér er prófað hvernig hleðslan **kemur sér** við grunninn, ekki hvort tölurnar
séu réttar — það er gert í ``test_mbl_svor.py``:

* Fleiri en eitt eintak mega liggja í töflunum samtímis, aðgreind eftir
  sóknartíma, svo eldri sókn glatist ekki þegar sú nýrri er hlaðin.
* Endurkeyrsla á sama eintaki tvítelur ekki.
* Finnist mynstur ekki kemur skýr villa og **ekkert** er skrifað; hálft svar
  er ekki niðurstaða (regla 6).
* Skilyrðin í ``005_mbl_regex.sql`` hafna tómri niðurstöðu og svari án eintaks.

Allar fyrirspurnir eru með breytum (regla 5). Prófin eru netlaus og nota
gervieintök úr ``mbl_gervigogn`` — frosna eintakinu er aldrei skrifað (regla 10).

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import sqlite3
import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from mbl_gervigogn import GERVI_HTML, GERVI_SVOR, skrifa_eintak  # noqa: E402
from mbl_grunnur import GrunnProf  # noqa: E402
from vinnsla.mbl_eintak import lesa_eintak  # noqa: E402
from vinnsla.mbl_hledsla import (  # noqa: E402
    HledsluVilla,
    hlada_eintak,
    hlada_ollu,
)
from vinnsla.mbl_mynstur import UtdrattarVilla  # noqa: E402

# Sóknartímar gervieintakanna, á forminu sem skráarheitin bera.
FYRRI_SOKN = "20260907T103959Z"
SEINNI_SOKN = "20260916T120851Z"


class MorgEintokProf(GrunnProf):
    """Mega tvö eintök liggja í töflunni samtímis, aðgreind eftir sóknartíma?"""

    def setUp(self) -> None:
        super().setUp()
        self.hra = self.mappa / "hra"
        self.fyrra = skrifa_eintak(self.hra, FYRRI_SOKN)
        # Seinna eintakið hefur eitt auglýsingaauðkenni til viðbótar.
        seinna_html = GERVI_HTML.replace(
            'Ads.renderSlot("9999-1", {});',
            'Ads.renderSlot("9999-1", {});\nAds.renderSlot("9999-2", {});',
        )
        self.seinna = skrifa_eintak(self.hra, SEINNI_SOKN, seinna_html)
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
        slod = skrifa_eintak(self.hra, SEINNI_SOKN, an_auglysinga)

        with self.assertRaises(UtdrattarVilla) as samhengi:
            hlada_eintak(self.samband, lesa_eintak(slod))

        self.assertIn("MYNSTUR_AUGLYSINGAREITUR", str(samhengi.exception))
        self.assertEqual(self._fjoldi(), 0)
        self.assertEqual(self._fjoldi(tafla_svor=True), 0)

    def test_endurhledsla_tvitelur_ekki(self) -> None:
        """Endurkeyrsla á sama eintaki er eðlileg og má ekki tvítelja."""
        slod = skrifa_eintak(self.hra, SEINNI_SOKN)
        fyrri = hlada_eintak(self.samband, lesa_eintak(slod))
        seinni = hlada_eintak(self.samband, lesa_eintak(slod))

        self.assertFalse(fyrri.var_thegar_hladid)
        self.assertTrue(seinni.var_thegar_hladid)
        self.assertEqual(seinni.snapshot_id, fyrri.snapshot_id)
        self.assertEqual(self._fjoldi(), 1)
        self.assertEqual(self._fjoldi(tafla_svor=True), 5)

    def test_breytt_eintak_undir_sama_tima_stodvar(self) -> None:
        """Sami sóknartími en annað innihald þýðir að hrágagnið hefur breyst."""
        slod = skrifa_eintak(self.hra, SEINNI_SOKN)
        hlada_eintak(self.samband, lesa_eintak(slod))

        breytt = GERVI_HTML.replace('"121.33"', '"999.99"')
        skrifa_eintak(self.hra, SEINNI_SOKN, breytt)

        with self.assertRaises(HledsluVilla) as samhengi:
            hlada_eintak(self.samband, lesa_eintak(slod))
        self.assertIn("aðra SHA-256", str(samhengi.exception))

    def test_tom_nidurstada_kemst_ekki_i_grunninn(self) -> None:
        """Skilyrðin í 005 hafna línu sem mynstrið hitti aldrei á (regla 6)."""
        slod = skrifa_eintak(self.hra, SEINNI_SOKN)
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
