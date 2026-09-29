"""Próf fyrir útflutning Hagstofunnar í ``hagstofan.json`` (issue #15).

Grunnurinn er byggður úr frosnu ``data/raw/hagstofan/`` í tímabundinni möppu og
fluttur út í aðra tímabundna möppu. Tölurnar eru bornar við frosna viðmiðið
(``docs/vidmid/vidmid.json``, lesið með ``test_hagstofan_vidmid.lesa_vidmid``)
— ekki við tölur slegnar inn hér.

Lærdómurinn úr #47: staðfesting sem getur stemmt af tilviljun er ekki
staðfesting. Þess vegna er ``uppfaert`` borið við provenance.json *og* sýnt að
það fylgi grunninum þegar honum er breytt — annars gæti fasti eða klukkan
staðist fyrra prófið.

    python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import utflutningur_grunnur as ug

from test_hagstofan_vidmid import lesa_prosentustig, lesa_vidmid  # noqa: E402

from gagnagrunnur.tenging import tenging  # noqa: E402
from utflutningur import hagstofan_json  # noqa: E402
from utflutningur.flytja_ut import flytja_ut  # noqa: E402
from utflutningur.json_skrif import UtflutningsVilla, utc_timastimpill  # noqa: E402

VAENT_STAERDIR = [1, 1, 3, 1, 4, 3]
LEYFDAR_SUMMUR = {99.9, 100.0, 100.1}


def setUpModule() -> None:
    global _TMP, GRUNNUR, SKRA
    _TMP = tempfile.TemporaryDirectory()
    mappa = Path(_TMP.name)
    GRUNNUR = ug.byggja_grunn(mappa / "rannsokn.sqlite")
    (mappa / "ut").mkdir()
    flytja_ut(mappa / "ut", GRUNNUR)
    SKRA = mappa / "ut" / hagstofan_json.SKRAARHEITI


def tearDownModule() -> None:
    _TMP.cleanup()


class SnidProf(unittest.TestCase):
    def setUp(self) -> None:
        self.umslag = ug.lesa_json(SKRA)

    def test_reitir_umslagsins(self) -> None:
        self.assertEqual(list(self.umslag), ["uppfaert", "heimild", "gogn", "lysigogn"])

    def test_uppfaert_er_soknartiminn_ur_provenance(self) -> None:
        provenance = ug.lesa_json(ug.HAGSTOFAN_RA / "provenance.json")
        self.assertEqual(self.umslag["uppfaert"], utc_timastimpill(provenance["fetched_at_utc"]))

    def test_heimild_nefnir_hagstofuna_og_toflu(self) -> None:
        self.assertTrue(self.umslag["heimild"].startswith("Hagstofa Íslands — px.hagstofa.is/"))
        self.assertIn("SKO04208b.px", self.umslag["heimild"])

    def test_fyrirspurnin_er_query_json_obreytt(self) -> None:
        self.assertEqual(
            self.umslag["lysigogn"]["fyrirspurn"],
            ug.lesa_json(ug.HAGSTOFAN_RA / "query.json"),
        )

    def test_afmorkunin_er_2017_n3_og_hlutfall(self) -> None:
        afmorkun = {a["vidd"]: (a["kodi"], a["gildi"]) for a in self.umslag["lysigogn"]["afmorkun"]}
        self.assertEqual(
            afmorkun,
            {"Innritunarár": ("2017", "2017"),
             "Tími": ("n+3", "Sex árum eftir innritun"),
             "Fjöldi/Hlutfall": ("1", "Hlutfall %")},
        )

    def test_viddastaerdir_og_fjoldi_gilda(self) -> None:
        lysigogn = self.umslag["lysigogn"]
        self.assertEqual([v["staerd"] for v in lysigogn["viddir"]], VAENT_STAERDIR)
        self.assertEqual(lysigogn["tafla"]["fjoldi_gilda"], 36)
        for vidd in lysigogn["viddir"]:
            with self.subTest(vidd=vidd["kodi"]):
                self.assertEqual(sum(g["valid"] for g in vidd["gildi"]), vidd["staerd"])

    def test_tolur_eru_runnadar_a_einn_aukastaf(self) -> None:
        for rod in self.umslag["gogn"]:
            for reitur in ("brautskradir", "brottfallnir", "enn_i_nami", "samtals"):
                with self.subTest(rod=(rod["namssvid_kodi"], rod["kyn_kodi"]), reitur=reitur):
                    self.assertEqual(round(rod[reitur], 1), rod[reitur])


class VidmidProf(unittest.TestCase):
    """Sömu 36 tölur og gamla síðan birti — lesnar úr útfluttu skránni."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.umslag = ug.lesa_json(SKRA)

    def _ur_skranni(self) -> dict[tuple[str, str, str], float]:
        stodur = self.umslag["lysigogn"]["stodur"]
        return {
            (rod["namssvid"], rod["kyn"], stada["heiti"]): rod[stada["reitur"]]
            for rod in self.umslag["gogn"]
            for stada in stodur
        }

    def test_36_gildi_hvert_eins_og_i_vidmidinu(self) -> None:
        ur_skranni, vidmid = self._ur_skranni(), lesa_vidmid()
        self.assertEqual(len(vidmid), 36)
        self.assertEqual(set(ur_skranni), set(vidmid))
        for lykill, vaent in sorted(vidmid.items()):
            with self.subTest(namssvid=lykill[0], kyn=lykill[1], stada=lykill[2]):
                self.assertEqual(ur_skranni[lykill], vaent)

    def test_mismunirnir_eru_their_sem_gamla_sidan_fullyrti(self) -> None:
        munir = {m["lysing"]: m["prosentustig"] for m in self.umslag["lysigogn"]["munir"]}
        self.assertEqual(set(munir.values()), lesa_prosentustig())
        self.assertEqual(munir["Verkfræði miðað við öll svið, bæði kyn"], 10.8)
        self.assertEqual(munir["Konur miðað við karla í verkfræði"], 0.3)
        self.assertEqual(munir["Konur miðað við karla á öllum sviðum"], 5.6)

    def test_stoduflokkarnir_leggja_saman_i_hundrad(self) -> None:
        for rod in self.umslag["gogn"]:
            with self.subTest(namssvid=rod["namssvid"], kyn=rod["kyn"]):
                self.assertIn(rod["samtals"], LEYFDAR_SUMMUR)


