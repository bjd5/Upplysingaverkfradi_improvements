"""Skref 5a í Central Perk-greiningunni: samantekt í töflur (issue #14, P2.6).

Flutt úr ``src/phoebe_central_perk.py`` (commit ``2865ed6``): ``summarise`` —
óbreytt, svo ``summary.json`` stemmi bæti fyrir bæti við viðmiðið.

**Nýtt í stað þess sem féll niður:** gamla skriftan skrifaði Markdown-texta,
Markdown-töflu af segðunum og SVG-punktarit (regla 2: HTML, CSS og myndrit
verða til í ``web/`` og ``utflutningur/``, ekki í vinnslunni). Tölurnar sem
myndin bar — hópur og hlutdeild Phoebe í hverju handriti — eru hér
``episode_rows``, og segðirnar sem Markdown-skráin sýndi eru ``pattern_rows``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import math
import statistics
from typing import Sequence

try:  # keyrt sem eining innan pakkans
    from .central_perk_greining import EpisodeResult
    from .central_perk_mynstur import (
        CENTRAL_PERK_GROUP, DOCUMENTED_PATTERNS, GROUP_ORDER, MAIN_CAST, PHOEBE_SINGS,
    )
except ImportError:  # keyrt beint úr möppunni
    from central_perk_greining import EpisodeResult
    from central_perk_mynstur import (
        CENTRAL_PERK_GROUP, DOCUMENTED_PATTERNS, GROUP_ORDER, MAIN_CAST, PHOEBE_SINGS,
    )

PERCENTAGE_POINTS = 100

EPISODE_FIELDS = [
    "episode_id", "group", "has_central_perk", "singing_scenes",
    *(f"words_{name.lower()}" for name in MAIN_CAST),
    "main_cast_words", "phoebe_share",
]


def _median(values: list[float], what: str) -> float:
    """Miðgildi; tóm röð er villa með skýringu, ekki ``StatisticsError`` úr djúpinu."""
    if not values:
        raise ValueError(f"Ekkert gildi fyrir {what} — miðgildi er óskilgreint.")
    return statistics.median(values)


def group_summary(results: Sequence[EpisodeResult], group: str) -> dict[str, float | int]:
    """Fjöldi, miðgildi og meðaltal hlutdeildar Phoebe og miðgildi hlutfallsins í einum hópi.

    Hlutfallið „hinir fimm á móti Phoebe“ er aðeins reiknað fyrir handrit
    þar sem hún segir eitthvað (endanlegt gildi).
    """
    rows = [row for row in results if row.group == group]
    shares = [row.phoebe_share for row in rows]
    ratios = [row.friends_to_phoebe_ratio for row in rows
              if math.isfinite(row.friends_to_phoebe_ratio)]
    return {
        "n": len(rows),
        "median_phoebe_share": _median(shares, f"hlutdeild Phoebe í hópnum {group}"),
        "mean_phoebe_share": statistics.mean(shares),
        "median_friends_to_phoebe_ratio": _median(ratios, f"hlutfallið í hópnum {group}"),
    }


def summarise(results: Sequence[EpisodeResult]) -> dict[str, object]:
    """Miðgildi og meðaltal hlutdeildar Phoebe í hverjum hópi (``summary.json``).

    Miðgildi er aðalmælikvarðinn: tvöföld og óvenju löng handrit hefðu annars
    of mikil áhrif. Lyklar og röð eru óbreytt úr gömlu skriftunni.
    """
    groups = {group: group_summary(results, group) for group in GROUP_ORDER}
    singing_rows = [row for row in results if row.group == PHOEBE_SINGS]
    song_share = groups[PHOEBE_SINGS]["median_phoebe_share"]
    cp_share = groups[CENTRAL_PERK_GROUP]["median_phoebe_share"]
    return {
        "transcript_files": len(results),
        "singing_files": len(singing_rows),
        "singing_scenes": sum(row.singing_scenes for row in singing_rows),
        "singing_episode_ids": [row.episode_id for row in singing_rows],
        "groups": groups,
        # Munurinn á miðgildum söng- og Central Perk-hópsins, í prósentustigum.
        "median_difference_percentage_points":
            PERCENTAGE_POINTS * (float(song_share) - float(cp_share)),
    }


def episode_rows(results: Sequence[EpisodeResult]) -> list[dict[str, object]]:
    """Ein röð á handritaskrá — tölurnar sem punktaritið gamla sýndi, og orðin að baki."""
    rows = []
    for result in results:
        row: dict[str, object] = {
            "episode_id": result.episode_id,
            "group": result.group,
            "has_central_perk": int(result.has_central_perk),
            "singing_scenes": result.singing_scenes,
        }
        row.update({f"words_{name.lower()}": result.words[name] for name in MAIN_CAST})
        row["main_cast_words"] = result.main_cast_words
        row["phoebe_share"] = result.phoebe_share
        rows.append(row)
    return rows


def pattern_rows() -> list[dict[str, str]]:
    """Segðirnar orðréttar úr kóðanum, með skýringum — svo síðan sýni það sem keyrði."""
    return [
        {"name": name, "pattern": pattern.pattern, "catches": catches, "misses": misses}
        for name, pattern, catches, misses in DOCUMENTED_PATTERNS
    ]
