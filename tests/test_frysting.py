"""Próf fyrir frystingu hrágagna — mælitækið á að gögnin séu ósnert (regla 4).

Sett upp á sys.path hér í stað sameiginlegrar hjálparskráar: P0.3 og P1.1 eru
sitt hvor grein og sameiginleg skrá myndi stangast á í samruna.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT / "src" / "python"))

from sofnun import hragogn  # noqa: E402


class VaentarSummurProf(unittest.TestCase):
    """Bæði provenance-sniðin sem eru í notkun verða að lesast."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _provenance(self, skjal: dict) -> None:
        (self.mappa / "provenance.json").write_text(json.dumps(skjal), encoding="utf-8")

    def test_summa_per_skra(self) -> None:
        self._provenance({"sha256": {"svar.json": "abc"}})
        self.assertEqual(hragogn.vaentar_summur(self.mappa), {"svar.json": "abc"})

    def test_ein_summa_med_nefndri_skra(self) -> None:
        (self.mappa / "svar.json").write_text("[]", encoding="utf-8")
        (self.mappa / "annad.json").write_text("[]", encoding="utf-8")
        self._provenance({"sha256": "abc", "response_file": "svar.json"})
        self.assertEqual(hragogn.vaentar_summur(self.mappa), {"svar.json": "abc"})

    def test_ein_summa_og_ein_gagnaskra(self) -> None:
        (self.mappa / "events.json").write_text("[]", encoding="utf-8")
        self._provenance({"sha256": "abc"})
        self.assertEqual(hragogn.vaentar_summur(self.mappa), {"events.json": "abc"})

    def test_ein_summa_og_margar_skrar_stodvar(self) -> None:
        """Óljós summa er villa, ekki ágiskun — annars væri sannreyningin sýndarmennska."""
        (self.mappa / "a.json").write_text("[]", encoding="utf-8")
        (self.mappa / "b.json").write_text("[]", encoding="utf-8")
        self._provenance({"sha256": "abc"})
        with self.assertRaises(ValueError):
            hragogn.vaentar_summur(self.mappa)

    def test_ekkert_provenance_gefur_tomt(self) -> None:
        self.assertEqual(hragogn.vaentar_summur(self.mappa), {})


class LysaSkrarProf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        (self.mappa / "svar.json").write_text("[1]", encoding="utf-8")
        self.summa = hragogn.sha256_af(self.mappa / "svar.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_rett_summa_er_stadfest(self) -> None:
        skrar = hragogn.lysa_skrar(self.mappa, {"svar.json": self.summa})
        self.assertTrue(skrar[0]["stadfest_vid_provenance"])
        self.assertEqual(skrar[0]["sha256"], self.summa)

    def test_onefnd_skra_er_skrad_en_ekki_stadfest(self) -> None:
        skrar = hragogn.lysa_skrar(self.mappa, {})
        self.assertFalse(skrar[0]["stadfest_vid_provenance"])

    def test_rong_summa_stodvar_keyrslu(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256 stemmir ekki"):
            hragogn.lysa_skrar(self.mappa, {"svar.json": "0" * 64})


class StadfestaProf(unittest.TestCase):
    """`stadfesta` á að finna breytta, horfna OG óskráða skrá."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rot = Path(self._tmp.name)
        self.safnmappa = self.rot / "data" / "raw" / "prof"
        self.safnmappa.mkdir(parents=True)
        (self.safnmappa / "svar.json").write_text("[1]", encoding="utf-8")

        self.frysting = self.rot / "data" / "raw" / "frysting.json"
        self._plastur = mock.patch.multiple(hragogn, ROT=self.rot, FRYSTING=self.frysting)
        self._plastur.start()
        hragogn.skra_safn(
            {
                "heiti": "prof",
                "mappa": "data/raw/prof",
                "fjoldi_skraa": 1,
                "staerd_baet": (self.safnmappa / "svar.json").stat().st_size,
                "skrar": hragogn.lysa_skrar(self.safnmappa),
            }
        )

    def tearDown(self) -> None:
        self._plastur.stop()
        self._tmp.cleanup()

    def test_osnert_safn_stemmir(self) -> None:
        self.assertEqual(hragogn.stadfesta(), 0)

    def test_breytt_skra_finnst(self) -> None:
        (self.safnmappa / "svar.json").write_text("[2]", encoding="utf-8")
        self.assertEqual(hragogn.stadfesta(), 1)

    def test_horfin_skra_finnst(self) -> None:
        (self.safnmappa / "svar.json").unlink()
        self.assertEqual(hragogn.stadfesta(), 1)

    def test_oskrad_skra_finnst(self) -> None:
        (self.safnmappa / "auka.json").write_text("[3]", encoding="utf-8")
        self.assertEqual(hragogn.stadfesta(), 1)

    def test_vantar_frystingu_stodvar(self) -> None:
        self.frysting.unlink()
        with self.assertRaises(FileNotFoundError):
            hragogn.stadfesta()


class AudkenniProf(unittest.TestCase):
    """User-Agent verður að auðkenna verkefnið og ekki bera netfang (regla 4)."""

    def test_sjalfgefid_audkenni_hefur_ekkert_netfang(self) -> None:
        with mock.patch.dict("os.environ", {hragogn.AUDKENNIS_BREYTA: ""}):
            audkenni = hragogn.notandi_audkenni()
        self.assertNotIn("@", audkenni)
        self.assertIn("Upplysingaverkfradi", audkenni)

    def test_netfang_ur_umhverfi_gefur_advorun(self) -> None:
        with mock.patch.dict("os.environ", {hragogn.AUDKENNIS_BREYTA: "prof (a@b.is)"}):
            with self.assertLogs(hragogn.log, level="WARNING"):
                self.assertEqual(hragogn.notandi_audkenni(), "prof (a@b.is)")


class FrosinGognProf(unittest.TestCase):
    """Gögnin sem ERU fryst í þessu repo-i eiga alltaf að stemma við frysting.json."""

    def test_hragognin_eru_osnert(self) -> None:
        self.assertEqual(hragogn.stadfesta(), 0)

    def test_tmdb_er_skrad_ofryst(self) -> None:
        """Safn sem ekki tókst að frysta má ekki hverfa þegjandi (regla 6)."""
        skjal = json.loads(hragogn.FRYSTING.read_text(encoding="utf-8"))
        ofryst = {faersla["heiti"] for faersla in skjal["ofryst"]}
        self.assertIn("tmdb", ofryst)


if __name__ == "__main__":
    unittest.main()
