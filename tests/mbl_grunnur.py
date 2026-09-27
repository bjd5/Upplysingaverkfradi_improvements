"""Sameiginleg umgjörð fyrir mbl-próf sem þurfa raunverulegan SQL-grunn (issue #9).

Grunnurinn í prófunum er byggður **úr sömu migrations og alvörugrunnurinn** —
``gagnagrunnur.keyrari.keyra`` á ``src/sql/migrations/``, aldrei handskrifað
``CREATE TABLE`` í prófi. Annars prófuðu prófin annað skema en það sem er
keyrt (regla 5).

Fyrirspurnin ``SVOR_SQL`` er hér því tvær prófskrár nota hana: hún er
staðfestingin á kröfunni í issue #9 um að öll fimm svörin fáist úr SQL.
Breytur fara alltaf inn sem ``?`` — aldrei strengjasamsetning (regla 5).

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py`` og hleður henni því aðeins þegar prófin flytja hana inn.
"""

from __future__ import annotations

import logging
import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur.keyrari import MIGRATIONS_MAPPA, keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from mbl_vidmid import FROSNA_EINTAKID  # noqa: E402
from vinnsla.mbl_eintak import Eintak, finna_eintok  # noqa: E402

# Keyrarinn varar við götum í migration-númerum (002–004 eru á greinum hinna
# agentanna) og hleðslan skráir hvert eintak. Hvorugt er villa og hvorugt er
# það sem þessi próf mæla — þögnin er aðeins hér, ekki í keyrslunni sjálfri.
THOGGUD_LOG = ("gagnagrunnur.keyrari", "vinnsla.mbl_hledsla")

for heiti in THOGGUD_LOG:
    logging.getLogger(heiti).setLevel(logging.ERROR)

# Ein fyrirspurn sem svarar öllum fimm spurningunum og sýnir um leið hvaðan
# hvert svar kemur: mynstrið, eintakið og sóknartíminn fylgja hverri línu.
SVOR_SQL = """
SELECT e.question_number AS nr,
       e.question_key    AS lykill,
       e.question_is     AS spurning,
       e.value_number    AS gildi,
       e.value_text      AS svar,
       e.unit            AS eining,
       e.pattern_name    AS mynsturheiti,
       e.pattern         AS mynstur,
       e.pattern_flags   AS mynsturflogg,
       e.scope_name      AS afmorkun,
       e.scope_pattern   AS afmorkunarmynstur,
       e.match_count     AS tilvik,
       e.distinct_count  AS einstok,
       e.sample_match    AS synishorn,
       e.notes           AS takmarkanir,
       s.raw_file        AS eintak,
       s.fetched_at      AS sott,
       s.source_url      AS upprunaslod
  FROM mbl_extractions e
  JOIN mbl_snapshots   s ON s.id = e.snapshot_id
 WHERE s.fetched_at = ?
 ORDER BY e.question_number
"""

# Sama fyrirspurn afmörkuð við eina spurningu — notuð þegar próf svarar einni
# spurningu æfingarinnar í einu.
EITT_SVAR_SQL = SVOR_SQL.replace(
    "WHERE s.fetched_at = ?", "WHERE s.fetched_at = ? AND e.question_key = ?"
)


class GrunnProf(unittest.TestCase):
    """Tómur grunnur með raunverulegu migration-unum, einn á hvert próf."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.samband = opna(self.mappa / "prof.sqlite")
        self.addCleanup(self.samband.close)
        keyra(self.samband, MIGRATIONS_MAPPA)

    def svor(self, sott: str) -> list[sqlite3.Row]:
        """Öll fimm svörin fyrir eitt eintak — alltaf með breytu, aldrei f-streng."""
        return self.samband.execute(SVOR_SQL, (sott,)).fetchall()

    def eitt_svar(self, sott: str, lykill: str) -> sqlite3.Row:
        """Eitt svar úr SQL. Finnist það ekki fellur prófið með læsilegri villu."""
        rad = self.samband.execute(EITT_SVAR_SQL, (sott, lykill)).fetchone()
        self.assertIsNotNone(
            rad, f"Spurningin {lykill!r} er ekki svaranleg úr grunninum fyrir {sott}."
        )
        return rad

    def frosna_eintakid(self) -> Eintak:
        """Frosna eintakið úr ``data/raw/mbl/`` — lesið, aldrei skrifað."""
        eintok = [
            e for e in finna_eintok() if e.skraarheiti.startswith(FROSNA_EINTAKID)
        ]
        self.assertTrue(
            eintok,
            f"{FROSNA_EINTAKID}.html finnst ekki í data/raw/mbl/. Það er eina "
            "eintakið sem til er — sjá data/raw/README.md.",
        )
        return eintok[0]
