"""Hleðsla mbl-eintaka og útdráttarniðurstaðna í SQL-grunninn (issue #9).

Brúin milli ``mbl_utdrattur`` og töflnanna úr ``005_mbl_regex.sql``. Hver
niðurstaða er skrifuð **ásamt mynstrinu sem framkallaði hana** og tilvísun í
eintakið sem hún var lesin úr, svo talan sé rekjanleg alla leið aftur í
hrágagnið (regla 8).

Allar fyrirspurnir eru með breytum — aldrei strengjasamsetning (regla 5).

Hvað gerist sé eintak þegar í grunninum:

* **sama SHA-256** — ekkert er gert. Endurkeyrsla á sama eintaki er eðlileg
  og á ekki að tvítelja niðurstöður.
* **annað SHA-256 undir sama sóknartíma** — :class:`HledsluVilla`. Þá lýsir
  grunnurinn ekki lengur því eintaki sem er á diski og þögul yfirskrift væri
  verri en stöðvun (regla 6).

Fleiri en eitt eintak mega liggja í töflunum samtímis; þau eru aðgreind eftir
``fetched_at``, svo eldri sókn glatast ekki þegar sú nýrri er hlaðin.

Handvirk keyrsla á sjálfgefna grunninn — migrations fyrst, svo hleðslan, og
svörin lesin aftur út úr SQL til staðfestingar::

    PYTHONPATH=src/python python3 -m vinnsla.mbl_hledsla
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection

from .mbl_eintak import Eintak, finna_eintok
from .mbl_utdrattur import Utdrattur, draga_ut_allt

log = logging.getLogger(__name__)

EINTAK_SQL = """
INSERT INTO mbl_snapshots (
    fetched_at, source_url, raw_file, sha256, md5,
    content_length_bytes, status_code, content_type, loaded_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UTDRATTUR_SQL = """
INSERT INTO mbl_extractions (
    snapshot_id, question_number, question_key, question_is,
    pattern_name, pattern, pattern_flags, scope_name, scope_pattern,
    value_number, value_text, unit,
    match_count, distinct_count, sample_match, notes, extracted_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

LEITA_SQL = "SELECT id, sha256 FROM mbl_snapshots WHERE fetched_at = ?"

# Svörin lesin aftur út úr grunninum: það sem fór inn á að koma út, og hvert
# svar á að benda á sitt eintak. Þetta er staðfestingin á kröfu issue #9 um að
# öll fimm svörin fáist úr SQL.
STADFESTA_SQL = """
SELECT e.question_number AS nr,
       e.question_is     AS spurning,
       e.value_text      AS svar,
       e.pattern_name    AS mynsturheiti,
       s.raw_file        AS eintak
  FROM mbl_extractions e
  JOIN mbl_snapshots   s ON s.id = e.snapshot_id
 WHERE s.fetched_at = ?
 ORDER BY e.question_number
"""

SQL_TAFLA_ER_TIL = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?"

# Töflurnar úr 005_mbl_regex.sql. Vanti þær hefur migration ekki verið keyrð.
TOFLUR = ("mbl_snapshots", "mbl_extractions")

# Spurningar æfingarinnar eru fimm og ekkert eintak er hálfsvarað.
SVOR_A_EINTAK = 5


class HledsluVilla(RuntimeError):
    """Grunnurinn og eintakið á diski lýsa ekki sama svari."""


@dataclass(frozen=True)
class Hledsla:
    """Niðurstaða þess að hlaða einu eintaki."""

    eintak: Eintak
    snapshot_id: int
    utdraettir: tuple[Utdrattur, ...]
    var_thegar_hladid: bool

    @property
    def fjoldi(self) -> int:
        """Fjöldi útdráttarlína sem voru skrifaðar."""
        return len(self.utdraettir)


def _nuna() -> str:
    """Tímastimpill í ISO 8601, UTC, á sekúndunákvæmni."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def finna_eintak_i_grunni(samband: Connection, sotta_stund: str) -> dict | None:
    """Skilar skráðu eintaki með þennan sóknartíma, eða ``None``."""
    rad = samband.execute(LEITA_SQL, (sotta_stund,)).fetchone()
    return dict(rad) if rad is not None else None


def skra_eintak(samband: Connection, eintak: Eintak) -> int:
    """Skrifar eintakið í ``mbl_snapshots`` og skilar auðkenni þess."""
    bendill = samband.execute(
        EINTAK_SQL,
        (
            eintak.sotta_stund,
            eintak.upprunaslod,
            eintak.skraarheiti,
            eintak.sha256,
            eintak.md5,
            eintak.staerd,
            eintak.stada,
            eintak.efnistegund,
            _nuna(),
        ),
    )
    audkenni = bendill.lastrowid
    if audkenni is None:
        raise HledsluVilla(
            f"Fékk ekkert auðkenni þegar {eintak.skraarheiti} var skráð."
        )
    return audkenni


def skra_utdratt(samband: Connection, snapshot_id: int, utdrattur: Utdrattur) -> None:
    """Skrifar eina útdráttarlínu ásamt mynstrinu sem framkallaði hana."""
    spurning = utdrattur.spurning
    samband.execute(
        UTDRATTUR_SQL,
        (
            snapshot_id,
            spurning.numer,
            spurning.lykill,
            spurning.texti,
            utdrattur.mynsturheiti,
            utdrattur.mynstur,
            utdrattur.mynsturflogg,
            utdrattur.afmorkun_heiti,
            utdrattur.afmorkun_mynstur,
            utdrattur.gildi,
            utdrattur.gildistexti,
            spurning.eining,
            utdrattur.tilvik,
            utdrattur.einstok,
            utdrattur.synishorn,
            spurning.takmarkanir,
            _nuna(),
        ),
    )


def krefjast_taflna(samband: Connection) -> None:
    """Stöðvar með skýrri villu hafi migration 005 ekki verið keyrð.

    Án þessa félli hleðslan á ``no such table``, sem segir ekki hvað á að gera.
    """
    for tafla in TOFLUR:
        if samband.execute(SQL_TAFLA_ER_TIL, (tafla,)).fetchone() is None:
            raise HledsluVilla(
                f"Taflan {tafla} er ekki til. Keyrðu migrations fyrst "
                "(gagnagrunnur.keyrari.keyra eða scripts/endurbyggja-grunn.sh)."
            )


def hlada_eintak(samband: Connection, eintak: Eintak) -> Hledsla:
    """Hleður einu eintaki: svarinu sjálfu og spurningunum fimm.

    Falli útdráttur fellur hleðslan öll — hálft svar er ekki niðurstaða
    (regla 6). :class:`UtdrattarVilla` er aldrei gripin hér.
    """
    krefjast_taflna(samband)
    fyrir = finna_eintak_i_grunni(samband, eintak.sotta_stund)
    if fyrir is not None:
        if fyrir["sha256"] != eintak.sha256:
            raise HledsluVilla(
                f"{eintak.skraarheiti} er þegar skráð undir sóknartímanum "
                f"{eintak.sotta_stund} en með aðra SHA-256.\n"
                f"  í grunni: {fyrir['sha256']}\n"
                f"  á diski:  {eintak.sha256}\n"
                "Hrágögnum er aldrei breytt eftir á (regla 4). Endurbyggðu "
                "grunninn með scripts/endurbyggja-grunn.sh í stað þess að "
                "skrifa yfir skráða niðurstöðu."
            )
        log.info("%s er þegar í grunninum — sleppt.", eintak.skraarheiti)
        return Hledsla(
            eintak=eintak,
            snapshot_id=int(fyrir["id"]),
            utdraettir=(),
            var_thegar_hladid=True,
        )

    utdraettir = tuple(draga_ut_allt(eintak.lesa_html()))
    snapshot_id = skra_eintak(samband, eintak)
    for utdrattur in utdraettir:
        skra_utdratt(samband, snapshot_id, utdrattur)

    log.info(
        "Hlóð %s (%s): %d svör.",
        eintak.skraarheiti,
        eintak.sotta_stund,
        len(utdraettir),
    )
    return Hledsla(
        eintak=eintak,
        snapshot_id=snapshot_id,
        utdraettir=utdraettir,
        var_thegar_hladid=False,
    )


def hlada_ollu(samband: Connection, mappa: Path | None = None) -> list[Hledsla]:
    """Hleður öllum eintökum möppunnar, elsta fyrst.

    Tóm mappa er villa en ekki tómur listi — sjá ``mbl_eintak.finna_eintok``.
    """
    return [hlada_eintak(samband, eintak) for eintak in finna_eintok(mappa)]


def stadfesta_svor(samband: Connection, sotta_stund: str) -> list[dict]:
    """Les svörin fimm aftur út úr SQL og staðfestir að þau séu öll komin.

    Hleðsla sem skrifar fjögur svör af fimm er ekki niðurstaða, svo frávik
    stöðvar keyrsluna í stað þess að skila hálfu korti (regla 6).
    """
    radir = [dict(rad) for rad in samband.execute(STADFESTA_SQL, (sotta_stund,))]
    if len(radir) != SVOR_A_EINTAK:
        raise HledsluVilla(
            f"Eintakið {sotta_stund} á að hafa {SVOR_A_EINTAK} svör í grunninum "
            f"en SQL skilar {len(radir)}. Spurningarnar fimm eru ekki allar "
            "svaranlegar úr grunninum."
        )
    return radir


def _keyra_eina_serd() -> int:
    """Keyrir migrations og hleðsluna á sjálfgefna grunninn — handvirk keyrsla.

    Migrations eru keyrðar með keyraranum úr ``gagnagrunnur.keyrari``, aldrei
    með eigin útgáfu af honum (regla 5).
    """
    from gagnagrunnur.keyrari import keyra
    from gagnagrunnur.tenging import tenging

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    with tenging() as samband:
        keyra(samband)
        hledslur = hlada_ollu(samband)
        for hledsla in hledslur:
            print(f"# {hledsla.eintak.skraarheiti} ({hledsla.eintak.sotta_stund})")
            for rad in stadfesta_svor(samband, hledsla.eintak.sotta_stund):
                print(f"  {rad['nr']}. {rad['spurning']} {rad['svar']} "
                      f"[{rad['mynsturheiti']}]")
    return 0


if __name__ == "__main__":
    sys.exit(_keyra_eina_serd())
