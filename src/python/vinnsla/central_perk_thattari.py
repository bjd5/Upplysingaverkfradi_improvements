"""Skref 2 í Central Perk-greiningunni: blokkir → senur og tilsvör (issue #14, P2.6).

Flutt úr ``src/phoebe_central_perk.py`` (commit ``2865ed6``): ``Dialogue``,
``is_scene_start``, ``is_central_perk_scene``, ``normalise_speaker``,
``count_words`` og ``block_contexts``.

Þessi þáttari er **sér** frá ``friends_thattari`` (P2.5) af ásettu ráði:
ræðumannamynstrið, orðamynstrið og ``normalise_speaker`` (sem skilar
``str | None`` og hafnar hópum) eru önnur, og tölur viðmiðsins byggja á þeim.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .central_perk_lestur import Block, clean_text
from .central_perk_mynstur import (
    CENTRAL_PERK, NAME_ALIAS_PATTERNS, SCENE_START_RE, SPEAKER_RE, STAGE_DIRECTION_RE,
    WORD_RE,
)


@dataclass(frozen=True)
class Dialogue:
    """Eitt tilsvar eftir þáttun.

    ``speaker_label`` er nafnið eins og það stóð í handritinu; ``speaker`` er
    kanóníska nafnið (ein aðalpersónanna sex) eða ``None`` ef ræðumaðurinn er
    gestur, hópur eða óþekkjanlegur.
    """

    episode_id: str
    scene_index: int
    in_central_perk: bool
    speaker_label: str
    speaker: str | None
    line: str
    word_count: int
    source_index: int


@dataclass(frozen=True)
class BlockContext:
    """Blokk ásamt senunúmeri sínu og hvort senan er í Central Perk."""

    block: Block
    scene_index: int
    in_central_perk: bool


def is_scene_start(text: str) -> bool:
    """Hefst blokkin á sviðsfyrirsögn (``[Scene: …]``, ``(Cut to …)`` o.s.frv.)?"""
    return bool(SCENE_START_RE.search(text))


def is_central_perk_scene(text: str) -> bool:
    """Sviðsfyrirsögn sem nefnir Central Perk, t.d. ``[Scene: Central Perk, …]``."""
    return is_scene_start(text) and CENTRAL_PERK in text.casefold()


def normalise_speaker(label: str) -> str | None:
    """Færir nafn ræðumanns á kanónískt nafn aðalpersónu, annars ``None``.

    Leitað er að hverju samheiti sem heilu orði í nafninu, svo
    ``Phoebe (singing)`` og ``PHOEBE`` finnast bæði. Ef nafnið nefnir fleiri
    en eina aðalpersónu (``Monica and Phoebe``) er það hópur og telst engum.
    """
    names = {canonical for pattern, canonical in NAME_ALIAS_PATTERNS if pattern.search(label)}
    return next(iter(names)) if len(names) == 1 else None


def count_words(text: str) -> int:
    """Töluð orð í tilsvari: sviðsleiðbeiningar í svigum fyrst fjarlægðar."""
    return len(WORD_RE.findall(STAGE_DIRECTION_RE.sub(" ", text)))


def block_contexts(blocks: Sequence[Block]) -> list[BlockContext]:
    """Senurakning fyrir ALLAR blokkir, í röð.

    Senuteljarinn hækkar við hverja sviðsfyrirsögn og ``in_central_perk``
    helst þar til næsta fyrirsögn kemur. Söngleitin þarf þetta fyrir
    sjálfstæðar sviðslýsingar sem eru ekki tilsvör.
    """
    contexts: list[BlockContext] = []
    scene_index = 0
    in_central_perk = False
    for block in blocks:
        if is_scene_start(block.text):
            scene_index += 1
            in_central_perk = is_central_perk_scene(block.text)
        contexts.append(BlockContext(block, scene_index, in_central_perk))
    return contexts


def dialogue_from_blocks(episode_id: str, blocks: Sequence[Block]) -> list[Dialogue]:
    """Tilsvörin í blokkunum, hvert með senu sinni.

    Sviðsfyrirsagnir eru ekki tilsvör. Blokk sem er hvorki fyrirsögn né
    ``Nafn: …`` (kreditlínur, „Commercial Break“, sjálfstæðar sviðslýsingar)
    er sleppt.
    """
    dialogue: list[Dialogue] = []
    for context in block_contexts(blocks):
        text = context.block.text
        if is_scene_start(text):
            continue
        match = SPEAKER_RE.match(text)
        if not match:
            continue
        label, line = match.groups()
        line = clean_text(line)
        dialogue.append(Dialogue(
            episode_id=episode_id,
            scene_index=context.scene_index,
            in_central_perk=context.in_central_perk,
            speaker_label=clean_text(label),
            speaker=normalise_speaker(label),
            line=line,
            word_count=count_words(line),
            source_index=context.block.source_index,
        ))
    return dialogue
