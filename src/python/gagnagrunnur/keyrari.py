"""Keyrari fyrir SQL-migrations (regla 5).

Öll uppbygging grunnsins verður til úr ``src/sql/migrations/``, númeruðum í
röð. Hver migration er keyrð nákvæmlega einu sinni og skráð í töfluna
``schema_migrations`` með SHA-256 af innihaldi sínu.

Kjarnareglan: **migration er aldrei breytt eftir að hún hefur verið keyrð.**
Breytist innihaldið stöðvast keyrslan, því þá lýsir sagan ekki lengur þeim
grunni sem til er og hann er ekki endurbyggjanlegur.

Keyrarinn er ræstur úr ``src/python/main.py --skref hlada`` og úr
``scripts/endurbyggja-grunn.sh``.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection, Error as SqliteVilla

from .tenging import ROT

log = logging.getLogger(__name__)

MIGRATIONS_MAPPA = ROT / "src" / "sql" / "migrations"

# Regla 1.2: 001_kebab-case.sql — ASCII, lágstafir, engin bil.
SKRAARMYNSTUR = re.compile(r"^(\d{3,})_([a-z0-9]+(?:[-_][a-z0-9]+)*)\.sql$")

# Færslustýring inni í migration myndi rjúfa heildina sem beita() treystir á.
FAERSLUSTYRING = re.compile(r"(?mi)^\s*(COMMIT|ROLLBACK)\b")
LINUATHUGASEMD = re.compile(r"--[^\n]*")
BLOKKARATHUGASEMD = re.compile(r"/\*.*?\*/", re.DOTALL)

TAFLA_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    number     INTEGER PRIMARY KEY,  -- númerið úr skráarheitinu
    name       TEXT    NOT NULL,     -- heitið úr skráarheitinu
    checksum   TEXT    NOT NULL,     -- SHA-256 af innihaldi skrárinnar
    applied_at TEXT    NOT NULL      -- ISO 8601, UTC
)
"""


class MigrationVilla(RuntimeError):
    """Migration-sagan stemmir ekki — grunnurinn er ekki endurbyggjanlegur."""


@dataclass(frozen=True)
class Migration:
    """Ein migration-skrá á diski."""

    numer: int
    heiti: str
    slod: Path
    summa: str

    @property
    def skraarheiti(self) -> str:
        return self.slod.name


def summa_skrar(slod: Path) -> str:
    """SHA-256 af innihaldi skrárinnar, sextándakerfi."""
    return hashlib.sha256(slod.read_bytes()).hexdigest()


def finna_migrations(mappa: Path | None = None) -> list[Migration]:
    """Les allar migration-skrár í númeraröð.

    Skrá sem passar ekki við ``SKRAARMYNSTUR`` stöðvar keyrslu í stað þess að
    vera sleppt þegjandi (regla 6) — annars gæti migration horfið úr röðinni.
    """
    mappa = mappa or MIGRATIONS_MAPPA
    if not mappa.is_dir():
        raise MigrationVilla(f"Migration-mappan finnst ekki: {mappa}")

    fundnar: dict[int, Migration] = {}
    for slod in sorted(mappa.glob("*.sql")):
        samsvorun = SKRAARMYNSTUR.match(slod.name)
        if samsvorun is None:
            raise MigrationVilla(
                f"Skráarheitið {slod.name} passar ekki við 001_heiti.sql "
                "(ASCII, lágstafir, bandstrik — regla 1.2)."
            )
        numer = int(samsvorun.group(1))
        ef_fyrir = fundnar.get(numer)
        if ef_fyrir is not None:
            raise MigrationVilla(
                f"Tvær migrations bera númerið {numer:03d}: "
                f"{ef_fyrir.skraarheiti} og {slod.name}. Númer verða að vera einkvæm."
            )
        fundnar[numer] = Migration(
            numer=numer,
            heiti=samsvorun.group(2),
            slod=slod,
            summa=summa_skrar(slod),
        )

    i_rod = [fundnar[numer] for numer in sorted(fundnar)]
    _vara_vid_gotum(i_rod)
    return i_rod


def _vara_vid_gotum(migrations: list[Migration]) -> None:
    """Varar við götum í númeraröðinni — gat getur þýtt týnda migration.

    Þetta er viðvörun en ekki villa: meðan fimm agentar vinna samhliða
    (#6–#10) verða göt tímabundið til á greinum.
    """
    vaent = [m.numer for m in migrations]
    got = sorted(set(range(1, max(vaent, default=0) + 1)) - set(vaent))
    if got:
        log.warning(
            "Göt í migration-númerum: %s. Vantar migration eða er hún á annarri grein?",
            ", ".join(f"{n:03d}" for n in got),
        )


def tryggja_toflu(samband: Connection) -> None:
    """Býr til ``schema_migrations`` sé hún ekki þegar til."""
    samband.execute(TAFLA_DDL)


