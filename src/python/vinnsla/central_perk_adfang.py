"""Frosnu Central Perk-skrárnar: SHA-staðfesting og lestur (issue #10, #24).

Aðfangið er **þrjár frosnar skrár** í ``data/processed/central-perk-frosid/``
— bætaeins afrit af skránum sem gamla greiningin
(``src/phoebe_central_perk.py`` @ ``2865ed6``) skrifaði og liggja í viðmiðinu
``docs/vidmid/generated/``. Viðmiðið er sönnunargagnið og er aldrei lesið
hér (``data/processed/README.md``, kafli 2). Handritin sjálf eru aldrei lesin
(issue #3, valkostur A). Áður en skrá er lesin er SHA-256 hennar borin við
summu viðmiðsins í ``docs/vidmid/provenance.json`` (safnið ``generated``), og
mappan verður að geyma nákvæmlega skrárnar þrjár; ósannreynd skrá fer ekki
lengra.

Hvert gildi er lesið sem sú gerð sem það á að vera og innan marka sinna.
Frávik eru aldrei leiðrétt: þau stöðva keyrsluna með skýringu (regla 6).

* ``-summary.json`` — hóparnir, miðgildin og söngurinn, óafrúnnað.
* ``.svg`` — einn punktur á handritsskrá: litur = hópur, ``<title>`` =
  þáttakóði og hlutdeild Phoebe í % með einum aukastaf. Það er eina frosna
  heimildin á handritastigi. Staðsetning punktsins (cy) er reiknuð úr
  óafrúnnaðri hlutdeild og er borin við ``<title>``; x-staðan við dálk hópsins.
* ``-regex.md`` — segðirnar orðréttar. Lesturinn er sannaður taplaus: skráin
  er endurrituð úr lesnu röðunum og verður að verða bætaeins.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from gagnagrunnur.tenging import ROT

from .central_perk_mynstur import GROUP_ORDER

ADFANGSMAPPA = ROT / "data" / "processed" / "central-perk-frosid"
PROVENANCE = ROT / "docs" / "vidmid" / "provenance.json"
SAFN = "generated"

SUMMARY = "phoebe-central-perk-summary.json"
SVG = "phoebe-central-perk.svg"
REGEX = "phoebe-central-perk-regex.md"
SKRAR = (SUMMARY, SVG, REGEX)

SUMMARY_LYKLAR = ("transcript_files", "singing_files", "singing_scenes",
                  "singing_episode_ids", "groups", "median_difference_percentage_points")
HOPALYKLAR = ("n", "median_phoebe_share", "mean_phoebe_share",
              "median_friends_to_phoebe_ratio")
THATTAKODI = re.compile(r"^[0-9]{4}(?:-[0-9]{4})?$")

# Litir hópanna í myndinni (GROUP_COLOURS í gömlu skriftunni).
LITIR = {"#64748B": "no_central_perk", "#0284C7": "central_perk", "#7C3AED": "phoebe_sings"}
PUNKTUR = re.compile(
    r'<circle cx="(?P<x>[0-9]+\.[0-9])" cy="(?P<y>[0-9]+\.[0-9])" r="4\.2" '
    r'fill="(?P<litur>#[0-9A-F]{6})" fill-opacity="0\.58">'
    r"<title>(?P<kodi>[^:<]+): (?P<hlutdeild>[0-9]{1,3}\.[0-9])%</title></circle>"
)
GRINDARLINA = re.compile(
    r'<line x1="92" x2="926" y1="(?P<y>[0-9.]+)" y2="(?P=y)" stroke="#E2E8F0"/>\s*'
    r'<text [^>]*>(?P<pct>[0-9]+)%</text>'
)
MIDGILDISLINA = re.compile(
    r'<line x1="(?P<x1>[0-9.]+)" x2="(?P<x2>[0-9.]+)" y1="(?P<y>[0-9.]+)" y2="(?P=y)" '
    r'stroke="(?P<litur>#[0-9A-F]{6})" stroke-width="5"'
)
# Hnit í myndinni eru námunduð að 0,1 px; <title> að 0,1 %.
HNITASKREF = 0.1
PROSENTUSKREF = 0.1
PROMILL = 1000

SEGD = re.compile(
    r"#### `(?P<nafn>[A-Z_]+_RE)`\n\n```python\n(?P<segd>[^\n]+)\n```\n\n"
    r"\*\*Grípur:\*\* (?P<gripur>[^\n]+)\n\n\*\*Sleppur:\*\* (?P<sleppur>[^\n]+)\n"
)


class CentralPerkVilla(RuntimeError):
    """Frosnu skrárnar eru ekki þær sem voru frystar, eða stangast á."""


@dataclass(frozen=True)
class Skra:
    """Ein staðfest skrá."""

    heiti: str
    sha256: str
    staerd: int


@dataclass(frozen=True)
class Punktur:
    """Ein handritsskrá í myndinni."""

    kodi: str
    hopur: str
    promill: int
    x: float
    y: float


def stutt_slod(slod: Path) -> str:
    """Slóð afstæð við rót verkefnisins þegar hún liggur þar."""
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)


def stadfesta_skrar(mappa: Path = ADFANGSMAPPA, provenance: Path = PROVENANCE) -> list[Skra]:
    """SHA-256 skránna þriggja borin við provenance; skrá umfram eða fyrsta frávik stöðvar."""
    if not provenance.is_file():
        raise CentralPerkVilla(f"Vantar {stutt_slod(provenance)} — ekki hægt að staðfesta aðfangið.")
    sofn = [s for s in json.loads(provenance.read_text(encoding="utf-8")).get("sofn", [])
            if s.get("heiti") == SAFN]
    if len(sofn) != 1:
        raise CentralPerkVilla(f"Provenance nefnir safnið {SAFN!r} {len(sofn)} sinnum, ekki einu.")
    skradar: dict[str, list[str]] = {}
    for skra in sofn[0].get("skrar", []):
        skradar.setdefault(Path(str(skra["slod"])).name, []).append(str(skra["sha256"]))

    if not mappa.is_dir():
        raise CentralPerkVilla(f"Aðfangsmappan {stutt_slod(mappa)} er ekki til.")
    a_diski = {p.name for p in mappa.iterdir()}
    if a_diski - set(SKRAR):
        raise CentralPerkVilla(
            f"{stutt_slod(mappa)} geymir skrár umfram þær þrjár: {sorted(a_diski - set(SKRAR))}.")

    stadfestar = []
    for heiti in SKRAR:
        summur = skradar.get(heiti, [])
        if len(summur) != 1:
            raise CentralPerkVilla(f"Provenance nefnir {heiti} {len(summur)} sinnum í {SAFN}.")
        slod = mappa / heiti
        if not slod.is_file():
            raise CentralPerkVilla(f"Frosna skráin {stutt_slod(slod)} er ekki til.")
        baeti = slod.read_bytes()
        summa = hashlib.sha256(baeti).hexdigest()
        if summa != summur[0]:
            raise CentralPerkVilla(
                f"{heiti} stemmir ekki við provenance.\n  skráð SHA-256:   {summur[0]}\n"
                f"  á diski SHA-256: {summa}\nSkráin er ekki það sem var fryst."
            )
        stadfestar.append(Skra(heiti=heiti, sha256=summa, staerd=len(baeti)))
    return stadfestar


def heiltala(gildi: object, stadur: str) -> int:
    """JSON-heiltala ≥ 0 (``True`` er ekki tala)."""
    if isinstance(gildi, bool) or not isinstance(gildi, int) or gildi < 0:
        raise CentralPerkVilla(f"{stadur}: {gildi!r} er ekki heiltala ≥ 0.")
    return gildi


def rauntala(gildi: object, stadur: str, lagmark: float, hamark: float) -> float:
    """Endanleg JSON-rauntala innan marka."""
    if isinstance(gildi, bool) or not isinstance(gildi, (int, float)) \
            or not math.isfinite(gildi) or not lagmark <= gildi <= hamark:
        raise CentralPerkVilla(f"{stadur}: {gildi!r} er ekki tala á bilinu {lagmark}–{hamark}.")
    return float(gildi)


def lesa_samantekt(mappa: Path = ADFANGSMAPPA) -> dict:
    """``summary.json`` með hverjum reit sannreyndum."""
    skjal = json.loads((mappa / SUMMARY).read_text(encoding="utf-8"))
    if not isinstance(skjal, dict) or tuple(skjal) != SUMMARY_LYKLAR:
        raise CentralPerkVilla(f"{SUMMARY}: lyklarnir eru ekki {list(SUMMARY_LYKLAR)}.")
    for lykill in ("transcript_files", "singing_files", "singing_scenes"):
        heiltala(skjal[lykill], f"{SUMMARY} {lykill}")
    kodar = skjal["singing_episode_ids"]
    if not isinstance(kodar, list) or any(
            not isinstance(k, str) or not THATTAKODI.match(k) for k in kodar):
        raise CentralPerkVilla(f"{SUMMARY}: singing_episode_ids eru ekki þáttakóðar.")
    if kodar != sorted(set(kodar)):
        raise CentralPerkVilla(f"{SUMMARY}: singing_episode_ids eru tvíteknir eða óraðaðir.")
    hopar = skjal["groups"]
    if not isinstance(hopar, dict) or tuple(hopar) != GROUP_ORDER:
        raise CentralPerkVilla(f"{SUMMARY}: hóparnir eru ekki {list(GROUP_ORDER)}.")
    for hopur, gildi in hopar.items():
        stadur = f"{SUMMARY} groups.{hopur}"
        if not isinstance(gildi, dict) or tuple(gildi) != HOPALYKLAR:
            raise CentralPerkVilla(f"{stadur}: lyklarnir eru ekki {list(HOPALYKLAR)}.")
        heiltala(gildi["n"], f"{stadur}.n")
        rauntala(gildi["median_phoebe_share"], f"{stadur}.median_phoebe_share", 0, 1)
        rauntala(gildi["mean_phoebe_share"], f"{stadur}.mean_phoebe_share", 0, 1)
        if rauntala(gildi["median_friends_to_phoebe_ratio"], f"{stadur}.ratio", 0, math.inf) == 0:
            raise CentralPerkVilla(f"{stadur}: hlutfallið hinir/Phoebe er 0.")
    rauntala(skjal["median_difference_percentage_points"], f"{SUMMARY} munur", -100, 100)
    return skjal


def _kvardi(svg: str) -> tuple[float, float]:
    """(y við 0 %, px á hvert prósent) úr grindarlínum myndarinnar — línulegt."""
    grind = [(float(m["y"]), int(m["pct"])) for m in GRINDARLINA.finditer(svg)]
    if len(grind) < 2:
        raise CentralPerkVilla(f"{SVG}: grindarlínur ásins fundust ekki.")
    (y0, p0), (y1, p1) = grind[0], grind[-1]
    halli = (y0 - y1) / (p1 - p0)
    for y, pct in grind:
        if abs(y0 - halli * (pct - p0) - y) > HNITASKREF:
            raise CentralPerkVilla(f"{SVG}: ásinn er ekki línulegur við {pct}%.")
    return y0 + halli * p0, halli


def lesa_punkta(mappa: Path = ADFANGSMAPPA) -> tuple[list[Punktur], dict[str, tuple]]:
    """Punktar myndarinnar og miðgildislína hvers hóps: {hópur: (x1, x2, hlutdeild 0–1)}."""
    svg = (mappa / SVG).read_text(encoding="utf-8")
    nulllina, halli = _kvardi(svg)
    punktar = []
    for m in PUNKTUR.finditer(svg):
        if m["litur"] not in LITIR:
            raise CentralPerkVilla(f"{SVG}: punktur {m['kodi']} hefur óþekktan lit {m['litur']}.")
        if not THATTAKODI.match(m["kodi"]):
            raise CentralPerkVilla(f"{SVG}: {m['kodi']!r} er ekki þáttakóði.")
        promill = int(m["hlutdeild"].replace(".", ""))
        if promill > PROMILL:
            raise CentralPerkVilla(f"{SVG}: {m['kodi']} hefur hlutdeild {m['hlutdeild']}% > 100%.")
        punktar.append(Punktur(m["kodi"], LITIR[m["litur"]], promill, float(m["x"]), float(m["y"])))
    if len(punktar) != svg.count("<circle"):
        raise CentralPerkVilla(
            f"{SVG}: {svg.count('<circle')} punktar en {len(punktar)} lesanlegir — engum sleppt.")
    kodar = [p.kodi for p in punktar]
    if len(set(kodar)) != len(kodar):
        raise CentralPerkVilla(f"{SVG}: sami þáttakóði kemur tvisvar fyrir.")

    # Ef y er reiknað úr óafrúnnaðri hlutdeild má það víkja um hálft
    # prósentuskref frá <title> auk hálfs hnitaskrefs.
    vikmork = PROSENTUSKREF / 2 + HNITASKREF / 2 / halli + 1e-9
    for p in punktar:
        ur_hniti = (nulllina - p.y) / halli
        if abs(ur_hniti - p.promill / 10) > vikmork:
            raise CentralPerkVilla(
                f"{SVG}: {p.kodi} er teiknaður við {ur_hniti:.3f}% en merktur {p.promill / 10}%.")

    midgildi = {}
    for m in MIDGILDISLINA.finditer(svg):
        if m["litur"] in LITIR:
            hopur = LITIR[m["litur"]]
            if hopur in midgildi:
                raise CentralPerkVilla(f"{SVG}: tvær miðgildislínur fyrir {hopur}.")
            midgildi[hopur] = (float(m["x1"]), float(m["x2"]),
                               (nulllina - float(m["y"])) / halli / 100)
    if tuple(sorted(midgildi)) != tuple(sorted(GROUP_ORDER)):
        raise CentralPerkVilla(f"{SVG}: miðgildislínur fundust fyrir {sorted(midgildi)}.")
    for p in punktar:
        x1, x2, _ = midgildi[p.hopur]
        if not x1 <= p.x <= x2:
            raise CentralPerkVilla(f"{SVG}: {p.kodi} er litaður {p.hopur} en stendur utan dálksins.")
    return punktar, midgildi


def lesa_segdir(mappa: Path = ADFANGSMAPPA) -> list[tuple[str, str, str, str]]:
    """(nafn, segð, grípur, sleppur) í röð skrárinnar — sannað taplaust."""
    texti = (mappa / REGEX).read_text(encoding="utf-8")
    radir = [(m["nafn"], m["segd"], m["gripur"], m["sleppur"]) for m in SEGD.finditer(texti)]
    endurritad = "\n".join(
        f"#### `{n}`\n\n```python\n{s}\n```\n\n**Grípur:** {g}\n\n**Sleppur:** {sl}\n"
        for n, s, g, sl in radir)
    if not radir or endurritad != texti:
        raise CentralPerkVilla(f"{REGEX}: skráin er ekki á sniðinu sem lesturinn þekkir.")
    for nafn, segd, _, _ in radir:
        try:
            re.compile(segd)
        except re.error as villa:
            raise CentralPerkVilla(f"{REGEX}: {nafn} er ekki gild segð — {villa}") from villa
    if len({r[0] for r in radir}) != len(radir):
        raise CentralPerkVilla(f"{REGEX}: sama segðarheiti kemur tvisvar fyrir.")
    return radir
