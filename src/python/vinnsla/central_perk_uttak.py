"""Úttak Central Perk-greiningarinnar í ``data/processed/`` (issue #14, P2.6).

Skref 5 í ``src/phoebe_central_perk.py`` (commit ``2865ed6``) — *taka saman*
og *skrifa* — og inngangur skriftunnar (``main``, ``--audit``).

Skrár í ``data/processed/phoebe-central-perk/``:

* ``phoebe-central-perk-summary.json`` — bæti fyrir bæti sama og viðmiðið
  ``docs/vidmid/generated/phoebe-central-perk-summary.json`` (engir
  tímastimplar voru í henni og engir bætast við, sbr. #47);
* ``phoebe-central-perk-episodes.csv`` — hópur, orð og hlutdeild Phoebe í
  hverju handriti (tölurnar sem SVG-punktaritið bar);
* ``phoebe-central-perk-regex.json`` — segðirnar orðréttar úr kóðanum með
  skýringum (efnið sem Markdown-skráin bar);
* ``_meta.json`` — hvaðan tölurnar koma (safn, commit, afmörkun).

**Það sem fellur niður (regla 2):** ``-summary.md``, ``-regex.md`` og ``.svg``.
Texti, töflur og myndrit verða til í ``web/`` og ``utflutningur/``. Þessi
eining skrifar **aðeins** í ``data/processed/`` og neitar ``web/gogn/``.

**Höfundaréttur (issue #3):** úttakið eru tölur og auðkenni skráa, aldrei
handritstexti. Yfirferðarlistinn (``--audit``) inniheldur texta og fer því
eingöngu á skjá.

Keyrsla án nets (tengingin við ``main.py`` er issue #39)::

    FRIENDS_HANDRIT_MAPPA=/slóð/á/season \\
        PYTHONPATH=src/python python3 -m vinnsla.central_perk_uttak [--audit]

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import logging
import math
import statistics
import sys
from pathlib import Path
from typing import Sequence

from .central_perk_greining import EpisodeResult, analyse, audit_lines
from .central_perk_mynstur import (
    CENTRAL_PERK_GROUP, DOCUMENTED_PATTERNS, GROUP_ORDER, MAIN_CAST, PHOEBE_SINGS,
)
from .friends_handrit import (
    EXCLUDED_FILES, ROT, SOURCE_COMMIT, SOURCE_REPOSITORY, TranscriptError, transcript_paths,
)
from .phoebe_uttak import write_csv, write_json
from .varnagli import krefjast_utan_vefs

log = logging.getLogger(__name__)

OUTPUT_DIR = ROT / "data" / "processed" / "phoebe-central-perk"
GENERATOR = "src/python/vinnsla/central_perk_uttak.py"
SUMMARY_FILE = "phoebe-central-perk-summary.json"
EPISODES_FILE = "phoebe-central-perk-episodes.csv"
PATTERNS_FILE = "phoebe-central-perk-regex.json"
META_FILE = "_meta.json"
OUTPUT_FILES = (SUMMARY_FILE, EPISODES_FILE, PATTERNS_FILE, META_FILE)


# --- Samantekt í töflur ---------------------------------------------------------
#
# ``summarise`` er óbreytt úr gömlu skriftunni svo ``summary.json`` stemmi bæti
# fyrir bæti við viðmiðið. Í stað Markdown-töflunnar og SVG-punktaritsins sem
# féllu niður (regla 2) koma ``episode_rows`` — hópur og hlutdeild Phoebe í
# hverju handriti — og ``pattern_rows``, segðirnar sem Markdown-skráin sýndi.

PERCENTAGE_POINTS = 100

EPISODE_FIELDS = [
    "episode_id", "group", "has_central_perk", "singing_scenes",
    *(f"words_{name.lower()}" for name in MAIN_CAST),
    "main_cast_words", "phoebe_share",
]


def _median(values: list[float], what: str) -> float:
    """Miðgildi; tóm röð er villa með skýringu, ekki ``StatisticsError`` úr djúpinu."""
    if not values:
        raise ValueError(f"Ekkert gildi fyrir {what} — miðgildi er óskilgreint.")
    return statistics.median(values)


def group_summary(results: Sequence[EpisodeResult], group: str) -> dict[str, float | int]:
    """Fjöldi, miðgildi og meðaltal hlutdeildar Phoebe og miðgildi hlutfallsins í einum hópi.

    Hlutfallið „hinir fimm á móti Phoebe“ er aðeins reiknað fyrir handrit
    þar sem hún segir eitthvað (endanlegt gildi).
    """
    rows = [row for row in results if row.group == group]
    shares = [row.phoebe_share for row in rows]
    ratios = [row.friends_to_phoebe_ratio for row in rows
              if math.isfinite(row.friends_to_phoebe_ratio)]
    return {
        "n": len(rows),
        "median_phoebe_share": _median(shares, f"hlutdeild Phoebe í hópnum {group}"),
        "mean_phoebe_share": statistics.mean(shares),
        "median_friends_to_phoebe_ratio": _median(ratios, f"hlutfallið í hópnum {group}"),
    }


def summarise(results: Sequence[EpisodeResult]) -> dict[str, object]:
    """Miðgildi og meðaltal hlutdeildar Phoebe í hverjum hópi (``summary.json``).

    Miðgildi er aðalmælikvarðinn: tvöföld og óvenju löng handrit hefðu annars
    of mikil áhrif. Lyklar og röð eru óbreytt úr gömlu skriftunni.
    """
    groups = {group: group_summary(results, group) for group in GROUP_ORDER}
    singing_rows = [row for row in results if row.group == PHOEBE_SINGS]
    song_share = groups[PHOEBE_SINGS]["median_phoebe_share"]
    cp_share = groups[CENTRAL_PERK_GROUP]["median_phoebe_share"]
    return {
        "transcript_files": len(results),
        "singing_files": len(singing_rows),
        "singing_scenes": sum(row.singing_scenes for row in singing_rows),
        "singing_episode_ids": [row.episode_id for row in singing_rows],
        "groups": groups,
        # Munurinn á miðgildum söng- og Central Perk-hópsins, í prósentustigum.
        "median_difference_percentage_points":
            PERCENTAGE_POINTS * (float(song_share) - float(cp_share)),
    }


def episode_rows(results: Sequence[EpisodeResult]) -> list[dict[str, object]]:
    """Ein röð á handritaskrá — tölurnar sem punktaritið gamla sýndi, og orðin að baki."""
    rows = []
    for result in results:
        row: dict[str, object] = {
            "episode_id": result.episode_id,
            "group": result.group,
            "has_central_perk": int(result.has_central_perk),
            "singing_scenes": result.singing_scenes,
        }
        row.update({f"words_{name.lower()}": result.words[name] for name in MAIN_CAST})
        row["main_cast_words"] = result.main_cast_words
        row["phoebe_share"] = result.phoebe_share
        rows.append(row)
    return rows


def pattern_rows() -> list[dict[str, str]]:
    """Segðirnar orðréttar úr kóðanum, með skýringum — svo síðan sýni það sem keyrði."""
    return [
        {"name": name, "pattern": pattern.pattern, "catches": catches, "misses": misses}
        for name, pattern, catches, misses in DOCUMENTED_PATTERNS
    ]


# --- Skrifað ----------------------------------------------------------------------

def metadata(results: Sequence[EpisodeResult]) -> dict[str, object]:
    """``_meta.json``: uppruni talnanna — án vegguklukkustimpils (#47)."""
    return {
        "generator": GENERATOR,
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "transcript_files_used": len(results),
        "transcript_files_excluded": sorted(EXCLUDED_FILES),
        "files": list(OUTPUT_FILES),
    }


def write_outputs(results: Sequence[EpisodeResult],
                  directory: Path | str | None = None) -> list[Path]:
    """Skrifar skrárnar fjórar í ``directory`` (sjálfgefið ``OUTPUT_DIR``)."""
    folder = Path(directory) if directory is not None else OUTPUT_DIR
    krefjast_utan_vefs(folder)
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / SUMMARY_FILE, summarise(results))
    write_csv(folder / EPISODES_FILE, EPISODE_FIELDS, episode_rows(results))
    write_json(folder / PATTERNS_FILE, {"patterns": pattern_rows()})
    write_json(folder / META_FILE, metadata(results))
    return [folder / name for name in OUTPUT_FILES]


