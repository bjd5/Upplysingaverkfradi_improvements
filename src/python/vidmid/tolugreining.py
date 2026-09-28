"""Finnur tölur í íslenskum texta og flokkar þær eftir tegund.

Þetta er kjarninn í P0.2. Gamla síðan birtir tölurnar sínar aðeins sem texta, og
íslenskt tölusnið er margvís: þúsundir eru skrifaðar bæði með punkti (61.161) og
með bili (70 553), aukastafir með kommu (2,95), hlutföll með tvípunkti (6,7:1).
Í sama texta liggja tölur sem eru EKKI niðurstöður: þáttaauðkenni (0405),
issue-tilvísanir (#14), ISO-dagsetningar, CSS-gildi og tölur inni í regex.

Aðferðin er ein raðbundin segð: fyrsta mynstrið sem passar á tiltekinn stað
vinnur. Þess vegna er röðin í MYNSTUR merkingarbær — sértækustu mynstrin fyrst,
almenna heiltalan síðust. Ekkert er hent: tala sem er ekki niðurstaða fær
tegund og `visst=False` í staðinn, svo hún verði áfram rekjanleg (regla 8).

Bandstrik er skiltákn jafnoft og það er mínus (issue #38). Þess vegna gildir
ein regla um formerki: ASCII-bandstrik er mínus aðeins þegar það stendur eitt
og sér á undan tölunni (sjá FORMERKI), og keðja af tölum sem bandstrik bindur
saman er skráð sem eitt auðkenni, ekki sem tvær eða fjórar tölur.
"""

from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple

MANUDIR = (
    "janúar|febrúar|mars|apríl|maí|júní|júlí|ágúst|september|október"
    "|nóvember|desember"
)

# Einingar sem standa strax á eftir tölu og eru þess virði að skrá sérstaklega.
# Beygingarmyndirnar eru taldar upp fullum fetum; íslensk beyging er ekki
# reglusetjanleg með viðskeytaklippingu án þess að búa til rugl.
EININGAR = {
    "%": "%", "prósent": "%", "prósentustig": "prósentustig",
    "km": "km", "m": "m", "mb": "MB", "kb": "KB", "gb": "GB",
    "dagur": "dagar", "dagar": "dagar", "daga": "dagar", "dögum": "dagar",
    "dag": "dagar", "utc-dögum": "dagar", "utc-dag": "dagar",
    "klukkustund": "klukkustundir", "klukkustundir": "klukkustundir",
    "sekúnda": "sekúndur", "sekúndur": "sekúndur", "sekúndum": "sekúndur",
    "atburður": "atburðir", "atburðir": "atburðir", "atburði": "atburðir",
    "jarðskjálftar": "jarðskjálftar", "jarðskjálfta": "jarðskjálftar",
    "skjálftar": "jarðskjálftar", "skjálfta": "jarðskjálftar",
    "skrá": "skrár", "skrár": "skrár", "skrám": "skrár", "skráa": "skrár",
    "handrit": "handrit", "handritum": "handrit", "handrita": "handrit",
    "handritaskrám": "handritaskrár", "handritaskrár": "handritaskrár",
    "þáttur": "þættir", "þættir": "þættir", "þætti": "þættir",
    "þáttum": "þættir", "þáttaröð": "þáttaraðir", "þáttaraðir": "þáttaraðir",
    "lína": "línur", "línur": "línur", "línum": "línur", "línu": "línur",
    "tilsvar": "tilsvör", "tilsvör": "tilsvör", "tilsvörum": "tilsvör",
    "orð": "orð", "orðum": "orð", "orða": "orð",
    "sena": "senur", "senur": "senur", "senum": "senur", "sena.": "senur",
    "textablokk": "textablokkir", "textablokkir": "textablokkir",
    "textablokkum": "textablokkir",
    "sviðsfyrirsögn": "sviðsfyrirsagnir", "sviðsfyrirsagnir": "sviðsfyrirsagnir",
    "sviðsleiðbeining": "sviðsleiðbeiningar",
    "sviðsleiðbeiningar": "sviðsleiðbeiningar",
    "token": "tokenar", "tokenar": "tokenar", "tokena": "tokenar",
    "commit": "commit", "stafur": "stafir", "stafir": "stafir",
    "stafa": "stafir", "stöfum": "stafir",
    "málsgrein": "málsgreinar", "málsgreinar": "málsgreinar",
    "nemandi": "nemendur", "nemendur": "nemendur", "nemenda": "nemendur",
    "fréttir": "fréttir", "frétta": "fréttir", "fyrirsögn": "fyrirsagnir",
    "fyrirsagnir": "fyrirsagnir", "fyrirsagna": "fyrirsagnir",
}

