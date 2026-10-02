"""Próf fyrir sameiginlega JSON-lagið (``utflutningur.json_skrif``, issue #15).

Kjarninn sem hér er sannaður: **misheppnaður útflutningur skilur eldri skrá
eftir óbreytta** — bæti fyrir bæti — og skilur ekkert rusl eftir í möppunni.
Hvert próf byrjar á að skrifa „eldri skrá" og reynir svo útflutning sem á að
bregðast á ólíkum stigum: sannreyning, JSON-ritun, stærðarþak og sjálf
skrifin á diskinn.

Prófin skrifa eingöngu í tímabundna möppu, aldrei í ``web/gogn/``.

    python3.12 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from utflutningur import json_skrif  # noqa: E402
from utflutningur.json_skrif import (  # noqa: E402
    UtflutningsVilla,
    byggja_umslag,
    sem_baeti,
    skrifa_umslag,
)

SKRA = "gagnasafn.json"
UPPFAERT = "2026-09-10T09:02:26+00:00"
HEIMILD = "Prófheimild — dæmi.is/slod"
ELDRA = b'{"eldri": "skra"}\n'


def gott_umslag() -> dict:
    return byggja_umslag(UPPFAERT, HEIMILD, [{"a": 1.5}], {"lysing": "próf"})


class UmslagProf(unittest.TestCase):
    def test_reitaroedin_er_fost(self) -> None:
        self.assertEqual(list(gott_umslag()), ["uppfaert", "heimild", "gogn", "lysigogn"])

    def test_z_og_plus_null_verda_sama_snid(self) -> None:
        self.assertEqual(
            byggja_umslag("2026-09-24T11:22:18Z", HEIMILD, [1])["uppfaert"],
            "2026-09-24T11:22:18+00:00",
        )

    def test_annad_timabelti_er_faert_i_utc(self) -> None:
        self.assertEqual(
            byggja_umslag("2026-09-24T12:22:18+01:00", HEIMILD, [1])["uppfaert"],
            "2026-09-24T11:22:18+00:00",
        )

    def test_timastimpill_an_timabeltis_er_hafnad(self) -> None:
        with self.assertRaises(UtflutningsVilla):
            byggja_umslag("2026-09-24T11:22:18", HEIMILD, [1])

    def test_tomur_gagnalisti_er_hafnad(self) -> None:
        with self.assertRaises(UtflutningsVilla):
            byggja_umslag(UPPFAERT, HEIMILD, [])

    def test_aud_heimild_er_hafnad(self) -> None:
        with self.assertRaises(UtflutningsVilla):
            byggja_umslag(UPPFAERT, "  ", [1])

    def test_othekktur_reitur_er_hafnad(self) -> None:
        umslag = gott_umslag()
        umslag["aukalega"] = 1
        with self.assertRaises(UtflutningsVilla):
            sem_baeti(umslag)

    def test_osamraemt_uppfaert_er_hafnad(self) -> None:
        umslag = gott_umslag()
        umslag["uppfaert"] = "2026-09-10T09:02:26Z"
        with self.assertRaises(UtflutningsVilla):
            sem_baeti(umslag)

    def test_sama_umslag_gefur_somu_baeti(self) -> None:
        self.assertEqual(sem_baeti(gott_umslag()), sem_baeti(gott_umslag()))

    def test_baetin_eru_gilt_json_med_islenskum_stofum(self) -> None:
        baeti = sem_baeti(byggja_umslag(UPPFAERT, "Veðurstofa Íslands", [1]))
        self.assertIn("Veðurstofa Íslands".encode(), baeti)
        self.assertEqual(json.loads(baeti)["heimild"], "Veðurstofa Íslands")


class AtomiskSkrifProf(unittest.TestCase):
    """Eldri skrá stendur óbreytt þegar útflutningur bregst — á hvaða stigi sem er."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.mappa = Path(tmp.name)
        self.slod = self.mappa / SKRA
        self.slod.write_bytes(ELDRA)

    def assert_oskert(self) -> None:
        self.assertEqual(self.slod.read_bytes(), ELDRA)
        self.assertEqual(sorted(p.name for p in self.mappa.iterdir()), [SKRA])

    def test_heppnud_skrif_leysa_eldri_skra_af_holmi(self) -> None:
        skrifa_umslag(self.mappa, SKRA, gott_umslag())
        self.assertEqual(json.loads(self.slod.read_bytes())["heimild"], HEIMILD)
        self.assertEqual(sorted(p.name for p in self.mappa.iterdir()), [SKRA])

    def test_skrifud_skra_er_lesanleg_ollum(self) -> None:
        skrifa_umslag(self.mappa, SKRA, gott_umslag())
        self.assertEqual(self.slod.stat().st_mode & 0o777, json_skrif.HEIMILDIR_SKRAR)

    def test_ogilt_umslag_breytir_engu(self) -> None:
        umslag = gott_umslag()
        del umslag["heimild"]
        with self.assertRaises(UtflutningsVilla):
            skrifa_umslag(self.mappa, SKRA, umslag)
        self.assert_oskert()

    def test_nan_i_gognum_breytir_engu(self) -> None:
        umslag = gott_umslag()
        umslag["gogn"] = [{"gildi": float("nan")}]
        with self.assertRaises(UtflutningsVilla):
            skrifa_umslag(self.mappa, SKRA, umslag)
        self.assert_oskert()

    def test_oritanlegt_gildi_breytir_engu(self) -> None:
        umslag = gott_umslag()
        umslag["gogn"] = [{"gildi": object()}]
        with self.assertRaises(UtflutningsVilla):
            skrifa_umslag(self.mappa, SKRA, umslag)
        self.assert_oskert()

    def test_of_stor_skra_breytir_engu(self) -> None:
        umslag = gott_umslag()
        umslag["gogn"] = ["x" * json_skrif.HAMARKS_BAETI]
        with self.assertRaises(UtflutningsVilla):
            skrifa_umslag(self.mappa, SKRA, umslag)
        self.assert_oskert()

    def test_villa_i_midjum_skrifum_breytir_engu(self) -> None:
        """Diskurinn bregst eftir að bætin eru farin í tímabundnu skrána."""
        with mock.patch.object(json_skrif.os, "fsync", side_effect=OSError("diskur fullur")):
            with self.assertRaises(OSError):
                skrifa_umslag(self.mappa, SKRA, gott_umslag())
        self.assert_oskert()

    def test_villa_i_tilfaerslu_breytir_engu(self) -> None:
        with mock.patch.object(json_skrif.os, "replace", side_effect=OSError("bannað")):
            with self.assertRaises(OSError):
                skrifa_umslag(self.mappa, SKRA, gott_umslag())
        self.assert_oskert()

    def test_mappa_sem_er_ekki_til_er_ekki_bin_til(self) -> None:
        vantar = self.mappa / "ekki-til"
        with self.assertRaises(UtflutningsVilla):
            skrifa_umslag(vantar, SKRA, gott_umslag())
        self.assertFalse(vantar.exists())

    def test_os_replace_er_notad_med_skra_i_somu_moppu(self) -> None:
        """Atómískt aðeins innan sama skráarkerfis: tímabundna skráin verður að vera við hliðina."""
        upprunalegt = os.replace
        kollud: list[tuple[str, str]] = []

        def skra(fra: str, til: object) -> None:
            kollud.append((str(fra), str(til)))
            upprunalegt(fra, til)

        with mock.patch.object(json_skrif.os, "replace", side_effect=skra):
            skrifa_umslag(self.mappa, SKRA, gott_umslag())
        self.assertEqual(len(kollud), 1)
        self.assertEqual(Path(kollud[0][0]).parent, self.mappa)
        self.assertEqual(Path(kollud[0][1]), self.slod)


if __name__ == "__main__":
    unittest.main()
