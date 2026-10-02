"""Samningsskrárnar og lýsigögnin (issue #14, pakki P2.5).

Gamla síðan ``site/friends/phoebe-statistics.qmd`` las sex skrár með föstum
heitum og dálkum („samningsskrár“), og ``_meta.json`` segir hvaða skrár,
reglur og gæðamat liggja að baki. Lyklar, dálkar og röð eru óbreytt úr
``src/phoebe_analysis.py`` (commit ``2865ed6``) svo úttakið megi bera saman
við frosna viðmiðið bæti fyrir bæti.

**Tvö frávik, bæði viljandi:**

* ``generated_at`` (``summary.json``) og ``generated_utc`` (``_meta.json``)
  eru felld brott. Vegguklukkustimpill lætur afleidda skrá virðast nýja þótt
  gögnin séu óbreytt (issue #47); útflutningslagið setur ``uppfaert`` (regla 5.4).
* ``generator`` og ``note`` vísa á nýju eininguna, ekki gömlu skriftuna, og
  ``_meta.json`` fær ``source_commit`` — commit handritasafnsins sem var greint.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from .friends_handrit import DOUBLE_EPISODE_FILES, EXCLUDED_FILES, SOURCE_COMMIT
from .friends_thattari import ACTION, OTHER, PERSON, SCENE
from .phoebe_greining import Analysis
from .phoebe_skilgreiningar import (
    DISPLAY_ORDER, FRIENDS, MAX_GUESTS_IN_CONTRACT, PERCENT_DECIMALS, PHOEBE,
    SHARE_DECIMALS, TITLES,
)

GENERATOR = "src/python/vinnsla/phoebe_uttak.py"
SUMMARY_NOTE = ("Raunniðurstoður ur src/python/vinnsla/phoebe_uttak.py. "
                "Sja docs/adferdafraedi.md fyrir aðferðafraeði.")
# Grunnlína „jafnt pláss“: einn sjötti á hvern vinanna sex.
EQUAL_SHARE = 1 / len(FRIENDS)

SCREENTIME_FIELDS = ["season", "character", "lines", "words", "line_share"]
MENTIONS_FIELDS = ["season", "mentions", "episodes", "mentions_per_episode"]
SPEAKS_WITH_FIELDS = ["character", "lines_to_phoebe", "lines_from_phoebe", "scenes_together"]
MATRIX_FIELDS = ["speaker", "addressee", "lines"]
PHRASE_FIELDS = ["phrase", "count", "first_season", "last_season"]


def summary(a: Analysis) -> dict:
    """``summary.json``: fyrirsagnartölur síðunnar."""
    st = a.screentime
    others = [c for c in FRIENDS if c != PHOEBE]
    others_lines = sum(st.total_lines[c] for c in others)
    others_words = sum(st.total_words[c] for c in others)
    present = sum(r["n_aired_episodes"] for r in st.episode_rows if r["phoebe_lines"] > 0)
    top_partner = max(a.talkers, key=lambda r: r["replies_to_phoebe"])["character"]
    return dict(
        placeholder=False,
        note=SUMMARY_NOTE,
        source="fangj/delvinso Friends-handrit, 227 handritsskrar (236 thaettir)",
        character="Phoebe Buffay",
        characters=[TITLES[c] for c in DISPLAY_ORDER],
        seasons=len(st.counts.seasons),
        episodes=sum(st.counts.aired.values()),
        episodes_present=present,
        lines_total=st.total_lines[PHOEBE],
        words_total=st.total_words[PHOEBE],
        line_share=round(st.total_lines[PHOEBE] / st.grand_lines, SHARE_DECIMALS),
        line_share_baseline=round(EQUAL_SHARE, SHARE_DECIMALS),
        words_per_line=round(st.total_words[PHOEBE] / st.total_lines[PHOEBE], PERCENT_DECIMALS),
        words_per_line_others=round(others_words / others_lines, PERCENT_DECIMALS),
        top_partner=TITLES[top_partner])


def screentime_rows(a: Analysis) -> list[dict]:
    """``screentime-by-season.csv``: línur, orð og hlutdeild í birtingarröð."""
    st = a.screentime
    rows = []
    for s in st.counts.seasons:
        season_lines = sum(st.lines_by_season[s][c] for c in FRIENDS)
        for c in DISPLAY_ORDER:
            rows.append(dict(season=s, character=TITLES[c],
                             lines=st.lines_by_season[s][c], words=st.words_by_season[s][c],
                             line_share=round(st.lines_by_season[s][c] / season_lines,
                                              SHARE_DECIMALS)))
    return rows


def mentions_rows(a: Analysis) -> list[dict]:
    """``mentions-by-season.csv``: nafntilvik í tali á hvern sýndan þátt."""
    return [dict(season=r["season"], mentions=r["mentions_in_dialogue_total"],
                 episodes=r["episodes"],
                 mentions_per_episode=round(r["mentions_in_dialogue_total"] / r["episodes"],
                                            PERCENT_DECIMALS))
            for r in a.mentions.season_rows]


def speaks_with_rows(a: Analysis) -> list[dict]:
    """``speaks-with-phoebe.csv``: vinirnir fimm og efstu gestirnir saman."""
    rows = [dict(character=TITLES[r["character"]],
                 lines_to_phoebe=r["replies_to_phoebe"],
                 lines_from_phoebe=r["phoebe_replies_to"],
                 scenes_together=r["shared_speaking_scenes"])
            for r in a.talkers]
    rows += [dict(character=g["character"].title(),
                  lines_to_phoebe=g["replies_to_phoebe"],
                  lines_from_phoebe=g["phoebe_replies_to"],
                  scenes_together=g["shared_speaking_scenes"])
             for g in a.guests[:MAX_GUESTS_IN_CONTRACT]]
    rows.sort(key=lambda r: -(r["lines_to_phoebe"] + r["lines_from_phoebe"]))
    return rows


def matrix_rows(a: Analysis) -> list[dict]:
    """``interaction-matrix.csv``: öll 30 pör vinanna, báðar áttir."""
    return [dict(speaker=TITLES[sp], addressee=TITLES[ad], lines=a.pairs[(sp, ad)])
            for sp in DISPLAY_ORDER for ad in DISPLAY_ORDER if sp != ad]


def metadata(a: Analysis) -> dict:
    """``_meta.json``: hvaða skrár, hvaða reglur og hversu vel þáttunin tókst."""
    counts = a.screentime.counts
    kinds = a.kind_counts
    return dict(
        generator=GENERATOR,
        source_dataset=("data/external/delvinso-friends/season (HTML-handrit, "
                        "fangj.github.io/friends afleiða)"),
        source_note=("delvinso-utgafan er notuð thvi thar er buið að laga "
                     "brotna HTML-byggingu i 0911 og 0915."),
        transcript_files_used=len(a.episodes),
        transcript_files_excluded=sorted(EXCLUDED_FILES),
        aired_episodes_covered=sum(counts.aired.values()),
        episodes_per_season={str(s): counts.aired[s] for s in counts.seasons},
        parse_quality=dict(
            total_text_blocks=a.total_blocks,
            speaker_lines=kinds[PERSON],
            scene_headings=kinds[SCENE],
            stage_directions=kinds[ACTION],
            unclassified=kinds[OTHER],
            unclassified_pct=a.unclassified_pct),
        friends_line_totals={c: a.screentime.total_lines[c] for c in FRIENDS},
        friends_word_totals={c: a.screentime.total_words[c] for c in FRIENDS},
        conventions=dict(
            group_lines_excluded=True,
            group_lines_note=("Linur eins og 'All:' eða 'Monica and Phoebe:' eru ekki "
                              "eignaðar einstaklingum."),
            phoebe_sr_and_ursula_excluded=True,
            word_definition="Orð = regex [a-z][a-z'-]* eftir að svigainnskot voru fjarlaegð.",
            double_episode_files=sorted(DOUBLE_EPISODE_FILES)),
        source_commit=SOURCE_COMMIT)
