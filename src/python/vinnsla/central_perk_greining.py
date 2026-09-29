"""Skref 3–4 í Central Perk-greiningunni: söngmerking, orð og samanburðarhópur.

Flutt úr ``src/phoebe_central_perk.py`` (commit ``2865ed6``, issue #14, P2.6):
``phoebe_singing_scenes`` og yfirferðarhamurinn ``audit`` (skref 3), og
``EpisodeResult``, ``analyse_episode`` og ``analyse`` (skref 4).

**Söngreglurnar eru viljandi íhaldssamar:** aðeins söngur sem umritari merkti
*skýrt* telst með. Yfirferðarhamurinn prentar víðari lista (allar Central
Perk-blokkir sem nefna tónlist) sem manneskja las yfir áður en reglurnar voru
festar; niðurstaða þeirrar yfirferðar er fest í
``tests/test_central_perk_raunhandrit.py``. Skráaleitin (``transcript_paths``) er ekki
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
        CENTRAL_PERK_GROUP, MAIN_CAST, MUSIC_RE, NO_CENTRAL_PERK, PHOEBE,
        PHOEBE_PERFORMANCE_RE, PHOEBE_SINGS, SINGING_CUE_RE, SPEAKER_RE,
    )
    from .central_perk_thattari import (
        block_contexts, dialogue_from_blocks, is_central_perk_scene, is_scene_start,
        normalise_speaker,
    )
    from .friends_handrit import episode_code, transcript_paths
except ImportError:  # keyrt beint úr möppunni
    from central_perk_lestur import Block, read_blocks
    from central_perk_mynstur import (
        CENTRAL_PERK_GROUP, MAIN_CAST, MUSIC_RE, NO_CENTRAL_PERK, PHOEBE,
        PHOEBE_PERFORMANCE_RE, PHOEBE_SINGS, SINGING_CUE_RE, SPEAKER_RE,
    )
    from central_perk_thattari import (
        block_contexts, dialogue_from_blocks, is_central_perk_scene, is_scene_start,
        normalise_speaker,
    )
    from friends_handrit import episode_code, transcript_paths


# --- Skref 3: söngmerking -------------------------------------------------------

# Breidd blokknúmers í yfirferðarlistanum (sama snið og gamla skriftan).
AUDIT_INDEX_WIDTH = 4


def is_phoebe_singing_line(text: str) -> bool:
    """Tilsvar Phoebe með söngmerkingu í nafninu eða línunni (``SINGING_CUE_RE``)."""
    match = SPEAKER_RE.match(text)
    if not match:
        return False
    label, line = match.groups()
    return normalise_speaker(label) == PHOEBE and bool(
        SINGING_CUE_RE.search(label) or SINGING_CUE_RE.search(line)
    )


def marks_phoebe_singing(text: str) -> bool:
    """Merkir blokkin (í Central Perk-senu) að Phoebe syngi?

    Þrjár leiðir, í þessari röð:

    - sviðsfyrirsögnin sjálf lýsir Phoebe koma fram (``PHOEBE_PERFORMANCE_RE``);
    - tilsvar Phoebe ber söngmerkingu í svigum (``is_phoebe_singing_line``);
    - sjálfstæð sviðslýsing — ekki tilsvar — segir að Phoebe syngi.

    Tilsvar annarrar persónu sem *nefnir* söng Phoebe telst ekki.
    """
    if is_scene_start(text) and PHOEBE_PERFORMANCE_RE.search(text):
        return True
    if SPEAKER_RE.match(text):
        return is_phoebe_singing_line(text)
    return bool(PHOEBE_PERFORMANCE_RE.search(text))


def phoebe_singing_scenes(blocks: Sequence[Block]) -> set[int]:
    """Númer þeirra sena í Central Perk þar sem handritið merkir söng Phoebe."""
    return {
        context.scene_index
        for context in block_contexts(blocks)
        if context.in_central_perk and marks_phoebe_singing(context.block.text)
    }


def audit_candidates(blocks: Sequence[Block]) -> list[tuple[Block, Block]]:
    """(sviðsfyrirsögn, blokk) fyrir hverja Central Perk-blokk sem nefnir tónlist.

    Fyrirsögnin er síðasta Central Perk-fyrirsögn á undan blokkinni.
    """
    candidates: list[tuple[Block, Block]] = []
    heading: Block | None = None
    in_central_perk = False
    for block in blocks:
        if is_scene_start(block.text):
            in_central_perk = is_central_perk_scene(block.text)
            if in_central_perk:
                heading = block
        if in_central_perk and heading is not None and MUSIC_RE.search(block.text):
            candidates.append((heading, block))
    return candidates


def audit_lines(path: Path) -> list[str]:
    """Yfirferðarlistinn fyrir eitt handrit, tilbúinn til prentunar; tómur ef ekkert.

    Listinn inniheldur handritstexta og fer því aðeins á skjá, aldrei í skrá
    sem gæti ratað í git (issue #3).
    """
    candidates = audit_candidates(read_blocks(path))
    if not candidates:
        return []
    lines = ["", f"## {episode_code(path)}"]
    seen_headings: set[int] = set()
    for heading, block in candidates:
        if heading.source_index not in seen_headings:
            lines.append(f"SCENE {heading.source_index:>{AUDIT_INDEX_WIDTH}}: {heading.text}")
            seen_headings.add(heading.source_index)
        lines.append(f"{block.source_index:>{AUDIT_INDEX_WIDTH}}: {block.text}")
    return lines


# --- Skref 4: orð og samanburðarhópur ---------------------------------------------


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
