"""Próf fyrir æfingasíurnar sem SQL á ``weather_stations`` (issue #8).

Skilyrði #8 fyrir verklokum er að **svörin við spurningum æfingarinnar fáist úr
SQL-fyrirspurnum** — ekki úr Python-útreikningi ofan á töfluna og ekki úr nýrri
beiðni til þjónustunnar. Þessi próf hlaða frosna eintakinu í tímabundinn grunn
og spyrja hann sömu fimm spurninga sem gamla síðan sendi
``api.vedur.is/weather/stations``.

Væntu tölurnar eru **lesnar úr frosna viðmiðinu** í
``docs/vidmid/generated/vedurstofa-siur.md`` með ``lesa_vidmid_siur()``, ekki
slegnar inn hér. Tala sem er slegin inn á tveimur stöðum fer fyrr eða síðar á
skjön, og þá mælir prófið innsláttinn en ekki gögnin.

Prófin eru NETLAUS og snerta hvorki ``data/raw/`` né ``web/gogn/`` (regla 10).

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.keyrari import keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from vinnsla import vedurstodvar_fyrirspurnir as spurn  # noqa: E402
from vinnsla import vedurstodvar_samanburdur as sam  # noqa: E402
from vinnsla import vedurstodvar_hledsla as hledsla  # noqa: E402
from vinnsla.vedurstodvar_fyrirspurnir import FyrirspurnaVilla  # noqa: E402

# Heiti síutalnanna eins og viðmiðstaflan skrifar þau.
VIDMID_ENGIN_SIA = "engin sía"
VIDMID_VIRKAR = "`active=true`"
VIDMID_KASSI = "`polygon`"
VIDMID_KASSI_VIRKAR = "`polygon` + `active=true`"
VIDMID_AUDKENNI = f"`station_id={sam.VALIN_STOD}`"

# Fyrirspurnirnar sem þessi pakki tekur að sér. #11 (P1.7) safnar
# fyrirspurnum hinna gagnasafnanna og á ekki að endurgera þessar.
VAENTAR_FYRIRSPURNIR = frozenset(
    {
        "allar_stodvar",
        "fjoldi_stodva",
        "stod_eftir_audkenni",
        "virkar_stodvar",
        "fjoldi_virkra",
        "stodvar_i_marghyrningi",
        "virkar_stodvar_i_marghyrningi",
        "naesta_virka_stod",
        "naesta_aflagda_stod",
        "naesta_virka_langtimastod",
    }
)


class FyrirspurnasafnProf(unittest.TestCase):
    """Skráin sjálf: heitin, breyturnar og að ekkert gildi sé límt í SQL."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.safn = spurn.lesa_fyrirspurnir()

    def test_allar_vaentar_fyrirspurnir_eru_i_skranni(self) -> None:
        self.assertEqual(set(self.safn), set(VAENTAR_FYRIRSPURNIR))

    def test_hver_fyrirspurn_er_otom(self) -> None:
        for heiti, sql in self.safn.items():
            with self.subTest(fyrirspurn=heiti):
                self.assertTrue(sql.strip(), f"{heiti} er tóm")

    def test_engin_fyrirspurn_notar_strengjasamsetningu(self) -> None:
        """Regla 5: gildi fara inn sem ``?``, aldrei sem innsett texti.

        Staðgenglar Python-sniðmáta (``%s``, ``{}``, f-strengur) í .sql-skrá
        eru merki um að einhver hafi ætlað að setja gildi inn í fyrirspurnina
        áður en hún er keyrð.
        """
        for heiti, sql in self.safn.items():
            with self.subTest(fyrirspurn=heiti):
                self.assertNotIn("%s", sql)
                self.assertNotIn("{", sql)
                self.assertNotIn("f'", sql)
                self.assertNotIn('f"', sql)

    def test_hver_fyrirspurn_ber_athugasemd_um_hvad_hun_svarar(self) -> None:
        for heiti, sql in self.safn.items():
            with self.subTest(fyrirspurn=heiti):
                self.assertTrue(
                    any(lina.strip().startswith("--") for lina in sql.splitlines()),
                    f"{heiti} hefur enga athugasemd um hvað hún svarar",
                )

    def test_tvitekid_heiti_stodvar_lestur(self) -> None:
        """Tvær fyrirspurnir með sama heiti — önnur myndi annars horfa þegjandi."""
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "tvitekid.sql"
            slod.write_text(
                "-- @fyrirspurn: sama\nSELECT 1;\n\n-- @fyrirspurn: sama\nSELECT 2;\n",
                encoding="utf-8",
            )
            with self.assertRaises(FyrirspurnaVilla) as samhengi:
                spurn.lesa_fyrirspurnir(slod)
        self.assertIn("sama", str(samhengi.exception))

    def test_skra_an_merkja_stodvar_lestur(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            slod = Path(mappa) / "merkjalaus.sql"
            slod.write_text("SELECT 1;\n", encoding="utf-8")
            with self.assertRaises(FyrirspurnaVilla):
                spurn.lesa_fyrirspurnir(slod)

    def test_vantandi_skra_stodvar_lestur(self) -> None:
        with tempfile.TemporaryDirectory() as mappa:
            with self.assertRaises(FyrirspurnaVilla):
                spurn.lesa_fyrirspurnir(Path(mappa) / "ekki-til.sql")

    def test_okunn_fyrirspurn_gefur_skyra_villu(self) -> None:
        with self.assertRaises(FyrirspurnaVilla) as samhengi:
            spurn.fyrirspurn("engin_slik_fyrirspurn")
        self.assertIn("engin_slik_fyrirspurn", str(samhengi.exception))


class HladinnGrunnurProf(unittest.TestCase):
    """Grunnur með frosna eintakinu, byggður einu sinni fyrir alla undirklasa."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.samband = opna(Path(cls._tmp.name) / "vedurstodvar.sqlite")
        keyra(cls.samband)
        hledsla.hlada(cls.samband)
        cls.samband.commit()
        spurn.skra_fjarlaegdarfall(cls.samband)
        cls.vidmid = sam.lesa_vidmid_siur()
        cls.mork = sam.kassi(sam.VR_II_BREIDD, sam.VR_II_LENGD, sam.RADIUS_KM)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.samband.close()
        cls._tmp.cleanup()


class SiurUrSqlProf(HladinnGrunnurProf):
    """Fimm beiðnir gömlu síðunnar, framkvæmdar sem fyrirspurnir á töflunni."""

    def test_engin_sia_gefur_sama_fjolda_og_vidmidid(self) -> None:
        self.assertEqual(
            spurn.fjoldi_stodva(self.samband), self.vidmid[VIDMID_ENGIN_SIA]
        )

    def test_fjoldi_stodva_stemmir_vid_radirnar_sjalfar(self) -> None:
        """COUNT og listinn verða að segja sömu sögu."""
        self.assertEqual(
            spurn.fjoldi_stodva(self.samband), len(spurn.allar_stodvar(self.samband))
        )

    def test_active_true_gefur_sama_fjolda_og_vidmidid(self) -> None:
        """``active=true`` er ``end_year IS NULL`` — 343 stöðvar í eintakinu."""
        self.assertEqual(
            spurn.fjoldi_virkra(self.samband), self.vidmid[VIDMID_VIRKAR]
        )

    def test_virkar_stodvar_hafa_allar_null_lokaar(self) -> None:
        radir = spurn.virkar_stodvar(self.samband)
        self.assertEqual(len(radir), self.vidmid[VIDMID_VIRKAR])
        self.assertTrue(all(rad["end_year"] is None for rad in radir))

    def test_polygon_gefur_sama_fjolda_og_vidmidid(self) -> None:
        self.assertEqual(
            len(spurn.stodvar_i_marghyrningi(self.samband, self.mork)),
            self.vidmid[VIDMID_KASSI],
        )

    def test_polygon_og_active_gefa_sama_fjolda_og_vidmidid(self) -> None:
        self.assertEqual(
            len(spurn.virkar_stodvar_i_marghyrningi(self.samband, self.mork)),
            self.vidmid[VIDMID_KASSI_VIRKAR],
        )

    def test_kassinn_siar_baedi_breidd_og_lengd(self) -> None:
        """Mörkin mega ekki víxlast: allar stöðvar í svarinu liggja í kassanum."""
        min_lengd, min_breidd, max_lengd, max_breidd = self.mork
        for rad in spurn.stodvar_i_marghyrningi(self.samband, self.mork):
            with self.subTest(stod=rad["station_id"]):
                self.assertGreaterEqual(rad["lat"], min_breidd)
                self.assertLessEqual(rad["lat"], max_breidd)
                self.assertGreaterEqual(rad["lon"], min_lengd)
                self.assertLessEqual(rad["lon"], max_lengd)

    def test_virkar_i_kassa_eru_hlutmengi_theirra_i_kassanum(self) -> None:
        i_kassa = {rad["station_id"] for rad in spurn.stodvar_i_marghyrningi(self.samband, self.mork)}
        virkar = {
            rad["station_id"]
            for rad in spurn.virkar_stodvar_i_marghyrningi(self.samband, self.mork)
        }
        self.assertTrue(virkar <= i_kassa)

    def test_station_id_gefur_eina_stod(self) -> None:
        rad = spurn.stod_eftir_audkenni(self.samband, sam.VALIN_STOD)
        self.assertIsNotNone(rad)
        self.assertEqual(rad["station_id"], sam.VALIN_STOD)
        self.assertEqual(self.vidmid[VIDMID_AUDKENNI], 1)

    def test_okunnugt_audkenni_gefur_none_en_ekki_villu(self) -> None:
        self.assertIsNone(spurn.stod_eftir_audkenni(self.samband, -1))

    def test_audkenni_fer_inn_sem_breyta_ekki_sem_sql(self) -> None:
        """Texti í breytu er gildi, ekki SQL: taflan stendur eftir óhreyfð.

        Þetta er reglan 5 mæld en ekki ályktuð — færi gildið inn með
        strengjasamsetningu myndi ``DROP TABLE`` hér eyða töflunni.
        """
        self.assertIsNone(
            spurn.stod_eftir_audkenni(self.samband, "1469; DROP TABLE weather_stations")
        )
        self.assertEqual(
            spurn.fjoldi_stodva(self.samband), self.vidmid[VIDMID_ENGIN_SIA]
        )


class StodvavalUrSqlProf(HladinnGrunnurProf):
    """Þrjú stöðvaval æfingarinnar, röðuð eftir fjarlægð inni í SQL."""

    def vidmidssvar(self, heiti: str) -> tuple[int, str, int]:
        return sam.VIDMID_SVOR[heiti]

    def test_naesta_virka_stod_er_su_sem_vidmidid_valdi(self) -> None:
        audkenni, nafn, metrar = self.vidmidssvar("naesta")
        rad = spurn.naesta_virka_stod(self.samband, sam.VR_II_BREIDD, sam.VR_II_LENGD)
        self.assertEqual(rad["station_id"], audkenni)
        self.assertEqual(rad["name"], nafn)
        self.assertEqual(rad["metrar"], metrar)
        self.assertIsNone(rad["end_year"])

    def test_naesta_aflagda_stod_er_su_sem_vidmidid_valdi(self) -> None:
        audkenni, nafn, metrar = self.vidmidssvar("naesta_aflogd")
        rad = spurn.naesta_aflagda_stod(self.samband, sam.VR_II_BREIDD, sam.VR_II_LENGD)
        self.assertEqual(rad["station_id"], audkenni)
        self.assertEqual(rad["name"], nafn)
        self.assertEqual(rad["metrar"], metrar)
        self.assertIsNotNone(rad["end_year"])

    def test_langtimastod_er_su_sem_vidmidid_valdi(self) -> None:
        audkenni, nafn, metrar = self.vidmidssvar("langtimastod")
        rad = spurn.naesta_virka_langtimastod(
            self.samband,
            sam.VR_II_BREIDD,
            sam.VR_II_LENGD,
            sam.VIDMIDSAR - sam.AR_AFTUR_I_TIMANN,
        )
        self.assertEqual(rad["station_id"], audkenni)
        self.assertEqual(rad["name"], nafn)
        self.assertEqual(rad["metrar"], metrar)

    def test_langtimastod_er_fjaer_en_naesta_virka(self) -> None:
        """Nálægð og samfelld tímaröð eru tvö ólík skilyrði (takmörkun í skjalinu)."""
        naesta = spurn.naesta_virka_stod(self.samband, sam.VR_II_BREIDD, sam.VR_II_LENGD)
        langtima = spurn.naesta_virka_langtimastod(
            self.samband,
            sam.VR_II_BREIDD,
            sam.VR_II_LENGD,
            sam.VIDMIDSAR - sam.AR_AFTUR_I_TIMANN,
        )
        self.assertGreater(langtima["metrar"], naesta["metrar"])

    def test_fjarlaegdarfallid_verdur_ad_vera_skrad(self) -> None:
        """Án fallsins fellur fyrirspurnin — hún skilar ekki röðun í kyrrþey."""
        with tempfile.TemporaryDirectory() as mappa:
            samband = opna(Path(mappa) / "an-falls.sqlite")
            try:
                keyra(samband)
                with self.assertRaises(sqlite3.OperationalError):
                    spurn.naesta_virka_stod(samband, sam.VR_II_BREIDD, sam.VR_II_LENGD)
            finally:
                samband.close()


if __name__ == "__main__":
    unittest.main()
