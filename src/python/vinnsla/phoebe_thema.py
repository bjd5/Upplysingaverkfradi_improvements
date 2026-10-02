"""Nærvera og þemu Phoebe: nafntilvik, einkennisorð, fólk og frasar (issue #14, P2.5).

**Nærvera** (``count_mentions``) mælir hana þegar hún þegir sjálf: nafnið í
ræðu annarra, í hennar eigin ræðu og í sviðsleiðbeiningum. Nöfn hinna fimm
eru talin líka, til samanburðar. Svigainnskot í tilsvari teljast
sviðsleiðbeining, ekki tal. Úr skrefi 2b í ``src/phoebe_analysis.py``.

**Þemu** (``corpus_counts`` o.fl.) telja mynstrin í ``phoebe_skilgreiningar``
annaðhvort í hennar eigin ræðu (``PHOEBE_SCOPE``) eða í öllum
handritstextanum (``ALL_SCOPE``), svo hægt sé að sýna hlut hennar í hverju
þema. Úr skrefi 4c og samningsskránni ``signature-phrases.csv``.

Hvort tveggja er flutt óbreytt að virkni úr commit ``2865ed6``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass

from .friends_thattari import ACTION, PAREN_RE, PERSON, SCENE, Episode, Line
from .phoebe_plass import SeasonCounts
from .phoebe_skilgreiningar import (
    FRIENDS, OTHER_NAME_RES, PEOPLE, PERCENT_DECIMALS, PHOEBE, PHOEBE_FORMAL_RE,
    PHOEBE_NAME_RE, PHOEBE_NICK_RE, SIGNATURE_PHRASES,
)


# --- Nærvera: nafntilvik ------------------------------------------------------

@dataclass(frozen=True)
class Mentions:
    """Nafntilvik eftir þáttaröð, hver nefnir hana og samanburður nafnanna."""

    season_rows: list[dict]
    by_speaker: Counter
    name_totals: Counter

    @property
    def peak(self) -> dict:
        """Þáttaröðin með flest nafntilvik í tali á hvern þátt."""
        return max(self.season_rows, key=lambda r: r["dialogue_mentions_per_episode"])

    @property
    def lowest(self) -> dict:
        """Þáttaröðin með fæst nafntilvik í tali á hvern þátt."""
        return min(self.season_rows, key=lambda r: r["dialogue_mentions_per_episode"])


def _change_pct(current: float, previous: float | None) -> float | None:
    """Breyting frá fyrri þáttaröð í %; ``None`` þar sem enginn samanburður er."""
    if not previous:
        return None
    return round(100.0 * (current - previous) / previous, PERCENT_DECIMALS)


def _season_row(s: int, counts: SeasonCounts, m: Counter, by_speaker: Counter,
                previous: float | None) -> dict:
    dialogue = m["in_dialogue_by_others"] + m["in_own_dialogue"]
    per_episode = round(dialogue / counts.aired[s], PERCENT_DECIMALS)
    top = by_speaker.most_common(1)
    return dict(
        season=s, episodes=counts.aired[s], transcript_files=counts.files[s],
        mentions_in_dialogue_by_others=m["in_dialogue_by_others"],
        mentions_in_own_dialogue=m["in_own_dialogue"],
        mentions_in_dialogue_total=dialogue,
        mentions_in_stage_directions=m["in_stage_directions"],
        mentions_total=dialogue + m["in_stage_directions"],
        mentions_formal_phoebe=m["formal_phoebe"],
        mentions_nickname_pheebs=m["nickname_pheebs"],
        dialogue_mentions_per_episode=per_episode,
        change_vs_prev_season_pct=_change_pct(per_episode, previous),
        top_mentioner=top[0][0] if top else None,
        top_mentioner_count=top[0][1] if top else 0)


def count_mentions(episodes: list[Episode], counts: SeasonCounts) -> Mentions:
    """Telur nafntilvik Phoebe (og hinna fimm) eftir þáttaröð og ræðumanni."""
    mentions: dict[int, Counter] = defaultdict(Counter)
    by_speaker_season: dict[int, Counter] = defaultdict(Counter)
    by_speaker: Counter = Counter()
    other_mentions: dict[int, Counter] = defaultdict(Counter)

    for episode in episodes:
        s = episode.season
        for line in episode.lines:
            if line.kind == PERSON:
                spoken = line.spoken
                inline_directions = " ".join(PAREN_RE.findall(line.text))
                for c, pattern in OTHER_NAME_RES.items():
                    other_mentions[s][c] += len(pattern.findall(spoken))
                other_mentions[s][PHOEBE] += len(PHOEBE_NAME_RE.findall(spoken))

                n_formal = len(PHOEBE_FORMAL_RE.findall(spoken))
                n_nick = len(PHOEBE_NICK_RE.findall(spoken))
                n_all = n_formal + n_nick
                if n_all:
                    if line.speaker == PHOEBE:
                        mentions[s]["in_own_dialogue"] += n_all
                    else:
                        mentions[s]["in_dialogue_by_others"] += n_all
                        by_speaker_season[s][line.speaker] += n_all
                        by_speaker[line.speaker] += n_all
                mentions[s]["formal_phoebe"] += n_formal
                mentions[s]["nickname_pheebs"] += n_nick
                mentions[s]["in_stage_directions"] += len(
                    PHOEBE_NAME_RE.findall(inline_directions))
            elif line.kind in (SCENE, ACTION):
                mentions[s]["in_stage_directions"] += len(PHOEBE_NAME_RE.findall(line.text))

    rows = []
    previous = None
    for s in counts.seasons:
        row = _season_row(s, counts, mentions[s], by_speaker_season[s], previous)
        previous = row["dialogue_mentions_per_episode"]
        rows.append(row)

    name_totals: Counter = Counter()
    for s in counts.seasons:
        for c in FRIENDS:
            name_totals[c] += other_mentions[s][c]
    return Mentions(season_rows=rows, by_speaker=by_speaker, name_totals=name_totals)


# --- Þemu: einkennisorð, fólk og frasar ------------------------------------------

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
