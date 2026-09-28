"""Fastar og mynstur Phoebe-greiningarinnar (issue #14, pakki P2.5).

Allt sem afmarkar úrtakið eða ræður talningu er nefnt hér, ekki grafið í
föllunum (regla 6): hverjar vinirnir sex eru, hvaða nafnmyndir teljast,
þröskuldar orðagreiningarinnar og hve margar raðir hver tafla geymir.
Gildin eru óbreytt úr ``src/phoebe_analysis.py`` (commit ``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re

FRIENDS = ("phoebe", "rachel", "ross", "chandler", "monica", "joey")
PHOEBE = "phoebe"
OTHER_FRIENDS = tuple(name for name in FRIENDS if name != PHOEBE)
# Röðin sem gamla síðan sýndi persónurnar í (samningsskrárnar).
DISPLAY_ORDER = ("phoebe", "rachel", "monica", "chandler", "joey", "ross")
TITLES = {name: name.title() for name in FRIENDS}

PERCENT_DECIMALS = 2
SHARE_DECIMALS = 4
LIFT_DECIMALS = 3

# ---------------------------------------------------------------- nafntilvik
# \w* tekur eignarfall og beygingar með (Phoebe's, Phoebes).
PHOEBE_NAME_RE = re.compile(r"\bph(?:oe|ee)b\w*\b", re.I)   # bæði formin
PHOEBE_FORMAL_RE = re.compile(r"\bphoeb\w*\b", re.I)        # Phoebe, Phoebs
PHOEBE_NICK_RE = re.compile(r"\bpheeb\w*\b", re.I)          # Pheebs, Pheeboh

# (?<![\w']) / (?![\w']) í stað \b svo „c'mon“ teljist ekki sem „Mon“.
_NB = r"(?<![\w'])"
_NA = r"(?![\w'])"
OTHER_NAME_RES = {
    "rachel": re.compile(_NB + r"(?:rachel(?:'s)?|rach)" + _NA, re.I),
    "ross": re.compile(_NB + r"(?:ross(?:'s|es|')?)" + _NA, re.I),
    "chandler": re.compile(_NB + r"(?:chandler(?:'s)?|chan)" + _NA, re.I),
    "monica": re.compile(_NB + r"(?:monica(?:'s)?|mon|mnca)" + _NA, re.I),
    "joey": re.compile(_NB + r"(?:joey(?:'s)?|joe)" + _NA, re.I),
}

# ------------------------------------------------------------------- tengsl
# Nafn Phoebe í fyrstu eða síðustu orðum línu er ávarpsmerki.
ADDRESS_EDGE_WORDS = 3
# Aðeins efstu gestirnir eru geymdir; halinn er langur og lítið segjandi.
MAX_GUEST_ROWS = 20
MAX_GUESTS_IN_CONTRACT = 10
# Munur efstu tveggja undir þessu (%) telst í raun jafntefli.
EFFECTIVE_TIE_PCT = 2.0

# ---------------------------------------------------------------- orðaforði
# Log-odds með Dirichlet-prior (Monroe, Colaresi & Quinn 2008).
PRIOR_SIZE = 1000.0
MIN_WORD_TOTAL = 40
MIN_WORD_LENGTH = 3
MAX_DISTINCTIVE_ROWS = 60
MAX_DISTINCTIVE_IN_REPORT = 25
PER_TEN_THOUSAND = 10000
# Þættir þurfa þetta margar línur vinanna til að komast á hlutfallslistann.
MIN_LINES_FOR_SHARE_RANKING = 100
TOP_EPISODES = 15

# Algeng orð sem eru undanskilin í leitinni að sérkennilegum orðum Phoebe.
STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "if", "so", "as", "of", "at", "by",
    "for", "with", "about", "to", "from", "in", "on", "out", "up", "down",
    "is", "am", "are", "was", "were", "be", "been", "being", "do", "does",
    "did", "have", "has", "had", "will", "would", "can", "could", "should",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "this", "that",
    "these", "those", "there", "here", "what", "who", "when", "where", "why",
    "how", "not", "no", "yes", "all", "just", "know", "like", "get", "got",
    "go", "going", "gonna", "well", "oh", "okay", "ok", "right", "yeah",
    "hey", "uh", "um", "s", "t", "m", "re", "ve", "ll", "d", "don", "didn",
    "you're", "i'm", "it's", "that's", "don't", "didn't", "can't", "won't",
    "i'll", "you'll", "he's", "she's", "we're", "they're", "i've", "isn't",
})

# -------------------------------------------------------------------- þemu
# Þemuorð Phoebe. Talin í lágstöfuðum texta, svo mynstrin eru án flagga.
SIGNATURE_TOPICS = {
    "smelly cat": re.compile(r"smelly cat"),
    "grandma": re.compile(r"\bgrandma\w*\b"),
    "guitar": re.compile(r"\bguitar\w*\b"),
    "sing/song": re.compile(r"\bsing\w*\b|\bsong\w*\b"),
    "massage": re.compile(r"\bmassag\w*\b"),
    "aura": re.compile(r"\baura\w*\b"),
    "karma/spirit/psychic": re.compile(r"\bkarma\b|\bspirit\w*\b|\bpsychic\w*\b"),
    "vegetarian/meat": re.compile(r"\bvegetarian\w*\b|\bmeat\b"),
    "y'know": re.compile(r"\by'?know\b"),
    "oh my god": re.compile(r"oh my god"),
}
ALIAS_TERMS = {
    "regina phalange": re.compile(r"regina phalange"),
    "princess consuela": re.compile(r"princess consuela"),
    "banana hammock": re.compile(r"banana hammock"),
    "buffay": re.compile(r"\bbuffay\b"),
    "ursula": re.compile(r"\bursula\b"),
}
PEOPLE = {
    "mike": re.compile(r"\bmike\b"), "david": re.compile(r"\bdavid\b"),
    "ursula": re.compile(r"\bursula\b"), "frank": re.compile(r"\bfrank\b"),
    "gary": re.compile(r"\bgary\b"), "duncan": re.compile(r"\bduncan\b"),
    "roger": re.compile(r"\broger\b"), "parker": re.compile(r"\bparker\b"),
}
SIGNATURE_PHRASES = {
    "smelly cat": re.compile(r"smelly cat"),
    "oh my god": re.compile(r"oh my god"),
    "y'know": re.compile(r"y'?know\b"),
    "no no no": re.compile(r"\bno,? no,? no\b"),
    "oh honey": re.compile(r"oh,? honey\b"),
    "you guys": re.compile(r"\byou guys\b"),
    "my grandma": re.compile(r"\bmy grandmo?a?ther\b|\bmy grandma\b"),
    "wait wait": re.compile(r"\bwait,? wait\b"),
    "ooh": re.compile(r"\boo+h\b"),
    "regina phalange": re.compile(r"regina phalange"),
    "princess consuela": re.compile(r"princess consuela"),
}


def pct(part: float, whole: float, decimals: int = PERCENT_DECIMALS) -> float:
    """Hlutfall í prósentum; 0 í stað deilingar með núlli."""
    return round(100.0 * part / whole, decimals) if whole else 0.0
