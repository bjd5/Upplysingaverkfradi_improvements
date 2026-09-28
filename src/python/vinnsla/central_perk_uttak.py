"""Úttak Central Perk-greiningarinnar í ``data/processed/`` (issue #14, P2.6).

Skref 5b í ``src/phoebe_central_perk.py`` (commit ``2865ed6``) — *skrifa* — og
inngangur skriftunnar (``main``, ``--audit``).

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
import sys
from pathlib import Path
from typing import Sequence

try:  # keyrt sem eining innan pakkans
    from .central_perk_greining import EpisodeResult, analyse
    from .central_perk_samantekt import EPISODE_FIELDS, episode_rows, pattern_rows, summarise
    from .central_perk_songur import audit_lines
    from .friends_handrit import (
        EXCLUDED_FILES, ROT, SOURCE_COMMIT, SOURCE_REPOSITORY, TranscriptError, transcript_paths,
    )
    from .phoebe_uttak import ensure_outside_web, write_csv, write_json
except ImportError:  # keyrt beint úr möppunni
    from central_perk_greining import EpisodeResult, analyse
    from central_perk_samantekt import EPISODE_FIELDS, episode_rows, pattern_rows, summarise
    from central_perk_songur import audit_lines
    from friends_handrit import (
        EXCLUDED_FILES, ROT, SOURCE_COMMIT, SOURCE_REPOSITORY, TranscriptError, transcript_paths,
    )
    from phoebe_uttak import ensure_outside_web, write_csv, write_json

log = logging.getLogger(__name__)

OUTPUT_DIR = ROT / "data" / "processed" / "phoebe-central-perk"
GENERATOR = "src/python/vinnsla/central_perk_uttak.py"
SUMMARY_FILE = "phoebe-central-perk-summary.json"
EPISODES_FILE = "phoebe-central-perk-episodes.csv"
PATTERNS_FILE = "phoebe-central-perk-regex.json"
META_FILE = "_meta.json"
OUTPUT_FILES = (SUMMARY_FILE, EPISODES_FILE, PATTERNS_FILE, META_FILE)


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
    ensure_outside_web(folder)
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
