"""Skref 4 í Central Perk-greiningunni: orð og samanburðarhópur (issue #14, P2.6).

Flutt úr ``src/phoebe_central_perk.py`` (commit ``2865ed6``): ``EpisodeResult``,
``analyse_episode`` og ``analyse``. Skráaleitin (``transcript_paths``) er ekki
lengur hér heldur sameiginleg í ``friends_handrit`` — sama val á skrám (227 af
229) og gamla skriftan, en tóm eða týnd mappa er nú villa, ekki tóm greining.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:  # keyrt sem eining innan pakkans
    from .central_perk_lestur import Block, read_blocks
    from .central_perk_mynstur import (
        CENTRAL_PERK_GROUP, MAIN_CAST, NO_CENTRAL_PERK, PHOEBE, PHOEBE_SINGS,
    )
    from .central_perk_songur import phoebe_singing_scenes
    from .central_perk_thattari import dialogue_from_blocks, is_central_perk_scene
    from .friends_handrit import episode_code, transcript_paths
except ImportError:  # keyrt beint úr möppunni
    from central_perk_lestur import Block, read_blocks
    from central_perk_mynstur import (
        CENTRAL_PERK_GROUP, MAIN_CAST, NO_CENTRAL_PERK, PHOEBE, PHOEBE_SINGS,
    )
    from central_perk_songur import phoebe_singing_scenes
    from central_perk_thattari import dialogue_from_blocks, is_central_perk_scene
    from friends_handrit import episode_code, transcript_paths


@dataclass(frozen=True)
class EpisodeResult:
    """Niðurstaða fyrir eina handritaskrá: hópur, söngsenur og orð hverrar persónu."""

    episode_id: str
    group: str
    has_central_perk: bool
    singing_scenes: int
    words: dict[str, int]

    @property
    def main_cast_words(self) -> int:
        """Orð aðalpersónanna sex samanlagt."""
        return sum(self.words.values())

    @property
    def phoebe_share(self) -> float:
        """Hlutdeild Phoebe af orðum aðalpersónanna sex, 0–1 (0 ef enginn talar)."""
        if not self.main_cast_words:
            return 0.0
        return self.words[PHOEBE] / self.main_cast_words

    @property
    def friends_to_phoebe_ratio(self) -> float:
        """Orð hinna fimm á móti hverju orði Phoebe; óendanlegt ef hún þegir."""
        phoebe_words = self.words[PHOEBE]
        if not phoebe_words:
            return math.inf
        return (self.main_cast_words - phoebe_words) / phoebe_words


def comparison_group(singing_scenes: int, has_central_perk: bool) -> str:
    """Hópurinn í forgangsröð: söngur, svo Central Perk, svo hvorugt."""
    if singing_scenes:
        return PHOEBE_SINGS
    if has_central_perk:
        return CENTRAL_PERK_GROUP
    return NO_CENTRAL_PERK


def main_cast_words(episode_id: str, blocks: Sequence[Block]) -> dict[str, int]:
    """Töluð orð hverrar aðalpersónu; gestir og hópar (``speaker is None``) ekki taldir."""
    words = {name: 0 for name in MAIN_CAST}
    for row in dialogue_from_blocks(episode_id, blocks):
        if row.speaker in words:
            words[row.speaker] += row.word_count
    return words


def episode_result(episode_id: str, blocks: Sequence[Block]) -> EpisodeResult:
    """Blokkir eins handrits → ``EpisodeResult``."""
    singing_scenes = len(phoebe_singing_scenes(blocks))
    has_central_perk = any(is_central_perk_scene(block.text) for block in blocks)
    return EpisodeResult(
        episode_id=episode_id,
        group=comparison_group(singing_scenes, has_central_perk),
        has_central_perk=has_central_perk,
        singing_scenes=singing_scenes,
        words=main_cast_words(episode_id, blocks),
    )


def analyse_episode(path: Path) -> EpisodeResult:
    """Eitt handrit → orð hverrar aðalpersónu og samanburðarhópur."""
    return episode_result(episode_code(path), read_blocks(path))


def analyse(directory: Path | str | None = None) -> list[EpisodeResult]:
    """Keyrir ``analyse_episode`` á öll greind handrit, í stafrófsröð.

    ``directory`` ræðst eins og í ``friends_handrit.transcript_dir``: rökin,
    annars ``FRIENDS_HANDRIT_MAPPA``, annars sjálfgefna mappan utan git.
    """
    return [analyse_episode(path) for path in transcript_paths(directory)]
