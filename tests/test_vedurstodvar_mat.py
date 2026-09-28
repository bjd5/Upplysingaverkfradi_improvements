"""Próf fyrir mat á nothæfi veðurstöðva á gervigögnum (issue #14, pakki P2.4).

Stöðvarnar eru settar beint norður af VR-II. Á lengdarbaug er stórbaugsfjarlægð
nákvæmlega ``R · Δbreidd``, svo hver stöð fær þekkta fjarlægð og hægt er að
smíða tilvik sem greina á milli réttrar og rangrar útfærslu — til dæmis
rúnnunar á undan eða eftir frádrætti.

Hvert skilyrði er prófað þar sem það á að BRESTA, ekki aðeins þar sem það
heldur: staðfesting sem getur stemmt af tilviljun er ekki staðfesting
(``docs/agenta-verkefni.md``, kafli 6).

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import math
import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from vinnsla.vedurstodvar_faersla import Stod  # noqa: E402
from vinnsla.vedurstodvar_mat import (  # noqa: E402
    MatVilla,
    hlutfall_prosent,
    meta,
    rada_eftir_fjarlaegd,
)
from vinnsla.vedurstodvar_samanburdur import (  # noqa: E402
    JORD_RADIUS_KM,
    RADIUS_KM,
    VR_II_BREIDD,
    VR_II_LENGD,
    kassi,
)

VIDMIDUNARAR = 1976


def _stod(audkenni: int, km_nordur: float, start: int = 2000, lok: int | None = None) -> Stod:
    """Gervistöð ``km_nordur`` km beint norður af VR-II."""
    return Stod(
        station_id=audkenni,
        name=f"Stöð {audkenni}",
        abbr=f"S{audkenni}",
        station_type="sjálfvirk",
        lat=VR_II_BREIDD + math.degrees(km_nordur / JORD_RADIUS_KM),
        lon=VR_II_LENGD,
        elevation_m=10.0,
        wigos_id=None,
        owner=None,
        start_year=start,
        end_year=lok,
    )


class Rodun(unittest.TestCase):
    def test_fjarlaegdin_er_su_sem_stodin_var_sett_i(self) -> None:
        [stod] = rada_eftir_fjarlaegd([_stod(1, 1.2345)], VR_II_BREIDD, VR_II_LENGD)
        self.assertAlmostEqual(stod.km, 1.2345, places=9)
        self.assertEqual(stod.metrar, 1235)

    def test_radad_a_orunnadri_fjarlaegd(self) -> None:
        # Báðar rúnnast í 900 m. Röðun á rúnnuðum metrum héldi röð inntaksins
        # (stöðug röðun) og setti 1 fyrst — röng stöð.
        stodvar = [_stod(1, 0.9004), _stod(2, 0.9001)]
        radad = rada_eftir_fjarlaegd(stodvar, VR_II_BREIDD, VR_II_LENGD)
        self.assertEqual([s.metrar for s in radad], [900, 900])
        self.assertEqual([s.station_id for s in radad], [2, 1])


class ValStodvar(unittest.TestCase):
    def test_naesta_aflogd_er_ekki_valin(self) -> None:
        mat = meta([_stod(1, 0.6, lok=1963), _stod(2, 0.7)], vidmidunarar=VIDMIDUNARAR)
        self.assertEqual(mat.naesta.station_id, 1)
        self.assertFalse(mat.naesta.er_virk)
        self.assertEqual(mat.valin.station_id, 2)

    def test_munurinn_er_runnadur_eftir_fradratt(self) -> None:
        # 600,4 m og 650,6 m: rétt er round(50,2) = 50, en 651 − 600 = 51.
        mat = meta([_stod(1, 0.6004), _stod(2, 0.6506, lok=1963)], vidmidunarar=VIDMIDUNARAR)
        self.assertEqual((mat.valin.metrar, mat.naesta_aflogd.metrar), (600, 651))
        self.assertEqual(mat.munur_metrar, 50)

    def test_engin_aflogd_i_kassa_gefur_engan_mun(self) -> None:
        mat = meta([_stod(1, 0.6), _stod(2, 20.0, lok=1963)], vidmidunarar=VIDMIDUNARAR)
        self.assertIsNone(mat.naesta_aflogd)
        self.assertIsNone(mat.munur_metrar)

    def test_stodvar_utan_kassans_eru_ekki_i_rodinni(self) -> None:
        mat = meta([_stod(1, 0.6), _stod(2, 6.0), _stod(3, 1.0)], vidmidunarar=VIDMIDUNARAR)
        self.assertEqual([s.station_id for s in mat.naestu], [1, 3])


class JadarKassans(unittest.TestCase):
    """``polygon``-sían tekur jaðarinn með (sama og BETWEEN í SQL-inu)."""

    def _a_breidd(self, audkenni: int, breidd: float) -> Stod:
        stod = _stod(audkenni, 0.0)
        return Stod(**{**stod.__dict__, "lat": breidd})

    def test_stod_a_jadrinum_er_med_en_rett_utan_hans_ekki(self) -> None:
        max_breidd = kassi(VR_II_BREIDD, VR_II_LENGD, RADIUS_KM)[3]
        a_jadri = self._a_breidd(1, max_breidd)
        utan = self._a_breidd(2, math.nextafter(max_breidd, math.inf))
        mat = meta([a_jadri, utan], vidmidunarar=VIDMIDUNARAR)
        self.assertEqual([s.station_id for s in mat.naestu], [1])


class Langtimastod(unittest.TestCase):
    def test_valin_sem_naer_aftur_er_sjalf_langtimastodin(self) -> None:
        mat = meta([_stod(1, 0.6, start=1950), _stod(2, 0.8, start=1920)], vidmidunarar=VIDMIDUNARAR)
        self.assertTrue(mat.valin_naer_aftur)
        self.assertEqual(mat.langtimastod, mat.valin)

    def test_leitad_utan_kassans_og_framhja_aflagdri(self) -> None:
        stodvar = [
            _stod(1, 0.6, start=2022),              # valin, of ung
            _stod(2, 1.0, start=1900, lok=1990),    # nógu gömul en aflögð
            _stod(3, 2.0, start=1977),              # virk en einu ári of ung
            _stod(4, 8.0, start=1976),              # utan kassans, stenst
        ]
        mat = meta(stodvar, vidmidunarar=VIDMIDUNARAR)
        self.assertFalse(mat.valin_naer_aftur)
        self.assertEqual(mat.langtimastod.station_id, 4)
        self.assertEqual(mat.langtimastod.metrar, 8000)

    def test_engin_langtimastod_gefur_none(self) -> None:
        mat = meta([_stod(1, 0.6, start=2022), _stod(2, 3.0, start=1977)], vidmidunarar=VIDMIDUNARAR)
        self.assertIsNone(mat.langtimastod)


class MatBrestur(unittest.TestCase):
    """Tilvikin þar sem gamla skriftan stöðvaði keyrsluna — og þetta mat líka."""

    def test_tomt_eintak(self) -> None:
        with self.assertRaisesRegex(MatVilla, "tómt"):
            meta([])

    def test_engin_stod_i_kassa(self) -> None:
        with self.assertRaisesRegex(MatVilla, "Engin stöð fannst"):
            meta([_stod(1, 20.0)])

    def test_engin_virk_stod_i_kassa_thott_virk_se_utan_hans(self) -> None:
        with self.assertRaisesRegex(MatVilla, "Engin virk stöð"):
            meta([_stod(1, 0.6, lok=1963), _stod(2, 20.0)])


class Hlutfall(unittest.TestCase):
    def test_sama_runnun_og_gamla_skriftan(self) -> None:
        # Gamla skriftan: f"{100 * virkar / allar:.0f}". Borið saman á öllum
        # brotum upp að 200, þar með talið hálfum prósentum (1/8 = 12,5 %).
        for heild in range(1, 201):
            for hluti in range(heild + 1):
                self.assertEqual(
                    hlutfall_prosent(hluti, heild),
                    int(f"{100 * hluti / heild:.0f}"),
                    (hluti, heild),
                )

    def test_hlutfall_af_engu_er_villa(self) -> None:
        with self.assertRaises(MatVilla):
            hlutfall_prosent(0, 0)


if __name__ == "__main__":
    unittest.main()
