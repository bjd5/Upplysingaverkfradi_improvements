"""Úttak Phoebe-greiningarinnar í ``data/processed/phoebe-stats/`` (issue #14, P2.5).

Síðasta skrefið í upprunaskriftunni ``src/phoebe_analysis.py`` (commit
``2865ed6``) — *skrifa*. Sömu 17 skrár og gamla skriftan skrifaði, með sömu
heitum, dálkum og bætum (sjá ``phoebe_samningur`` um tvö viljandi frávik).

**Það sem fellur niður:** speglunin í ``site/friends/phoebe-stats/`` (Quarto)
og prentaða yfirlitið. Engin tala fer héðan beint í birtingu: flæðið er
handrit → vinnsla → SQL-grunnur → ``web/gogn/`` (kafli 0), og HTML verður til
í ``web/`` (regla 2). Þessi eining skrifar **aðeins** í ``data/processed/`` og
neitar að skrifa í ``web/gogn/``.

**Höfundaréttur (issue #3):** úttakið eru tölur um textann — talningar,
hlutföll og tíðnitöflur — aldrei handritstexti.

Keyrsla án nets, með eigin inngangi (tengingin við ``main.py`` er issue #39)::

    FRIENDS_HANDRIT_MAPPA=/slóð/á/season \\
        PYTHONPATH=src/python python3 -m vinnsla.phoebe_uttak

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # keyrt sem eining innan pakkans
    from .friends_handrit import ROT, TranscriptError
    from .phoebe_greining import Analysis, analyse
    from .phoebe_ordafordi import DISTINCTIVE_FIELDS
    from .phoebe_samningur import (
        MATRIX_FIELDS, MENTIONS_FIELDS, PHRASE_FIELDS, SCREENTIME_FIELDS, SPEAKS_WITH_FIELDS,
        matrix_rows, mentions_rows, metadata, screentime_rows, speaks_with_rows, summary,
    )
    from .phoebe_skyrslur import (
        extra_stats_report, mentions_report, screentime_report, top_talkers_report,
    )
except ImportError:  # keyrt beint úr möppunni
    from friends_handrit import ROT, TranscriptError
    from phoebe_greining import Analysis, analyse
    from phoebe_ordafordi import DISTINCTIVE_FIELDS
    from phoebe_samningur import (
        MATRIX_FIELDS, MENTIONS_FIELDS, PHRASE_FIELDS, SCREENTIME_FIELDS, SPEAKS_WITH_FIELDS,
        matrix_rows, mentions_rows, metadata, screentime_rows, speaks_with_rows, summary,
    )
    from phoebe_skyrslur import (
        extra_stats_report, mentions_report, screentime_report, top_talkers_report,
    )

log = logging.getLogger(__name__)

OUTPUT_DIR = ROT / "data" / "processed" / "phoebe-stats"
WEB_DATA_DIR = ROT / "web" / "gogn"
JSON_INDENT = 2
# csv-einingin skrifar \r\n sjálfgefið og frosna viðmiðið ber þau bæti.
CSV_LINE_TERMINATOR = "\r\n"


@dataclass(frozen=True)
class JsonFile:
    """JSON-skrá sem á að skrifa."""

    name: str
    payload: dict


@dataclass(frozen=True)
class CsvFile:
    """CSV-skrá sem á að skrifa, með fastri dálkaröð."""

    name: str
    fields: list[str]
    rows: list[dict]


def _fields_of(rows: list[dict]) -> list[str]:
    """Dálkar töflu = lyklar fyrstu raðar; tóm tafla er villa, ekki tóm skrá."""
    if not rows:
        raise ValueError("Tafla án raða — dálkarnir eru óskilgreindir.")
    return list(rows[0])


def output_files(a: Analysis) -> list[JsonFile | CsvFile]:
    """Allar 17 skrárnar í sömu röð og gamla skriftan skrifaði þær."""
    st = a.screentime
    return [
        JsonFile("phoebe-top-talkers.json", top_talkers_report(a)),
        CsvFile("phoebe-top-talkers.csv", _fields_of(a.talkers), a.talkers),
        CsvFile("phoebe-top-talkers-by-season.csv", _fields_of(a.season_talkers), a.season_talkers),
        JsonFile("phoebe-mentions-by-season.json", mentions_report(a)),
        CsvFile("phoebe-mentions-by-season.csv", _fields_of(a.mentions.season_rows),
                a.mentions.season_rows),
        JsonFile("phoebe-screentime-by-season.json", screentime_report(a)),
        CsvFile("phoebe-screentime-by-season.csv", _fields_of(st.season_rows), st.season_rows),
        CsvFile("phoebe-per-episode.csv", _fields_of(st.episode_rows), st.episode_rows),
        JsonFile("phoebe-extra-stats.json", extra_stats_report(a)),
        CsvFile("phoebe-distinctive-words.csv", DISTINCTIVE_FIELDS, a.distinctive),
        JsonFile("summary.json", summary(a)),
        CsvFile("screentime-by-season.csv", SCREENTIME_FIELDS, screentime_rows(a)),
        CsvFile("mentions-by-season.csv", MENTIONS_FIELDS, mentions_rows(a)),
        CsvFile("speaks-with-phoebe.csv", SPEAKS_WITH_FIELDS, speaks_with_rows(a)),
        CsvFile("interaction-matrix.csv", MATRIX_FIELDS, matrix_rows(a)),
        CsvFile("signature-phrases.csv", PHRASE_FIELDS, a.phrase_rows),
        JsonFile("_meta.json", metadata(a)),
    ]


def write_json(path: Path, payload: dict) -> None:
    """Skrifar JSON með íslenskum stöfum óbreyttum og línuskilum í lokin."""
    text = json.dumps(payload, ensure_ascii=False, indent=JSON_INDENT)
    path.write_text(text + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Skrifar CSV með fastri dálkaröð; aukalykill í röð er villa, ekki þögn."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator=CSV_LINE_TERMINATOR)
        writer.writeheader()
        writer.writerows(rows)


def ensure_outside_web(directory: Path) -> None:
    """Stöðvar skrif inn í ``web/gogn/`` — vinnslan skrifar aldrei í birtingarlagið."""
    resolved = directory.resolve()
    if resolved == WEB_DATA_DIR or WEB_DATA_DIR in resolved.parents:
        raise ValueError(
            f"Vinnslan skrifar ekki í {WEB_DATA_DIR}. Þangað fer aðeins JSON frá "
            "útflutningslaginu eftir að grunnurinn hefur verið byggður (kafli 0)."
        )


def write_outputs(a: Analysis, directory: Path | str | None = None) -> list[Path]:
    """Skrifar allar skrárnar í ``directory`` (sjálfgefið ``data/processed/phoebe-stats``)."""
    folder = Path(directory) if directory is not None else OUTPUT_DIR
    ensure_outside_web(folder)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for item in output_files(a):
        path = folder / item.name
        if isinstance(item, JsonFile):
            write_json(path, item.payload)
        else:
            write_csv(path, item.fields, item.rows)
        written.append(path)
    return written


def run(transcripts: Path | str | None = None, directory: Path | str | None = None) -> list[Path]:
    """Keyrir alla Phoebe-vinnsluna: lesa, þátta, telja, skrifa."""
    a = analyse(transcripts)
    written = write_outputs(a, directory)
    log.info("Greindi %d handritsskrár (%d textablokkir, %.2f%% óflokkað); skrifaði %d skrár.",
             len(a.episodes), a.total_blocks, a.unclassified_pct, len(written))
    return written


def main(argv: list[str] | None = None) -> int:
    """Handvirk keyrsla: ``python3 -m vinnsla.phoebe_uttak [--handrit M] [--uttak M]``."""
    parser = argparse.ArgumentParser(description="Phoebe-tölfræði úr Friends-handritunum.")
    parser.add_argument("--handrit", help="mappan season/ (annars FRIENDS_HANDRIT_MAPPA)")
    parser.add_argument("--uttak", help=f"úttaksmappa (sjálfgefið {OUTPUT_DIR.relative_to(ROT)})")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    try:
        written = run(args.handrit, args.uttak)
    except TranscriptError as error:
        log.error("%s", error)
        return 1
    for path in written:
        print(f"skrifaði: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
