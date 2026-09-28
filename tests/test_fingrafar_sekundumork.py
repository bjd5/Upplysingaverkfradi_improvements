"""Fingrafarið yfir þvinguð sekúndumörk — og næmni þess (issue #47).

Tvær hraðar byggingar í röð lenda oftast innan sömu sekúndu og stemma **af
tilviljun**, svo próf sem treystir á tímasetningu getur ekki séð villuna. Hér
er klukkan því þvinguð: bygging A fær stimpilinn ``…00:00:00`` og bygging B
``…00:00:01``. Sömu heimildir, sama skema, önnur sekúnda — sama fingrafar.

Byggingarnar hlaða raunverulegu frosnu gögnunum úr ``data/raw/`` (Hagstofan og
mbl), því það eru þær hleðslur sem skrifa ``loaded_at`` og ``extracted_at``.
Hrágögnin eru aðeins lesin; grunnarnir eru í tímabundinni möppu (regla 10).

Næmniprófin keyra á sömu hlöðnu grunnum: tól sem undanskilur of mikið er verra
en gagnslaust, svo breytt gagnagildi og breyttur fjöldi raða verða að breyta
summunni.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import logging
import sys
import tempfile
import unittest
from pathlib import Path
from sqlite3 import Connection
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

import vinnsla.hagstofan  # noqa: E402,F401  — hlaðið svo _nuna finnist
import vinnsla.mbl_hledsla  # noqa: E402,F401
from gagnagrunnur.fingrafar import _oruggt_nafn, fingrafar  # noqa: E402
from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna, tenging  # noqa: E402
from vinnsla.hagstofan import hlada as hlada_hagstofu  # noqa: E402
from vinnsla.mbl_hledsla import hlada_ollu as hlada_mbl  # noqa: E402

# Sekúnda skilur byggingarnar að — það sem tvær raunverulegar keyrslur gera
# um leið og þær eru ekki hraðari en klukkan.
STIMPILL_A = "2026-01-01T00:00:00+00:00"
STIMPILL_B = "2026-01-01T00:00:01+00:00"

# Einingarnar sem skrifa keyrslustimpla í dag. Prófið patchar HVERJA einingu
# pípunnar sem á `_nuna`, ekki aðeins þessar, svo ný hleðsla sé þvinguð líka;
# listinn er aðeins lágmarkið sem verður að finnast, annars prófar prófið ekkert.
KLUKKUEININGAR_LAGMARK = frozenset(
    {"gagnagrunnur.keyrari", "vinnsla.hagstofan", "vinnsla.mbl_hledsla"}
)
PAKKAR_PIPUNNAR = ("gagnagrunnur.", "vinnsla.")

# Keyrarinn og hleðslurnar skrá hvert skref; það er ekki það sem hér er mælt.
for _heiti in ("gagnagrunnur.keyrari", "vinnsla.hagstofan", "vinnsla.mbl_hledsla"):
    logging.getLogger(_heiti).setLevel(logging.ERROR)


def _klukkueiningar() -> list[str]:
    """Allar hlaðnar einingar pípunnar sem sækja tíma í eigið ``_nuna``."""
    return sorted(
        heiti
        for heiti, eining in list(sys.modules.items())
        if heiti.startswith(PAKKAR_PIPUNNAR) and callable(getattr(eining, "_nuna", None))
    )


def byggja(slod: Path, stimpill: str) -> None:
    """Hrein bygging: migrations, Hagstofan og mbl — með klukkuna fasta á ``stimpill``.

    Hver hleðsla fær eigin færslu, eins og í raunverulegri keyrslu.
    """
    with mock.patch.dict("os.environ", {"RANNSOKN_GRUNNUR": str(slod)}):
        with _fost_klukka(stimpill):
            with tenging(slod) as samband:
                keyra(samband)
            with tenging(slod) as samband:
                hlada_hagstofu(samband)
            with tenging(slod) as samband:
                hlada_mbl(samband)


class _fost_klukka:  # noqa: N801  — notað sem `with`, les eins og fall
    """Setur ``_nuna`` í öllum klukkueiningum pípunnar á fast gildi."""

    def __init__(self, stimpill: str) -> None:
        self._patchar = [
            mock.patch(f"{heiti}._nuna", lambda s=stimpill: s) for heiti in _klukkueiningar()
        ]

    def __enter__(self) -> None:
        for patch in self._patchar:
            patch.start()

    def __exit__(self, *_: object) -> None:
        for patch in reversed(self._patchar):
            patch.stop()


class SekundumorkProf(unittest.TestCase):
    """Tvær byggingar úr sömu heimildum, sekúnda á milli, eitt fingrafar."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        mappa = Path(cls._tmp.name)
        cls.slod_a = mappa / "a.sqlite"
        cls.slod_b = mappa / "b.sqlite"
        byggja(cls.slod_a, STIMPILL_A)
        byggja(cls.slod_b, STIMPILL_B)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _opna(self, slod: Path) -> Connection:
        samband = opna(slod)
        self.addCleanup(samband.close)
        return samband

    def test_klukkan_er_raunverulega_thvingud(self) -> None:
        """Án þessa gæti prófið hér á eftir staðist af því að ekkert var patchað."""
        vantar = KLUKKUEININGAR_LAGMARK - set(_klukkueiningar())
        self.assertFalse(vantar, f"Þessar einingar eiga að hafa _nuna: {sorted(vantar)}")
        a, b = self._opna(self.slod_a), self._opna(self.slod_b)
        for tafla, dalkur in (
            ("schema_migrations", "applied_at"),
            ("hagstofan_datasets", "loaded_at"),
            ("mbl_snapshots", "loaded_at"),
            ("mbl_extractions", "extracted_at"),
        ):
            with self.subTest(tafla=tafla, dalkur=dalkur):
                # Auðkenni fara í gegnum hvítlistann eins og í fingrafar.py (regla 5).
                sql = f"SELECT DISTINCT {_oruggt_nafn(dalkur)} FROM {_oruggt_nafn(tafla)}"
                self.assertEqual([r[0] for r in a.execute(sql)], [STIMPILL_A])
                self.assertEqual([r[0] for r in b.execute(sql)], [STIMPILL_B])

    def test_sekunda_a_milli_gefur_sama_fingrafar(self) -> None:
        """Kjarni #47 — féll á main: fingrafarið mældi hvenær, ekki hvað."""
        a, b = self._opna(self.slod_a), self._opna(self.slod_b)
        self.assertEqual(
            fingrafar(a),
            fingrafar(b),
            "Tvær byggingar úr sömu heimildum með sekúndu á milli gefa sitt hvort "
            "fingrafar. Keyrslustimpill telur með í summunni — sjá REGLAN í "
            "gagnagrunnur/fingrafar.py.",
        )


