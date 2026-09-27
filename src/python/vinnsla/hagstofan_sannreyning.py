"""Sannreyning frystu gagnanna: það sem stöðvar hleðsluna áður en hún byrjar.

Rangur lestur á json-stat2 gefur tölur sem líta rétt út en eiga við annað —
brautskráningarhlutfall kvenna endar á karlalínunni. Villan sést hvergi, því
báðar tölurnar eru gildar prósentur. Eina vörnin er að neita að lesa gögn sem
stemma ekki, og þær neitanir eru allar saman komnar hér:

* skrárnar eru læsilegt JSON og ósnertar frá frystingu (reglur 4 og 8),
* svarið er sú útgáfa json-stat sem einingin kann,
* **fjöldi gilda er nákvæmlega margfeldi víddastærðanna.**

Síðasta atriðið er kjarninn: stemmi hann ekki hefur lestur farið úrskeiðis og
engin lína má fara í grunninn (regla 6 — hálf tafla er verri en engin).

Byggingarathuganir sem varða eina vídd (heil ``category.index``-röð, samsvörun
við kóðabókina) eru í ``hagstofan_viddir`` þar sem víddin verður til; hér eru
þær athuganir sem ná yfir gagnasafnið í heild.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .hagstofan_snid import STUDD_UTGAFA, UPPRUNASKRA, JsonstatVilla

if TYPE_CHECKING:  # aðeins fyrir gerðarmerkingar — enginn keyrsluinnflutningur
    from .hagstofan_snid import Vidd


def lesa_json(slod: Path) -> dict[str, Any]:
    """Les JSON-skrá og kastar skiljanlegri villu finnist hún ekki eða sé gölluð."""
    if not slod.is_file():
        raise JsonstatVilla(f"Frysta skráin finnst ekki: {slod}")
    try:
        innihald = json.loads(slod.read_text(encoding="utf-8"))
    except json.JSONDecodeError as villa:
        raise JsonstatVilla(f"{slod} er ekki gilt JSON: {villa}") from villa
    if not isinstance(innihald, dict):
        raise JsonstatVilla(f"{slod} átti að geyma hlut en geymir {type(innihald)}.")
    return innihald


def krefjast_strengs(gogn: dict[str, Any], lykill: str, skra: str) -> str:
    """Sækir strengjareit og stöðvar sé hann tómur eða af rangri gerð."""
    gildi = gogn.get(lykill)
    if not isinstance(gildi, str) or not gildi.strip():
        raise JsonstatVilla(f"{skra} vantar reitinn {lykill!r} sem texta.")
    return gildi


def sannreyna_summur(mappa: Path, upprunagogn: dict[str, Any]) -> None:
    """Ber SHA-256 frystu skránna saman við ``provenance.json`` (reglur 4 og 8)."""
    skradar = upprunagogn.get("sha256")
    if not isinstance(skradar, dict) or not skradar:
        raise JsonstatVilla(
            f"{mappa / UPPRUNASKRA} geymir engar SHA-256 gátsummur. Án þeirra er "
            "ekki hægt að staðfesta að frystu gögnin séu ósnert."
        )
    for skraarheiti, vaent in sorted(skradar.items()):
        _sannreyna_summu(mappa / skraarheiti, vaent)


def _sannreyna_summu(slod: Path, vaent: str) -> None:
    """Stöðvar hafi ein skrá breyst frá frystingu."""
    if not slod.is_file():
        raise JsonstatVilla(f"{slod} er skráð í provenance en finnst ekki.")
    raun = hashlib.sha256(slod.read_bytes()).hexdigest()
    if raun != vaent:
        raise JsonstatVilla(
            f"{slod} hefur breyst frá frystingu.\n"
            f"  skráð SHA-256:   {vaent}\n"
            f"  á diski SHA-256: {raun}\n"
            "Hrágögnum er aldrei breytt eftir á (regla 4); sæktu óbreyttu "
            "skrána úr git."
        )


def sannreyna_utgafu(svar: dict[str, Any]) -> None:
    """Stöðvar sé svarið ekki json-stat2 af þeirri útgáfu sem einingin kann."""
    if svar.get("class") != "dataset":
        raise JsonstatVilla(
            f"Svarið er af gerðinni {svar.get('class')!r} en verður að vera 'dataset'."
        )
    utgafa = str(svar.get("version", ""))
    if utgafa != STUDD_UTGAFA:
        raise JsonstatVilla(
            f"Svarið er json-stat útgáfa {utgafa!r}; einingin les aðeins "
            f"{STUDD_UTGAFA!r}. Ný útgáfa getur breytt merkingu `size` og "
            "`category.index` og yrði þá lesin rangt."
        )


def sannreyna_gildafjolda(fjoldi: int, viddir: tuple[Vidd, ...]) -> None:
    """Stöðvar stemmi fjöldi gilda ekki við margfeldi víddastærðanna.

    json-stat2 skilar marghliða töflu sem flötum lista. Sé hann ekki nákvæmlega
    jafnlangur margfeldi ``size`` er ekki vitað hvaða gildi á við hvaða
    samsetningu vídda, og þá er hver einasta tala í töflunni ómarktæk.
    """
    vaentur = math.prod(vidd.staerd for vidd in viddir)
    if fjoldi != vaentur:
        staerdir = " x ".join(f"{v.kodi}={v.staerd}" for v in viddir)
        raise JsonstatVilla(
            f"Fjöldi gilda stemmir ekki við víddastærðirnar: `value` telur "
            f"{fjoldi} gildi en {staerdir} gefur {vaentur}. "
            "Lestur á json-stat2 hefur farið úrskeiðis og engin lína er skrifuð."
        )
