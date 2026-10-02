"""Þáttari Friends-handritanna: HTML → textablokkir → flokkaðar línur.

Sameiginleg eining fyrir Friends-greiningarnar (issue #14). Flutt óbreytt að
virkni úr ``src/phoebe_analysis.py`` (upprunaverkefnið, commit ``2865ed6``);
föllin halda nöfnum sínum.

Hver textablokk fer í einn af fjórum flokkum (``LINE_KINDS``):

- ``scene``  — hefst á ``[`` eða ``(at ``; hækkar senuteljarann.
- ``action`` — hefst á ``(``; sjálfstæð sviðsleiðbeining.
- ``person`` — ``Nafn: texti`` þar sem nafnið þekkist sem ræðumaður.
- ``other``  — allt annað (kreditlínur, „Commercial Break“, „End“).

Skilgreiningar sem allar tölurnar hvíla á:

- **Lína** = ein ``Nafn: texti`` blokk. Hvorki setning né prentlína.
- **Orð** = ``[a-z][a-z'-]*`` eftir að svigainnskot voru fjarlægð, því
  ``(hlær)`` er sviðsleiðbeining en ekki talað orð (``spoken_words``).
- **Hóplínur** (``All:``, ``Monica and Phoebe:``) fá ``is_group=True`` og eru
  ekki eignaðar einstaklingum.
- **Phoebe Sr., Ursula og Mrs Buffay eru ekki Phoebe** (``NOT_PHOEBE_LABELS``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

from .friends_handrit import aired_episodes, episode_code, html_title, read_html, season_of

SCENE = "scene"
ACTION = "action"
PERSON = "person"
OTHER = "other"
LINE_KINDS = (SCENE, ACTION, PERSON, OTHER)

# Sértákn sem blokkatög eru umrituð í áður en textinn er klofinn; kemur aldrei
# fyrir í handritunum sjálfum.
SEP = "\x00"
# Tög sem marka nýja textablokk. <br> er talið með því hluti þáttaraðar 2
# notar það í stað <p> á milli tilsvara.
BLOCK_TAGS = re.compile(r"(?i)</?(br|p|div|hr|h[1-6]|tr|table|li|ul|ol|blockquote)[^>]*>")
HEAD_SCRIPT_COMMENT_RE = re.compile(r"(?is)<head.*?</head>|<script.*?</script>|<!--.*?-->")
INLINE_TAG_RE = re.compile(r"<[^>]*>")
WHITESPACE_RE = re.compile(r"\s+")
# Stafir sem cp1252-skrár skildu eftir í latin-1-afkóðun: gæsalappir og strik.
CP1252_LEFTOVERS = (
    ("\xa0", " "), ("\x85", "..."), ("\x92", "'"), ("\x93", '"'),
    ("\x94", '"'), ("\x96", "-"), ("\x97", "-"),
)

# Tilsvar: ``Nafn: texti``. Nafnið er í mesta lagi 41 stafur og má bera einn
# sviga (``Phoebe (singing):``), svo langar sviðslýsingar með tvípunkti lendi
# ekki sem ræðumaður.
SPEAKER_RE = re.compile(
    r"^([A-Za-z][A-Za-z0-9'&/,\.\- ]{0,40}(?:\s*\([^)]{0,60}\))?)\s*:\s*(.*)$")
# Sviðsleiðbeining innan tilsvars: ``(hlær)``, ``(til Joey)``.
PAREN_RE = re.compile(r"\([^)]*\)")
# Eitt talað orð. Tölur teljast ekki orð; bandstrikuð orð telja sem eitt.
WORD_RE = re.compile(r"[a-z][a-z'\-]*")
SCENE_PREFIX = "["
LOCATION_PREFIX = "(at "
ACTION_PREFIX = "("

# Merki sem líta út eins og ræðumaður en eru það ekki. „Transcribed by: …“
# passar við SPEAKER_RE, svo umritarinn yrði annars talinn persóna.
NON_SPEAKER_LABELS = re.compile(
    r"^(transcribed|written|teleplay|story|directed|produced|adapted|"
    r"with minor|minor |additional|note|parts? i+|final check|converted|"
    r"originally written|edited)\b"
)
# Merki með fleiri orðum en þetta er löng setning, þ.e. sviðsleiðbeining.
MAX_SPEAKER_WORDS = 4
LABEL_TRAILING_PUNCTUATION = ".,;"

# Persónur sem má ALDREI rugla saman við Phoebe: móðirin, tvíburasystirin o.fl.
# Þær eru sjálfstæðar persónur í gögnunum og fá eigið merki óbreytt.
NOT_PHOEBE_LABELS = frozenset({
    "phoebe sr", "phoebe sr.", "mrs buffay", "mrs. buffay", "ursula",
    "phoebe's assistant", "phoebe's friends", "photographer",
    "the photographer", "buffay, the vampire layer",
})
GROUP_LABELS = frozenset({
    "all", "both", "everyone", "everybody", "the guys", "the girls",
    "guys", "girls", "the gang", "gang", "others", "the others",
})
# Nöfn tengd með kommu, „and“, & eða / eru hópur.
GROUP_JOINER_RE = re.compile(r",| and |&|/")

# Samræming á nöfnum ræðumanna. Handritin stytta nöfn í fjóra stafi í hluta
# þáttaraðar 2 og nota bæði fornafn og fullt nafn; án töflunnar teldist sama
# persóna tvisvar.
SPEAKER_ALIASES = {
    "phoe": "phoebe", "pheebs": "phoebe", "phoebe buffay": "phoebe",
    "rach": "rachel", "rachel green": "rachel",
    "mnca": "monica", "mnca.": "monica", "monica geller": "monica",
    "chan": "chandler", "chandler bing": "chandler",
    "ross geller": "ross", "joey tribbiani": "joey",
}


@dataclass(frozen=True, slots=True)
class Line:
    """Ein flokkuð textablokk.

    ``spoken`` er textinn án svigainnskota; ``spoken_lower`` og ``text_lower``
    eru reiknuð einu sinni hér því greiningin fer margsinnis yfir hverja línu.
    """

    kind: str
    speaker: str
    is_group: bool
    text: str
    scene: int
    spoken: str
    spoken_lower: str
    text_lower: str


@dataclass(frozen=True)
class Episode:
    """Ein handritaskrá, þáttuð."""

    file: str
    code: str
    season: int
    title: str
    n_episodes: int
    lines: tuple[Line, ...]


def html_to_blocks(text: str) -> list[str]:
    """Klýfur HTML í textablokkir. Blokkamörk = <p>, <br>, <div>, <hr>, ...

    Fjögur skref: henda haus, skriftum og athugasemdum; umrita blokkatög í
    ``SEP``; henda inline-tögum án þess að kljúfa; lagfæra stafi sem
    cp1252-skrár skildu eftir.
    """
    text = HEAD_SCRIPT_COMMENT_RE.sub("", text)
    text = BLOCK_TAGS.sub(SEP, text)
    text = INLINE_TAG_RE.sub("", text)
    text = html.unescape(text)
    for leftover, replacement in CP1252_LEFTOVERS:
        text = text.replace(leftover, replacement)
    blocks = (WHITESPACE_RE.sub(" ", part).strip() for part in text.split(SEP))
    return [block for block in blocks if block]


def normalise_speaker(label: str) -> tuple[str, bool]:
    """Skilar (kanónísku nafni, er_hópur); ``('', False)`` ef ekki ræðumaður.

    Hóplínur fá ``er_hópur=True``: væru þær eignaðar einstaklingum teldist ein
    lína tvisvar eða oftar.
    """
    lab = PAREN_RE.sub("", label).strip().lower().rstrip(LABEL_TRAILING_PUNCTUATION)
    lab = WHITESPACE_RE.sub(" ", lab)
    if not lab or NON_SPEAKER_LABELS.match(lab):
        return "", False
    if len(lab.split()) > MAX_SPEAKER_WORDS:
        return "", False
    if lab in NOT_PHOEBE_LABELS:
        return lab, False
    if lab in GROUP_LABELS or GROUP_JOINER_RE.search(lab):
        return lab, True
    return SPEAKER_ALIASES.get(lab, lab), False


def make_line(kind: str, speaker: str, is_group: bool, text: str, scene: int) -> Line:
    """Býr til ``Line`` og reiknar afleiddu textamyndirnar einu sinni."""
    spoken = PAREN_RE.sub(" ", text)
    return Line(kind=kind, speaker=speaker, is_group=is_group, text=text, scene=scene,
                spoken=spoken, spoken_lower=spoken.lower(), text_lower=text.lower())


def classify_blocks(blocks: list[str]) -> list[Line]:
    """Flokkar textablokkir í röð og rekur senunúmerið (sjá docstring einingarinnar)."""
    lines: list[Line] = []
    scene = 0
    for block in blocks:
        if block.startswith(SCENE_PREFIX) or block.lower().startswith(LOCATION_PREFIX):
            scene += 1
            lines.append(make_line(SCENE, "", False, block, scene))
            continue
        if block.startswith(ACTION_PREFIX):
            lines.append(make_line(ACTION, "", False, block, scene))
            continue
        match = SPEAKER_RE.match(block)
        if match:
            speaker, is_group = normalise_speaker(match.group(1))
            if speaker:
                lines.append(make_line(PERSON, speaker, is_group, match.group(2).strip(), scene))
                continue
        lines.append(make_line(OTHER, "", False, block, scene))
    return lines


def parse_episode(path: Path | str) -> Episode:
    """Ein handritaskrá → ``Episode`` með flokkuðum línum í röð."""
    raw = read_html(path)
    return Episode(
        file=Path(path).name,
        code=episode_code(path),
        season=season_of(path),
        title=html_title(raw),
        n_episodes=aired_episodes(path),
        lines=tuple(classify_blocks(html_to_blocks(raw))),
    )


def spoken_words(text: str) -> list[str]:
    """Orð sem eru raunverulega töluð — sviðsleiðbeiningar í svigum fjarlægðar."""
    return WORD_RE.findall(PAREN_RE.sub(" ", text).lower())


def speaker_lines(episode: Episode, include_groups: bool = False) -> list[Line]:
    """Tilsvör þáttarins í röð; hóplínum sleppt nema beðið sé um þær."""
    return [
        line for line in episode.lines
        if line.kind == PERSON and (include_groups or not line.is_group)
    ]
