"""Greiningarskýrslurnar fjórar sem JSON-hlutir (issue #14, pakki P2.5).

Hver skýrsla geymir spurningu, aðferð, einingu, fyrirsagnartölur og
töflurnar sjálfar. Lyklar, röð þeirra og textarnir eru **óbreyttir** úr
``src/phoebe_analysis.py`` (commit ``2865ed6``): frosna viðmiðið í
``data/processed/phoebe-stats/`` er borið saman við úttakið bæti fyrir bæti, og
textarnir eru því látnir standa eins og þeir voru skrifaðir þá.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from .phoebe_greining import Analysis
from .phoebe_ordafordi import upper_median
from .phoebe_skilgreiningar import (
    EFFECTIVE_TIE_PCT, FRIENDS, MAX_DISTINCTIVE_IN_REPORT, MIN_LINES_FOR_SHARE_RANKING,
    PERCENT_DECIMALS, PEOPLE, PHOEBE, TOP_EPISODES, pct,
)


def _best(rows: list[dict], key: str) -> str:
    return max(rows, key=lambda r: r[key])["character"]


def top_talkers_report(a: Analysis) -> dict:
    """``phoebe-top-talkers.json``: hver talar mest við Phoebe."""
    first, second = a.talkers[0], a.talkers[1]
    gap_pct = pct(first["adjacent_turns"] - second["adjacent_turns"], second["adjacent_turns"])
    return dict(
        question="Hver talar mest við Phoebe?",
        method=("Nalaeg raeðuskipti innan somu senu: ef X talar straxa eftir Phoebe "
                "(eða Phoebe straxa eftir X) telst thad ein samskipti. Til stuðnings: "
                "senur thar sem aðeins Phoebe og X tala, sameiginlegar senur, "
                "og linur X sem nefna Phoebe a nafn."),
        unit="fjoldi raeðuskipta (turns)",
        headline=dict(
            top_talker=first["character"],
            adjacent_turns=first["adjacent_turns"],
            runner_up=second["character"],
            runner_up_turns=second["adjacent_turns"],
            gap_pct=gap_pct,
            is_effectively_a_tie=gap_pct < EFFECTIVE_TIE_PCT,
            tie_note=(
                f"{first['character'].title()} og "
                f"{second['character'].title()} skilja aðeins "
                f"{gap_pct}% að a raeðuskiptum - thad er innan skekkjumarka "
                f"aðferðarinnar. Notið stuðningsmaelikvarðana "
                f"(two_person_scene_lines, lines_mentioning_phoebe, "
                f"interaction_lift) til að greina a milli."),
            highest_lift=_best(a.talkers, "interaction_lift"),
            most_one_on_one=_best(a.talkers, "two_person_scene_lines"),
            says_her_name_most=_best(a.talkers, "lines_mentioning_phoebe"),
            top_non_friend=a.guests[0]["character"] if a.guests else None),
        overall=a.talkers,
        by_season=a.season_talkers,
        non_friend_characters=a.guests)


def mentions_report(a: Analysis) -> dict:
    """``phoebe-mentions-by-season.json``: hversu oft er Phoebe nefnd."""
    rows = a.mentions.season_rows
    peak, lowest = a.mentions.peak, a.mentions.lowest
    return dict(
        question="Hversu oft er Phoebe nefnd i handritunum, eftir season?",
        method=("Talin eru oll tilvik nafnmynda (regex \\bph(oe|ee)b\\w*\\b): "
                "Phoebe, Phoebe's, Phoebs, Pheebs, Pheeboh. Aðgreint eftir thvi "
                "hvort nafnið kemur fyrir i raeðu annarra, i hennar eigin raeðu "
                "eða i sviðsleiðbeiningum. Sviga-innskot i raeðu eru fjarlaegð "
                "aður en talið er i raeðuflokkunum."),
        unit="fjoldi nafntilvika",
        headline=dict(
            total_mentions=sum(r["mentions_total"] for r in rows),
            total_in_dialogue=sum(r["mentions_in_dialogue_total"] for r in rows),
            peak_season=peak["season"],
            peak_per_episode=peak["dialogue_mentions_per_episode"],
            lowest_season=lowest["season"],
            lowest_per_episode=lowest["dialogue_mentions_per_episode"],
            nickname_pheebs_total=sum(r["mentions_nickname_pheebs"] for r in rows)),
        by_season=rows,
        who_says_her_name_overall=[dict(character=c, mentions=n)
                                   for c, n in a.mentions.by_speaker.most_common()
                                   if c in FRIENDS],
        name_mentions_comparison=[dict(character=c, spoken_mentions=a.mentions.name_totals[c])
                                  for c, _ in a.mentions.name_totals.most_common()])


def _phoebe_overall(a: Analysis, key: str):
    return next(r[key] for r in a.screentime.overall_rows if r["character"] == PHOEBE)


def screentime_report(a: Analysis) -> dict:
    """``phoebe-screentime-by-season.json``: plássið eftir þáttaröð og í heild."""
    trend = a.screentime.share_trend
    return dict(
        question="Screentime Phoebe a moti hinum fimm vinunum, eftir season",
        method=("Maelikvarðar: fjoldi raeðulina, fjoldi toluðra orða (svigainnskot "
                "fjarlaegð) og fjoldi sena thar sem personan talar. Hoplinur "
                "('All:', 'Monica and Phoebe:') eru undanskildar."),
        units=dict(lines="raeðulinur", words="toluð orð",
                   speaking_scenes="senur með a.m.k. einni raeðulinu",
                   share_pct="hlutfall af samtolu vinanna sex"),
        headline=dict(
            phoebe_rank_overall=_phoebe_overall(a, "rank_by_lines"),
            phoebe_line_share_pct=_phoebe_overall(a, "line_share_pct"),
            phoebe_best_season=max(trend, key=lambda r: r["line_share_pct"])["season"],
            phoebe_worst_season=min(trend, key=lambda r: r["line_share_pct"])["season"]),
        overall=a.screentime.overall_rows,
        by_season=a.screentime.season_rows,
        phoebe_share_trend=trend)


def _episode_summary(row: dict, share_first: bool = False) -> dict:
    head = dict(episode_code=row["episode_code"], season=row["season"], title=row["title"])
    if share_first:
        return dict(head, phoebe_line_share_pct=row["phoebe_line_share_pct"],
                    phoebe_lines=row["phoebe_lines"])
    return dict(head, phoebe_lines=row["phoebe_lines"],
                phoebe_line_share_pct=row["phoebe_line_share_pct"])


def _talkativeness(a: Analysis) -> dict:
    v = a.vocabulary
    lines = a.screentime.total_lines[PHOEBE]
    words = a.screentime.total_words[PHOEBE]
    return dict(
        total_lines=lines, total_words=words,
        words_per_line=round(words / lines, PERCENT_DECIMALS),
        median_words_per_line=upper_median(v.phoebe_line_lengths),
        longest_line_words=max(v.phoebe_line_lengths),
        one_word_lines=sum(1 for n in v.phoebe_line_lengths if n == 1),
        question_lines=v.questions,
        question_line_pct=pct(v.questions, lines),
        exclamation_lines=v.exclamations,
        exclamation_line_pct=pct(v.exclamations, lines),
        words_per_line_ranking=sorted(
            [dict(character=r["character"], words_per_line=r["words_per_line"])
             for r in a.screentime.overall_rows],
            key=lambda r: -r["words_per_line"]))


def extra_stats_report(a: Analysis) -> dict:
    """``phoebe-extra-stats.json``: talháttur, jaðarþættir, þemu og sérkennileg orð."""
    episodes = a.screentime.episode_rows
    by_lines = sorted(episodes, key=lambda r: -r["phoebe_lines"])
    by_share = sorted([r for r in episodes if r["friends_lines_total"] >= MIN_LINES_FOR_SHARE_RANKING],
                      key=lambda r: -r["phoebe_line_share_pct"])
    return dict(
        question="Aðrar tolfraeðilegar niðurstoður um Phoebe",
        talkativeness=_talkativeness(a),
        top_episodes_by_lines=[_episode_summary(r) for r in by_lines[:TOP_EPISODES]],
        bottom_episodes_by_lines=[_episode_summary(r) for r in by_lines[-TOP_EPISODES:]],
        top_episodes_by_share=[_episode_summary(r, share_first=True)
                               for r in by_share[:TOP_EPISODES]],
        signature_topics=[dict(topic=k, phoebe_uses=a.signature_phoebe[k],
                               whole_script_uses=a.signature_all[k],
                               phoebe_share_pct=pct(a.signature_phoebe[k], a.signature_all[k]))
                          for k, _ in a.signature_phoebe.most_common()],
        aliases_and_family=[dict(term=k, occurrences=v)
                            for k, v in a.alias_counts.most_common()],
        phoebe_mentions_of_people_by_season=[
            dict(season=r["season"], **{k: r[k] for k in PEOPLE}) for r in a.people_rows],
        distinctive_words_note=("z-gildi ur log-odds hlutfalli með Dirichlet-prior "
                                "(Monroe, Colaresi & Quinn 2008). Ha jakvaeð gildi = "
                                "orð sem Phoebe notar hlutfallslega miklu oftar en "
                                "hinir fimm."),
        distinctive_words_top=a.distinctive[:MAX_DISTINCTIVE_IN_REPORT])
