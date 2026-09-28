"""Próf fyrir fyrirspurnasafnið og lesarann ``gagnagrunnur.fyrirspurnir`` (issue #11).

Tvennt er prófað hér, og hvort tveggja þar sem það á að **bresta** (kafli 15):

* **Safnið sjálft.** Hvítlistinn og ``src/sql/queries/`` segja sömu sögu; hver
  skrá ber haus með spurningu, síðu og breytum; síðan sem hún nefnir er til;
  fjöldi ``?`` stemmir við hausinn og engin skrá ber Python-sniðmát.
* **Lesarinn.** Heiti utan hvítlistans — líka ``../`` og algild slóð — er
  hafnað áður en nokkur skrá er opnuð, og gallaður haus stöðvar lesturinn.

Talnasamanburðurinn við viðmiðið er í ``test_fyrirspurnir_vidmid.py``.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

import sql_samsetning  # noqa: E402
from fyrirspurnir_grunnur import DAEMISBREYTUR, hladinn_grunnur  # noqa: E402
from hjalp import PYTHON_ROT  # noqa: E402

from gagnagrunnur import fyrirspurnir as fs  # noqa: E402

# Eina þekkta samsetningin í src/python: fingrafar.py setur TÖFLUNÖFN inn í
# ``PRAGMA table_info`` og ``SELECT … FROM`` eftir hvítlista (_oruggt_nafn),
# því SQLite tekur ekki við auðkennum sem ?-breytum. Engin gildi. Fjöldinn er
# festur: ný samsetning þar — eða hvar sem er annars staðar — fellir prófið.
THEKKTAR_SAMSETNINGAR = {"gagnagrunnur/fingrafar.py": 6}
LAGMARK_KEYRSLUKALLA = 40

SIDUSLOD = re.compile(r"web/[a-z0-9/-]+\.html")
PYTHON_SNIDMAT = ("%s", "%(", "{", "}", "f'", 'f"')


class SafnidProf(unittest.TestCase):
    """Hver skrá í ``src/sql/queries/`` er skjalfest, á hvítlistanum og keyranleg."""

    def test_hvitlistinn_og_mappan_segja_somu_sogu(self) -> None:
        """Skrá utan listans er ónotanleg; lína án skrár er brotin lofun."""
        self.assertEqual(fs.skrar_i_moppu(), fs.FYRIRSPURNIR)

    def test_heitin_eru_ascii_lagstafir_og_bandstrik(self) -> None:
        for heiti in fs.FYRIRSPURNIR:
            with self.subTest(heiti=heiti):
                self.assertRegex(heiti, f"^{fs.HEITISMYNSTUR.pattern}$")

    def test_hver_fyrirspurn_hefur_gildan_haus(self) -> None:
        for heiti in sorted(fs.FYRIRSPURNIR):
            with self.subTest(heiti=heiti):
                fyrirspurn = fs.lesa(heiti)
                self.assertTrue(fyrirspurn.spurning)
                self.assertTrue(fyrirspurn.sida)

    def test_sidan_sem_hausinn_nefnir_er_til(self) -> None:
        for heiti in sorted(fs.FYRIRSPURNIR):
            with self.subTest(heiti=heiti):
                sidur = SIDUSLOD.findall(fs.lesa(heiti).sida)
                self.assertTrue(sidur, "Síða: nefnir enga web/…html-slóð")
                for sida in sidur:
                    self.assertTrue((ROT / sida).is_file(), sida)

    def test_engin_skra_ber_python_snidmat(self) -> None:
        """Regla 5: gildi fara inn sem ``?``. ``%s``, ``{}`` o.þ.h. eru merki um
        að einhver hafi ætlað að líma gildi inn í fyrirspurnina."""
        for heiti in sorted(fs.FYRIRSPURNIR):
            with self.subTest(heiti=heiti):
                sql = fs.lesa(heiti).sql
                for merki in PYTHON_SNIDMAT:
                    self.assertNotIn(merki, sql)


class KeyrslaProf(unittest.TestCase):
    """Hver fyrirspurn á hvítlistanum keyrð á grunni með öllum söfnunum hlöðnum.

    Talnasamanburðurinn við viðmiðið er í test_fyrirspurnir_<safn>.py og
    test_vedurstodvar_fyrirspurnir.py; hér er aðeins krafist að engin
    fyrirspurn sé óprófuð, brotin eða tóm.
    """

    def test_hver_fyrirspurn_keyrir_og_skilar_rodum(self) -> None:
        samband = hladinn_grunnur()
        for heiti in sorted(fs.FYRIRSPURNIR):
            with self.subTest(heiti=heiti):
                breytur = DAEMISBREYTUR.get(heiti, ())
                self.assertEqual(len(breytur), len(fs.lesa(heiti).breytur),
                                 "vantar dæmisbreytur í fyrirspurnir_grunnur.DAEMISBREYTUR")
                self.assertTrue(fs.keyra(samband, heiti, breytur))

    def test_daemisbreytur_eru_adeins_fyrir_til_fyrirspurnir(self) -> None:
        self.assertLessEqual(set(DAEMISBREYTUR), fs.FYRIRSPURNIR)


class StrengjasamsetningProf(unittest.TestCase):
    """Regla 5 yfir allan Python-kóðann: engin SQL sett saman úr strengjum.

    Sama AST-leit og P1.6 notaði á fimm hleðslueiningar (sql_samsetning.py),
    víkkuð yfir hverja .py-skrá í src/python/.
    """

    def test_engin_samsetning_i_src_python(self) -> None:
        kollin = 0
        for skra in sorted(PYTHON_ROT.rglob("*.py")):
            afstaed = skra.relative_to(PYTHON_ROT).as_posix()
            fundid, n = sql_samsetning.brot(skra.read_text(encoding="utf-8"))
            kollin += n
            with self.subTest(skra=afstaed):
                self.assertEqual(len(fundid), THEKKTAR_SAMSETNINGAR.get(afstaed, 0), fundid)
        self.assertGreaterEqual(kollin, LAGMARK_KEYRSLUKALLA,
                                "Leitin fann of fá keyrslukall — sannar ekkert.")

    def test_leitin_ser_hverja_samsetningarleid(self) -> None:
        """Næmni: hvert sýnidæmi verður að finnast (kafli 15)."""
        for kodi in ('c.execute(f"SELECT * FROM t WHERE id = {x}")',
                     'c.execute("SELECT * FROM t WHERE id = " + x)',
                     'c.execute("SELECT * FROM t WHERE id = %s" % x)',
                     'c.execute("SELECT * FROM t WHERE id = {}".format(x))',
                     'sql = "SELECT * FROM t"\nsql += " WHERE id = " + x',
                     'c.execute(fyrirspurnir[x])',
                     'c.execute(lesa(x).sql)'):
            with self.subTest(kodi=kodi):
                self.assertTrue(sql_samsetning.brot(kodi)[0])

    def test_breytur_og_lesarinn_eru_ekki_samsetning(self) -> None:
        for kodi in ('c.execute("SELECT 1 FROM t WHERE id = ?", (x,))',
                     'fyrirspurnir.keyra(c, "skjalftar-dypt")'):
            with self.subTest(kodi=kodi):
                fundid, kollin = sql_samsetning.brot(kodi)
                self.assertEqual((fundid, kollin), ([], 1))


class LesarinnProf(unittest.TestCase):
    """Lesarinn hafnar öllu utan hvítlistans og öllum ranglega skjalfestum skrám."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.mappa = Path(self._tmp.name)
        self.heiti = sorted(fs.FYRIRSPURNIR)[0]

    def skrifa(self, texti: str) -> None:
        (self.mappa / f"{self.heiti}.sql").write_text(texti, encoding="utf-8")

    def haus(self, breytur: str = "-- Breytur: engar") -> str:
        return (f"-- {self.heiti}.sql\n-- Spurning: Prófun?\n"
                f"-- Síða: web/index.html\n{breytur}\n\n")

    def test_heiti_utan_hvitlistans(self) -> None:
        for heiti in ("ekki-til", "../migrations/001_gagnasofnun",
                      "/etc/passwd", f"{self.heiti}.sql", self.heiti.upper()):
            with self.subTest(heiti=heiti), self.assertRaises(fs.FyrirspurnaVilla):
                fs.lesa(heiti)

    def test_engin_skra_er_opnud_fyrir_heiti_utan_listans(self) -> None:
        with mock.patch.object(Path, "read_text") as lestur:
            with self.assertRaises(fs.FyrirspurnaVilla):
                fs.lesa("../../CLAUDE")
        lestur.assert_not_called()

    def test_gild_skra_lesin(self) -> None:
        self.skrifa(self.haus("-- Breytur:\n--   ?1 fyrsta\n--   ?2 önnur")
                    + "SELECT ? + ? AS summa; -- athugasemd með ?\n")
        fyrirspurn = fs.lesa(self.heiti, self.mappa)
        self.assertEqual(fyrirspurn.breytur, ("fyrsta", "önnur"))

    def test_skra_vantar(self) -> None:
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, "finnst ekki"):
            fs.lesa(self.heiti, self.mappa)

    def test_rong_fyrsta_lina(self) -> None:
        self.skrifa("-- annad.sql\n" + self.haus()[len(f"-- {self.heiti}.sql\n"):] + "SELECT 1;")
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, "fyrsta línan"):
            fs.lesa(self.heiti, self.mappa)

    def test_spurning_vantar(self) -> None:
        self.skrifa(self.haus().replace("-- Spurning: Prófun?\n", "") + "SELECT 1;")
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, "Spurning"):
            fs.lesa(self.heiti, self.mappa)

    def test_sida_vantar(self) -> None:
        self.skrifa(self.haus().replace("-- Síða: web/index.html\n", "") + "SELECT 1;")
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, "Síða"):
            fs.lesa(self.heiti, self.mappa)

    def test_fleiri_stadgenglar_en_hausinn_lysir(self) -> None:
        self.skrifa(self.haus() + "SELECT * FROM t WHERE id = ?;")
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, r"1 \?-staðgengla en hausinn lýsir 0"):
            fs.lesa(self.heiti, self.mappa)

    def test_faerri_stadgenglar_en_hausinn_lysir(self) -> None:
        self.skrifa(self.haus("-- Breytur:\n--   ?1 a\n--   ?2 b") + "SELECT ?;")
        with self.assertRaises(fs.FyrirspurnaVilla):
            fs.lesa(self.heiti, self.mappa)

    def test_spurningarmerki_i_streng_er_ekki_stadgengill(self) -> None:
        self.skrifa(self.haus() + "SELECT 'hvað?' AS texti, \"dálkur?\" FROM t;")
        self.assertEqual(fs.lesa(self.heiti, self.mappa).breytur, ())

    def test_gat_i_numerum_breytna(self) -> None:
        self.skrifa(self.haus("-- Breytur:\n--   ?1 a\n--   ?3 c") + "SELECT ?, ?;")
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, r"\?3"):
            fs.lesa(self.heiti, self.mappa)

    def test_numeradir_og_nefndir_stadgenglar_bannadir(self) -> None:
        for sql in ("SELECT ?1;", "SELECT :gildi;", "SELECT @gildi;"):
            with self.subTest(sql=sql):
                self.skrifa(self.haus("-- Breytur:\n--   ?1 a") + sql)
                with self.assertRaisesRegex(fs.FyrirspurnaVilla, "ónúmeraðir"):
                    fs.lesa(self.heiti, self.mappa)

    def test_rangur_fjoldi_breytna_vid_keyrslu(self) -> None:
        heiti = "vedurstodvar-stod-eftir-audkenni"
        with self.assertRaisesRegex(fs.FyrirspurnaVilla, "tekur 1 breytur"):
            fs.keyra(None, heiti, ())


if __name__ == "__main__":
    unittest.main()
