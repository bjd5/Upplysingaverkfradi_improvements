"""Próf fyrir hleðslu Hagstofugagnanna í grunninn (issue #7, migration 003).

Prófin eru NETLAUS: þau lesa frystu skrárnar í ``data/raw/hagstofan/`` og byggja
grunninn í tímabundinni möppu. Hrágögnunum er aldrei breytt — þegar próf þarf
gölluð gögn afritar það skrárnar fyrst og skemmir afritið (regla 10).

Kjarninn sem hér er festur:

* grunnurinn geymir **36** mælingar,
* 36 er nákvæmlega margfeldi víddastærðanna ``[1, 1, 3, 1, 4, 3]``,
* víddaheitin sjálf eru í grunninum, ekki aðeins kóðarnir,
* **stemmi fjöldi gilda ekki við margfeldið stöðvast keyrslan** og ekkert
  ratar í grunninn (regla 6 — hálf tafla er verri en engin).

Allar tölur eru lesnar úr grunninum með SQL, ekki endurreiknaðar í Python.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna, tenging  # noqa: E402
from vinnsla.hagstofan import HRAGOGN, hlada  # noqa: E402
from vinnsla.hagstofan_sannreyning import sannreyna_gildafjolda  # noqa: E402
from vinnsla.hagstofan_snid import (  # noqa: E402
    SVARSKRA,
    UPPRUNASKRA,
    JsonstatVilla,
    Vidd,
)

# Töfluauðkennið er leitt af endapunktinum í provenance.json.
AUDKENNI = "SKO04208b"

# Staðfest úr data/raw/hagstofan/response.json: `size` og lengd `value`.
VAENT_STAERDIR = [1, 1, 3, 1, 4, 3]
VAENTAR_MAELINGAR = 36

# Víddirnar sex í röð `id`, með heiti sem valdir kóðar þeirra bera.
VAENTAR_VIDDIR = [
    "Innritunarár",
    "Tími",
    "Nemendur",
    "Fjöldi/Hlutfall",
    "Námssvið",
    "Kyn",
]

# Heiti — ekki kóðar — sem verða að vera læsileg upp úr grunninum.
VAENT_HEITI = {
    ("Nemendur", "5"): "Brautskráðir alls",
    ("Nemendur", "6"): "Brottfallnir",
    ("Nemendur", "7"): "Enn í námi",
    ("Námssvið", "07"): "Verkfræði, framleiðsla og mannvirkjagerð",
    ("Kyn", "2"): "Konur",
    ("Tími", "n+3"): "Sex árum eftir innritun",
}

SQL_FJOLDI = "SELECT COUNT(*) FROM hagstofan_observations WHERE dataset_id = ?"
SQL_STAERDIR = (
    "SELECT size FROM hagstofan_dimensions WHERE dataset_id = ? ORDER BY position"
)
SQL_VIDDAHEITI = (
    "SELECT code, label FROM hagstofan_dimensions WHERE dataset_id = ? "
    "ORDER BY position"
)
SQL_GILDISHEITI = (
    "SELECT label FROM hagstofan_dimension_values "
    "WHERE dataset_id = ? AND dimension_code = ? AND code = ?"
)
SQL_SKRAD_FJOLDI = "SELECT value_count FROM hagstofan_datasets WHERE id = ?"


def byggja_grunn(slod: Path, mappa: Path | None = None) -> None:
    """Keyrir migrations á tóman grunn og hleður Hagstofugögnunum í hann."""
    with tenging(slod) as samband:
        keyra(samband)
    with tenging(slod) as samband:
        hlada(samband, mappa)


def afrita_hragogn(mark: Path) -> Path:
    """Afritar frystu skrárnar svo próf geti skemmt afritið en ekki frumritið."""
    shutil.copytree(HRAGOGN, mark)
    return mark


def sleppa_einu_gildi(mappa: Path) -> None:
    """Fjarlægir eitt gildi úr ``value`` svo fjöldinn stemmi ekki við margfeldið."""
    slod = mappa / SVARSKRA
    svar = json.loads(slod.read_text(encoding="utf-8"))
    svar["value"] = svar["value"][:-1]
    slod.write_text(json.dumps(svar, ensure_ascii=False), encoding="utf-8")


def uppfaera_summu(mappa: Path, skraarheiti: str) -> None:
    """Skráir nýja SHA-256 í afritið svo gátsummuvörnin fari ekki af stað fyrst."""
    slod = mappa / UPPRUNASKRA
    upprunagogn = json.loads(slod.read_text(encoding="utf-8"))
    upprunagogn["sha256"][skraarheiti] = hashlib.sha256(
        (mappa / skraarheiti).read_bytes()
    ).hexdigest()
    slod.write_text(
        json.dumps(upprunagogn, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class HledsluProf(unittest.TestCase):
    """Grunnurinn er byggður einu sinni fyrir klasann — hleðslan er afleiða."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.slod = Path(cls._tmp.name) / "rannsokn.sqlite"
        byggja_grunn(cls.slod)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self.samband = opna(self.slod)
        self.addCleanup(self.samband.close)

    def test_fjoldi_maelinga_i_grunninum_er_36(self) -> None:
        fjoldi = self.samband.execute(SQL_FJOLDI, (AUDKENNI,)).fetchone()[0]
        self.assertEqual(fjoldi, VAENTAR_MAELINGAR)

    def test_36_er_margfeldi_viddastaerdanna_i_grunninum(self) -> None:
        """Talan á að vera afleiða víddanna, ekki tilviljun — bæði úr grunninum."""
        staerdir = [rad[0] for rad in self.samband.execute(SQL_STAERDIR, (AUDKENNI,))]
        fjoldi = self.samband.execute(SQL_FJOLDI, (AUDKENNI,)).fetchone()[0]

        self.assertEqual(staerdir, VAENT_STAERDIR)
        self.assertEqual(math.prod(staerdir), VAENTAR_MAELINGAR)
        self.assertEqual(fjoldi, math.prod(staerdir))

    def test_skradur_gildafjoldi_stemmir_vid_toflunna(self) -> None:
        skrad = self.samband.execute(SQL_SKRAD_FJOLDI, (AUDKENNI,)).fetchone()[0]
        fjoldi = self.samband.execute(SQL_FJOLDI, (AUDKENNI,)).fetchone()[0]
        self.assertEqual(skrad, fjoldi)

    def test_viddirnar_eru_i_rod_id_med_heiti(self) -> None:
        radir = list(self.samband.execute(SQL_VIDDAHEITI, (AUDKENNI,)))
        self.assertEqual([rad["code"] for rad in radir], VAENTAR_VIDDIR)
        for rad in radir:
            self.assertTrue(rad["label"], f"Víddin {rad['code']} er heitislaus")

    def test_viddaheitin_sjalf_eru_i_grunninum(self) -> None:
        """Kóðinn `5` segir engum neitt; `Brautskráðir alls` gerir það."""
        for (vidd, kodi), vaent in VAENT_HEITI.items():
            with self.subTest(vidd=vidd, kodi=kodi):
                rad = self.samband.execute(
                    SQL_GILDISHEITI, (AUDKENNI, vidd, kodi)
                ).fetchone()
                self.assertIsNotNone(rad, f"{vidd}/{kodi} vantar í kóðabókina")
                self.assertEqual(rad["label"], vaent)

    def test_okvaldir_kodar_eru_lika_i_kodabokinni(self) -> None:
        """Án þeirra sést ekki hvaða sneið af töflunni frysta fyrirspurnin tók."""
        rad = self.samband.execute(
            SQL_GILDISHEITI, (AUDKENNI, "Innritunarár", "2014")
        ).fetchone()
        self.assertEqual(rad["label"], "2014")

        valid = self.samband.execute(
            "SELECT selected, value_index FROM hagstofan_dimension_values "
            "WHERE dataset_id = ? AND dimension_code = ? AND code = ?",
            (AUDKENNI, "Innritunarár", "2014"),
        ).fetchone()
        self.assertEqual(valid["selected"], 0)
        self.assertIsNone(valid["value_index"])

    def test_endurkeyrsla_gefur_sama_fjolda(self) -> None:
        """Hleðslan er endurkeyranleg: grunnurinn verður sá sami, ekki tvöfaldur."""
        with tenging(self.slod) as samband:
            hlada(samband)
        fjoldi = self.samband.execute(SQL_FJOLDI, (AUDKENNI,)).fetchone()[0]
        self.assertEqual(fjoldi, VAENTAR_MAELINGAR)