# Bandstrik er mínus AÐEINS þegar það stendur eitt og sér á undan tölunni.
# Inni í auðkenni (0-20000-0-04030), skýrslunúmeri (VÍ 2009-013), þáttabili
# (1017-1018) eða slóð bindur það tvennt saman og er skiltákn, ekki formerki —
# og þá stendur stafur, tölustafur eða annað skilmerki fast á undan því.
# U+2212 (−) er hins vegar aldrei annað en mínus og þarf enga vörn.
FORMERKI = r"(?:−|(?<![\w.,/%+])-)?"

# Röðin ræður. Fyrsta mynstrið sem passar vinnur — sértækt fyrst, almennt síðast.
MYNSTUR: tuple[tuple[str, str], ...] = (
    # Tímastimplar og dagsetningar. Þarf að koma fyrir öllu tölulegu, annars
    # verður 2023-11-01 lesið sem þremur tölum.
    ("timastimpill", r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:[.,]\d+)?)?"
                     r"(?:Z|[+−-]\d{2}:?\d{2})?"),
    ("dagsetning", r"\d{4}-\d{2}-\d{2}"),
    ("vika", r"\d{4}-W\d{2}"),
    ("dagsetning", rf"\d{{1,2}}\.(?:\s*[–—-]\s*\d{{1,2}}\.)?\s*(?:{MANUDIR})"
                   r"[a-záðéíóúýþæö]*(?:\s+\d{4})?"),
    ("dagsetning", r"\d{1,2}\.\d{1,2}\.(?:\d{4})?(?!\d)"),
    ("klukka", r"(?<![\d.,:])\d{1,2}:\d{2}(?::\d{2})?(?![\d:])"),
    # Tilvísanir og auðkenni sem líta út eins og tölur en eru nöfn.
    ("litur", r"#[0-9a-fA-F]{3,8}\b"),
    ("tilvisun", r"#\d+\b"),
    ("myndnumer", r"\b\d{1,3}\.\d{1,3}(?=:)"),
    ("thattaraudkenni", r"\b0\d{3}(?:-\d{4})?\b"),
    ("kodatala", r"\{\d+(?:,\d+)?\}"),
    ("css", r"\b\d+(?:[.,]\d+)?(?:px|rem|em|pt|vh|vw|ch)\b"),
    ("aukenni", r"\b(?:v|nr\.?|no\.?)\d+\b"),
    ("aukenni", r"\b[A-Za-zÁÐÉÍÓÚÝÞÆÖáðéíóúýþæö][\w+.-]*\d[\w+.-]*\b"),
    ("aukenni", r"\b\d+[A-Za-zÁÐÉÍÓÚÝÞÆÖáðéíóúýþæö][\w+.-]*\b"),
    # Tölur sem eru niðurstöður.
    ("arabil", r"\b(?:1[89]\d{2}|20\d{2})\s*[–—-]\s*(?:1[89]\d{2}|20\d{2})\b"),
    # Tölur bundnar saman með bandstriki eru eitt auðkenni, ekki tvær tölur:
    # 0-20000-0-04030 (WIGOS), 2009-013 (skýrslunúmer), 1017-1018 (þáttabil).
    # Verður að koma EFTIR dagsetningum, þáttaauðkenni og arabili — þau eru
    # sértækari myndir af sömu keðju (2023-11-01, 0212-0213, 2014-2023).
    ("aukenni", r"\b\d+(?:-\d+)+\b"),
    ("hlutfallstala", FORMERKI + r"\d+(?:[.,]\d+)?\s*:\s*\d+(?:[.,]\d+)?"),
    # % á eftir tveimur sextándastöfum (%3A, %28, %2C) er prósentukóðun í
    # slóð, ekki prósentumerki — táknið tilheyrir NÆSTA stafnum, ekki
    # tölunni á undan (issue #44). Vörnin er því hægra megin við %, ekki
    # vinstra megin eins og FORMERKI er fyrir bandstrikið (issue #38).
    ("hlutfall", FORMERKI + r"\d{1,3}(?:[.  ]\d{3})*(?:,\d+)?\s*%"
                            r"(?![0-9A-Fa-f]{2})"),
    # Formerkið á eftir bilstrikinu þarf enga vörn: það stendur alltaf á eftir
    # – eða — og getur því ekki verið bandstrik inni í auðkenni.
    ("bil", FORMERKI + r"\d+(?:,\d+)?\s*[–—]\s*[−-]?\d+(?:,\d+)?"),
    ("thusund", FORMERKI + r"\d{1,3}(?:[.   ]\d{3})+(?:,\d+)?(?![\d.,])"),
    ("desimal", FORMERKI + r"\d+,\d+"),
    ("desimal_punktur", FORMERKI + r"\d+\.\d+(?!\d)"),
    ("ar", r"\b(?:1[89]\d{2}|20\d{2})\b"),
    ("heiltala", FORMERKI + r"\d+"),
)

