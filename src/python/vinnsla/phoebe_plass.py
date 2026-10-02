"""Plássið: línur, orð og senur hverrar aðalpersónu (issue #14, pakki P2.5).

Mælir umfang — hversu mikið hver vinanna sex talar, eftir þætti, þáttaröð og
í heild. Hóplínur og gestir eru undanskilin, svo hlutföllin leggist saman í
100% innan vinahópsins. Flutt óbreytt að virkni úr skrefi 2a í
``src/phoebe_analysis.py`` (commit ``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .friends_thattari import PERSON, Episode, Line, spoken_words
from .phoebe_skilgreiningar import FRIENDS, PERCENT_DECIMALS, PHOEBE, pct


@dataclass(frozen=True)
class SeasonCounts:
    """Þáttaraðirnar, sýndir þættir og handritsskrár á hverja (tvíþættir deila skrá)."""

    seasons: list[int]
    aired: Counter
    files: Counter


@dataclass(frozen=True)
class Screentime:
    """Niðurstaða plásstalningarinnar; raðir eru ``dict`` í dálkaröð úttaksins."""

    counts: SeasonCounts
    episode_rows: list[dict]
    season_rows: list[dict]
    overall_rows: list[dict]
    share_trend: list[dict]
    lines_by_season: dict[int, Counter]
    words_by_season: dict[int, Counter]
    total_lines: Counter
    total_words: Counter

    @property
    def grand_lines(self) -> int:
        """Samtala lína vinanna sex."""
        return sum(self.total_lines.values())


def season_counts(episodes: list[Episode]) -> SeasonCounts:
    """Telur sýnda þætti og handritsskrár á hverja þáttaröð."""
    aired: Counter = Counter()
    files: Counter = Counter()
    for episode in episodes:
        aired[episode.season] += episode.n_episodes
        files[episode.season] += 1
    return SeasonCounts(sorted({e.season for e in episodes}), aired, files)


def friend_lines(episode: Episode) -> list[Line]:
    """Tilsvör vinanna sex í þættinum — án hóplína og gesta."""
    return [
        line for line in episode.lines
        if line.kind == PERSON and not line.is_group and line.speaker in FRIENDS
    ]


def _episode_row(episode: Episode, lines: Counter, words: Counter) -> dict:
    total_lines = sum(lines[c] for c in FRIENDS)
    total_words = sum(words[c] for c in FRIENDS)
    row = dict(episode_code=episode.code, season=episode.season, title=episode.title,
               n_aired_episodes=episode.n_episodes,
               friends_lines_total=total_lines, friends_words_total=total_words,
               phoebe_lines=lines[PHOEBE], phoebe_words=words[PHOEBE],
               phoebe_line_share_pct=pct(lines[PHOEBE], total_lines),
               phoebe_word_share_pct=pct(words[PHOEBE], total_words))
    for c in FRIENDS:
        row[f"{c}_lines"] = lines[c]
        row[f"{c}_words"] = words[c]
    return row


def _ratio(numerator: int, denominator: int) -> float:
    """Deiling námunduð í tvo aukastafi; 0 ef nefnarinn er núll (persóna sem þegir)."""
    return round(numerator / denominator, PERCENT_DECIMALS) if denominator else 0.0


def _season_rows(counts: SeasonCounts, lines_ct, words_ct, chars_ct, scenes_ct) -> list[dict]:
    rows = []
    for s in counts.seasons:
        season_lines = sum(lines_ct[s][c] for c in FRIENDS)
        season_words = sum(words_ct[s][c] for c in FRIENDS)
        aired = counts.aired[s]
        group = []
        for c in FRIENDS:
            group.append(dict(
                season=s, character=c,
                lines=lines_ct[s][c], words=words_ct[s][c],
                characters_typed=chars_ct[s][c],
                speaking_scenes=len(scenes_ct[s][c]),
                line_share_pct=pct(lines_ct[s][c], season_lines),
                word_share_pct=pct(words_ct[s][c], season_words),
                lines_per_episode=round(lines_ct[s][c] / aired, PERCENT_DECIMALS),
                words_per_episode=round(words_ct[s][c] / aired, PERCENT_DECIMALS),
                words_per_line=_ratio(words_ct[s][c], lines_ct[s][c]),
                rank_by_lines=0))
        for rank, row in enumerate(sorted(group, key=lambda r: -r["lines"]), 1):
            row["rank_by_lines"] = rank
        rows.extend(group)
    return rows


def _overall_rows(total_lines: Counter, total_words: Counter, total_scenes) -> list[dict]:
    grand_lines = sum(total_lines.values())
    grand_words = sum(total_words.values())
    rows = sorted(
        [dict(character=c, lines=total_lines[c], words=total_words[c],
              speaking_scenes=len(total_scenes[c]),
              line_share_pct=pct(total_lines[c], grand_lines),
              word_share_pct=pct(total_words[c], grand_words),
              words_per_line=_ratio(total_words[c], total_lines[c]))
         for c in FRIENDS],
        key=lambda r: -r["lines"])
    for rank, row in enumerate(rows, 1):
        row["rank_by_lines"] = rank
    return rows


def count_screentime(episodes: list[Episode]) -> Screentime:
    """Telur línur, orð, stafi og senur vinanna eftir þætti, þáttaröð og í heild."""
    counts = season_counts(episodes)
    lines_ct: dict[int, Counter] = defaultdict(Counter)
    words_ct: dict[int, Counter] = defaultdict(Counter)
    chars_ct: dict[int, Counter] = defaultdict(Counter)
    scenes_ct: dict[int, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    episode_rows = []

    for episode in episodes:
        s = episode.season
        ep_lines: Counter = Counter()
        ep_words: Counter = Counter()
        for line in friend_lines(episode):
            c = line.speaker
            n_words = len(spoken_words(line.text))
            ep_lines[c] += 1
            ep_words[c] += n_words
            lines_ct[s][c] += 1
            words_ct[s][c] += n_words
            chars_ct[s][c] += len(line.spoken.strip())
            scenes_ct[s][c].add((episode.file, line.scene))
        episode_rows.append(_episode_row(episode, ep_lines, ep_words))

    total_lines: Counter = Counter()
    total_words: Counter = Counter()
    total_scenes: dict[str, set] = defaultdict(set)
    for s in counts.seasons:
        for c in FRIENDS:
            total_lines[c] += lines_ct[s][c]
            total_words[c] += words_ct[s][c]
            total_scenes[c] |= scenes_ct[s][c]

    share_trend = [
        dict(season=s,
             line_share_pct=pct(lines_ct[s][PHOEBE], sum(lines_ct[s][c] for c in FRIENDS)),
             word_share_pct=pct(words_ct[s][PHOEBE], sum(words_ct[s][c] for c in FRIENDS)))
        for s in counts.seasons
    ]
    return Screentime(
        counts=counts,
        episode_rows=episode_rows,
        season_rows=_season_rows(counts, lines_ct, words_ct, chars_ct, scenes_ct),
        overall_rows=_overall_rows(total_lines, total_words, total_scenes),
        share_trend=share_trend,
        lines_by_season=lines_ct,
        words_by_season=words_ct,
        total_lines=total_lines,
        total_words=total_words,
    )
