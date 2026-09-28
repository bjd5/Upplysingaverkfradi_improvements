"""Hleðsla Friends-talnanna í grunninn (issue #10).

Flæðið er einstefna (kafli 0 í CLAUDE.md), en með einni tilfærslu sem
höfundarétturinn ræður (issue #3, valkostur A): aðfangið er ekki hrágögn í
``data/raw/`` heldur **afleiddu tölurnar** í ``data/processed/phoebe-stats/``.
Handritin eru hvorki lesin né geymd; enginn handritstexti fer í grunninn.

Skref hleðslunnar, og hvert þeirra stöðvar keyrsluna við frávik (regla 6):

1. SHA-256 hverrar talnaskrár borin við ``docs/vidmid/provenance.json``
   (``vinnsla.friends_skrar``).
2. Hver færsla sannreynd — gerð, mörk, einkvæmni lykla
   (``vinnsla.friends_faerslur`` og ``vinnsla.friends_phoebe_faerslur``).
3. Samræmi milli skráa sannað (``vinnsla.friends_samraemi``).
4. Allt sett inn í einni færslu og grunnurinn spurður á eftir: fjöldi raða,
   gæðamat þáttunarinnar, línur hvers vinar og ``interaction_lift`` úr
   SQL-sýnunum verða að stemma við skrárnar.

Hleðslan er endurkeyranleg: hún hreinsar Friends-töflurnar og setur allt inn á
ný. Auðkenni eru náttúrulegir lyklar úr gögnunum, aldrei AUTOINCREMENT, svo
sama aðfang gefur sama grunn. Eini keyrslustimpillinn er
``friends_sources.loaded_at`` (sögnin ``loaded`` — sjá #47).

Keyrsla frá rót verkefnisins::

    PYTHONPATH=src/python python3 -m vinnsla.friends_hledsla

Netlaust. Eingöngu staðalsafnið (regla 10). Ekki tengt við ``main.py`` (#39).
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur import fyrirspurnir
from gagnagrunnur.keyrari import keyra
from gagnagrunnur.tenging import tenging

from .friends_handrit import SOURCE_COMMIT
from .friends_samraemi import Gogn, safna
from .friends_skrar import (
    PROVENANCE, STATS_MAPPA, HledsluVilla, Skra, stadfesta_skrar, stutt_slod,
)

log = logging.getLogger(__name__)

TRANSCRIPT_REPOSITORY = "delvinso/friends"
ANALYSIS_REPOSITORY = "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe"
ANALYSIS_COMMIT = "2865ed6"
LEYFI = (
    "fangj/friends: ekkert leyfi (afrit aðdáenda á höfundarréttarvörðum "
    "handritum). delvinso/friends: MIT, nær yfir kóðann en ekki endilega "
    "textann. Aðeins afleiddar tölur geymdar — valkostur A, issue #3."
)
# lift er námundað að 3 aukastöfum í skránni; sýnin námundar eins.
LIFT_VIKMORK = 0.0005

# (tafla, INSERT) í innsetningarröð — foreldrar á undan börnum. Eytt er í
# öfugri röð svo framandi lyklar haldi allan tímann.
INNSETNINGAR: tuple[tuple[str, str], ...] = (
    ("friends_sources",
     "INSERT INTO friends_sources (id, transcript_repository, transcript_commit, "
     "analysis_repository, analysis_commit, analysis_script, analysis_generated_utc, "
     "stats_directory, provenance_file, licence, loaded_at) "
     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"),
    ("friends_source_files",
     "INSERT INTO friends_source_files (file_name, sha256, size_bytes) VALUES (?, ?, ?)"),
    ("friends_parse_blocks",
     "INSERT INTO friends_parse_blocks (block_kind, blocks) VALUES (?, ?)"),
    ("friends_seasons",
     "INSERT INTO friends_seasons (season, aired_episodes) VALUES (?, ?)"),
    ("friends_transcript_files",
     "INSERT INTO friends_transcript_files (episode_code, season, title, aired_episodes) "
     "VALUES (?, ?, ?, ?)"),
    ("friends_excluded_files",
     "INSERT INTO friends_excluded_files (file_name) VALUES (?)"),
    ("friends_characters",
     "INSERT INTO friends_characters (character_name, is_friend) VALUES (?, ?)"),
    ("friends_episode_lines",
     "INSERT INTO friends_episode_lines (episode_code, character_name, lines, words) "
     "VALUES (?, ?, ?, ?)"),
    ("friends_season_characters",
     "INSERT INTO friends_season_characters (season, character_name, characters_typed, "
     "speaking_scenes) VALUES (?, ?, ?, ?)"),
    ("friends_interactions",
     "INSERT INTO friends_interactions (speaker, addressee, lines) VALUES (?, ?, ?)"),
    ("phoebe_exchanges",
     "INSERT INTO phoebe_exchanges (character_name, replies_to_phoebe, "
     "phoebe_replies_to, shared_scenes) VALUES (?, ?, ?, ?)"),
    ("phoebe_friend_interactions",
     "INSERT INTO phoebe_friend_interactions (character_name, two_person_scene_lines, "
     "lines_mentioning_phoebe, lines_naming_phoebe_at_edge) VALUES (?, ?, ?, ?)"),
    ("phoebe_exchanges_by_season",
     "INSERT INTO phoebe_exchanges_by_season (season, character_name, "
     "replies_to_phoebe, phoebe_replies_to) VALUES (?, ?, ?, ?)"),
    ("phoebe_mentions_by_season",
     "INSERT INTO phoebe_mentions_by_season (season, in_dialogue_by_others, "
     "in_own_dialogue, in_stage_directions, formal_phoebe, nickname_pheebs, "
     "top_mentioner, top_mentioner_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"),
    ("phoebe_signature_phrases",
     "INSERT INTO phoebe_signature_phrases (phrase, occurrences, first_season, "
     "last_season) VALUES (?, ?, ?, ?)"),
    ("phoebe_distinctive_words",
     "INSERT INTO phoebe_distinctive_words (word, z_score, phoebe_count, others_count) "
     "VALUES (?, ?, ?, ?)"),
)

# Töfluheiti eru ekki breytur í SQL og því skrifuð út sem fastir strengir —
# engin samsetning (regla 5). Eytt í öfugri innsetningarröð (börn fyrst).
EYDINGAR: tuple[str, ...] = (
    "DELETE FROM phoebe_distinctive_words",
    "DELETE FROM phoebe_signature_phrases",
    "DELETE FROM phoebe_mentions_by_season",
    "DELETE FROM phoebe_exchanges_by_season",
    "DELETE FROM phoebe_friend_interactions",
    "DELETE FROM phoebe_exchanges",
    "DELETE FROM friends_interactions",
    "DELETE FROM friends_season_characters",
    "DELETE FROM friends_episode_lines",
    "DELETE FROM friends_characters",
    "DELETE FROM friends_excluded_files",
    "DELETE FROM friends_transcript_files",
    "DELETE FROM friends_seasons",
    "DELETE FROM friends_parse_blocks",
    "DELETE FROM friends_source_files",
    "DELETE FROM friends_sources",
)
TALNING = (
    "SELECT 'friends_sources', COUNT(*) FROM friends_sources UNION ALL "
    "SELECT 'friends_source_files', COUNT(*) FROM friends_source_files UNION ALL "
    "SELECT 'friends_parse_blocks', COUNT(*) FROM friends_parse_blocks UNION ALL "
    "SELECT 'friends_seasons', COUNT(*) FROM friends_seasons UNION ALL "
    "SELECT 'friends_transcript_files', COUNT(*) FROM friends_transcript_files UNION ALL "
    "SELECT 'friends_excluded_files', COUNT(*) FROM friends_excluded_files UNION ALL "
    "SELECT 'friends_characters', COUNT(*) FROM friends_characters UNION ALL "
    "SELECT 'friends_episode_lines', COUNT(*) FROM friends_episode_lines UNION ALL "
    "SELECT 'friends_season_characters', COUNT(*) FROM friends_season_characters UNION ALL "
    "SELECT 'friends_interactions', COUNT(*) FROM friends_interactions UNION ALL "
    "SELECT 'phoebe_exchanges', COUNT(*) FROM phoebe_exchanges UNION ALL "
    "SELECT 'phoebe_friend_interactions', COUNT(*) FROM phoebe_friend_interactions UNION ALL "
    "SELECT 'phoebe_exchanges_by_season', COUNT(*) FROM phoebe_exchanges_by_season UNION ALL "
    "SELECT 'phoebe_mentions_by_season', COUNT(*) FROM phoebe_mentions_by_season UNION ALL "
    "SELECT 'phoebe_signature_phrases', COUNT(*) FROM phoebe_signature_phrases UNION ALL "
    "SELECT 'phoebe_distinctive_words', COUNT(*) FROM phoebe_distinctive_words"
)

# Staðfestingin spyr sömu fyrirspurna og síðan birtir (src/sql/queries/, #11),
# svo hleðslan staðfestir nákvæmlega þær tölur sem fara á síðuna.
GAEDAMAT = "friends-thattunargaedi"
VINALINUR = "friends-plass-alls"
LIFT = "friends-interaction-lift"
GAEDADALKAR = ("total_blocks", "speaker_lines", "scene_headings", "stage_directions",
               "unclassified", "unclassified_pct")


def _nuna() -> str:
    """Tímastimpill í ISO 8601, UTC, á sekúndunákvæmni (klukka keyrslunnar)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _radir(gogn: Gogn, skrar: list[Skra], mappa: Path, provenance: Path) -> dict[str, list]:
    """Raðirnar sem fara í hverja töflu, eftir töfluheiti."""
    uppruni = (
        1, TRANSCRIPT_REPOSITORY, SOURCE_COMMIT, ANALYSIS_REPOSITORY, ANALYSIS_COMMIT,
        str(gogn.meta["generator"]), str(gogn.meta["generated_utc"]),
        stutt_slod(mappa), stutt_slod(provenance), LEYFI, _nuna(),
    )
    return {
        "friends_sources": [uppruni],
        "friends_source_files": [(s.heiti, s.sha256, s.staerd) for s in skrar],
        "friends_parse_blocks": gogn.blokkir,
        "friends_seasons": gogn.thattarodir,
        "friends_transcript_files": gogn.handritsskrar,
        "friends_excluded_files": gogn.undanskildar,
        "friends_characters": gogn.personur,
        "friends_episode_lines": gogn.linur,
        "friends_season_characters": gogn.thattarodarpersonur,
        "friends_interactions": gogn.samskipti,
        "phoebe_exchanges": gogn.skipti,
        "phoebe_friend_interactions": gogn.vinaskipti,
        "phoebe_exchanges_by_season": gogn.skipti_eftir_rod,
        "phoebe_mentions_by_season": gogn.nafntilvik,
        "phoebe_signature_phrases": gogn.ordtok,
        "phoebe_distinctive_words": gogn.ord,
    }


