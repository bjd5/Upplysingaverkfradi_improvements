"""Próf fyrir hleðslu stöðvaskrár Veðurstofunnar í grunninn (issue #8).

Prófin eru NETLAUS: þau hlaða frosna eintakinu í ``data/raw/vedurstodvar/`` í
tímabundinn grunn og spyrja hann. Eintakið er SHA-staðfest og breytist ekki,
svo fjöldatölurnar hér eru fastar staðreyndir **um það eintak** — ekki um
lifandi stöðu stöðvaskrár Veðurstofunnar. Frystingin er einmitt það sem gerir
þessar tölur prófanlegar: gamla verkefnið sótti listann upp á nýtt í hverri
byggingu og gat því ekki fest neina tölu.

Hrágögnin eru aldrei snert (regla 10) — prófin sem þurfa gallað eintak afrita
möppuna í tímabundna möppu og skemma afritið.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.fingrafar import fingrafar  # noqa: E402
from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from vinnsla import vedurstodvar_hledsla as hledsla  # noqa: E402
from vinnsla.vedurstodvar_hledsla import HledsluVilla  # noqa: E402

# Staðreyndir um frosna eintakið stations-20260924T112218Z.json.
FJOLDI_STODVA = 778
FJOLDI_VIRKRA = 343
FJOLDI_AFLAGDRA = FJOLDI_STODVA - FJOLDI_VIRKRA

TELJA_ALLAR = "SELECT COUNT(*) FROM weather_stations"
TELJA_VIRKAR = "SELECT COUNT(*) FROM weather_stations WHERE end_year IS NULL"
TELJA_AFLAGDAR = "SELECT COUNT(*) FROM weather_stations WHERE end_year IS NOT NULL"
TELJA_TOMSTRENG = "SELECT COUNT(*) FROM weather_stations WHERE end_year = ''"
TELJA_ADRAR_GERDIR = (
    "SELECT COUNT(*) FROM weather_stations "
    "WHERE typeof(end_year) NOT IN ('null', 'integer')"
)


def opna_med_toflum(mappa: Path):
    """Tómur grunnur með öllum migrations keyrðum."""
    samband = opna(mappa / "vedurstodvar.sqlite")
    keyra(samband)
    return samband


class HladidEintakProf(unittest.TestCase):
    """Frosna eintakið er hlaðið einu sinni og grunnurinn spurður."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.samband = opna_med_toflum(Path(cls._tmp.name))
        cls.nidurstada = hledsla.hlada(cls.samband)
        cls.samband.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()

    def telja(self, fyrirspurn: str) -> int:
        return int(self.samband.execute(fyrirspurn).fetchone()[0])

    # --- fjöldatölurnar -------------------------------------------------

    def test_allar_stodvar_komust_i_tofluna(self) -> None:
        self.assertEqual(self.telja(TELJA_ALLAR), FJOLDI_STODVA)

    def test_fjoldi_med_null_lokaar(self) -> None:
        """343 stöðvar eru enn starfræktar — sama tala og ``active=true`` skilaði."""
        self.assertEqual(self.telja(TELJA_VIRKAR), FJOLDI_VIRKRA)

    def test_fjoldi_aflagdra(self) -> None:
        self.assertEqual(self.telja(TELJA_AFLAGDAR), FJOLDI_AFLAGDRA)

    def test_virkar_og_aflagdar_telja_allar_stodvarnar(self) -> None:
        """Engin stöð dettur milli skilyrðanna tveggja."""
        self.assertEqual(
            self.telja(TELJA_VIRKAR) + self.telja(TELJA_AFLAGDAR), FJOLDI_STODVA
        )

    # --- NULL, ekki tómstrengur -----------------------------------------

    def test_ekkert_lokaar_er_tomstrengur(self) -> None:
        """``end_year = ''`` telur 0 — annars væri ``IS NULL`` ómarktækt skilyrði."""
        self.assertEqual(self.telja(TELJA_TOMSTRENG), 0)

    def test_lokaar_er_alltaf_null_eda_heiltala(self) -> None:
        self.assertEqual(self.telja(TELJA_ADRAR_GERDIR), 0)

    def test_stod_sem_maelir_enn_hefur_none_i_python(self) -> None:
        """Gildið sem kemur upp úr grunninum er ``None``, ekki tómstrengur."""
        rad = self.samband.execute(
            "SELECT end_year FROM weather_stations WHERE station_id = ?", (1469,)
        ).fetchone()
        self.assertIsNone(rad["end_year"])

    # --- yfirlitið og skráningin ----------------------------------------

    def test_nidurstada_segir_sama_og_taflan(self) -> None:
        self.assertEqual(self.nidurstada.fjoldi, FJOLDI_STODVA)
        self.assertEqual(self.nidurstada.virkar, FJOLDI_VIRKRA)
        self.assertEqual(self.nidurstada.aflagdar, FJOLDI_AFLAGDRA)

    def test_nidurstada_nefnir_eintakid_og_soknartimann(self) -> None:
        provenance = json.loads(
            (hledsla.FROSID / "provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.nidurstada.eintak, provenance["response_file"])
        self.assertEqual(self.nidurstada.sott_utc, provenance["fetched_at_utc"])

    def test_soknin_er_skrad_i_fetch_log(self) -> None:
        """Hver tala á sér rekjanlega leið aftur í hrágögnin (regla 8)."""
        radir = self.samband.execute(
            "SELECT service, endpoint, fetched_at, record_count, raw_file, notes "
            "FROM fetch_log WHERE service = ?",
            (hledsla.THJONUSTA,),
        ).fetchall()

        self.assertEqual(len(radir), 1)
        skraning = dict(radir[0])
        self.assertEqual(skraning["record_count"], FJOLDI_STODVA)
        self.assertIn("vedurstodvar", skraning["raw_file"])
        self.assertIn("api.vedur.is", skraning["endpoint"])
        self.assertIn("Frosið eintak", skraning["notes"])


class EndurkeyrsluProf(unittest.TestCase):
    """Sama eintak á að gefa sama grunn, hversu oft sem hlaðið er."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.samband = opna_med_toflum(Path(self._tmp.name))

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def test_tvaer_hledslur_gefa_sama_grunn(self) -> None:
        fyrri = hledsla.hlada(self.samband)
        seinni = hledsla.hlada(self.samband)

        self.assertEqual(fyrri, seinni)
        self.assertEqual(
            self.samband.execute(TELJA_ALLAR).fetchone()[0], FJOLDI_STODVA
        )

    def test_endurkeyrsla_breytir_ekki_fingrafari_grunnsins(self) -> None:
        """Fjöldatölur eru ekki nóg — fingrafarið mælir grunninn allan.

        ``fetch_log.id`` er AUTOINCREMENT, svo DELETE + INSERT gaf áður nýtt
        auðkenni í hverri keyrslu. Fjöldatölurnar stóðu í stað en fingrafarið
        hreyfðist, og þá mældi það hversu oft var hlaðið í stað þess hvað var
        hlaðið — grunnurinn var ekki lengur hrein afleiða (regla 5).
        """
        hledsla.hlada(self.samband)
        fyrra_fingrafar = fingrafar(self.samband)

        hledsla.hlada(self.samband)

        self.assertEqual(fingrafar(self.samband), fyrra_fingrafar)

    def test_endurkeyrsla_heldur_audkenni_sofnunarskraningarinnar(self) -> None:
        """Skráningin heldur auðkenninu sínu; annars vísar ekkert stöðugt í hana."""
        hledsla.hlada(self.samband)
        fyrra_audkenni = self.samband.execute(
            "SELECT id FROM fetch_log WHERE service = ?", (hledsla.THJONUSTA,)
        ).fetchone()[0]

        hledsla.hlada(self.samband)

        self.assertEqual(
            self.samband.execute(
                "SELECT id FROM fetch_log WHERE service = ?", (hledsla.THJONUSTA,)
            ).fetchone()[0],
            fyrra_audkenni,
        )

    def test_endurkeyrsla_safnar_ekki_upp_sofnunarsogu(self) -> None:
        hledsla.hlada(self.samband)
        hledsla.hlada(self.samband)

        fjoldi = self.samband.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE service = ?", (hledsla.THJONUSTA,)
        ).fetchone()[0]
        self.assertEqual(fjoldi, 1)

    def test_onnur_sofn_i_fetch_log_eru_osnert(self) -> None:
        """Hleðslan á sína eigin skráningu — ekki skráningar annarra safna."""
        self.samband.execute(
            "INSERT INTO fetch_log (service, endpoint, fetched_at, raw_file) "
            "VALUES (?, ?, ?, ?)",
            ("annad-safn", "https://example.is/api", "2026-09-01T00:00:00Z", "x.json"),
        )
        hledsla.hlada(self.samband)

        fjoldi = self.samband.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE service = ?", ("annad-safn",)
        ).fetchone()[0]
        self.assertEqual(fjoldi, 1)


class GallaAdEintakProf(unittest.TestCase):
    """Frávik stöðva hleðsluna — þau laumast ekki í grunninn (regla 6)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        # Afrit af frosnu möppunni; hrágögnin sjálf eru aldrei snert (regla 10).
        self.frosid = self.mappa / "vedurstodvar"
        shutil.copytree(hledsla.FROSID, self.frosid)
        self.samband = opna_med_toflum(self.mappa)

    def tearDown(self) -> None:
        self.samband.close()
        self._tmp.cleanup()

    def provenance(self) -> dict:
        return json.loads((self.frosid / "provenance.json").read_text(encoding="utf-8"))

    def skrifa_provenance(self, skjal: dict) -> None:
        (self.frosid / "provenance.json").write_text(
            json.dumps(skjal, ensure_ascii=False), encoding="utf-8"
        )

    def test_afritid_hledst_eins_og_frumritid(self) -> None:
        """Viðmið hinna prófanna: óbreytt afrit hleðst án athugasemda."""
        nidurstada = hledsla.hlada(self.samband, self.frosid)
        self.assertEqual(nidurstada.fjoldi, FJOLDI_STODVA)

    def test_breytt_eintak_stodvar_hledslu(self) -> None:
        """SHA-summan er eina vörnin gegn því að eintakið hafi breyst eftir frystingu."""
        skjal = self.provenance()
        slod = self.frosid / skjal["response_file"]
        stodvar = json.loads(slod.read_text(encoding="utf-8"))
        stodvar[0]["ending"] = 1999
        slod.write_text(json.dumps(stodvar, ensure_ascii=False), encoding="utf-8")

        with self.assertRaises(HledsluVilla) as samhengi:
            hledsla.hlada(self.samband, self.frosid)
        self.assertIn("provenance", str(samhengi.exception))
        self.assertEqual(self.samband.execute(TELJA_ALLAR).fetchone()[0], 0)

    def test_rangur_fjoldi_i_provenance_stodvar_hledslu(self) -> None:
        skjal = self.provenance()
        skjal["station_count"] = FJOLDI_STODVA - 1
        self.skrifa_provenance(skjal)

        with self.assertRaises(HledsluVilla) as samhengi:
            hledsla.hlada(self.samband, self.frosid)
        self.assertIn(str(FJOLDI_STODVA), str(samhengi.exception))

    def test_vantandi_provenance_stodvar_hledslu(self) -> None:
        (self.frosid / "provenance.json").unlink()

        with self.assertRaises(HledsluVilla) as samhengi:
            hledsla.hlada(self.samband, self.frosid)
        self.assertIn("regla 4", str(samhengi.exception))

    def test_vantandi_reitur_i_provenance_stodvar_hledslu(self) -> None:
        skjal = self.provenance()
        del skjal["sha256"]
        self.skrifa_provenance(skjal)

        with self.assertRaises(HledsluVilla) as samhengi:
            hledsla.hlada(self.samband, self.frosid)
        self.assertIn("sha256", str(samhengi.exception))

    def test_vantandi_eintak_stodvar_hledslu(self) -> None:
        skjal = self.provenance()
        (self.frosid / skjal["response_file"]).unlink()

        with self.assertRaises(HledsluVilla) as samhengi:
            hledsla.hlada(self.samband, self.frosid)
        self.assertIn(skjal["response_file"], str(samhengi.exception))


if __name__ == "__main__":
    unittest.main()
