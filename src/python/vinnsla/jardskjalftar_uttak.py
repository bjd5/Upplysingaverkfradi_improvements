"""Úttak skjálftavinnslunnar í ``data/processed/`` (issue #14, pakki P2.3).

Fimmta og síðasta skrefið í upprunaskriftunni ``src/earthquakes.py`` — *skrifa*.
Gamla skriftan skrifaði tvennt: CSV-töflur undir ``data/processed/earthquakes/``
og Markdown-búta undir ``site/_generated/`` sem Quarto límdi inn í síðuna.

**Markdown-bútarnir eru ekki fluttir.** Í þessu verkefni fer engin tala úr Python
beint í birtingu: flæðið er ``data/raw/`` → vinnsla → SQL-grunnur → ``web/gogn/``
(kafli 0), og HTML verður til í ``web/`` en ekki hér (regla 2). Þessi eining
skrifar því **aðeins** afleiddar töflur í ``data/processed/`` og aldrei í
``web/gogn/``.

Þrjár skrár, allar afleiddar og allar endurbyggjanlegar úr frosna svarinu:

* ``events.csv`` — ein lína á atburð, dálkar í sömu röð og taflan ``earthquakes``.
* ``daily.csv`` — ein lína á hvern UTC-dag, líka dagana með núll atburði.
* ``samantekt.json`` — lýsandi tölfræði úrtaksins (sjá ``jardskjalftar_talning.draga_saman``).

Úttakið er **hrein afleiða hrágagnanna**: það inniheldur engan keyrslutíma og
engan vegguklukkustimpil, svo tvær keyrslur á sömu gögnum gefa sömu bæti.
Stimpill sem breytist við hverja keyrslu myndi láta úttakið virðast nýtt þótt
gögnin séu óbreytt — sama gildran og lærðist af issue #47.

Keyrsla án nets, með eigin inngangi (tengingin við ``src/python/main.py`` er
issue #39)::

    PYTHONPATH=src/python python3 -m vinnsla.jardskjalftar_uttak

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

try:  # keyrt sem eining innan pakkans (venjulega leiðin)
    from .jardskjalftar import Skjalfti, lesa_skjalfta
    from .jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, lesa_afmorkun
    from .jardskjalftar_talning import DagsTalning, Samantekt, dagleg_talning, draga_saman
except ImportError:  # keyrt beint úr möppunni
    from jardskjalftar import Skjalfti, lesa_skjalfta
    from jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, lesa_afmorkun
    from jardskjalftar_talning import DagsTalning, Samantekt, dagleg_talning, draga_saman

log = logging.getLogger(__name__)

ROT = Path(__file__).resolve().parents[3]
UNNID = ROT / "data" / "processed" / "earthquakes"

ATBURDASKRA = "events.csv"
DAGASKRA = "daily.csv"
SAMANTEKTARSKRA = "samantekt.json"

# Dálkarnir eru lesnir úr gagnaklösunum sjálfum. Þannig getur dálkur hvorki
# horfið úr CSV-skránni né bæst í hana án þess að klasinn breytist líka.
ATBURDASVID = tuple(svid.name for svid in fields(Skjalfti))
DAGASVID = tuple(svid.name for svid in fields(DagsTalning))


@dataclass(frozen=True)
class Uttak:
    """Það sem vinnslan skrifaði — slóðirnar og tölurnar sem prófin bera saman."""

    atburdaskra: Path
    dagaskra: Path
    samantektarskra: Path
    atburdir: int
    dagar: int


def skrifa_csv(slod: Path, rader: list[dict[str, object]], svid: tuple[str, ...]) -> None:
    """Skrifar CSV-skrá með fastri dálkaröð og UTF-8 kóðun.

    Línuskilin eru ``\\n`` á öllum stýrikerfum svo skráin verði sú sama hvar sem
    hún er byggð.
    """
    slod.parent.mkdir(parents=True, exist_ok=True)
    with slod.open("w", encoding="utf-8", newline="") as skrifari:
        tafla = csv.DictWriter(skrifari, fieldnames=svid, lineterminator="\n")
        tafla.writeheader()
        tafla.writerows(rader)


def skrifa_samantekt(slod: Path, samantekt: Samantekt) -> None:
    """Skrifar samantektina sem JSON með íslenskum stöfum óbreyttum."""
    slod.parent.mkdir(parents=True, exist_ok=True)
    texti = json.dumps(asdict(samantekt), ensure_ascii=False, indent=2, sort_keys=True)
    slod.write_text(texti + "\n", encoding="utf-8")


def skrifa_uttak(
    skjalftar: list[Skjalfti],
    dagatalning: list[DagsTalning],
    samantekt: Samantekt,
    mappa: Path | str | None = None,
) -> Uttak:
    """Skrifar allar þrjár afleiddu skrárnar í ``data/processed/earthquakes/``.

    Skrifar **aldrei** í ``web/gogn/``: sú mappa fær aðeins JSON frá
    útflutningslaginu eftir að grunnurinn hefur verið byggður (kafli 0).
    """
    mappa = Path(mappa) if mappa is not None else UNNID
    _krefjast_utan_vefs(mappa)

    atburdaskra = mappa / ATBURDASKRA
    dagaskra = mappa / DAGASKRA
    samantektarskra = mappa / SAMANTEKTARSKRA

    skrifa_csv(atburdaskra, [asdict(s) for s in skjalftar], ATBURDASVID)
    skrifa_csv(dagaskra, [asdict(d) for d in dagatalning], DAGASVID)
    skrifa_samantekt(samantektarskra, samantekt)

    return Uttak(
        atburdaskra=atburdaskra,
        dagaskra=dagaskra,
        samantektarskra=samantektarskra,
        atburdir=len(skjalftar),
        dagar=len(dagatalning),
    )


def vinna_skjalfta(
    slod: Path | str | None = None,
    afmorkun: Afmorkun | None = None,
    mappa: Path | str | None = None,
) -> Uttak:
    """Keyrir alla skjálftavinnsluna: lesa, sannreyna, telja, draga saman, skrifa.

    Sjálfgefið er engin netumferð — lesið er úr frosna svarinu í
    ``data/raw/vedur-quakes/`` (regla 4). Falli eitthvað á leiðinni fellur
    ``SkjalftaVilla`` og engin hálfunnin tala kemst í ``data/processed/``.
    """
    afmorkun = afmorkun if afmorkun is not None else lesa_afmorkun()
    skjalftar = lesa_skjalfta(slod, afmorkun)
    dagatalning = dagleg_talning(skjalftar, afmorkun)
    samantekt = draga_saman(skjalftar, dagatalning)
    uttak = skrifa_uttak(skjalftar, dagatalning, samantekt, mappa)

    log.info(
        "Vann %d jarðskjálfta á %d UTC-dögum; %d dagar án atburðar.",
        uttak.atburdir,
        uttak.dagar,
        samantekt.dagar_an_atburda,
    )
    return uttak


def _krefjast_utan_vefs(mappa: Path) -> None:
    """Stöðvar skrif inn í ``web/gogn/``.

    Vinnslan á aldrei að skrifa í birtingarlagið. Þetta er varnagli við flæðið
    í kafla 0, ekki snyrting: rétt slóð á ekki að vera eina vörnin.
    """
    vefgogn = ROT / "web" / "gogn"
    if mappa.resolve() == vefgogn or vefgogn in mappa.resolve().parents:
        raise SkjalftaVilla(
            f"Vinnslan skrifar ekki í {vefgogn}. Þangað fer aðeins JSON frá "
            "útflutningslaginu eftir að grunnurinn hefur verið byggður (kafli 0)."
        )


def _keyra_eina_serd() -> int:
    """Keyrir vinnsluna á frosna svarinu og prentar tölurnar — handvirk keyrsla."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    uttak = vinna_skjalfta()
    print(f"atburðir: {uttak.atburdir}")
    print(f"dagar: {uttak.dagar}")
    for skra in (uttak.atburdaskra, uttak.dagaskra, uttak.samantektarskra):
        print(f"skrifaði: {skra.relative_to(ROT)}")
    return 0


if __name__ == "__main__":
    sys.exit(_keyra_eina_serd())