def _setja_inn(samband: Connection, radir: dict[str, list]) -> dict[str, int]:
    """Hreinsar töflurnar og setur raðirnar inn; skilar fjölda í hverri töflu."""
    for eyding in EYDINGAR:
        samband.execute(eyding)
    for tafla, innsetning in INNSETNINGAR:
        try:
            samband.executemany(innsetning, radir[tafla])
        except sqlite3.IntegrityError as villa:
            raise HledsluVilla(f"{tafla}: grunnurinn hafnaði færslu — {villa}") from villa
    fjoldi = dict(samband.execute(TALNING).fetchall())
    for tafla, _ in INNSETNINGAR:
        if fjoldi.get(tafla) != len(radir[tafla]):
            raise HledsluVilla(
                f"{tafla}: {len(radir[tafla])} raðir sendar en {fjoldi.get(tafla)} í töflunni."
            )
    return fjoldi


def _stadfesta_ur_sql(samband: Connection, gogn: Gogn) -> None:
    """Spyr sýnirnar og ber svörin við skrárnar — SQL verður að segja það sama."""
    gaedi = gogn.meta["parse_quality"]
    vaent = (gaedi["total_text_blocks"], gaedi["speaker_lines"], gaedi["scene_headings"],
             gaedi["stage_directions"], gaedi["unclassified"], gaedi["unclassified_pct"])
    gaedarod = fyrirspurnir.keyra(samband, GAEDAMAT)[0]
    fengid = tuple(gaedarod[dalkur] for dalkur in GAEDADALKAR)
    if fengid != vaent:
        raise HledsluVilla(f"friends_parse_quality gaf {fengid}, _meta.json segir {vaent}.")

    for vinur in fyrirspurnir.keyra(samband, VINALINUR):
        nafn, linur, ord_ = vinur["character_name"], vinur["lines"], vinur["words"]
        vaent_vinur = (gogn.meta["friends_line_totals"][nafn.lower()],
                       gogn.meta["friends_word_totals"][nafn.lower()])
        if (linur, ord_) != vaent_vinur:
            raise HledsluVilla(f"{nafn}: SQL gaf {(linur, ord_)}, _meta.json {vaent_vinur}.")

    lift = {rad["character_name"]: rad["interaction_lift"]
            for rad in fyrirspurnir.keyra(samband, LIFT)}
    if set(lift) != set(gogn.lift_ur_skra):
        raise HledsluVilla(f"phoebe_interaction_lift nær yfir {sorted(lift)}.")
    for nafn, gildi in gogn.lift_ur_skra.items():
        if abs(lift[nafn] - gildi) > LIFT_VIKMORK:
            raise HledsluVilla(f"interaction_lift {nafn}: SQL {lift[nafn]}, skráin {gildi}.")