class NaemniProf(unittest.TestCase):
    """Á hlöðnum grunni: raunveruleg breyting á gögnum breytir summunni."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        slod = Path(self._tmp.name) / "grunnur.sqlite"
        byggja(slod, STIMPILL_A)
        self.samband = opna(slod)
        self.addCleanup(self.samband.close)
        self.fyrir = fingrafar(self.samband)

    def _breyta(self, sql: str) -> None:
        bendill = self.samband.execute(sql)
        self.assertGreater(bendill.rowcount, 0, "Breytingin snerti enga línu.")
        self.samband.commit()

    def test_breytt_hagstofugildi_breytir_fingrafari(self) -> None:
        self._breyta(
            "UPDATE hagstofan_observations SET value = value + 1 "
            "WHERE rowid = (SELECT min(rowid) FROM hagstofan_observations "
            "WHERE value IS NOT NULL)"
        )
        self.assertNotEqual(fingrafar(self.samband), self.fyrir)

    def test_breytt_mbl_gildi_breytir_fingrafari(self) -> None:
        self._breyta(
            "UPDATE mbl_extractions SET match_count = match_count + 1 "
            "WHERE rowid = (SELECT min(rowid) FROM mbl_extractions)"
        )
        self.assertNotEqual(fingrafar(self.samband), self.fyrir)

    def test_faerri_linur_breyta_fingrafari(self) -> None:
        self._breyta(
            "DELETE FROM hagstofan_observations "
            "WHERE rowid = (SELECT max(rowid) FROM hagstofan_observations)"
        )
        self.assertNotEqual(fingrafar(self.samband), self.fyrir)

    def test_breyttur_sotttimi_breytir_fingrafari(self) -> None:
        """fetched_at er eiginleiki gagnanna (lesinn úr provenance) og telur með."""
        self._breyta(
            "UPDATE hagstofan_datasets SET fetched_at = '1999-01-01T00:00:00+00:00'"
        )
        self.assertNotEqual(fingrafar(self.samband), self.fyrir)


if __name__ == "__main__":
    unittest.main()
