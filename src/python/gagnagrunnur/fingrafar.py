"""Fingrafar af grunninum — sami grunnur gefur sömu summu.

Þetta er mælitækið á bak við reglu 5: grunnurinn er **afleiða, ekki frumgagn**.
Tvær hreinar endurbyggingar úr sömu migrations og sömu hrágögnum eiga að gefa
sama fingrafar. Gera þær það ekki er eitthvað í pípunni sem veltur á keyrslu
frekar en á gögnum.

Tímastimplar eru undanskildir: þeir segja *hvenær* var byggt, ekki *hvað* var
byggt. Þeir dálkar eru taldir upp í ``BREYTILEGIR_DALKAR``.

Keyrsla utan frá::

    PYTHONPATH=src/python python3 -m gagnagrunnur.fingrafar [slod-a-grunni]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from sqlite3 import Connection

from .tenging import tenging

# Dálkar sem breytast milli keyrslna og segja ekkert um innihald grunnsins.
BREYTILEGIR_DALKAR: dict[str, tuple[str, ...]] = {
    "schema_migrations": ("applied_at",),
}

# Hvítlisti fyrir nöfn sem fara inn í SQL sem auðkenni (regla 5). Gildi fara
# ALLTAF inn sem breytur; auðkenni er ekki hægt að binda, svo þau eru
# sannreynd hér og vitnuð — aldrei bara skeytt saman.
NAFNAMYNSTUR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _oruggt_nafn(nafn: str) -> str:
    """Sannreynir auðkenni gegn hvítlistanum og skilar því vitnuðu."""
    if not NAFNAMYNSTUR.match(nafn):
        raise ValueError(
            f"Nafnið {nafn!r} stenst ekki hvítlistann og fer ekki inn í fyrirspurn."
        )
    return f'"{nafn}"'


def _toflur(samband: Connection) -> list[str]:
    """Nöfn allra taflna verkefnisins, í stafrófsröð."""
    radir = samband.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [rad["name"] for rad in radir]


def _skema(samband: Connection) -> list[str]:
    """Allar skilgreiningar í grunninum sem texti, í fastri röð."""
    radir = samband.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' "
        "ORDER BY type, name"
    ).fetchall()
    return [
        f"{rad['type']}|{rad['name']}|{' '.join((rad['sql'] or '').split())}"
        for rad in radir
    ]


def _dalkar(samband: Connection, tafla: str) -> list[str]:
    """Dálkar töflunnar sem telja með í fingrafarinu, í skilgreiningarröð."""
    radir = samband.execute(f"PRAGMA table_info({_oruggt_nafn(tafla)})").fetchall()
    sleppt = BREYTILEGIR_DALKAR.get(tafla, ())
    return [rad["name"] for rad in radir if rad["name"] not in sleppt]


def _innihald(samband: Connection, tafla: str) -> list[str]:
    """Allar raðir töflunnar sem texti, í fastri röð og án breytilegra dálka."""
    dalkar = _dalkar(samband, tafla)
    if not dalkar:
        fjoldi = samband.execute(
            f"SELECT count(*) AS n FROM {_oruggt_nafn(tafla)}"
        ).fetchone()["n"]
        return [f"radir: {fjoldi}"]

    listi = ", ".join(_oruggt_nafn(d) for d in dalkar)
    radir = samband.execute(
        f"SELECT {listi} FROM {_oruggt_nafn(tafla)} ORDER BY {listi}"
    ).fetchall()
    return [json.dumps(list(rad), default=str, ensure_ascii=False) for rad in radir]


def lysing(samband: Connection) -> str:
    """Grunnurinn allur sem texti í fastri röð — lesanlegt form fingrafarsins."""
    linur = ["# skema", *_skema(samband)]
    for tafla in _toflur(samband):
        linur.append(f"# tafla {tafla} ({', '.join(_dalkar(samband, tafla))})")
        linur.extend(_innihald(samband, tafla))
    return "\n".join(linur) + "\n"


def fingrafar(samband: Connection) -> str:
    """SHA-256 af ``lysing()`` — eitt gildi sem tvær byggingar má bera saman við."""
    return hashlib.sha256(lysing(samband).encode("utf-8")).hexdigest()


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description="Fingrafar af SQL-grunninum")
    thattari.add_argument(
        "slod", nargs="?", default=None, help="Slóð á grunninn (sjálfgefið: úr tenging)"
    )
    thattari.add_argument(
        "--texti", action="store_true", help="Prenta lýsinguna sjálfa í stað summunnar"
    )
    valkostir = thattari.parse_args(rok)

    with tenging(valkostir.slod) as samband:
        print(lysing(samband) if valkostir.texti else fingrafar(samband), end="")
        if not valkostir.texti:
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
