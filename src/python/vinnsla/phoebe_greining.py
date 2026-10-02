"""Phoebe-greiningin í heild: les handritin og keyrir allar talningarnar.

Tengir saman einingarnar (issue #14, pakki P2.5) í þeirri röð sem
``main()`` gömlu skriftunnar ``src/phoebe_analysis.py`` (commit ``2865ed6``)
gerði, og skilar öllum niðurstöðunum í einum hlut, ``Analysis``, sem
skýrslu- og úttakseiningarnar lesa:

1. **Lesa og þátta** — ``friends_handrit`` + ``friends_thattari``.
2. **Telja** — ``phoebe_plass`` (plássið), ``phoebe_thema`` (nærvera og þemu),
   ``phoebe_tengsl`` (tengsl og ``interaction_lift``) og ``phoebe_ordafordi``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .friends_handrit import transcript_paths
from .friends_thattari import LINE_KINDS, OTHER, Episode, parse_episode
from .phoebe_ordafordi import Vocabulary, count_vocabulary, distinctive_words
from .phoebe_plass import Screentime, count_screentime
from .phoebe_skilgreiningar import ALIAS_TERMS, SIGNATURE_TOPICS, pct
from .phoebe_tengsl import (
    count_interactions, guest_rows, interaction_matrix, season_talker_rows, talker_rows,
)
from .phoebe_thema import (
    ALL_SCOPE, PHOEBE_SCOPE, Mentions, corpus_counts, count_mentions, people_by_season,
    signature_phrases,
)


@dataclass(frozen=True)
class Analysis:
    """Allar niðurstöður greiningarinnar; skýrslurnar eru reiknaðar úr þessu einu."""

    episodes: list[Episode]
    kind_counts: Counter
    screentime: Screentime
    mentions: Mentions
    talkers: list[dict]
    season_talkers: list[dict]
    guests: list[dict]
    pairs: Counter
    vocabulary: Vocabulary
    distinctive: list[dict]
    signature_phoebe: Counter
    signature_all: Counter
    alias_counts: Counter
    people_rows: list[dict]
    phrase_rows: list[dict]

    @property
    def total_blocks(self) -> int:
        """Allar textablokkir sem þáttarinn flokkaði."""
        return sum(self.kind_counts.values())

    @property
    def unclassified_pct(self) -> float:
        """Hlutfall blokka sem lentu í ``other`` — gæðamat á þáttuninni."""
        return pct(self.kind_counts[OTHER], self.total_blocks)


def count_line_kinds(episodes: list[Episode]) -> Counter:
    """Fjöldi textablokka í hverjum flokki. Hátt hlutfall ``other`` þýddi að
    þáttarinn missti af tilsvörum; talan fer í ``_meta.json``."""
    counts: Counter = Counter()
    for episode in episodes:
        for line in episode.lines:
            counts[line.kind] += 1
    unknown = set(counts) - set(LINE_KINDS)
    if unknown:
        raise ValueError(f"Þáttarinn skilaði óþekktum flokkum: {sorted(unknown)}")
    return counts


def analyse_episodes(episodes: list[Episode]) -> Analysis:
    """Keyrir allar talningarnar á þáttuðum þáttum."""
    if not episodes:
        raise ValueError("Engir þættir til að greina.")
    screentime = count_screentime(episodes)
    interactions = count_interactions(episodes)
    vocabulary = count_vocabulary(episodes)
    return Analysis(
        episodes=episodes,
        kind_counts=count_line_kinds(episodes),
        screentime=screentime,
        mentions=count_mentions(episodes, screentime.counts),
        talkers=talker_rows(interactions, screentime.total_lines),
        season_talkers=season_talker_rows(interactions, screentime.counts.seasons),
        guests=guest_rows(interactions),
        pairs=interaction_matrix(episodes),
        vocabulary=vocabulary,
        distinctive=distinctive_words(vocabulary),
        signature_phoebe=corpus_counts(episodes, SIGNATURE_TOPICS, PHOEBE_SCOPE),
        signature_all=corpus_counts(episodes, SIGNATURE_TOPICS, ALL_SCOPE),
        alias_counts=corpus_counts(episodes, ALIAS_TERMS, ALL_SCOPE),
        people_rows=people_by_season(episodes, screentime.counts.seasons),
        phrase_rows=signature_phrases(episodes),
    )


def analyse(directory: Path | str | None = None) -> Analysis:
    """Les og þáttar öll handritin í möppunni og keyrir greininguna."""
    return analyse_episodes([parse_episode(path) for path in transcript_paths(directory)])
