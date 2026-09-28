"""Sannreyning hverrar færslu í Friends-talnaskránum (issue #10).

Hver reitur er lesinn sem sú gerð sem hann á að vera — heiltala, rauntala,
óauður texti — og innan þeirra marka sem gögnin eiga sér (þáttaröð 1–10,
enginn neikvæður fjöldi). Tvítekinn lykill stöðvar lesturinn. Frávik eru
**aldrei** leiðrétt eða hunsuð: færsla sem stenst ekki stöðvar keyrsluna með
skýringu um skrá, línu og reit (regla 6).

Hér eru hjálparföllin og skrárnar um handritin sjálf (lýsigögn, skrár,
línur á þáttaröð); skrárnar um Phoebe — ræðuskipti, nafntilvik og orðaforða —
eru í ``vinnsla.friends_phoebe_faerslur``. Úttakið eru raðir á því formi sem
``INSERT``-skipanirnar í ``vinnsla.friends_hledsla`` taka við. Samræmi *milli*
skráa er prófað í ``vinnsla.friends_samraemi``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from .friends_skrar import HledsluVilla, lesa_csv, lesa_json
from .phoebe_skilgreiningar import FRIENDS, PHOEBE, TITLES

FYRSTA_ROD, SIDASTA_ROD = 1, 10
THATTAKODI = re.compile(r"^[0-9]{4}(?:-[0-9]{4})?$")
HEILTALA = re.compile(r"^[0-9]+$")
RAUNTALA = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")

PER_EPISODE = "phoebe-per-episode.csv"
PER_EPISODE_DALKAR = (
    "episode_code", "season", "title", "n_aired_episodes",
    "friends_lines_total", "friends_words_total",
    "phoebe_lines", "phoebe_words", "phoebe_line_share_pct", "phoebe_word_share_pct",
    *(f"{vinur}_{maelt}" for vinur in FRIENDS if vinur != PHOEBE
      for maelt in ("lines", "words")),
)
SCREENTIME = "phoebe-screentime-by-season.csv"
SCREENTIME_DALKAR = (
    "season", "character", "lines", "words", "characters_typed", "speaking_scenes",
    "line_share_pct", "word_share_pct", "lines_per_episode", "words_per_episode",
    "words_per_line", "rank_by_lines",
)
META = "_meta.json"
META_LYKLAR = (
    "generated_utc", "generator", "transcript_files_used", "transcript_files_excluded",
    "aired_episodes_covered", "episodes_per_season", "parse_quality",
    "friends_line_totals", "friends_word_totals", "conventions",
)
# Flokkarnir í `parse_quality` og nöfn þeirra í friends_parse_blocks.
BLOKKAFLOKKAR = {
    "speaker_lines": "speaker_line",
    "scene_headings": "scene_heading",
    "stage_directions": "stage_direction",
    "unclassified": "unclassified",
}


def heiltala(gildi: object, stadur: str, lagmark: int = 0, hamark: int | None = None) -> int:
    """Heiltala innan marka, úr CSV-streng eða JSON-tölu. ``stadur`` fer í villuna."""
    if isinstance(gildi, bool) or not (
        isinstance(gildi, int) or (isinstance(gildi, str) and HEILTALA.match(gildi))
    ):
        raise HledsluVilla(f"{stadur}: {gildi!r} er ekki heiltala ≥ 0.")
    tala = int(gildi)
    if tala < lagmark or (hamark is not None and tala > hamark):
        efri = "" if hamark is None else f"–{hamark}"
        raise HledsluVilla(f"{stadur}: {tala} er utan marka ({lagmark}{efri}).")
    return tala


def rauntala(gildi: str, stadur: str) -> float:
    """Rauntala úr CSV-streng; tómur reitur eða texti stöðvar."""
    if not RAUNTALA.match(gildi):
        raise HledsluVilla(f"{stadur}: {gildi!r} er ekki tala.")
    return float(gildi)


def texti(gildi: str, stadur: str) -> str:
    """Óauður texti án bila á jöðrum — annars er gildið ekki það sem var skrifað."""
    if not gildi or gildi != gildi.strip():
        raise HledsluVilla(f"{stadur}: {gildi!r} er tómur eða með bil á jöðrum.")
    return gildi


def rod(gildi: object, stadur: str) -> int:
    """Þáttaröð, 1–10."""
    return heiltala(gildi, stadur, FYRSTA_ROD, SIDASTA_ROD)


def vinur(gildi: str, stadur: str) -> str:
    """Nafn eins vinanna sex, á forminu sem grunnurinn geymir (``Phoebe``)."""
    lykill = gildi.lower()
    if lykill not in FRIENDS:
        raise HledsluVilla(f"{stadur}: {gildi!r} er ekki einn vinanna sex.")
    return TITLES[lykill]


def einkvaemt(lyklar: Iterable[object], skra: str) -> None:
    """Stöðvar ef sami lykill kemur tvisvar — þá væri talan tvíræð."""
    sed: set[object] = set()
    for lykill in lyklar:
        if lykill in sed:
            raise HledsluVilla(f"{skra}: tvítekinn lykill {lykill!r}.")
        sed.add(lykill)


def lesa_meta(mappa: Path) -> dict:
    """``_meta.json`` með öllum lyklum sem hleðslan og samræmisprófin nota."""
    meta = lesa_json(mappa, META)
    vantar = [lykill for lykill in META_LYKLAR if lykill not in meta]
    if vantar:
        raise HledsluVilla(f"{META} vantar lyklana {vantar}.")
    return meta


def blokkir(meta: dict) -> list[tuple[str, int]]:
    """Raðir í friends_parse_blocks: einn flokkur, einn fjöldi."""
    gaedi = meta["parse_quality"]
    return [
        (flokkur, heiltala(gaedi.get(lykill), f"{META} parse_quality.{lykill}"))
        for lykill, flokkur in BLOKKAFLOKKAR.items()
    ]


def thattarodir(meta: dict) -> list[tuple[int, int]]:
    """Raðir í friends_seasons úr ``episodes_per_season``."""
    radir = [
        (rod(lykill, f"{META} episodes_per_season"),
         heiltala(fjoldi, f"{META} episodes_per_season.{lykill}", 1, 30))
        for lykill, fjoldi in meta["episodes_per_season"].items()
    ]
    einkvaemt((r[0] for r in radir), META)
    return radir


def handritsskrar(mappa: Path) -> tuple[list[tuple], list[tuple]]:
    """Raðir í friends_transcript_files og friends_episode_lines."""
    skrar, linur = [], []
    for numer, rad in enumerate(lesa_csv(mappa, PER_EPISODE, PER_EPISODE_DALKAR), start=2):
        stadur = f"{PER_EPISODE} lína {numer}"
        kodi = texti(rad["episode_code"], f"{stadur} episode_code")
        if not THATTAKODI.match(kodi):
            raise HledsluVilla(f"{stadur}: þáttakóðinn {kodi!r} er ekki SSTT eða SSTT-SSTT.")
        skrar.append((
            kodi, rod(rad["season"], f"{stadur} season"),
            texti(rad["title"], f"{stadur} title"),
            heiltala(rad["n_aired_episodes"], f"{stadur} n_aired_episodes", 1, 2),
        ))
        vinalinur = [(
            kodi, TITLES[lykill],
            heiltala(rad[f"{lykill}_lines"], f"{stadur} {lykill}_lines"),
            heiltala(rad[f"{lykill}_words"], f"{stadur} {lykill}_words"),
        ) for lykill in FRIENDS]
        for dalkur, stak in (("friends_lines_total", 2), ("friends_words_total", 3)):
            if heiltala(rad[dalkur], f"{stadur} {dalkur}") != sum(r[stak] for r in vinalinur):
                raise HledsluVilla(f"{stadur}: {dalkur} er ekki summa vinanna sex.")
        linur.extend(vinalinur)
    einkvaemt((s[0] for s in skrar), PER_EPISODE)
    return skrar, linur


def thattarodarpersonur(mappa: Path) -> tuple[list[tuple], dict[tuple, tuple]]:
    """Raðir í friends_season_characters, og línur/orð skrárinnar til samanburðar.

    Línur og orð á þáttaröð eru ekki geymd (þau eru SUM() úr
    friends_episode_lines), en þeim er skilað svo samræmisprófin geti borið
    þau við summuna.
    """
    radir, linur_ord = [], {}
    for numer, rad in enumerate(lesa_csv(mappa, SCREENTIME, SCREENTIME_DALKAR), start=2):
        stadur = f"{SCREENTIME} lína {numer}"
        lykill = (rod(rad["season"], f"{stadur} season"), vinur(rad["character"], stadur))
        radir.append((
            *lykill,
            heiltala(rad["characters_typed"], f"{stadur} characters_typed"),
            heiltala(rad["speaking_scenes"], f"{stadur} speaking_scenes"),
        ))
        linur_ord[lykill] = (heiltala(rad["lines"], f"{stadur} lines"),
                             heiltala(rad["words"], f"{stadur} words"))
    einkvaemt(((r[0], r[1]) for r in radir), SCREENTIME)
    return radir, linur_ord
