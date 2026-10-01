"""Skref 1 í Central Perk-greiningunni: HTML-handrit → textablokkir (issue #14, P2.6).

Flutt úr ``src/phoebe_central_perk.py`` (commit ``2865ed6``): ``Block``,
``ParagraphParser``, ``clean_text``, ``clean_html_block`` og ``read_blocks``.

Lesturinn er **ekki** sá sami og ``friends_thattari`` notar (P2.5): hér er
aðeins texti innan ``<p>`` lesinn, ``<br>``-sniðið fær sérreglu, og bætin eru
afkóðuð sem UTF-8 með ``errors="replace"``. Tölur viðmiðsins byggja á þessum
lestri og því er hann fluttur óbreyttur.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from .central_perk_mynstur import (
    BREAK_MARKER, BREAK_MARKER_RE, INLINE_SPACE_RE, LINE_GAP_RE,
    MIN_PARAGRAPHS_FOR_P_FORMAT, SPACE_RE, TRANSCRIPT_DECODE_ERRORS, TRANSCRIPT_ENCODING,
)
from .friends_handrit import TranscriptError

NBSP = "\xa0"


@dataclass(frozen=True)
class Block:
    """Ein textablokk úr handriti, í þeirri röð sem hún stóð í skránni."""

    text: str
    source_index: int


def clean_text(value: str) -> str:
    """Þjappar bilum og afkóðar HTML-tákn (``&amp;``, ``&nbsp;``)."""
    return SPACE_RE.sub(" ", html.unescape(value).replace(NBSP, " ")).strip()


def clean_html_block(value: str) -> str:
    """Eins og ``clean_text`` en varðveitir ``BREAK_MARKER`` sem sjálfstætt tákn."""
    value = html.unescape(value).replace(NBSP, " ")
    value = INLINE_SPACE_RE.sub(" ", value)
    value = BREAK_MARKER_RE.sub(BREAK_MARKER, value)
    return value.strip()


class ParagraphParser(HTMLParser):
    """Dregur ``<p>``-málsgreinar út úr handriti og þolir óreglulegt HTML.

    Handritin eru handskrifað HTML frá tíunda áratugnum: málsgreinar eru
    stundum ólokaðar og ``<br>`` er notað í stað ``<p>`` í hluta þáttaraðar 2.
    ``<br>`` innan málsgreinar er skráð sem ``BREAK_MARKER`` svo
    ``read_blocks`` geti klofið blokkina eftir á.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self._inside_paragraph = False
        self._parts: list[str] = []
        self._source_index = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """``<p>`` byrjar málsgrein; ``<br>`` innan hennar verður ``BREAK_MARKER``."""
        if tag.lower() == "p":
            # Nýtt `<p>` lokar þeirri fyrri þótt `</p>` vanti.
            self._flush()
            self._inside_paragraph = True
        elif tag.lower() == "br" and self._inside_paragraph:
            self._parts.append(BREAK_MARKER)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """``<br/>`` og ``<p/>`` eru meðhöndluð eins og opnunarmerki."""
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        """``</p>`` lokar málsgreininni."""
        if tag.lower() == "p":
            self._flush()
            self._inside_paragraph = False

    def handle_data(self, data: str) -> None:
        """Safnar texta málsgreinarinnar."""
        # Texti utan `<p>` (titill, kreditlínur í `<h1>`/`<b>`) er hunsaður.
        if self._inside_paragraph:
            self._parts.append(data)

    def close(self) -> None:
        """Lýkur lestri og skráir síðustu málsgreinina, þótt ``</p>`` vanti."""
        super().close()
        self._flush()

    def _flush(self) -> None:
        text = clean_html_block("".join(self._parts))
        if text:
            self.blocks.append(Block(text=text, source_index=self._source_index))
            self._source_index += 1
        self._parts = []


def read_transcript_text(path: Path) -> str:
    """Les handrit sem UTF-8; ólæsileg bæti verða U+FFFD (sjá ``central_perk_mynstur``)."""
    try:
        return path.read_text(encoding=TRANSCRIPT_ENCODING, errors=TRANSCRIPT_DECODE_ERRORS)
    except OSError as error:
        raise TranscriptError(f"Gat ekki lesið handritið {path}: {error}") from error


def paragraphs(raw_html: str) -> list[Block]:
    """``<p>``-málsgreinar handrits, með ``BREAK_MARKER`` þar sem ``<br>`` stóð."""
    parser = ParagraphParser()
    parser.feed(raw_html)
    parser.close()
    return parser.blocks


def split_break_format(raw_blocks: list[Block]) -> list[Block]:
    """``<br>``-snið: klýfur blokkir þar sem tvö eða fleiri ``<br>`` standa saman.

    Það er línubilið sem umritarinn setti á milli tilsvara. Blokkirnar eru
    tölusettar upp á nýtt í röð.
    """
    split_blocks: list[Block] = []
    for block in raw_blocks:
        for part in LINE_GAP_RE.split(block.text):
            text = clean_text(part.replace(BREAK_MARKER, " "))
            if text:
                split_blocks.append(Block(text=text, source_index=len(split_blocks)))
    return split_blocks


def join_single_breaks(raw_blocks: list[Block]) -> list[Block]:
    """Venjulegt snið: stakt ``<br>`` innan málsgreinar er línuskil í sama tilsvari."""
    return [
        Block(text=clean_text(block.text.replace(BREAK_MARKER, " ")),
              source_index=block.source_index)
        for block in raw_blocks
    ]


def blocks_from_html(raw_html: str) -> list[Block]:
    """Klýfur HTML-texta handrits í textablokkir í röð.

    Flest handrit hafa eina ``<p>``-málsgrein á hvert tilsvar. Skrár með færri
    en ``MIN_PARAGRAPHS_FOR_P_FORMAT`` málsgreinar eru skrifaðar með ``<br>``
    (þáttaröð 2) og eru klofnar með ``split_break_format``.
    """
    raw_blocks = paragraphs(raw_html)
    if len(raw_blocks) < MIN_PARAGRAPHS_FOR_P_FORMAT:
        return split_break_format(raw_blocks)
    return join_single_breaks(raw_blocks)


def read_blocks(path: Path) -> list[Block]:
    """Les eitt handrit og skilar textablokkum í röð (sjá ``blocks_from_html``)."""
    return blocks_from_html(read_transcript_text(Path(path)))