def lesa_skradar(samband: Connection) -> dict[int, dict[str, str]]:
    """Skilar þeim migrations sem þegar hafa verið keyrðar, eftir númeri."""
    radir = samband.execute(
        "SELECT number, name, checksum, applied_at FROM schema_migrations "
        "ORDER BY number"
    ).fetchall()
    return {rad["number"]: dict(rad) for rad in radir}


def stadfesta_sogu(
    a_diski: list[Migration], skradar: dict[int, dict[str, str]]
) -> None:
    """Ber saman skráða sögu við það sem er á diski og stöðvar við misræmi."""
    eftir_numeri = {m.numer: m for m in a_diski}

    for numer, skrad in skradar.items():
        migration = eftir_numeri.get(numer)
        if migration is None:
            raise MigrationVilla(
                f"Migration {numer:03d} ({skrad['name']}) er skráð keyrð "
                f"{skrad['applied_at']} en finnst ekki í {MIGRATIONS_MAPPA.name}/. "
                "Grunnurinn er ekki endurbyggjanlegur úr þeim skrám sem eru til."
            )
        if migration.heiti != skrad["name"]:
            raise MigrationVilla(
                f"Migration {numer:03d} hét {skrad['name']} þegar hún var keyrð "
                f"en heitir núna {migration.heiti}. Endurnefndu ekki keyrða migration."
            )
        if migration.summa != skrad["checksum"]:
            raise MigrationVilla(
                f"Innihald {migration.skraarheiti} hefur breyst eftir að hún var "
                f"keyrð {skrad['applied_at']}.\n"
                f"  skráð SHA-256:   {skrad['checksum']}\n"
                f"  á diski SHA-256: {migration.summa}\n"
                "Migration er aldrei breytt eftir keyrslu (regla 5) — búðu til nýja "
                "migration í staðinn, eða endurbyggðu grunninn frá grunni með "
                "scripts/endurbyggja-grunn.sh."
            )

    _stadfesta_rod(a_diski, skradar)


def _stadfesta_rod(
    a_diski: list[Migration], skradar: dict[int, dict[str, str]]
) -> None:
    """Stöðvar ef óbeitt migration er með lægra númer en sú hæsta sem keyrð var.

    Væri henni bætt við aftan á fengist annar grunnur en við hreina
    endurbyggingu, og grunnurinn hætti að vera fyrirsjáanleg afleiða.
    """
    if not skradar:
        return
    haesta_keyrd = max(skradar)
    a_eftir = [m for m in a_diski if m.numer not in skradar and m.numer < haesta_keyrd]
    if a_eftir:
        heiti = ", ".join(m.skraarheiti for m in a_eftir)
        raise MigrationVilla(
            f"Þessar migrations eru óbeittar en bera lægra númer en {haesta_keyrd:03d} "
            f"sem þegar var keyrð: {heiti}. Keyrsla úr röð gæfi annan grunn en hrein "
            "endurbygging. Keyrðu scripts/endurbyggja-grunn.sh."
        )


def _an_athugasemda(sql: str) -> str:
    """Fjarlægir SQL-athugasemdir svo leit að COMMIT/ROLLBACK gefi ekki falskt svar."""
    return LINUATHUGASEMD.sub("", BLOKKARATHUGASEMD.sub("", sql))


def beita(samband: Connection, migration: Migration) -> None:
    """Keyrir eina migration og skráir hana — allt í einni færslu.

    Falli migration í miðju kafi er öllu rúllað til baka, líka færslunni í
    ``schema_migrations``. Grunnurinn situr því aldrei hálfbyggður.
    """
    sql = migration.slod.read_text(encoding="utf-8")

    faerslustyring = FAERSLUSTYRING.search(_an_athugasemda(sql))
    if faerslustyring is not None:
        raise MigrationVilla(
            f"{migration.skraarheiti} inniheldur {faerslustyring.group(1).upper()}. "
            "Migration stýrir ekki eigin færslu — keyrarinn gerir það, svo hægt sé "
            "að rúlla henni til baka í heilu lagi."
        )

    try:
        samband.executescript(sql)
        samband.execute(
            "INSERT INTO schema_migrations (number, name, checksum, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (migration.numer, migration.heiti, migration.summa, _nuna()),
        )
        samband.commit()
    except SqliteVilla as villa:
        samband.rollback()
        raise MigrationVilla(
            f"{migration.skraarheiti} féll og var rúllað til baka: {villa}"
        ) from villa

    log.info("Keyrði migration %s", migration.skraarheiti)


def _nuna() -> str:
    """Tímastimpill í ISO 8601, UTC, á sekúndunákvæmni."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def keyra(samband: Connection, mappa: Path | None = None) -> list[Migration]:
    """Keyrir þær migrations sem eftir standa og skilar þeim sem voru keyrðar."""
    tryggja_toflu(samband)
    samband.commit()

    a_diski = finna_migrations(mappa)
    skradar = lesa_skradar(samband)
    stadfesta_sogu(a_diski, skradar)

    obeittar = [m for m in a_diski if m.numer not in skradar]
    for migration in obeittar:
        beita(samband, migration)
    return obeittar