# Tegundir sem geta verið efnisleg niðurstaða. Hinar fá visst=False og eru
# skráðar áfram — betra að hafa of mikið en að missa tölu (verklýsing P0.2).
EKKI_EITT_GILDI = frozenset({
    "bil", "arabil", "timastimpill", "dagsetning", "vika", "klukka",
    "litur", "myndnumer", "thattaraudkenni", "aukenni", "kodatala", "css",
})

NIDURSTODUTEGUNDIR = frozenset({
    "heiltala", "desimal", "hlutfall", "bil", "hlutfallstala", "thusund",
})

_SEGD = re.compile(
    "|".join(f"(?P<g{i}>{m})" for i, (_, m) in enumerate(MYNSTUR)),
    re.IGNORECASE,
)
_TEGUND = {f"g{i}": t for i, (t, _) in enumerate(MYNSTUR)}
_ORD = re.compile(r"[\w%°:.,–—-]+", re.UNICODE)


class Tala(NamedTuple):
    """Ein tala eins og hún stendur í texta, með flokkun og tölugildi."""

    texti: str          # óbreytt eins og það stóð
    tegund: str         # heiltala, desimal, hlutfall, dagsetning, aukenni, ...
    gildi: float | int | None   # tölugildi, eða None fyrir bil og dagsetningar
    bil: tuple[float, float] | None  # endapunktar ef tegundin er bil
    eining: str | None  # %, dagar, jarðskjálftar, ... ef næsta orð segir það
    visst: bool         # True ef tegundin getur verið efnisleg niðurstaða
    upphaf: int         # staðsetning í textanum, til að endurfinna samhengið


def _tolugildi(texti: str, tegund: str) -> float | int | None:
    """Þýðir íslenskt tölusnið í tölu. None ef talan er ekki eitt gildi.

    Þúsundaskil eru punktur, bil eða fast bil (61.161, 70 553); aukastafamerki
    er komma (2,95). Eina undantekningin er desimal_punktur — tala úr kóða þar
    sem punkturinn er aukastafamerki að engilsaxneskum hætti.
    """
    if tegund in EKKI_EITT_GILDI:
        return None
    hreint = (texti.replace("−", "-").replace("\u00a0", "")
              .replace("\u202f", "").replace("%", "").strip())
    if tegund == "hlutfallstala":
        hreint = hreint.split(":")[0].strip()
    elif tegund == "tilvisun":
        hreint = hreint.lstrip("#")
    if tegund != "desimal_punktur":
        hreint = hreint.replace(".", "").replace(" ", "")
    hreint = hreint.replace(",", ".")
    try:
        gildi = float(hreint)
    except ValueError:
        return None
    return int(gildi) if "." not in hreint else gildi


def _bil(texti: str) -> tuple[float, float] | None:
    """Endapunktar bils (3–7, 0,07–11,26) svo prófanir geti borið þau saman."""
    hlutar = re.split(r"\s*[–—]\s*", texti.replace("−", "-"))
    if len(hlutar) != 2:
        return None
    try:
        return (float(hlutar[0].replace(",", ".")),
                float(hlutar[1].replace(",", ".")))
    except ValueError:
        return None


def _eining(texti: str, eftir: str) -> str | None:
    """Eining tölunnar: % úr tölunni sjálfri, annars fyrsta orðið á eftir."""
    if "%" in texti:
        return "%"
    m = _ORD.match(eftir.lstrip())
    if not m:
        return None
    ord_ = m.group(0).strip(".,:").lower()
    return EININGAR.get(ord_)


def finna_tolur(texti: str) -> list[Tala]:
    """Finnur allar tölur í textablokk og flokkar þær.

    Skilar þeim í þeirri röð sem þær standa í textanum. Tölur sem eru ekki
    efnisleg niðurstaða eru áfram með í listanum en hafa visst=False.
    """
    texti = unicodedata.normalize("NFC", texti)
    tolur: list[Tala] = []
    for m in _SEGD.finditer(texti):
        hopur = m.lastgroup
        if hopur is None:  # verður ekki, en þögul villa er verri en hrun
            raise RuntimeError(f"Mynstur passaði án hóps: {m.group(0)!r}")
        tegund = _TEGUND[hopur]
        hrar = m.group(0)
        tolur.append(Tala(
            texti=hrar.strip(),
            tegund=tegund,
            gildi=_tolugildi(hrar, tegund),
            bil=_bil(hrar) if tegund == "bil" else None,
            eining=_eining(hrar, texti[m.end():m.end() + 40]),
            visst=tegund in NIDURSTODUTEGUNDIR,
            upphaf=m.start(),
        ))
    return tolur