class StodvunarProf(unittest.TestCase):
    """Gögn sem stemma ekki mega aldrei rata inn — hálf tafla er verri en engin."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.slod = self.tmp / "rannsokn.sqlite"

    def _tom_grunnur(self) -> None:
        with tenging(self.slod) as samband:
            keyra(samband)

    def _skemmd_hragogn(self) -> Path:
        mappa = afrita_hragogn(self.tmp / "hragogn")
        sleppa_einu_gildi(mappa)
        uppfaera_summu(mappa, SVARSKRA)
        return mappa

    def test_hledsla_stodvast_vikji_gildafjoldi_fra_margfeldinu(self) -> None:
        self._tom_grunnur()
        mappa = self._skemmd_hragogn()

        with self.assertRaises(JsonstatVilla) as samhengi:
            with tenging(self.slod) as samband:
                hlada(samband, mappa)

        skilabod = str(samhengi.exception)
        self.assertIn("35", skilabod)
        self.assertIn(str(VAENTAR_MAELINGAR), skilabod)

    def test_ekkert_ratar_i_grunninn_thegar_hledslan_stodvast(self) -> None:
        self._tom_grunnur()
        mappa = self._skemmd_hragogn()

        with self.assertRaises(JsonstatVilla):
            with tenging(self.slod) as samband:
                hlada(samband, mappa)

        samband = opna(self.slod)
        self.addCleanup(samband.close)
        fjoldi = samband.execute(SQL_FJOLDI, (AUDKENNI,)).fetchone()[0]
        self.assertEqual(fjoldi, 0)

    def test_fyrri_hledsla_stendur_oskert_eftir_misheppnada_tilraun(self) -> None:
        """Allt eða ekkert: misheppnuð hleðsla má hvorki bæta við né eyða."""
        byggja_grunn(self.slod)
        mappa = self._skemmd_hragogn()

        with self.assertRaises(JsonstatVilla):
            with tenging(self.slod) as samband:
                hlada(samband, mappa)

        samband = opna(self.slod)
        self.addCleanup(samband.close)
        fjoldi = samband.execute(SQL_FJOLDI, (AUDKENNI,)).fetchone()[0]
        self.assertEqual(fjoldi, VAENTAR_MAELINGAR)

    def test_breytt_hragogn_stodva_hledsluna(self) -> None:
        """Gátsumman ver frystu gögnin (regla 4) — án hennar væri breytingin þögul."""
        self._tom_grunnur()
        mappa = afrita_hragogn(self.tmp / "hragogn")
        sleppa_einu_gildi(mappa)  # ENGIN uppfærsla á provenance.json

        with self.assertRaises(JsonstatVilla) as samhengi:
            with tenging(self.slod) as samband:
                hlada(samband, mappa)

        self.assertIn("breyst frá frystingu", str(samhengi.exception))


class GildafjoldaProf(unittest.TestCase):
    """Sannreyningin sjálf, án gagnagrunns."""

    @staticmethod
    def _vidd(kodi: str, staerd: int) -> Vidd:
        return Vidd(
            kodi=kodi, heiti=kodi, rod=0, staerd=staerd, er_timi=False, gildi=()
        )

    def _viddir(self) -> tuple[Vidd, ...]:
        return tuple(
            self._vidd(f"v{rod}", staerd)
            for rod, staerd in enumerate(VAENT_STAERDIR)
        )

    def test_rett_margfeldi_sleppur_i_gegn(self) -> None:
        sannreyna_gildafjolda(VAENTAR_MAELINGAR, self._viddir())

    def test_of_faa_gildi_stodva(self) -> None:
        with self.assertRaises(JsonstatVilla):
            sannreyna_gildafjolda(VAENTAR_MAELINGAR - 1, self._viddir())

    def test_of_morg_gildi_stodva(self) -> None:
        with self.assertRaises(JsonstatVilla):
            sannreyna_gildafjolda(VAENTAR_MAELINGAR + 1, self._viddir())

    def test_villan_nefnir_bada_fjoldana(self) -> None:
        """Villuboð sem segja ekki hvað stemmdi ekki eru gagnslaus (regla 6)."""
        with self.assertRaises(JsonstatVilla) as samhengi:
            sannreyna_gildafjolda(30, self._viddir())
        skilabod = str(samhengi.exception)
        self.assertIn("30", skilabod)
        self.assertIn(str(VAENTAR_MAELINGAR), skilabod)


if __name__ == "__main__":
    unittest.main()
