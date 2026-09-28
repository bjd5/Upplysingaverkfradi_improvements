"""Útflutningurinn í ``web/gogn/`` (issue #15): snið, ákvörðun, atómík og stærð.

Hvert skilyrði er prófað **þar sem það á að bresta** (docs/agenta-verkefni.md
kafli 15): ákvörðunin yfir þvinguð sekúndumörk og á grunni sem var endurbyggður
með annarri hleðsluklukku, atómíkin með safni sem fellur og diski sem fyllist.

Allt úttak fer í tímabundnar möppur; ``web/gogn/`` er aðeins lesið — í prófinu
sem krefst þess að skrárnar í git séu bætaeins nýjum útflutningi.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import ast
import sqlite3
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
import utflutningur_grunnur as ug
from hjalp import ROT

from keyrsla.utflutningur import flytja_allt  # noqa: E402
from keyrsla.villa import SkrefVilla  # noqa: E402
from utflutningur import flytja, skrifa  # noqa: E402
from utflutningur.skjal import LYKLAR, UtflutningsVilla  # noqa: E402

VEFGOGN = ROT / "web" / "gogn"
UTFLUTNINGSMAPPA = ROT / "src" / "python" / "utflutningur"
SIDUSKRAR = {s.skra for s in flytja.SOFN}
ALLAR_SKRAR = SIDUSKRAR | {flytja.YFIRLIT}

# Þak á samtölu web/gogn/. Regla 3.4 leyfir 500 KB í fyrstu hleðslu síðu. Síða
# les í mesta lagi eina gagnaskrá auk yfirlits; HTML, CSS, JS og SVG-myndrit
# (#17) eiga að hafa meirihlutann. 150 KB fyrir ALLAR skrárnar saman tryggir að
# engin ein skrá geti tekið meira en þriðjung þaksins, jafnvel þótt síðurnar
# stækki. Núverandi samtala er um 46 KB.
HAMARK_BAETI = 150 * 1024

# Mesti fjöldi aukastafa í hverri skrá — nákvæmnin sem gamla síðan birti.
AUKASTAFIR = {"skjalftar.json": 2, "hagstofan.json": 1, "mbl.json": 2,
              "phoebe-tolfraedi.json": 3, "vedurstodvar.json": 4, "yfirlit.json": 0}
# Hnit VR-II eru inntak (Nominatim), ekki mæling; þau fara óbreytt út.
OAFRUNNUD = {("vedurstodvar.json", "vidmidunarpunktur")}


def _fleytitolur(gildi, slod=()):
    if isinstance(gildi, float):
        yield slod, gildi
    elif isinstance(gildi, dict):
        for lykill, undir in gildi.items():
            yield from _fleytitolur(undir, (*slod, lykill))
    elif isinstance(gildi, list):
        for undir in gildi:
            yield from _fleytitolur(undir, slod)


def _bida_eftir_nyrri_sekundu() -> None:
    """Þvingar sekúndumörk: tvær keyrslur innan sömu sekúndu sanna ekkert (#47)."""
    upphaf = int(time.time())
    while int(time.time()) == upphaf:
        time.sleep(0.02)


class SnidProf(unittest.TestCase):
    def test_skrarnar_eru_thaer_sem_sidurnar_lesa(self) -> None:
        self.assertEqual(set(ug.baeti_moppu(ug.uttak())), ALLAR_SKRAR)
        for safn in flytja.SOFN:
            with self.subTest(skra=safn.skra):
                self.assertTrue((ROT / safn.sida).is_file(), safn.sida)

    def test_hver_skra_hefur_uppfaert_heimild_og_gogn(self) -> None:
        for heiti in ALLAR_SKRAR:
            with self.subTest(skra=heiti):
                skjal = ug.lesa(heiti)
                self.assertEqual(tuple(skjal), LYKLAR)
                self.assertIsInstance(skjal["heimild"], str)
                self.assertTrue(skjal["heimild"].strip())
                self.assertTrue(skjal["gogn"])
                stund = datetime.fromisoformat(skjal["uppfaert"])
                self.assertEqual(stund.utcoffset(), timedelta(0))
                self.assertEqual(stund.isoformat(), skjal["uppfaert"])

    def test_engin_skra_fyrir_central_perk_eda_tmdb(self) -> None:
        """Þau söfn eru ekki í grunninum; skrá fyrir þau kæmi úr annarri heimild."""
        for heiti in ALLAR_SKRAR:
            self.assertNotIn("central", heiti)
            self.assertNotIn("tmdb", heiti)

    def test_tolur_eru_namundadar_i_utflutningi(self) -> None:
        for heiti, aukastafir in AUKASTAFIR.items():
            for slod, tala in _fleytitolur(ug.lesa(heiti)):
                if (heiti, slod[1] if len(slod) > 1 else "") in OAFRUNNUD:
                    continue
                with self.subTest(skra=heiti, reitur="/".join(slod)):
                    self.assertEqual(tala, round(tala, aukastafir))

    def test_yfirlit_er_a_snidinu_sem_stada_gagna_js_les(self) -> None:
        """JS-ið telur ``gogn`` sem lista, skeytir ``heimild`` í texta og les ``uppfaert``."""
        yfirlit = ug.lesa(flytja.YFIRLIT)
        self.assertIsInstance(yfirlit["gogn"], list)
        self.assertEqual({f["skra"] for f in yfirlit["gogn"]}, SIDUSKRAR)
        for faersla in yfirlit["gogn"]:
            skjal = ug.lesa(faersla["skra"])
            self.assertEqual(faersla["uppfaert"], skjal["uppfaert"])
            self.assertEqual(faersla["heimild"], skjal["heimild"])
        self.assertEqual(yfirlit["uppfaert"], max(f["uppfaert"] for f in yfirlit["gogn"]))


class UppfaertProf(unittest.TestCase):
    """``uppfaert`` er gagnastimpill úr grunninum, ekki klukkan við útflutning."""

    def _grunngildi(self, sql: str) -> str:
        with sqlite3.connect(ug.grunnur()) as samband:
            return samband.execute(sql).fetchone()[0]

    def test_uppfaert_er_soknartimi_eda_reiknitimi_safnsins(self) -> None:
        vaent = {
            "hagstofan.json": self._grunngildi("SELECT fetched_at FROM hagstofan_datasets"),
            "vedurstodvar.json": self._grunngildi(
                "SELECT fetched_at FROM fetch_log WHERE service = 'vedurstofa-stodvar'"),
            "mbl.json": self._grunngildi("SELECT MAX(fetched_at) FROM mbl_snapshots"),
            "phoebe-tolfraedi.json": self._grunngildi(
                "SELECT analysis_generated_utc FROM friends_sources"),
        }
        for heiti, stimpill in vaent.items():
            with self.subTest(skra=heiti):
                self.assertEqual(
                    datetime.fromisoformat(ug.lesa(heiti)["uppfaert"]),
                    datetime.fromisoformat(stimpill).replace(microsecond=0),
                )

    def test_uppfaert_er_ekki_i_dag(self) -> None:
        """Bresta: væri klukkan notuð stæði dagurinn í dag í skránni."""
        i_dag = datetime.now().astimezone().date()
        for heiti in ALLAR_SKRAR:
            with self.subTest(skra=heiti):
                self.assertNotEqual(datetime.fromisoformat(ug.lesa(heiti)["uppfaert"]).date(), i_dag)


class AkvordunProf(unittest.TestCase):
    """Tveir útflutningar í röð gefa sömu bæti — líka yfir sekúndumörk."""

    def test_endurkeyrsla_yfir_sekundumork_gefur_somu_baeti(self) -> None:
        fyrri = ug.baeti_moppu(ug.uttak())
        _bida_eftir_nyrri_sekundu()
        seinni_mappa = ug.TMP / "endurkeyrsla"
        flytja.flytja_ut(ug.grunnur(), seinni_mappa)
        self.assertEqual(ug.baeti_moppu(seinni_mappa), fyrri)

    def test_endurbyggdur_grunnur_med_adra_hledsluklukku_gefur_somu_baeti(self) -> None:
        """Bresta: loaded_at er ólíkt í grunnunum tveimur, en má ekki ná í úttakið."""
        _bida_eftir_nyrri_sekundu()
        annar = ug.byggja_grunn(ug.TMP / "annar.sqlite")
        klukkur = [
            sqlite3.connect(slod).execute("SELECT loaded_at FROM friends_sources").fetchone()[0]
            for slod in (ug.grunnur(), annar)
        ]
        self.assertNotEqual(klukkur[0], klukkur[1], "prófið þvingaði ekki sekúndumörk")
        mappa = ug.TMP / "annar-grunnur"
        flytja.flytja_ut(annar, mappa)
        self.assertEqual(ug.baeti_moppu(mappa), ug.baeti_moppu(ug.uttak()))

    def test_skrarnar_i_git_eru_nyr_utflutningur(self) -> None:
        """web/gogn/ er afleiða (regla 5.4): handbreyting þar fellur á þessu prófi."""
        i_git = {h: b for h, b in ug.baeti_moppu(VEFGOGN).items() if h.endswith(".json")}
        self.assertEqual(i_git, ug.baeti_moppu(ug.uttak()))


class AtomiskSkrifProf(unittest.TestCase):
    """Falli eitthvað er engin skrá yfirskrifuð og engin tímabundin mappa eftir."""

    def setUp(self) -> None:
        self.mappa = ug.TMP / f"atom-{self.id().rsplit('.', 1)[-1]}"
        self.mappa.mkdir()
        for heiti in ALLAR_SKRAR:
            (self.mappa / heiti).write_bytes(b'{"gamalt": true}\n')
        self.fyrir = ug.baeti_moppu(self.mappa)

    def _ostodd(self) -> None:
        self.assertEqual(ug.baeti_moppu(self.mappa), self.fyrir)
        self.assertEqual([p for p in self.mappa.iterdir() if p.is_dir()], [])

    def test_safn_sem_fellur_skrifar_ekkert(self) -> None:
        def fellur(samband):
            raise UtflutningsVilla("gervivilla í miðju")
        sofn = list(flytja.SOFN)
        sofn[2] = flytja.Safn(sofn[2].skra, sofn[2].sida, sofn[2].fyrirspurnir, fellur)
        with self.assertRaisesRegex(UtflutningsVilla, sofn[2].skra):
            flytja.flytja_ut(ug.grunnur(), self.mappa, tuple(sofn))
        self._ostodd()

    def test_diskur_sem_fyllist_i_midjum_skrifum_skrifar_ekkert(self) -> None:
        raunverulegt = skrifa.os.fsync
        kollin = []

        def fyllist(fd):
            kollin.append(fd)
            if len(kollin) == 3:
                raise OSError(28, "No space left on device")
            raunverulegt(fd)

        with mock.patch.object(skrifa.os, "fsync", side_effect=fyllist):
            with self.assertRaises(OSError):
                flytja.flytja_ut(ug.grunnur(), self.mappa)
        self.assertEqual(len(kollin), 3)
        self._ostodd()

    def test_grunnur_sem_vantar_stodvar_skrefid_an_skrifa(self) -> None:
        vantar = ug.TMP / "ekki-til.sqlite"
        with self.assertRaisesRegex(SkrefVilla, "hlada"):
            flytja_allt(vantar, self.mappa)
        self.assertFalse(vantar.exists(), "útflutningurinn bjó til tóman grunn")
        self._ostodd()

    def test_heppnud_skrif_skilja_enga_timabundna_moppu_eftir(self) -> None:
        flytja.flytja_ut(ug.grunnur(), self.mappa)
        self.assertEqual(set(ug.baeti_moppu(self.mappa)), ALLAR_SKRAR)
        self.assertEqual([p for p in self.mappa.iterdir() if p.is_dir()], [])

    def test_oleyfilegt_skraarheiti_er_hafnad(self) -> None:
        for heiti in ("../utan.json", "undir/skra.json", "skra.txt"):
            with self.subTest(heiti=heiti), self.assertRaises(ValueError):
                skrifa.skrifa_allar({heiti: b"{}"}, self.mappa)
        self._ostodd()


class StaerdProf(unittest.TestCase):
    """Samantektir, ekki heilar töflur (#15, regla 3.4)."""

    def test_samtala_utflutningsins_er_undir_thakinu(self) -> None:
        staerdir = {h: len(b) for h, b in ug.baeti_moppu(ug.uttak()).items()}
        self.assertLessEqual(sum(staerdir.values()), HAMARK_BAETI, staerdir)

    def test_samtala_web_gogn_i_git_er_undir_thakinu(self) -> None:
        samtals = sum(p.stat().st_size for p in VEFGOGN.iterdir() if p.is_file())
        self.assertLessEqual(samtals, HAMARK_BAETI)


class EinstefnaProf(unittest.TestCase):
    """Útflutningurinn les grunninn eingöngu gegnum src/sql/queries/ (kafli 0)."""

    def test_utflutningur_les_hvorki_processed_ne_keyrir_eigid_sql(self) -> None:
        for skra in sorted(UTFLUTNINGSMAPPA.glob("*.py")):
            texti = skra.read_text(encoding="utf-8")
            with self.subTest(skra=skra.name):
                self.assertNotIn("processed", texti)
                kollin = [
                    h for h in ast.walk(ast.parse(texti))
                    if isinstance(h, ast.Call) and isinstance(h.func, ast.Attribute)
                    and h.func.attr in {"execute", "executemany", "executescript"}
                ]
                self.assertEqual(kollin, [], "SQL á að koma úr src/sql/queries/")

    def test_hvert_safn_telur_upp_fyrirspurnirnar_sem_thad_les(self) -> None:
        from gagnagrunnur.fyrirspurnir import FYRIRSPURNIR
        for safn in flytja.SOFN:
            with self.subTest(skra=safn.skra):
                self.assertTrue(safn.fyrirspurnir)
                self.assertLessEqual(set(safn.fyrirspurnir), FYRIRSPURNIR)


if __name__ == "__main__":
    unittest.main()
