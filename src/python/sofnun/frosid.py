"""Frosin eintök á eldri sniðum — þekkt og skilað, ekki sótt aftur (regla 4).

``sofnun.hragogn.finna_fyrra_svar`` þekkir eintak á því provenance-sniði sem
``sofnun.beidni`` skrifar: fingrafar beiðninnar er reiknað úr reitunum
``provider``, ``endpoint``, ``method`` og ``parameters``. Tvö söfn úr
upprunaverkefninu voru hins vegar fryst á **eldri sniðum** sem bera þá reiti
ekki:

* ``data/raw/hagstofan/provenance.json`` skráir ``methods`` í fleirtölu — tvö
  köll í einni skrá — og ``sha256`` sem kort af skráarheiti í summu. Hvorki
  ``provider`` né ``parameters`` eru þar.
* ``data/raw/mbl/mbl-*.json`` er lýsigagnaskrá skriftunnar sjálfrar
  (``source_url``, ``md5``) og heitir ekki ``provenance.json``.

Fingrafarið sér þau því ekki og lagið myndi senda beiðnina aftur. Þessi eining
þekkir sniðin, sannreynir skrána og skilar henni sem ``Svar``. Þannig sleppa öll
söfn kalli eftir sömu reglu, hvort sniðið sem provenance þeirra er á, og
sjálfgefin keyrsla sendir ekkert netkall.

**Ósannreynt eintak er ekki skilað.** Finnist engin skráð summa til að bera
skrána við, eða stemmi hún ekki, stöðvast keyrslan með ``FrosidVilla``. Þögult
skemmt hrágagn væri verra en ekkert (regla 6) — sama afstaða og í
``sofnun.hragogn``.

Einingin er ekki sama verk og ``vidmid.provenance``: þar er öll frystiskráin
``data/raw/frysting.json`` staðfest í einu, hér er **lesið** það sem liggur í
möppu eins safns þegar söfnun er keyrð.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .hragogn import HRAGOGN, Svar, mappa_safns

log = logging.getLogger(__name__)

ARFUR_PROVENANCE = "provenance.json"

# Summureitir sem eldri sniðin nota, í þeirri röð sem þeir eru reyndir. Heitið
# er líka heiti algrímsins í ``hashlib``. MD5 er ekki valið af öryggisástæðum —
# það er einfaldlega það sem gamla mbl-skriftan skráði, og spurningin hér er
# hvort skráin hafi breyst frá frystingu, ekki hvort einhver hafi falsað hana.
SUMMUREITIR = ("sha256", "md5")


class FrosidVilla(RuntimeError):
    """Frosið eintak er ósannreynanlegt, tvírætt, eða stemmir ekki við summu."""


@dataclass(frozen=True)
class Skrad:
    """Það sem eldra snið skráði um eina frosna skrá."""

    algrim: str      # heiti algrímsins í hashlib, t.d. "sha256"
    summa: str       # summan sem var skráð við frystingu
    heimild: Path    # skráin sem geymir summuna
    skjal: dict      # lýsigagnaskjalið sjálft; notað sem provenance svarsins


def frosin_eintok(thjonusta: str, mynstur: str, rot: Path = HRAGOGN) -> list[Path]:
    """Skilar frosnum skrám safnsins sem passa við ``mynstur`` (glob)."""
    mappa = mappa_safns(thjonusta, rot)
    if not mappa.is_dir():
        return []
    return sorted(skra for skra in mappa.glob(mynstur) if skra.is_file())


def _lesa_json(slod: Path) -> dict | None:
    """Les JSON-skjal; skilar ``None`` og segir frá sé það ónýtt (regla 6)."""
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as villa:
        log.warning("Hunsa ónýta lýsigagnaskrá %s: %s", slod.name, villa)
        return None
    if not isinstance(skjal, dict):
        log.warning("Hunsa %s: lýsigögn eiga að vera JSON-hlutur.", slod.name)
        return None
    return skjal


def _summa_ur_korti(skjal: dict, heiti: str) -> tuple[str, str] | None:
    """Sniðið hjá Hagstofunni: summureitur er kort af skráarheiti í summu."""
    for reitur in SUMMUREITIR:
        kort = skjal.get(reitur)
        if isinstance(kort, dict) and isinstance(kort.get(heiti), str):
            return reitur, kort[heiti]
    return None


def _summa_ur_skjali(skjal: dict) -> tuple[str, str] | None:
    """Sniðið hjá mbl: skjalið lýsir einni skrá og summan er stakt gildi."""
    for reitur in SUMMUREITIR:
        gildi = skjal.get(reitur)
        if isinstance(gildi, str):
            return reitur, gildi
    return None


def _skrad_um(skra: Path) -> Skrad:
    """Finnur skráða summu frosnu skrárinnar, eða fellur með ``FrosidVilla``.

    Tvö snið eru reynd: ``provenance.json`` möppunnar, sem skráir kort af
    skráarheiti í summu, og fylgiskrá með sama stofni (``mbl-….json``), sem
    lýsir einni skrá.
    """
    arfur = skra.parent / ARFUR_PROVENANCE
    if arfur.is_file():
        skjal = _lesa_json(arfur)
        if skjal is not None:
            fundid = _summa_ur_korti(skjal, skra.name)
            if fundid is not None:
                return Skrad(*fundid, heimild=arfur, skjal=skjal)

    fylgiskra = skra.with_suffix(".json")
    if fylgiskra != skra and fylgiskra.is_file():
        skjal = _lesa_json(fylgiskra)
        if skjal is not None:
            fundid = _summa_ur_skjali(skjal)
            if fundid is not None:
                return Skrad(*fundid, heimild=fylgiskra, skjal=skjal)

    raise FrosidVilla(
        f"{skra.name} liggur í {skra.parent.name}/ en engin skráð summa fannst "
        f"til að bera hana við — hvorki í {ARFUR_PROVENANCE} né í "
        f"{fylgiskra.name}. Ósannreynt hrágagn er ekki notað (regla 6)."
    )


def _stadfesta(skra: Path, skrad: Skrad) -> bytes:
    """Skilar bætum skrárinnar hafi summa hennar staðist, annars ``FrosidVilla``."""
    baeti = skra.read_bytes()
    reiknud = hashlib.new(skrad.algrim, baeti).hexdigest()
    if reiknud != skrad.summa.strip().lower():
        raise FrosidVilla(
            f"{skrad.algrim.upper()} stemmir ekki fyrir {skra.name}: "
            f"{skrad.heimild.name} skráir aðra summu. Hrágögnin hafa breyst frá "
            f"því þau voru fryst og tölur byggðar á þeim eru ekki rekjanlegar."
        )
    return baeti


def frosid_svar(thjonusta: str, mynstur: str, rot: Path = HRAGOGN) -> Svar | None:
    """Skilar frosnu eintaki safnsins sem ``Svar``, eða ``None`` sé það ekki til.

    Eintakið er sannreynt gegn skráðri summu áður en það er skilað. Stemmi hún
    ekki — eða passi fleiri en ein skrá við ``mynstur``, svo óljóst sé hvoru
    tölurnar tilheyra — stöðvast keyrslan með ``FrosidVilla`` í stað þess að
    byggja niðurstöður á hrágagni sem enginn getur rakið.
    """
    eintok = frosin_eintok(thjonusta, mynstur, rot)
    if not eintok:
        return None
    if len(eintok) > 1:
        heiti = ", ".join(skra.name for skra in eintok)
        raise FrosidVilla(
            f"{thjonusta}: {len(eintok)} eintök passa við '{mynstur}' ({heiti}). "
            f"Óljóst hvoru tölurnar tilheyra — eitt frosið eintak á safn."
        )

    skra = eintok[0]
    skrad = _skrad_um(skra)
    baeti = _stadfesta(skra, skrad)
    log.info(
        "Sleppi kalli á %s — frosið eintak %s er sannreynt (%s).",
        thjonusta, skra.name, skrad.algrim,
    )
    return Svar(baeti=baeti, slod_skrar=skra, provenance=skrad.skjal, ur_safni=True)
