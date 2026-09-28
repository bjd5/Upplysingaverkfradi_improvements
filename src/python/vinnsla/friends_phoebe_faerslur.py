"""Sannreyning færslna í talnaskránum um Phoebe (issue #10).

Ræðuskipti (TENGSL), nafntilvik (NÆRVERA) og orðaforði. Sömu reglur og í
``vinnsla.friends_faerslur``, þaðan sem hjálparföllin koma: hver reitur er
lesinn sem sín gerð og innan sinna marka, tvítekinn lykill stöðvar, og ekkert
er leiðrétt hljóðlega (regla 6).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from pathlib import Path

from .friends_faerslur import einkvaemt, heiltala, rauntala, rod, texti, vinur
from .friends_skrar import HledsluVilla, lesa_csv

MATRIX = "interaction-matrix.csv"
MATRIX_DALKAR = ("speaker", "addressee", "lines")
SPEAKS_WITH = "speaks-with-phoebe.csv"
SPEAKS_WITH_DALKAR = ("character", "lines_to_phoebe", "lines_from_phoebe", "scenes_together")
TOP_TALKERS = "phoebe-top-talkers.csv"
TOP_TALKERS_DALKAR = (
    "character", "adjacent_turns", "replies_to_phoebe", "phoebe_replies_to",
    "two_person_scene_lines", "shared_speaking_scenes", "lines_mentioning_phoebe",
    "lines_naming_phoebe_at_edge", "adjacency_share_pct", "expected_share_pct",
    "interaction_lift", "total_lines_in_show", "rank",
)
TALKERS_BY_SEASON = "phoebe-top-talkers-by-season.csv"
TALKERS_BY_SEASON_DALKAR = (
    "season", "character", "adjacent_turns", "replies_to_phoebe", "phoebe_replies_to",
    "share_of_phoebe_interactions_pct",
)
MENTIONS = "phoebe-mentions-by-season.csv"
MENTIONS_DALKAR = (
    "season", "episodes", "transcript_files", "mentions_in_dialogue_by_others",
    "mentions_in_own_dialogue", "mentions_in_dialogue_total",
    "mentions_in_stage_directions", "mentions_total", "mentions_formal_phoebe",
    "mentions_nickname_pheebs", "dialogue_mentions_per_episode",
    "change_vs_prev_season_pct", "top_mentioner", "top_mentioner_count",
)
PHRASES = "signature-phrases.csv"
PHRASES_DALKAR = ("phrase", "count", "first_season", "last_season")
WORDS = "phoebe-distinctive-words.csv"
WORDS_DALKAR = (
    "word", "z_score", "phoebe_count", "others_count", "phoebe_per_10k", "others_per_10k",
)

def samskipti(mappa: Path) -> list[tuple[str, str, int]]:
    """Raðir í friends_interactions."""
    radir = []
    for numer, rad in enumerate(lesa_csv(mappa, MATRIX, MATRIX_DALKAR), start=2):
        stadur = f"{MATRIX} lína {numer}"
        radir.append((vinur(rad["speaker"], stadur), vinur(rad["addressee"], stadur),
                      heiltala(rad["lines"], f"{stadur} lines")))
    einkvaemt(((r[0], r[1]) for r in radir), MATRIX)
    return radir


def skipti(mappa: Path) -> list[tuple[str, int, int, int]]:
    """Raðir í phoebe_exchanges: allar persónur sem tala við Phoebe."""
    radir = []
    for numer, rad in enumerate(lesa_csv(mappa, SPEAKS_WITH, SPEAKS_WITH_DALKAR), start=2):
        stadur = f"{SPEAKS_WITH} lína {numer}"
        radir.append((
            texti(rad["character"], f"{stadur} character"),
            heiltala(rad["lines_to_phoebe"], f"{stadur} lines_to_phoebe"),
            heiltala(rad["lines_from_phoebe"], f"{stadur} lines_from_phoebe"),
            heiltala(rad["scenes_together"], f"{stadur} scenes_together"),
        ))
    einkvaemt((r[0] for r in radir), SPEAKS_WITH)
    return radir


def vinaskipti(mappa: Path) -> list[dict[str, str]]:
    """``phoebe-top-talkers.csv`` sannreynt; raðirnar sjálfar fyrir samræmisprófin."""
    radir = lesa_csv(mappa, TOP_TALKERS, TOP_TALKERS_DALKAR)
    for numer, rad in enumerate(radir, start=2):
        stadur = f"{TOP_TALKERS} lína {numer}"
        rad["character"] = vinur(rad["character"], stadur)
        for dalkur in TOP_TALKERS_DALKAR[1:]:
            if dalkur.endswith(("_pct", "_lift")):
                rauntala(rad[dalkur], f"{stadur} {dalkur}")
            else:
                heiltala(rad[dalkur], f"{stadur} {dalkur}")
    einkvaemt((r["character"] for r in radir), TOP_TALKERS)
    return radir


def skipti_eftir_rod(mappa: Path) -> list[tuple]:
    """Raðir í phoebe_exchanges_by_season."""
    radir = []
    for numer, rad in enumerate(
        lesa_csv(mappa, TALKERS_BY_SEASON, TALKERS_BY_SEASON_DALKAR), start=2
    ):
        stadur = f"{TALKERS_BY_SEASON} lína {numer}"
        svor = heiltala(rad["replies_to_phoebe"], f"{stadur} replies_to_phoebe")
        hennar = heiltala(rad["phoebe_replies_to"], f"{stadur} phoebe_replies_to")
        if heiltala(rad["adjacent_turns"], f"{stadur} adjacent_turns") != svor + hennar:
            raise HledsluVilla(f"{stadur}: adjacent_turns er ekki summa svaranna tveggja.")
        radir.append((rod(rad["season"], f"{stadur} season"),
                      vinur(rad["character"], stadur), svor, hennar))
    einkvaemt(((r[0], r[1]) for r in radir), TALKERS_BY_SEASON)
    return radir


def nafntilvik(mappa: Path) -> list[dict[str, str]]:
    """``phoebe-mentions-by-season.csv`` sannreynt, allir talnareitir sem int."""
    radir = lesa_csv(mappa, MENTIONS, MENTIONS_DALKAR)
    for numer, rad in enumerate(radir, start=2):
        stadur = f"{MENTIONS} lína {numer}"
        for dalkur in MENTIONS_DALKAR:
            if dalkur == "season":
                rad[dalkur] = rod(rad[dalkur], f"{stadur} season")
            elif dalkur == "top_mentioner":
                rad[dalkur] = vinur(rad[dalkur], stadur)
            elif dalkur == "change_vs_prev_season_pct" and numer == 2:
                if rad[dalkur] != "":  # fyrsta þáttaröð á sér enga fyrri
                    raise HledsluVilla(f"{stadur}: breyting frá fyrri þáttaröð á að vera auð.")
            elif dalkur.endswith(("_pct", "_per_episode")):
                rauntala(rad[dalkur], f"{stadur} {dalkur}")
            else:
                rad[dalkur] = heiltala(rad[dalkur], f"{stadur} {dalkur}")
    einkvaemt((r["season"] for r in radir), MENTIONS)
    return radir


def ordtok(mappa: Path) -> list[tuple[str, int, int, int]]:
    """Raðir í phoebe_signature_phrases."""
    radir = []
    for numer, rad in enumerate(lesa_csv(mappa, PHRASES, PHRASES_DALKAR), start=2):
        stadur = f"{PHRASES} lína {numer}"
        radir.append((texti(rad["phrase"], f"{stadur} phrase"),
                      heiltala(rad["count"], f"{stadur} count"),
                      rod(rad["first_season"], f"{stadur} first_season"),
                      rod(rad["last_season"], f"{stadur} last_season")))
    einkvaemt((r[0] for r in radir), PHRASES)
    return radir


def ord_phoebe(mappa: Path) -> list[tuple[str, float, int, int]]:
    """Raðir í phoebe_distinctive_words."""
    radir = []
    for numer, rad in enumerate(lesa_csv(mappa, WORDS, WORDS_DALKAR), start=2):
        stadur = f"{WORDS} lína {numer}"
        rauntala(rad["phoebe_per_10k"], f"{stadur} phoebe_per_10k")
        rauntala(rad["others_per_10k"], f"{stadur} others_per_10k")
        radir.append((texti(rad["word"], f"{stadur} word"),
                      rauntala(rad["z_score"], f"{stadur} z_score"),
                      heiltala(rad["phoebe_count"], f"{stadur} phoebe_count", 1),
                      heiltala(rad["others_count"], f"{stadur} others_count")))
    einkvaemt((r[0] for r in radir), WORDS)
    return radir
