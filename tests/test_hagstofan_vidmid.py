"""Ber Hagstofutölur grunnsins saman við viðmiðið úr gömlu síðunni (issue #7).

Krafa verkefnisins er að nýja síðan sýni sömu tölur og sú gamla
(docs/endurbygging.md, kafli 2). Viðmiðið er ``docs/vidmid/vidmid.json``, lesið
úr byggðu gömlu síðunni af ``src/python/vidmid/tolur.py``; mannlesanleg útgáfa
þess er ``docs/vidmid/vidmid/hagstofan.md`` og upprunalega framsetningin
``docs/vidmid/generated/hagstofan-results.md``.

Tvennt skiptir máli um aðferðina:

* **Hver einasta tala kemur úr SQL-fyrirspurn.** Ekkert er endurreiknað í
  Python — líka ekki mismunirnir í prósentustigum, sem eru dregnir saman í
  fyrirspurninni sjálfri. Væru þeir reiknaðir hér prófaði prófið sinn eigin
  reikning en ekki grunninn.
* **Viðmiðið er lesið, ekki afritað.** Talnalistinn kemur úr vidmid.json svo
  ekki sé hægt að laga próf að grunni í stað þess að laga grunn að viðmiði.

Víki tala er það villa þar til annað er sannað.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from test_hagstofan_hledsla import AUDKENNI, byggja_grunn  # noqa: E402

from gagnagrunnur.tenging import opna  # noqa: E402

VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
SIDA = "lotur/vefthjonustur/hagstofan.html"

# Kynjataflan í viðmiðinu ber námssvið og kyn saman í einum reit: „Alls · Konur".
KYNSKIL = " · "

# Prósentutölurnar í viðmiðinu eru allar `desimal`; kóðarnir í lýsigagnatöflunni
# eru `heiltala` og eiga ekkert erindi í þennan samanburð.
TEGUND_HLUTFALLS = "desimal"
EINING_PROSENTUSTIG = "prósentustig"

# Kóðar Hagstofunnar. Heitin eru í grunninum; kóðarnir eru lyklar fyrirspurna.
KODI_ALLS = "Alls"
KODI_VERKFRAEDI = "07"
KODI_BRAUTSKRADIR = "5"
KODI_KARLAR = "1"
KODI_KONUR = "2"

# Aukastafir gömlu síðunnar. Hún birti einn; við berum saman á sama nákvæmni.
AUKASTAFIR = 1

# Mismunirnir sem gamla síðan fullyrti, í prósentustigum.
MUNUR_VERKFRAEDI_ALLS = 10.8
MUNUR_KYN_VERKFRAEDI = 0.3
MUNUR_KYN_ALLS = 5.6

# Námundun gefur 99,9 eða 100,1 — gamla síðan nefnir öll þrjú gildin.
LEYFDAR_SUMMUR = {99.9, 100.0, 100.1}

SQL_ALLAR_TOLUR = """
SELECT field_label, sex_label, student_status_label, ROUND(value, ?) AS gildi
FROM hagstofan_labelled_observations
WHERE dataset_id = ?
"""

# Mismunur tveggja mælinga, dreginn saman í SQL en ekki í Python.
SQL_MUNUR = """
SELECT ROUND(
    (SELECT value FROM hagstofan_labelled_observations
      WHERE dataset_id = ? AND field_code = ? AND sex_code = ?
        AND student_status_code = ?)
  - (SELECT value FROM hagstofan_labelled_observations
      WHERE dataset_id = ? AND field_code = ? AND sex_code = ?
        AND student_status_code = ?), ?) AS munur
