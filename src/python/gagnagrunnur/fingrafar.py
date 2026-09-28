"""Fingrafar af grunninum — sami grunnur gefur sömu summu.

Þetta er mælitækið á bak við reglu 5: grunnurinn er **afleiða, ekki frumgagn**.
Tvær hreinar endurbyggingar úr sömu migrations og sömu hrágögnum eiga að gefa
sama fingrafar. Gera þær það ekki er eitthvað í pípunni sem veltur á keyrslu
frekar en á gögnum.

REGLAN — HVAÐ TELUR MEÐ
    Fingrafarið mælir það sem **heimildirnar** ákveða, ekki það sem **keyrslan**
    ákveður. Prófsteinninn á hvern dálk er ein spurning: getur rétt keyrsla úr
    sömu heimildum framkallað sama gildi aftur?

    * **Telur með** — gildið kemur úr hrágögnunum eða provenance þeirra og er
      þar með eiginleiki gagnanna. Dæmi: ``fetch_log.fetched_at``. Sóknin
      gerðist einu sinni, fyrir frystingu, og sóknartíminn er **lesinn** úr
      ``data/raw/**/provenance.json``. Hann er því sá sami í hverri byggingu að
      eilífu og breytist aðeins ef gögnin sjálf breytast — sem er nákvæmlega
      það sem fingrafarið á að sjá.
    * **Telur ekki með** — gildið verður til við keyrsluna sjálfa, af klukkunni
      á þeirri vél sem hlóð. Dæmi: ``hagstofan_datasets.loaded_at``. Hann er
      ``datetime.now()`` á hleðslustundu og **engin** endurbygging getur
      endurtekið hann, hversu rétt sem hún er.

    Auðkenni sem SQLite úthlutar teljast með. Þau standast prófsteininn: hrein
    bygging úr sömu heimildum úthlutar þeim eins. Hreyfist slíkt auðkenni milli
    bygginga er hleðslan ekki endurkeyranleg, og það á fingrafarið að segja —
    ekki hylma yfir (sjá #8 og #47).

NAFNAVENJAN SEM BER REGLUNA
    Tímastimpill sem keyrslan setur er nefndur ``<sögn>_at``, þar sem sögnin
    lýsir því sem **pípan** gerði við línuna: ``loaded_at``, ``extracted_at``,
    ``applied_at``. Sagnirnar eru í :data:`KEYRSLUSAGNIR` og reglan gildir í
    öllum töflum, líka þeim sem ekki eru til enn — ný migration erfir hana án
    þess að nokkuð sé skráð hér. Það er ástæðan fyrir því að hér er regla og
    ekki listi af töflum og dálkum: listi sem þarf að muna að uppfæra er sama
    villan aftur.

    ``fetched_at`` er ekki í þeim flokki þótt pípan sæki: gildið er lesið úr
    provenance, aldrei af klukkunni.

    Tímastimpill sem passar hvorugt — nýtt ``saved_at`` í migration 006, segjum
    — fellir ``tests/test_fingrafar.py`` með skýringu í stað þess að sleppa inn
    þegjandi. Þar er ákvörðunin tekin meðvitað, einu sinni.

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

# Sagnir sem lýsa því sem PÍPAN gerði við línuna — hlaða, draga út, beita
# migration. Tímastimpill sem heitir <sögn>_at er lesinn af klukkunni á
# keyrslustund og telur því ekki með (sjá REGLAN í haus skrárinnar).
#
# Hér eru AÐEINS sagnir sem ekkert nema pípan getur eignað sér. Tvíræðar
# sagnir eins og `created` og `updated` eru vísvitandi utan listans: heimild
# getur átt þær líka, svo nýr `updated_at` á að kalla á ákvörðun og fellir
# prófið þangað til hún er tekin.
KEYRSLUSAGNIR: frozenset[str] = frozenset(
    {
        "applied",
        "computed",
        "exported",
        "extracted",
        "generated",
        "imported",
        "ingested",
        "inserted",
        "loaded",
        "migrated",
        "processed",
        "transformed",
    }
)

# Nafnavenja verkefnisins: hver tímastimpilsdálkur endar á _at og sögnin er
# síðasta orðið fyrir endinguna (`loaded_at`, `first_loaded_at`).
TIMASTIMPILSMYNSTUR = re.compile(r"^(?:[a-z0-9_]+_)?(?P<sogn>[a-z]+)_at$")

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


def er_timastimpill(dalkur: str) -> bool:
    """Hvort dálksheitið sé tímastimpill samkvæmt nafnavenjunni (endar á ``_at``)."""
    return TIMASTIMPILSMYNSTUR.match(dalkur) is not None


def er_keyrslustimpill(dalkur: str) -> bool:
    """Hvort dálkurinn beri tíma keyrslunnar — og telji því ekki með.

    Svarið ræðst af nafninu einu, ekki af töflunni, svo reglan gildi eins í
    töflum sem ekki eru til enn::

        er_keyrslustimpill("loaded_at")   -> True   (klukkan við hleðslu)
        er_keyrslustimpill("fetched_at")  -> False  (lesinn úr provenance)
    """
    samsvorun = TIMASTIMPILSMYNSTUR.match(dalkur)
    return samsvorun is not None and samsvorun.group("sogn") in KEYRSLUSAGNIR


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


def _dalkanofn(samband: Connection, tafla: str) -> list[str]:
    """Öll dálksheiti töflunnar í skilgreiningarröð."""
    radir = samband.execute(f"PRAGMA table_info({_oruggt_nafn(tafla)})").fetchall()
    return [rad["name"] for rad in radir]


def _dalkar(samband: Connection, tafla: str) -> list[str]:
    """Dálkar töflunnar sem telja með í fingrafarinu, í skilgreiningarröð."""
    return [d for d in _dalkanofn(samband, tafla) if not er_keyrslustimpill(d)]


def sleppt_dalkar(samband: Connection, tafla: str) -> list[str]:
    """Dálkar töflunnar sem fingrafarið sleppir — tími keyrslunnar, ekki gögnin.

    Listinn er birtur í :func:`lysing` svo hver undanþága sé sýnileg og
    sannreynanleg í ``--texti``, ekki falin inni í summunni.
    """
    return [d for d in _dalkanofn(samband, tafla) if er_keyrslustimpill(d)]


def _innihald(samband: Connection, tafla: str) -> list[str]:
    """Allar raðir töflunnar sem texti, í fastri röð og án keyrslustimpla."""
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
        haus = f"# tafla {tafla} ({', '.join(_dalkar(samband, tafla))})"
        sleppt = sleppt_dalkar(samband, tafla)
        if sleppt:
            haus += f" — keyrslustimplar sleppt: {', '.join(sleppt)}"
        linur.append(haus)
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
