"""Bygging GeoJSON-svarsins — sannreynd áður en nokkuð er lesið úr henni.

Þessi eining veit hvað er gilt ``FeatureCollection``, gildur ``Point`` og gild
JSON-gerð. Hún veit ekkert um jarðskjálfta, síur beiðninnar né afleidda lykla
— það er í ``jardskjalftar.py``. Skilin liggja þar sem **snið** endar og
**efni** byrjar.

Allt sem ekki stenst fellur með ``SkjalftaVilla``; ekkert er lagað í kyrrþey
(regla 6).
"""

from __future__ import annotations

import json
from pathlib import Path

try:  # keyrt sem eining innan pakkans
    from .jardskjalftar_afmorkun import SkjalftaVilla
except ImportError:  # keyrt beint úr möppunni
    from jardskjalftar_afmorkun import SkjalftaVilla

GEOMETRY_LYKLAR = frozenset({"type", "coordinates"})


def lesa_features(slod: Path) -> list[object]:
    """Les GeoJSON-skrá og skilar ``features``-listanum óbreyttum."""
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except FileNotFoundError as villa:
        raise SkjalftaVilla(f"Hrágagnaskráin finnst ekki: {slod}") from villa
    except json.JSONDecodeError as villa:
        raise SkjalftaVilla(f"{slod} er ekki gilt JSON: {villa}") from villa

    if not isinstance(skjal, dict) or skjal.get("type") != "FeatureCollection":
        fannst = skjal.get("type") if isinstance(skjal, dict) else type(skjal).__name__
        raise SkjalftaVilla(
            f"{slod.name} er ekki GeoJSON FeatureCollection (type={fannst!r})."
        )

    faerslur = skjal.get("features")
    if not isinstance(faerslur, list):
        raise SkjalftaVilla(f"{slod.name}: 'features' er ekki listi.")
    return faerslur


def hnit(geometry: object, hvar: str) -> tuple[float, float]:
    """Skilar (lengdargráðu, breiddargráðu) úr GeoJSON-punkti."""
    rumfraedi = hlutur(geometry, GEOMETRY_LYKLAR, f"{hvar} geometry")
    if rumfraedi.get("type") != "Point":
        raise SkjalftaVilla(
            f"{hvar} geometry: type={rumfraedi.get('type')!r}, á að vera 'Point'."
        )
    hnitin = rumfraedi["coordinates"]
    if not isinstance(hnitin, list) or len(hnitin) != 2:
        raise SkjalftaVilla(
            f"{hvar} geometry: coordinates á að vera [lengd, breidd], fékk {hnitin!r}."
        )
    return (
        tala(hnitin[0], f"{hvar} lengdargráða"),
        tala(hnitin[1], f"{hvar} breiddargráða"),
    )


def hlutur(gildi: object, lyklar: frozenset[str], hvar: str) -> dict[str, object]:
    """Krefst JSON-hlutar með nákvæmlega þeim lyklum sem búist er við.

    Nýr eða horfinn lykill þýðir að svarið er ekki það snið sem sannreyningin
    var skrifuð fyrir. Það á að stöðva keyrslu svo einhver líti á breytinguna,
    ekki renna í gegn með dálk sem enginn skoðaði.
    """
    if not isinstance(gildi, dict):
        raise SkjalftaVilla(f"{hvar}: bjóst við JSON-hlut, fékk {type(gildi).__name__}.")
    fann = set(gildi)
    if fann != set(lyklar):
        vantar = sorted(set(lyklar) - fann)
        auka = sorted(fann - set(lyklar))
        raise SkjalftaVilla(
            f"{hvar}: lyklar stemma ekki. Vantar: {vantar or 'ekkert'}. "
            f"Óvæntir: {auka or 'engir'}."
        )
    return gildi


def texti(gildi: object, hvar: str) -> str:
    """Skilar textagildi; annað er villa."""
    if not isinstance(gildi, str):
        raise SkjalftaVilla(f"{hvar}: bjóst við texta, fékk {gildi!r}.")
    return gildi


def tala(gildi: object, hvar: str) -> float:
    """Skilar tölu úr JSON; ``bool`` er ekki tala þótt Python telji hana með."""
    if isinstance(gildi, bool) or not isinstance(gildi, (int, float)):
        raise SkjalftaVilla(f"{hvar}: bjóst við tölu, fékk {gildi!r}.")
    return float(gildi)
