"""Hagstofu- og mbl-fyrirspurnirnar bornar við viðmiðið (issue #11).

Viðmiðið er lesið úr ``docs/vidmid/vidmid.json`` með sömu uppflettingum og
``test_hagstofan_vidmid.py`` og ``mbl_vidmid.py`` nota. Munurinn á þeim prófum
og þessum: þar var SQL-ið strengur í prófinu og námundaði sjálft; hér er það
skráin sem síðan byggir á, óafrúnnuð, og námundað er í birtingarnákvæmni
gömlu síðunnar (einn aukastafur) með Python.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from fyrirspurnir_grunnur import HAGSTOFAN_TAFLA, MBL_EINTAK, hladinn_grunnur
from mbl_vidmid import FROSNA_EINTAKID, vidmidstolur

# Eining, ekki föll úr henni — annars keyrði unittest prófin hennar tvisvar.
import test_hagstofan_vidmid as hagvidmid  # noqa: E402

from gagnagrunnur.fyrirspurnir import FyrirspurnaVilla, keyra  # noqa: E402

AUKASTAFIR = hagvidmid.AUKASTAFIR
BRAUTSKRADIR = hagvidmid.KODI_BRAUTSKRADIR
MISMUNIR = (  # (svið A, kyn A, svið B, kyn B) — mismunirnir sem gamla síðan fullyrti
    (hagvidmid.KODI_VERKFRAEDI, hagvidmid.KODI_ALLS, hagvidmid.KODI_ALLS, hagvidmid.KODI_ALLS),
    (hagvidmid.KODI_VERKFRAEDI, hagvidmid.KODI_KONUR, hagvidmid.KODI_VERKFRAEDI, hagvidmid.KODI_KARLAR),
    (hagvidmid.KODI_ALLS, hagvidmid.KODI_KONUR, hagvidmid.KODI_ALLS, hagvidmid.KODI_KARLAR),
)


class HagstofanUrSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.samband = hladinn_grunnur()

    def munur(self, svid_a: str, kyn_a: str, svid_b: str, kyn_b: str) -> float:
        radir = keyra(self.samband, "hagstofan-munur",
                      (HAGSTOFAN_TAFLA, BRAUTSKRADIR, svid_a, kyn_a, svid_b, kyn_b))
        self.assertEqual(len(radir), 1)
        return radir[0]["difference_pp"]

    def test_hver_prosenta_er_tala_gomlu_sidunnar(self) -> None:
        ur_sql = {
            (r["field_label"], r["sex_label"], r["student_status_label"]):
                round(r["percentage"], AUKASTAFIR)
            for r in keyra(self.samband, "hagstofan-hlutfoll", (HAGSTOFAN_TAFLA,))
        }
        self.assertEqual(ur_sql, hagvidmid.lesa_vidmid())

    def test_mismunirnir_thrir(self) -> None:
        fengnir = {round(self.munur(*hopar), AUKASTAFIR) for hopar in MISMUNIR}
        self.assertEqual(fengnir, hagvidmid.lesa_prosentustig())

    def test_munur_er_a_minus_b(self) -> None:
        """Röð hópanna skiptir máli: víxl gefur gagnstætt formerki."""
        a_b = self.munur(*MISMUNIR[0])
        b_a = self.munur(MISMUNIR[0][2], MISMUNIR[0][3], MISMUNIR[0][0], MISMUNIR[0][1])
        self.assertGreater(a_b, 0)
        self.assertEqual(a_b, -b_a)

    def test_ohekktur_hopur_gefur_enga_linu(self) -> None:
        radir = keyra(self.samband, "hagstofan-munur",
                      (HAGSTOFAN_TAFLA, BRAUTSKRADIR, "99", "Alls", "Alls", "Alls"))
        self.assertEqual(radir, [])

    def test_stoduflokkarnir_leggjast_i_hundrad(self) -> None:
        summur = {(r["field_code"], r["sex_code"]): round(r["percentage_sum"], AUKASTAFIR)
                  for r in keyra(self.samband, "hagstofan-summur", (HAGSTOFAN_TAFLA,))}
        self.assertEqual(len(summur), 12)
        self.assertLessEqual(set(summur.values()), hagvidmid.LEYFDAR_SUMMUR)

    def test_breyta_er_gildi_ekki_sql(self) -> None:
        """Regla 5 mæld: texti í breytu finnur ekkert og eyðir engu."""
        radir = keyra(self.samband, "hagstofan-hlutfoll",
                      (f"{HAGSTOFAN_TAFLA}'; DROP TABLE hagstofan_observations; --",))
        self.assertEqual(radir, [])
        self.assertTrue(keyra(self.samband, "hagstofan-hlutfoll", (HAGSTOFAN_TAFLA,)))


class MblUrSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.samband = hladinn_grunnur()

    def test_svorin_fimm_eru_tolur_gomlu_sidunnar(self) -> None:
        radir = keyra(self.samband, "mbl-svor", (MBL_EINTAK, None, None))
        self.assertEqual([r["nr"] for r in radir], [1, 2, 3, 4, 5])
        self.assertEqual({r["lykill"]: r["gildi"] for r in radir},
                         vidmidstolur(FROSNA_EINTAKID))
        self.assertEqual({r["eintak"] for r in radir}, {f"{FROSNA_EINTAKID}.html"})

    def test_eitt_svar_eftir_lykli(self) -> None:
        vaent = vidmidstolur(FROSNA_EINTAKID)
        for lykill, gildi in vaent.items():
            with self.subTest(lykill=lykill):
                radir = keyra(self.samband, "mbl-svor", (MBL_EINTAK, lykill, lykill))
                self.assertEqual([r["gildi"] for r in radir], [gildi])

    def test_rangur_fjoldi_breytna_stodvar(self) -> None:
        with self.assertRaises(FyrirspurnaVilla):
            keyra(self.samband, "mbl-svor", (MBL_EINTAK,))


if __name__ == "__main__":
    unittest.main()
