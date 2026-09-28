"""Nærvera: hversu oft er nafn Phoebe nefnt (issue #14, pakki P2.5).

Mælir nærveru þegar hún þegir sjálf: nafnið í ræðu annarra, í hennar eigin
ræðu og í sviðsleiðbeiningum. Nöfn hinna fimm eru talin líka, til
samanburðar. Svigainnskot í tilsvari teljast sviðsleiðbeining, ekki tal.
Flutt óbreytt að virkni úr skrefi 2b í ``src/phoebe_analysis.py`` (``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

try:  # keyrt sem eining innan pakkans
    from .friends_thattari import ACTION, PAREN_RE, PERSON, SCENE, Episode
    from .phoebe_plass import SeasonCounts
    from .phoebe_skilgreiningar import (
        FRIENDS, OTHER_NAME_RES, PERCENT_DECIMALS, PHOEBE, PHOEBE_FORMAL_RE,
        PHOEBE_NAME_RE, PHOEBE_NICK_RE,
    )
except ImportError:  # keyrt beint úr möppunni
    from friends_thattari import ACTION, PAREN_RE, PERSON, SCENE, Episode
    from phoebe_plass import SeasonCounts
    from phoebe_skilgreiningar import (
        FRIENDS, OTHER_NAME_RES, PERCENT_DECIMALS, PHOEBE, PHOEBE_FORMAL_RE,
        PHOEBE_NAME_RE, PHOEBE_NICK_RE,
    )


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
