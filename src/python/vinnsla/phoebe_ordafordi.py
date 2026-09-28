"""Orðaforði Phoebe: sérkennileg orð og talháttur (issue #14, pakki P2.5).

Sérkennileg orð eru fundin með log-odds-hlutfalli með Dirichlet-prior
(Monroe, Colaresi & Quinn 2008). Hrá tíðni dugar ekki — algengustu orð hennar
eru líka algengustu orð hinna. Aðferðin ber saman hlutfallslega notkun og
deilir með öryggisbili, svo sjaldgæft orð sem kemur tvisvar fyrir trónir ekki
á toppnum. Flutt óbreytt að virkni úr skrefi 2d í ``src/phoebe_analysis.py``
(commit ``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

try:  # keyrt sem eining innan pakkans
    from .friends_thattari import Episode, spoken_words
    from .phoebe_plass import friend_lines
    from .phoebe_skilgreiningar import (
        LIFT_DECIMALS, MAX_DISTINCTIVE_ROWS, MIN_WORD_LENGTH, MIN_WORD_TOTAL,
        PER_TEN_THOUSAND, PERCENT_DECIMALS, PHOEBE, PRIOR_SIZE, STOPWORDS,
    )
except ImportError:  # keyrt beint úr möppunni
    from friends_thattari import Episode, spoken_words
    from phoebe_plass import friend_lines
    from phoebe_skilgreiningar import (
        LIFT_DECIMALS, MAX_DISTINCTIVE_ROWS, MIN_WORD_LENGTH, MIN_WORD_TOTAL,
        PER_TEN_THOUSAND, PERCENT_DECIMALS, PHOEBE, PRIOR_SIZE, STOPWORDS,
    )

# Dálkar sérkennilegu orðanna, fastir svo tóm tafla (lítið úrtak þar sem
# ekkert orð nær MIN_WORD_TOTAL) verði tóm skrá með haus en ekki villa.
DISTINCTIVE_FIELDS = ["word", "z_score", "phoebe_count", "others_count",
                      "phoebe_per_10k", "others_per_10k"]
QUESTION_MARK = "?"
EXCLAMATION_MARK = "!"


@dataclass
class Vocabulary:
    """Orðatíðni Phoebe og hinna fimm, og lengd hverrar línu hennar í orðum."""

    phoebe_words: Counter = field(default_factory=Counter)
    other_words: Counter = field(default_factory=Counter)
    phoebe_line_lengths: list[int] = field(default_factory=list)
    questions: int = 0
    exclamations: int = 0


def count_vocabulary(episodes: list[Episode]) -> Vocabulary:
    """Telur töluð orð vinanna sex, aðskilin í Phoebe og hina fimm."""
    result = Vocabulary()
    for episode in episodes:
        for line in friend_lines(episode):
            words = spoken_words(line.text)
            if line.speaker != PHOEBE:
                result.other_words.update(words)
                continue
            result.phoebe_words.update(words)
            result.phoebe_line_lengths.append(len(words))
            result.questions += QUESTION_MARK in line.spoken
            result.exclamations += EXCLAMATION_MARK in line.spoken
    return result


def log_odds_z(y1: int, y2: int, n1: int, n2: int, prior: float) -> float:
    """z-gildi log-odds-munar orðs milli tveggja texta með Dirichlet-prior.

    ``y1``/``y2`` eru tíðni orðsins í hvorum texta, ``n1``/``n2`` stærð textanna
    og ``prior`` er hlutdeild orðsins í priornum (``a0 * tíðni / heild``).
    """
    delta = (math.log((y1 + prior) / (n1 + PRIOR_SIZE - y1 - prior))
             - math.log((y2 + prior) / (n2 + PRIOR_SIZE - y2 - prior)))
    variance = 1.0 / (y1 + prior) + 1.0 / (y2 + prior)
    return delta / math.sqrt(variance)


def distinctive_words(vocabulary: Vocabulary) -> list[dict]:
    """Orðin sem Phoebe notar hlutfallslega oftast umfram hina (efstu ``MAX_DISTINCTIVE_ROWS``).

    Orð þarf minnst ``MIN_WORD_TOTAL`` tilvik alls, ``MIN_WORD_LENGTH`` stafi og
    má ekki vera stopporð.
    """
    ph, oth = vocabulary.phoebe_words, vocabulary.other_words
    n1, n2 = sum(ph.values()), sum(oth.values())
    background = ph + oth
    n_background = n1 + n2
    rows = []
    for word, total in background.items():
        if total < MIN_WORD_TOTAL or word in STOPWORDS or len(word) < MIN_WORD_LENGTH:
            continue
        prior = PRIOR_SIZE * total / n_background
        y1, y2 = ph[word], oth[word]
        rows.append(dict(
            word=word, z_score=round(log_odds_z(y1, y2, n1, n2, prior), LIFT_DECIMALS),
            phoebe_count=y1, others_count=y2,
            phoebe_per_10k=round(PER_TEN_THOUSAND * y1 / n1, PERCENT_DECIMALS),
            others_per_10k=round(PER_TEN_THOUSAND * y2 / n2, PERCENT_DECIMALS)))
    rows.sort(key=lambda r: -r["z_score"])
    return rows[:MAX_DISTINCTIVE_ROWS]


def upper_median(values: list[int]) -> int:
    """Efra miðgildi: ``sorted(values)[len // 2]``, eins og gamla skriftan reiknaði.

    Við sléttan fjölda er þetta EKKI meðaltal miðgildanna tveggja. Haldið
    óbreyttu því viðmiðið (``median_words_per_line``) byggir á því.
    """
    if not values:
        raise ValueError("Miðgildi tómrar talnaraðar er ekki skilgreint.")
    return sorted(values)[len(values) // 2]
