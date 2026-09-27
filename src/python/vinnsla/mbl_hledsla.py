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
"""

from __future__ import annotations

import logging
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


def hlada_eintak(samband: Connection, eintak: Eintak) -> Hledsla:
    """Hleður einu eintaki: svarinu sjálfu og spurningunum fimm.

    Falli útdráttur fellur hleðslan öll — hálft svar er ekki niðurstaða
    (regla 6). :class:`UtdrattarVilla` er aldrei gripin hér.
    """
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
