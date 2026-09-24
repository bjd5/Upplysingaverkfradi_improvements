"""Afmörkun skjálftabeiðninnar, lesin úr provenance.json.

Hrágögnin í ``data/raw/vedur-quakes/events.json`` eru svar við **einni** beiðni
með föstum síum: marghyrningi yfir Reykjanes, tímabili, stærðar- og
dýptarmörkum, atburðategund, matsaðferð og kerfi. Þessar síur ráða því hvað má
komast í grunninn — og þær eru **lesnar úr**
``data/raw/vedur-quakes/provenance.json``, aldrei ágiskaðar eða slegnar inn hér.
Tafla sem er slegin inn tvisvar fer á skjön (regla 8: hver tala á sér
rekjanlega leið aftur í hrágögn).

Tímabilið er líka það sem gefur ``earthquake_days`` sinn dagafjölda: hver
UTC-dagur frá upphafi (meðtöldu) til enda (undanskildum) fær línu, líka dagar
án atburðar.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
PROVENANCE = ROT / "data" / "raw" / "vedur-quakes" / "provenance.json"

# POLYGON((lengd breidd,lengd breidd,...)) eins og beiðnin sendi hann.
MARGHYRNINGUR = re.compile(r"^POLYGON\s*\(\((?P<hnit>[^()]+)\)\)$")

NAUDSYNLEGAR_BREYTUR = (
    "start_time",
    "end_time",
    "depth_min",
    "depth_max",
    "size_min",
    "size_max",
    "polygon",
    "type",
    "evaluation_mode",
    "system",
)


class SkjalftaVilla(ValueError):
    """Frávik í hrágögnum eða afmörkun þeirra.

    Sameiginleg villa einingarinnar. Hún er látin falla, aldrei þögguð: færsla
    sem stenst ekki beiðnina má ekki hverfa hljóðlega úr úrtakinu (regla 6).
    """


@dataclass(frozen=True)
class Afmorkun:
    """Síurnar sem beiðnin bað um — ramminn utan um löglegt úrtak."""

    upphaf: datetime  # meðtalið
    endir: datetime  # undanskilið
    staerd_min: float
    staerd_max: float
    dypt_min: float
    dypt_max: float
    lengd_min: float
    lengd_max: float
    breidd_min: float
    breidd_max: float
    atburdategund: str
    matsadferd: str
    kerfi: str
    leyfi: str


def lesa_afmorkun(slod: Path | str | None = None) -> Afmorkun:
    """Les afmörkun beiðninnar úr provenance.json.

    Vanti breytu sem beiðnin byggði á stöðvast keyrslan: úrtak sem enginn
    veit hvernig var afmarkað er ekki rannsóknargagn.
    """
    slod = Path(slod) if slod is not None else PROVENANCE
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except FileNotFoundError as villa:
        raise SkjalftaVilla(
            f"Provenance-skráin finnst ekki: {slod}. Afmörkun beiðninnar er "
            "forsenda hleðslunnar og er ekki ágiskuð."
        ) from villa
    except json.JSONDecodeError as villa:
        raise SkjalftaVilla(f"{slod} er ekki gilt JSON: {villa}") from villa

    breytur = skjal.get("parameters")
    if not isinstance(breytur, dict):
        raise SkjalftaVilla(f"{slod} hefur engan 'parameters'-hlut.")

    vantar = [heiti for heiti in NAUDSYNLEGAR_BREYTUR if heiti not in breytur]
    if vantar:
        raise SkjalftaVilla(
            f"{slod}: breyturnar {', '.join(vantar)} vantar í 'parameters'."
        )

    lengd_min, lengd_max, breidd_min, breidd_max = reitur_ur_marghyrningi(
        str(breytur["polygon"])
    )

    return Afmorkun(
        upphaf=_midnaetti(breytur["start_time"], "start_time"),
        endir=_midnaetti(breytur["end_time"], "end_time"),
        staerd_min=_tala(breytur["size_min"], "size_min"),
        staerd_max=_tala(breytur["size_max"], "size_max"),
        dypt_min=_tala(breytur["depth_min"], "depth_min"),
        dypt_max=_tala(breytur["depth_max"], "depth_max"),
        lengd_min=lengd_min,
        lengd_max=lengd_max,
        breidd_min=breidd_min,
        breidd_max=breidd_max,
        atburdategund=str(breytur["type"]),
        matsadferd=str(breytur["evaluation_mode"]),
        kerfi=str(breytur["system"]),
        leyfi=str(skjal.get("license", "óskráð")),
    )


def dagar(afmorkun: Afmorkun) -> list[str]:
    """Allir UTC-dagar tímabilsins á forminu YYYY-MM-DD, í tímaröð.

    Upphafið er meðtalið og endirinn undanskilinn, eins og beiðnin sagði.
    Dagar án atburðar eru með: þeir eru niðurstaða, ekki eyða.
    """
    if afmorkun.endir <= afmorkun.upphaf:
        raise SkjalftaVilla(
            f"Tímabil beiðninnar er tómt eða öfugsnúið: {afmorkun.upphaf.isoformat()} "
            f"til {afmorkun.endir.isoformat()}."
        )

    listi: list[str] = []
    dagur = afmorkun.upphaf
    while dagur < afmorkun.endir:
        listi.append(dagur.date().isoformat())
        dagur += timedelta(days=1)
    return listi


def reitur_ur_marghyrningi(wkt: str) -> tuple[float, float, float, float]:
    """Skilar (lengd_min, lengd_max, breidd_min, breidd_max) úr WKT-marghyrningi.

    Beiðnin notaði **ásrétta rétthyrningu** yfir Reykjanes. Fyrir slíkan
    marghyrning er umlykjandi kassinn nákvæmlega sami flötur, svo hnitapróf á
    kassanum er jafngilt prófi á marghyrningnum sjálfum. Sé marghyrningurinn
    ekki rétthyrndur stöðvast keyrslan — þá dygði kassaprófið ekki lengur og
    það á ekki að uppgötvast þegjandi.
    """
    samsvorun = MARGHYRNINGUR.match(wkt.strip())
    if samsvorun is None:
        raise SkjalftaVilla(f"Marghyrningurinn er ekki á WKT-formi: {wkt!r}")

    punktar: list[tuple[float, float]] = []
    for hluti in samsvorun.group("hnit").split(","):
        tolur = hluti.split()
        if len(tolur) != 2:
            raise SkjalftaVilla(f"Hnitið {hluti.strip()!r} er ekki lengd og breidd.")
        punktar.append((_tala(tolur[0], "lengd"), _tala(tolur[1], "breidd")))

    if len(punktar) < 4 or punktar[0] != punktar[-1]:
        raise SkjalftaVilla(f"Marghyrningurinn er ekki lokaður hringur: {wkt!r}")

    lengdir = sorted({lengd for lengd, _ in punktar})
    breiddir = sorted({breidd for _, breidd in punktar})
    if len(lengdir) != 2 or len(breiddir) != 2:
        raise SkjalftaVilla(
            f"Marghyrningurinn er ekki ásrétt rétthyrningur: {wkt!r}. "
            "Hnitaprófið í þessari einingu prófar umlykjandi kassa og dygði "
            "ekki fyrir annars konar form."
        )

    return lengdir[0], lengdir[1], breiddir[0], breiddir[1]


def _midnaetti(gildi: object, heiti: str) -> datetime:
    """Þáttar tímastimpil beiðninnar og krefst þess að hann sé miðnætti í UTC."""
    try:
        stimpill = datetime.fromisoformat(str(gildi))
    except ValueError as villa:
        raise SkjalftaVilla(f"{heiti}={gildi!r} er ekki gildur ISO 8601 tími.") from villa

    if stimpill.tzinfo is None or stimpill.utcoffset() != timedelta(0):
        raise SkjalftaVilla(
            f"{heiti}={gildi!r} er ekki í UTC. Dagalykillinn yrði þá ekki UTC-dagur."
        )

    stimpill = stimpill.astimezone(UTC)
    if (stimpill.hour, stimpill.minute, stimpill.second, stimpill.microsecond) != (
        0,
        0,
        0,
        0,
    ):
        raise SkjalftaVilla(
            f"{heiti}={gildi!r} er ekki á miðnætti. Tímabil sem byrjar eða endar "
            "inni í degi gefur hálfan dag í earthquake_days og því ranga talningu."
        )
    return stimpill


def _tala(gildi: object, heiti: str) -> float:
    """Skilar tölu úr provenance-gildi; bool er ekki tala þótt Python telji svo."""
    if isinstance(gildi, bool):
        raise SkjalftaVilla(f"{heiti}={gildi!r} er sannleiksgildi, ekki tala.")
    try:
        return float(gildi)  # type: ignore[arg-type]
    except (TypeError, ValueError) as villa:
        raise SkjalftaVilla(f"{heiti}={gildi!r} er ekki tala.") from villa