def run(transcripts: Path | str | None = None, directory: Path | str | None = None) -> list[Path]:
    """Keyrir alla Central Perk-vinnsluna: lesa, þátta, merkja söng, telja, skrifa."""
    results = analyse(transcripts)
    written = write_outputs(results, directory)
    log.info("Greindi %d handritaskrár; skrifaði %d skrár.", len(results), len(written))
    return written


def audit(transcripts: Path | str | None = None) -> None:
    """Prentar Central Perk-blokkir sem nefna tónlist, handrit fyrir handrit (á skjá)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for path in transcript_paths(transcripts):
        for line in audit_lines(path):
            print(line)


def main(argv: list[str] | None = None) -> int:
    """Handvirk keyrsla: ``python3 -m vinnsla.central_perk_uttak [--handrit M] [--uttak M]``."""
    parser = argparse.ArgumentParser(description="Phoebe syngur í Central Perk.")
    parser.add_argument("--handrit", help="mappan season/ (annars FRIENDS_HANDRIT_MAPPA)")
    parser.add_argument("--uttak", help=f"úttaksmappa (sjálfgefið {OUTPUT_DIR.relative_to(ROT)})")
    parser.add_argument("--audit", action="store_true",
                        help="prenta söngtilvik til yfirferðar í stað þess að skrifa")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    try:
        if args.audit:
            audit(args.handrit)
            return 0
        written = run(args.handrit, args.uttak)
    except TranscriptError as error:
        log.error("%s", error)
        return 1
    for path in written:
        print(f"skrifaði: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
