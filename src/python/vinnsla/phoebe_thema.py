"""Þemu Phoebe: einkennisorð, gervinöfn, fólk og frasar (issue #14, pakki P2.5).

Telur mynstrin í ``phoebe_skilgreiningar`` annaðhvort í hennar eigin ræðu
(``PHOEBE_SCOPE``) eða í öllum handritstextanum (``ALL_SCOPE``), svo hægt sé
að sýna hlut hennar í hverju þema. Flutt óbreytt að virkni úr skrefum 4c og
samningsskránni ``signature-phrases.csv`` í ``src/phoebe_analysis.py``
(commit ``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterator

try:  # keyrt sem eining innan pakkans
    from .friends_thattari import PERSON, Episode, Line
    from .phoebe_skilgreiningar import PEOPLE, PHOEBE, SIGNATURE_PHRASES
except ImportError:  # keyrt beint úr möppunni
    from friends_thattari import PERSON, Episode, Line
    from phoebe_skilgreiningar import PEOPLE, PHOEBE, SIGNATURE_PHRASES

PHOEBE_SCOPE = "phoebe"
ALL_SCOPE = "all"
SCOPES = (PHOEBE_SCOPE, ALL_SCOPE)


def phoebe_spoken(episodes: list[Episode]) -> Iterator[tuple[Episode, str]]:
    """(þáttur, lágstafað tal) fyrir hvert tilsvar Phoebe, í röð."""
    for episode in episodes:
        for line in episode.lines:
            if line.kind == PERSON and line.speaker == PHOEBE:
                yield episode, line.spoken_lower


def _scoped_text(line: Line, scope: str) -> str | None:
    if scope == ALL_SCOPE:
        return line.text_lower
    if line.kind != PERSON or line.speaker != PHOEBE:
        return None
    return line.spoken_lower


def combined_pattern(patterns: dict[str, re.Pattern]) -> re.Pattern:
    """Sameinar mynstrin í eitt ``p1|p2|…`` til forsíunar.

    Sameinaða mynstrið erfir flögg; ósamræmd flögg myndu breyta talningunni,
    svo þá fellur ``ValueError`` í stað þess að telja rangt.
    """
    flags = {pattern.flags for pattern in patterns.values()}
    if len(flags) != 1:
        raise ValueError("Mynstrin í einni talningu verða að hafa sömu flögg.")
    return re.compile("|".join(f"(?:{p.pattern})" for p in patterns.values()), flags.pop())


def corpus_counts(episodes: list[Episode], patterns: dict[str, re.Pattern],
                  scope: str = PHOEBE_SCOPE) -> Counter:
    """Telur hvert mynstur í tali Phoebe (``phoebe``) eða öllum textanum (``all``).

    Lína sem sameinaða mynstrið finnur ekkert í er ekki skoðuð frekar; það
    breytir engri tölu en sparar N yfirferðir á langflestum línum. Öll mynstrin
    eru lyklar í útkomunni, líka þau sem finnast hvergi.
    """
    if scope not in SCOPES:
        raise ValueError(f"Óþekkt svið talningar: {scope!r} (leyfð: {SCOPES}).")
    any_pattern = combined_pattern(patterns)
    counts = Counter({key: 0 for key in patterns})
    for episode in episodes:
        for line in episode.lines:
            text = _scoped_text(line, scope)
            if text is None or not any_pattern.search(text):
                continue
            for key, pattern in patterns.items():
                counts[key] += len(pattern.findall(text))
    return counts


def people_by_season(episodes: list[Episode], seasons: list[int]) -> list[dict]:
    """Hversu oft Phoebe nefnir hvern í ``PEOPLE``, eftir þáttaröð."""
    counts: dict[int, Counter] = defaultdict(Counter)
    for episode, text in phoebe_spoken(episodes):
        for key, pattern in PEOPLE.items():
            counts[episode.season][key] += len(pattern.findall(text))
    return [dict(season=s, **{key: counts[s][key] for key in PEOPLE}) for s in seasons]


def signature_phrases(episodes: list[Episode]) -> list[dict]:
    """Frasar Phoebe: fjöldi og fyrsta og síðasta þáttaröð sem hún segir þá."""
    total: Counter = Counter()
    first: dict[str, int] = {}
    last: dict[str, int] = {}
    for episode, text in phoebe_spoken(episodes):
        for name, pattern in SIGNATURE_PHRASES.items():
            n = len(pattern.findall(text))
            if not n:
                continue
            total[name] += n
            first[name] = min(first.get(name, episode.season), episode.season)
            last[name] = max(last.get(name, episode.season), episode.season)
    return [dict(phrase=p, count=total[p], first_season=first[p], last_season=last[p])
            for p, _ in total.most_common()]