def hlada(
    samband: Connection, mappa: Path = STATS_MAPPA, provenance: Path = PROVENANCE
) -> dict[str, int]:
    """Hleður Friends-tölunum og skilar fjölda raða í hverri töflu.

    Fallið stýrir ekki færslunni sjálft: kallandinn opnar grunninn með
    ``gagnagrunnur.tenging.tenging``, sem sér um commit eða rollback, svo
    grunnurinn situr aldrei með hálfa hleðslu. Allar fyrirspurnir eru með
    breytum eða fastir strengir (regla 5).
    """
    skrar = stadfesta_skrar(mappa, provenance)
    gogn = safna(mappa)
    fjoldi = _setja_inn(samband, _radir(gogn, skrar, mappa, provenance))
    _stadfesta_ur_sql(samband, gogn)
    return fjoldi


def main(rok: list[str] | None = None) -> int:
    """Keyrir migrations og hleður Friends-tölunum í grunninn."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    if rok:
        raise SystemExit(f"Þessi eining tekur enga viðbótarröksemd, fékk: {rok}")

    with tenging() as samband:
        keyra(samband)
        fjoldi = hlada(samband)
        gaedi = fyrirspurnir.keyra(samband, GAEDAMAT)[0]

    log.info(
        "Hlóð Friends-tölunum: %d handritsskrár, %d línuraðir, %d tilsvör af %d "
        "blokkum, %s%% óflokkað.",
        fjoldi["friends_transcript_files"], fjoldi["friends_episode_lines"],
        gaedi["speaker_lines"], gaedi["total_blocks"], gaedi["unclassified_pct"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
