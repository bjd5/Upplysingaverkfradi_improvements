"""Hleðsla jarðskjálftanna í SQL-grunninn (issue #6).

Les frosna svarið í ``data/raw/vedur-quakes/events.json``, sannreynir hverja
færslu (sjá ``jardskjalftar.py``) og skrifar hana í töflurnar sem
``src/sql/migrations/002_jardskjalftar.sql`` býr til:

* ``earthquake_days`` — ein lína á hvern UTC-dag tímabilsins, líka daga með
  núll atburði. Þeir dagar eru niðurstaða, ekki eyða.
* ``earthquakes`` — ein lína á atburð.

Dagarnir eru skrifaðir á undan atburðunum því ``earthquakes.utc_day`` vísar í
``earthquake_days.utc_day``: atburður utan tímabils beiðninnar kemst þá ekki
inn, hvorki um þessa leið né aðra.

**Allar fyrirspurnir eru með breytum** (regla 5). Hvergi er strengur skeyttur
inn í SQL.

Hleðslan er endurkeyranleg: hún hreinsar báðar töflur áður en hún skrifar, svo
grunnurinn er alltaf hrein afleiða hrágagnanna. Hún gerir **ekki** commit —
``gagnagrunnur.tenging.tenging`` sér um að ljúka færslunni.

Tengingu við ``src/python/main.py`` er haldið utan við þessa einingu af ásettu
ráði; hún bíður issue #11. Þangað til má keyra hleðsluna eina og sér::

    PYTHONPATH=src/python python3 -m vinnsla.jardskjalftar_hledsla

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection

try:  # keyrt sem eining innan pakkans (venjulega leiðin)
    from .jardskjalftar import Skjalfti, lesa_skjalfta, talning_eftir_degi
    from .jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, dagar, lesa_afmorkun
except ImportError:  # keyrt beint úr möppunni
    from jardskjalftar import Skjalfti, lesa_skjalfta, talning_eftir_degi
    from jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, dagar, lesa_afmorkun

log = logging.getLogger(__name__)

TOFLUR = ("earthquakes", "earthquake_days")

SQL_HREINSA_ATBURDI = "DELETE FROM earthquakes"
SQL_HREINSA_DAGA = "DELETE FROM earthquake_days"

SQL_SETJA_DAG = (
    "INSERT INTO earthquake_days (utc_day, event_count) VALUES (?, ?)"
)

SQL_SETJA_ATBURD = (
    "INSERT INTO earthquakes ("
    "    event_id, source_system, event_number, occurred_at, utc_day,"
    "    magnitude, magnitude_type, depth_km, latitude, longitude,"
    "    event_type, evaluation_mode"
    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

SQL_TELJA_ATBURDI = "SELECT count(*) AS fjoldi FROM earthquakes"
SQL_TELJA_DAGA = "SELECT count(*) AS fjoldi FROM earthquake_days"
SQL_TELJA_AN_KVARDA = (
    "SELECT count(*) AS fjoldi FROM earthquakes WHERE magnitude_type IS NULL"
)
SQL_TAFLA_ER_TIL = (
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?"
)


@dataclass(frozen=True)
class Talning:
    """Það sem hleðslan skrifaði — tölurnar sem prófin bera saman við."""

    atburdir: int
    dagar: int


def hlada(
    samband: Connection,
    slod: Path | str | None = None,
    afmorkun: Afmorkun | None = None,
) -> Talning:
    """Skrifar sannreynda skjálfta og alla daga tímabilsins í grunninn.

    Kallandinn ber ábyrgð á færslunni (commit/rollback) — notaðu
    ``gagnagrunnur.tenging.tenging``.

    Skilar fjölda atburða og fjölda daga eins og þeir eru **lesnir aftur út úr
    grunninum**, ekki eins og þeir voru taldir í minni.
    """
    afmorkun = afmorkun if afmorkun is not None else lesa_afmorkun()
    skjalftar = lesa_skjalfta(slod, afmorkun)
    dagalisti = dagar(afmorkun)
    talning = talning_eftir_degi(skjalftar, dagalisti)

    _krefjast_taflna(samband)

    # Börnin fyrst: earthquakes vísar í earthquake_days.
    samband.execute(SQL_HREINSA_ATBURDI)
    samband.execute(SQL_HREINSA_DAGA)

    samband.executemany(
        SQL_SETJA_DAG, [(dagur, talning[dagur]) for dagur in dagalisti]
    )
    samband.executemany(SQL_SETJA_ATBURD, [_rod(s) for s in skjalftar])

    nidurstada = _stadfesta(samband, len(skjalftar), len(dagalisti))
    log.info(
        "Hlóð %d jarðskjálftum á %d UTC-dögum (%s).",
        nidurstada.atburdir,
        nidurstada.dagar,
        afmorkun.leyfi,
    )
    return nidurstada


def _rod(skjalfti: Skjalfti) -> tuple[object, ...]:
    """Raðar gildum atburðar í sömu röð og dálkarnir í ``SQL_SETJA_ATBURD``."""
    return (
        skjalfti.event_id,
        skjalfti.source_system,
        skjalfti.event_number,
        skjalfti.occurred_at,
        skjalfti.utc_day,
        skjalfti.magnitude,
        skjalfti.magnitude_type,
        skjalfti.depth_km,
        skjalfti.latitude,
        skjalfti.longitude,
        skjalfti.event_type,
        skjalfti.evaluation_mode,
    )


def _krefjast_taflna(samband: Connection) -> None:
    """Stöðvar með skýrri villu hafi migration 002 ekki verið keyrð."""
    for tafla in TOFLUR:
        if samband.execute(SQL_TAFLA_ER_TIL, (tafla,)).fetchone() is None:
            raise SkjalftaVilla(
                f"Taflan {tafla} er ekki til. Keyrðu migrations fyrst "
                "(gagnagrunnur.keyrari.keyra eða scripts/endurbyggja-grunn.sh)."
            )


def _stadfesta(samband: Connection, vaentir: int, vaentir_dagar: int) -> Talning:
    """Les tölurnar aftur út úr grunninum og ber þær við það sem átti að fara inn."""
    atburdir = samband.execute(SQL_TELJA_ATBURDI).fetchone()["fjoldi"]
    dagafjoldi = samband.execute(SQL_TELJA_DAGA).fetchone()["fjoldi"]
    an_kvarda = samband.execute(SQL_TELJA_AN_KVARDA).fetchone()["fjoldi"]

    if atburdir != vaentir:
        raise SkjalftaVilla(
            f"{vaentir} atburðir voru sannreyndir en {atburdir} komust í grunninn."
        )
    if dagafjoldi != vaentir_dagar:
        raise SkjalftaVilla(
            f"Tímabilið telur {vaentir_dagar} UTC-daga en {dagafjoldi} línur "
            "eru í earthquake_days."
        )
    if an_kvarda:
        raise SkjalftaVilla(
            f"{an_kvarda} atburðir eru án magnitude_type. Stærð án skráðs kvarða "
            "er ekki samanburðarhæf."
        )
    return Talning(atburdir=atburdir, dagar=dagafjoldi)


def _keyra_eina_serd() -> int:
    """Keyrir migrations og hleðsluna á sjálfgefna grunninn — handvirk keyrsla."""
    from gagnagrunnur.keyrari import keyra
    from gagnagrunnur.tenging import tenging

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    with tenging() as samband:
        keyra(samband)
        talning = hlada(samband)
    print(f"atburðir: {talning.atburdir}")
    print(f"dagar: {talning.dagar}")
    return 0


if __name__ == "__main__":
    sys.exit(_keyra_eina_serd())