class GrunnurinnRaedurProf(unittest.TestCase):
    """Útflutningurinn fylgir grunninum — og bregst þegar grunnurinn er gallaður."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.slod = ug.afrita_grunn(GRUNNUR, Path(tmp.name) / "afrit.sqlite")

    def _breyta(self, sql: str, breytur: tuple = ()) -> None:
        with tenging(self.slod) as samband:
            samband.execute(sql, breytur)

    def _byggja(self) -> dict:
        with tenging(self.slod) as samband:
            return hagstofan_json.byggja(samband)

    def test_uppfaert_kemur_ur_grunninum_ekki_ur_klukkunni(self) -> None:
        self._breyta("UPDATE hagstofan_datasets SET fetched_at = ?", ("2001-02-03T04:05:06Z",))
        self.assertEqual(self._byggja()["uppfaert"], "2001-02-03T04:05:06+00:00")

    def test_tvaer_keyrslur_gefa_sama_umslag(self) -> None:
        self.assertEqual(json.dumps(self._byggja()), json.dumps(self._byggja()))

    def test_vantandi_maeling_stodvar_utflutning(self) -> None:
        self._breyta(
            "DELETE FROM hagstofan_observations WHERE flat_index = "
            "(SELECT MAX(flat_index) FROM hagstofan_observations)"
        )
        with self.assertRaises(UtflutningsVilla):
            self._byggja()

    def test_tomur_grunnur_stodvar_utflutning(self) -> None:
        self._breyta("DELETE FROM hagstofan_observations")
        self._breyta("DELETE FROM hagstofan_dimension_values")
        self._breyta("DELETE FROM hagstofan_dimensions")
        self._breyta("DELETE FROM hagstofan_datasets")
        with self.assertRaises(UtflutningsVilla):
            self._byggja()


if __name__ == "__main__":
    unittest.main()