"""

SQL_SUMMUR = """
SELECT field_label, sex_label, ROUND(SUM(value), ?) AS summa
FROM hagstofan_labelled_observations
WHERE dataset_id = ?
GROUP BY field_code, sex_code
"""


def lesa_vidmid() -> dict[tuple[str, str, str], float]:
    """Les prósentutölur gömlu síðunnar: (námssvið, kyn, staða) -> gildi."""
    gogn = json.loads(VIDMID_JSON.read_text(encoding="utf-8"))["gogn"]
    tolur: dict[tuple[str, str, str], float] = {}
    for rad in gogn:
        if rad.get("sida") != SIDA or rad.get("flokkur") != "tafla":
            continue
        if rad.get("tegund") != TEGUND_HLUTFALLS:
            continue
        tolur[_lykill(rad)] = float(rad["gildi"])
    return tolur


def _lykill(rad: dict[str, object]) -> tuple[str, str, str]:
    """Lykill viðmiðsraðar. Kyn stendur í línuheitinu eða er ósundurliðað."""
    lina = str(rad["lina"])
    svid, _, kyn = lina.partition(KYNSKIL)
    return svid, kyn or KODI_ALLS, str(rad["sulka"])


def lesa_prosentustig() -> set[float]:
    """Les mismunina sem gamla síðan fullyrti, í prósentustigum."""
    gogn = json.loads(VIDMID_JSON.read_text(encoding="utf-8"))["gogn"]
    return {
        float(rad["gildi"])
        for rad in gogn
        if rad.get("sida") == SIDA and rad.get("eining") == EINING_PROSENTUSTIG
    }


class VidmidProf(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.slod = Path(cls._tmp.name) / "rannsokn.sqlite"
        byggja_grunn(cls.slod)
        cls.vidmid = lesa_vidmid()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self.samband = opna(self.slod)
        self.addCleanup(self.samband.close)

    def _ur_grunninum(self) -> dict[tuple[str, str, str], float]:
        radir = self.samband.execute(SQL_ALLAR_TOLUR, (AUKASTAFIR, AUDKENNI))
        return {
            (rad["field_label"], rad["sex_label"], rad["student_status_label"]):
                rad["gildi"]
            for rad in radir
        }

    def _munur(self, svid_a: str, kyn_a: str, svid_b: str, kyn_b: str) -> float:
        rad = self.samband.execute(
            SQL_MUNUR,
            (
                AUDKENNI, svid_a, kyn_a, KODI_BRAUTSKRADIR,
                AUDKENNI, svid_b, kyn_b, KODI_BRAUTSKRADIR,
                AUKASTAFIR,
            ),
        ).fetchone()
        return rad["munur"]

    def test_vidmidid_telur_allar_36_tolurnar(self) -> None:
        """Gamla síðan birti hverja einustu mælingu — 12 ósundurliðaðar og 24 eftir kyni."""
        self.assertEqual(len(self.vidmid), 36)

    def test_hver_tala_i_grunninum_a_ser_samsvorun_i_vidmidinu(self) -> None:
        self.assertEqual(self._ur_grunninum(), self.vidmid)

    def test_engin_tala_vikur_fra_vidmidinu(self) -> None:
        """Sami samanburður, tala fyrir tölu, svo frávik sjáist hvert fyrir sig."""
        ur_grunninum = self._ur_grunninum()
        for lykill, vaent in sorted(self.vidmid.items()):
            with self.subTest(namssvid=lykill[0], kyn=lykill[1], stada=lykill[2]):
                self.assertEqual(ur_grunninum.get(lykill), vaent)

    def test_munur_verkfraedi_og_alls_er_10_8_prosentustig(self) -> None:
        self.assertEqual(
            self._munur(KODI_VERKFRAEDI, KODI_ALLS, KODI_ALLS, KODI_ALLS),
            MUNUR_VERKFRAEDI_ALLS,
        )

    def test_munur_kynja_i_verkfraedi_er_0_3_prosentustig(self) -> None:
        self.assertEqual(
            self._munur(KODI_VERKFRAEDI, KODI_KONUR, KODI_VERKFRAEDI, KODI_KARLAR),
            MUNUR_KYN_VERKFRAEDI,
        )

    def test_munur_kynja_a_ollum_svidum_er_5_6_prosentustig(self) -> None:
        self.assertEqual(
            self._munur(KODI_ALLS, KODI_KONUR, KODI_ALLS, KODI_KARLAR),
            MUNUR_KYN_ALLS,
        )

    def test_mismunirnir_thrir_eru_their_somu_og_i_vidmidinu(self) -> None:
        """Fastarnir hér að ofan eiga sér heimild í vidmid.json, ekki í minni."""
        self.assertEqual(
            lesa_prosentustig(),
            {MUNUR_VERKFRAEDI_ALLS, MUNUR_KYN_VERKFRAEDI, MUNUR_KYN_ALLS},
        )

    def test_stoduflokkarnir_thrir_leggja_saman_i_hundrad(self) -> None:
        """Hver nemandi er í einum flokki; námundun gefur 99,9 eða 100,1."""
        summur = {
            (rad["field_label"], rad["sex_label"]): rad["summa"]
            for rad in self.samband.execute(SQL_SUMMUR, (AUKASTAFIR, AUDKENNI))
        }
        self.assertEqual(len(summur), 12)
        for lykill, summa in sorted(summur.items()):
            with self.subTest(namssvid=lykill[0], kyn=lykill[1]):
                self.assertIn(summa, LEYFDAR_SUMMUR)
        self.assertEqual(set(summur.values()), LEYFDAR_SUMMUR)


if __name__ == "__main__":
    unittest.main()
