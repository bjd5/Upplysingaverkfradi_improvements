"""Friends-handritin sem skrár: hvar þau eru, hver eru greind og hvað þau heita.

Sameiginlegt skráalag fyrir báðar Friends-greiningarnar (issue #14):
``phoebe_*`` (P2.5) og Central Perk-greininguna (P2.6). Hér er ekkert þáttað
— aðeins ákveðið *hvaða* skrár eru lesnar, hvaða þáttaröð og hve marga sýnda
þætti hver þeirra geymir, og hvernig bætin verða að texta.

**Höfundaréttur (issue #3, valkostur A).** Handritin fara aldrei í þetta repo.
Sjálfgefna mappan er undir ``data/raw/`` sem ``.gitignore`` útilokar; henni má
líka vísa annað með umhverfisbreytunni ``FRIENDS_HANDRIT_MAPPA``. Viðmiðið var
reiknað úr ``season/`` í ``delvinso/friends-tv-show-analysis`` á commit
``a4641fed3d95bb9d9c7ba23681604c692f9b392a`` (submodule í upprunaverkefninu á
commit ``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]

# Utan git (``data/raw/*`` er í .gitignore) — handritin mega aldrei rata í repo-ið.
DEFAULT_TRANSCRIPT_DIR = ROT / "data" / "raw" / "friends-handrit" / "season"
TRANSCRIPT_DIR_ENV = "FRIENDS_HANDRIT_MAPPA"
TRANSCRIPT_SUFFIX = ".html"
SOURCE_REPOSITORY = "https://github.com/delvinso/friends-tv-show-analysis"
SOURCE_COMMIT = "a4641fed3d95bb9d9c7ba23681604c692f9b392a"

# Skrár sem eru ekki sýndir þættir og því ekki samanburðarhæfar: 0423uncut er
# önnur útgáfa af þætti sem er þegar í 0423, og 07outtakes er upptökuafgangur
# sem var aldrei sýndur. 229 skrár í möppunni, 227 greindar.
EXCLUDED_FILES = frozenset({"0423uncut.html", "07outtakes.html"})

# Skrár sem geyma tvo sýnda þætti (tvöfaldir þættir og lokaþættir). Skiptir
# máli fyrir „á hvern þátt“-tölur: 227 skrár svara til 236 þátta.
DOUBLE_EPISODE_FILES = frozenset({
    "0212-0213.html", "0423.html", "0523.html", "0615-0616.html",
    "0624.html", "0723.html", "0823.html", "0923-0924.html", "1017-1018.html",
})
EPISODES_IN_DOUBLE_FILE = 2
EPISODES_IN_SINGLE_FILE = 1

# Skráarheitið er SSTT[...]: tveir fyrstu stafirnir eru þáttaröðin.
SEASON_CODE_RE = re.compile(r"^(?P<season>[0-9]{2})")

# Handritin eru handskrifuð frá tíunda áratugnum og ekki öll í UTF-8. cp1252
# nær flestum hinna; latin-1 getur ekki mistekist og er því síðasta úrræðið.
STRICT_ENCODINGS = ("utf-8", "cp1252")
FALLBACK_ENCODING = "latin-1"

TITLE_RE = re.compile(r"(?is)<title>(.*?)</title>")
WHITESPACE_RE = re.compile(r"\s+")


class TranscriptError(Exception):
    """Handritin finnast ekki eða skrá stenst ekki væntanlegt snið."""


def transcript_dir(directory: Path | str | None = None) -> Path:
    """Mappan með handritunum: rökin, annars umhverfisbreytan, annars sjálfgefið.

    Fellur með ``TranscriptError`` ef mappan er ekki til — þögul tóm greining
    myndi skila núlli í hverja tölu.
    """
    if directory is None:
        directory = os.environ.get(TRANSCRIPT_DIR_ENV) or DEFAULT_TRANSCRIPT_DIR
    path = Path(directory)
    if not path.is_dir():
        raise TranscriptError(
            f"Handritamappan {path} er ekki til. Sæktu {SOURCE_REPOSITORY} á "
            f"commit {SOURCE_COMMIT} og vísaðu á undirmöppuna season/ með "
            f"{TRANSCRIPT_DIR_ENV} (handritin fara aldrei í git, issue #3)."
        )
    return path


def transcript_paths(directory: Path | str | None = None) -> list[Path]:
    """Handritaskrárnar sem eru greindar, í stafrófsröð og án ``EXCLUDED_FILES``."""
    folder = transcript_dir(directory)
    paths = sorted(
        path for path in folder.glob(f"*{TRANSCRIPT_SUFFIX}")
        if path.name not in EXCLUDED_FILES
    )
    if not paths:
        raise TranscriptError(f"Engin handrit ({TRANSCRIPT_SUFFIX}) fundust í {folder}.")
    return paths


def episode_code(path: Path | str) -> str:
    """Auðkenni skrárinnar án endingar, t.d. ``0212-0213``."""
    return Path(path).name.replace(TRANSCRIPT_SUFFIX, "")


def season_of(path: Path | str) -> int:
    """Þáttaröðin sem skráarheitið segir til um (tveir fyrstu stafirnir)."""
    match = SEASON_CODE_RE.match(Path(path).name)
    if match is None:
        raise TranscriptError(
            f"Skráarheitið {Path(path).name} byrjar ekki á tveggja stafa þáttaröð."
        )
    return int(match["season"])


def aired_episodes(path: Path | str) -> int:
    """Fjöldi sýndra þátta sem skráin geymir (2 fyrir tvöfalda þætti, annars 1)."""
    if Path(path).name in DOUBLE_EPISODE_FILES:
        return EPISODES_IN_DOUBLE_FILE
    return EPISODES_IN_SINGLE_FILE


def decode_transcript(raw: bytes) -> str:
    """Afkóðar bæti handrits: UTF-8, svo cp1252, svo latin-1 sem bregst aldrei."""
    for encoding in STRICT_ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode(FALLBACK_ENCODING)


def read_html(path: Path | str) -> str:
    """Les eitt handrit sem texta (sjá ``decode_transcript``)."""
    try:
        raw = Path(path).read_bytes()
    except OSError as error:
        raise TranscriptError(f"Gat ekki lesið handritið {path}: {error}") from error
    return decode_transcript(raw)


def html_title(raw_html: str) -> str:
    """Innihald ``<title>`` með HTML-táknum afkóðuðum og bilum þjöppuðum; annars ''."""
    match = TITLE_RE.search(raw_html)
    if match is None:
        return ""
    return WHITESPACE_RE.sub(" ", html.unescape(match.group(1))).strip()
