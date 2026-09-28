"""Skref 3 í Central Perk-greiningunni: söngmerking (issue #14, P2.6).

Flutt úr ``src/phoebe_central_perk.py`` (commit ``2865ed6``):
``phoebe_singing_scenes`` og yfirferðarhamurinn ``audit``.

Reglurnar eru viljandi íhaldssamar: aðeins söngur sem umritari merkti
*skýrt* telst með. Yfirferðarhamurinn prentar víðari lista (allar Central
Perk-blokkir sem nefna tónlist) sem manneskja las yfir áður en reglurnar
voru festar; niðurstaða þeirrar yfirferðar er fest í prófunum
(``tests/test_central_perk_raunhandrit.py``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

try:  # keyrt sem eining innan pakkans
    from .central_perk_lestur import Block, read_blocks
    from .central_perk_mynstur import (
        MUSIC_RE, PHOEBE, PHOEBE_PERFORMANCE_RE, SINGING_CUE_RE, SPEAKER_RE,
    )
    from .central_perk_thattari import (
        block_contexts, is_central_perk_scene, is_scene_start, normalise_speaker,
    )
    from .friends_handrit import episode_code
except ImportError:  # keyrt beint úr möppunni
    from central_perk_lestur import Block, read_blocks
    from central_perk_mynstur import (
        MUSIC_RE, PHOEBE, PHOEBE_PERFORMANCE_RE, SINGING_CUE_RE, SPEAKER_RE,
    )
    from central_perk_thattari import (
        block_contexts, is_central_perk_scene, is_scene_start, normalise_speaker,
    )
    from friends_handrit import episode_code

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
