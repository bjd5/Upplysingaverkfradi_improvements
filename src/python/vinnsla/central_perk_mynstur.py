"""Fastar og reglulegar segðir Central Perk-greiningarinnar (issue #14, P2.6).

Allt sem ræður *hvað* greiningin telur er hér, á einum stað: aðalpersónurnar
og samheiti nafna þeirra, segðirnar sem þátta handritin og merkja söng, og
þröskuldarnir sem lesturinn notar. Segðirnar eru orðréttar úr
``src/phoebe_central_perk.py`` í upprunaverkefninu (commit ``2865ed6``) —
``DOCUMENTED_PATTERNS`` prentar þær út og viðmiðið
``docs/vidmid/generated/phoebe-central-perk-regex.md`` sýnir að þær eru þær
sömu og keyrðu þá.

**Ath.:** þessi greining þáttar handritin á annan hátt en ``friends_thattari``
(Phoebe-tölfræðin, P2.5): annað ræðumannamynstur, annað orðamynstur og
aðeins ``<p>``-málsgreinar. Mynstrin tvö eru því viljandi aðskilin — að
sameina þau breytir tölum beggja greininga.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re

# Aðalpersónurnar sex. Aðeins orð þeirra eru talin; gestir og hópar ekki.
MAIN_CAST = ("Rachel", "Monica", "Phoebe", "Joey", "Chandler", "Ross")
PHOEBE = "Phoebe"

# Handritin skrifa nöfn ræðumanna með ýmsu móti — stytt í fjóra stafi í hluta
# þáttaraðar 2 (`Phoe`, `Mnca`, `Chan`, `Rach`) og stundum rangt stafsett
# (`Pheobe`). Hér er hvert afbrigði fært á eitt kanónískt nafn.
NAME_ALIASES = {
    "rachel": "Rachel",
    "rach": "Rachel",
    "monica": "Monica",
    "mnca": "Monica",
    "phoebe": "Phoebe",
    "pheobe": "Phoebe",
    "phoe": "Phoebe",
    "joey": "Joey",
    "chandler": "Chandler",
    "chan": "Chandler",
    "ross": "Ross",
}

# Byggð einu sinni hér, ekki í hverju kalli: `normalise_speaker` er kallað
# fyrir hvert `Nafn:`-label í öllum handritunum (~73 þúsund sinnum).
NAME_ALIAS_PATTERNS = tuple(
    (re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE), canonical)
    for alias, canonical in NAME_ALIASES.items()
)

SPACE_RE = re.compile(r"\s+")
# Bil sem ekki eru línuskil — þjappað innan blokkar svo `<br>`-merkin lifi.
INLINE_SPACE_RE = re.compile(r"[ \t\r\f\v]+")

# Sértákn sem `<br>` er umritað í meðan HTML er lesið, svo hægt sé að skipta
# blokkum á línuskilum eftir á. Táknið sjálft kemur aldrei fyrir í handritunum.
BREAK_MARKER = "␞"
BREAK_MARKER_RE = re.compile(rf"\s*{re.escape(BREAK_MARKER)}\s*")

# Skrá með færri `<p>`-málsgreinar en þetta er skrifuð með `<br>` (hluti
# þáttaraðar 2): allt handritið er þá ein risamálsgrein.
MIN_PARAGRAPHS_FOR_P_FORMAT = 20
# Í `<br>`-sniðinu skilja tvö eða fleiri `<br>` í röð að tilsvör.
MIN_BREAKS_BETWEEN_LINES = 2
LINE_GAP_RE = re.compile(rf"(?:{re.escape(BREAK_MARKER)}){{{MIN_BREAKS_BETWEEN_LINES},}}")

# Handritin eru lesin sem UTF-8 og ólæsileg bæti verða að U+FFFD. Það er
# EKKI sama afkóðun og `friends_handrit.read_html` (utf-8 → cp1252 → latin-1);
# á 18 handritum gefa þær ólíkan texta, og tölur viðmiðsins byggja á þessari.
TRANSCRIPT_ENCODING = "utf-8"
TRANSCRIPT_DECODE_ERRORS = "replace"

# Tilsvar: `Nafn: texti`. Nafnhlutinn má ekki innihalda tvípunkt eða línuskil
# og er að hámarki 100 stafir, svo langar sviðslýsingar með tvípunkti lendi
# ekki sem ræðumaður.
SPEAKER_RE = re.compile(r"^\s*([^:\n]{1,100}):\s*(.*)$", re.DOTALL)

# Orð = enskir bókstafir, með einni úrfellingu leyfðri (`don't`, `I’m`).
# Tölur og greinarmerki teljast ekki orð.
WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")

# Sviðsfyrirsögn: blokk sem hefst á hornklofa eða sviga með orði sem umritarar
# nota til að marka nýja senu eða klippingu (`[Scene: …]`, `(Cut to …)`,
# `[Later, …]`, `[Time lapse]`). Hver slík blokk hækkar senuteljarann.
SCENE_START_RE = re.compile(
    r"^\s*(?:\[[^]]*\b(?:scene|cut|later|time lapse|back at|meanwhile|opening credits|closing credits)\b"
    r"|\([^)]*\b(?:scene|cut to|cut back|later|time lapse|back at|meanwhile)\b)",
    re.IGNORECASE,
)
CENTRAL_PERK = "central perk"

# Víð leit að tónlistarorðum. Notuð AÐEINS í yfirferðarham til að draga fram
# blokkir sem manneskja fer svo yfir; hún ræður engri talningu.
MUSIC_RE = re.compile(
    r"\b(?:sing(?:s|ing)?|sung|song|guitar|perform(?:s|ing|ance)?|music(?:al)?)\b",
    re.IGNORECASE,
)

# Sviðsleiðbeiningar innan tilsvars: `(laughs)`, `[to Joey]`, `{pause}`.
# Þær eru fjarlægðar áður en orð eru talin, því þær eru ekki töluð.
STAGE_DIRECTION_RE = re.compile(r"\([^)]*\)|\[[^]]*\]|\{[^}]*\}")

# Skýr söngmerking í svigum eða hornklofum: `(singing)`, `(sings)`, `(sung)`,
# `(starts to sing)`, `(starts to play and sing)`. Passar ekki við `song` eða
# `guitar` ein og sér — það er viljandi (sjá `central_perk_songur`).
SINGING_CUE_RE = re.compile(
    r"[\[(][^)\]]*\b(?:singing|sings|sung|starts? to (?:play and )?sing)\b[^)\]]*[\])]",
    re.IGNORECASE,
)

# Sviðslýsing sem segir berum orðum að Phoebe sé að koma fram. Allt að 80
# stafir mega standa á milli nafnsins og sagnarinnar.
PHOEBE_PERFORMANCE_RE = re.compile(
    r"(?:\bphoebe(?:'s|’s)?\b.{0,80}\b(?:is singing|performing|finishing up a song)\b"
    r"|\bboth\b.{0,40}\bphoebe\b.{0,80}\bsinging\b)",
    re.IGNORECASE,
)

# Samanburðarhóparnir þrír, í þeirri röð sem þeir birtast.
NO_CENTRAL_PERK = "no_central_perk"
CENTRAL_PERK_GROUP = "central_perk"
PHOEBE_SINGS = "phoebe_sings"
GROUP_ORDER = (NO_CENTRAL_PERK, CENTRAL_PERK_GROUP, PHOEBE_SINGS)

# Segðirnar sem skýrslan sýnir lesandanum, í þeirri röð sem þær koma við sögu:
# (heiti, segð, hvað hún grípur, hvað sleppur). Textinn fer óbreyttur í
# úttakið svo síðan og kóðinn geti ekki orðið ósammála um hvað mynstrin gera.
DOCUMENTED_PATTERNS: tuple[tuple[str, re.Pattern[str], str, str], ...] = (
    (
        "SCENE_START_RE",
        SCENE_START_RE,
        "Byrjun senu. Blokk sem hefst á hornklofa eða sviga með orði á borð við "
        "`Scene`, `Cut to`, `Later` eða `Time lapse` hækkar senuteljarann og "
        "ræður hvort næstu tilsvör eru í Central Perk (ef fyrirsögnin nefnir "
        "staðinn).",
        "Senuskipti sem umritari skrifaði án hornklofa eða sviga, og senur sem "
        "gerast í Central Perk án þess að fyrirsögnin nefni staðinn.",
    ),
    (
        "SPEAKER_RE",
        SPEAKER_RE,
        "Tilsvar á forminu `Nafn: texti`. Fyrri hópurinn er ræðumaður (færður á "
        "kanónískt nafn með `NAME_ALIASES`), sá seinni línan sjálf.",
        "Tilsvör þar sem umritari sleppti tvípunktinum, og sviðslýsingar sem "
        "innihalda tvípunkt innan fyrstu 100 stafa lenda sem „ræðumaður“ sem "
        "engin aðalpersóna á og eru þá ekki taldar.",
    ),
    (
        "SINGING_CUE_RE",
        SINGING_CUE_RE,
        "Skýr söngmerking í svigum eða hornklofum í tilsvari Phoebe: `(singing)`, "
        "`(sings)`, `(sung)`, `(starts to sing)`. Senan telst söngsena aðeins ef "
        "hún er í Central Perk.",
        "Söngur sem umritari merkti ekki, eða merkti með orðum sem segðin leitar "
        "ekki að (`(humming)`, `(plays guitar)`). Misheppnaða byrjunin í `0107`, "
        "þar sem Phoebe slær einn hljóm áður en rafmagnið fer, fellur því utan.",
    ),
    (
        "PHOEBE_PERFORMANCE_RE",
        PHOEBE_PERFORMANCE_RE,
        "Sviðslýsing sem segir að Phoebe sé að koma fram: „Phoebe is singing“, "
        "„Phoebe's performing“, „Phoebe … finishing up a song“, „both … Phoebe … "
        "singing“. Grípur söng sem er lýst í sviðsfyrirsögn eða sjálfstæðri "
        "sviðslýsingu frekar en inni í tilsvari.",
        "Lýsingar með annarri orðanotkun (`Phoebe plays`, `Phoebe strums`) og "
        "tilvik þar sem nafnið og sögnin standa lengra en 80 stöfum hvort frá öðru.",
    ),
    (
        "STAGE_DIRECTION_RE",
        STAGE_DIRECTION_RE,
        "Sviðsleiðbeiningar innan tilsvars: `(laughs)`, `[to Joey]`, `{pause}`. "
        "Þær eru klipptar burt áður en orð eru talin.",
        "Óparaður svigi (t.d. `(laughs` án lokunar) sleppur í gegn og orðin í "
        "honum teljast töluð.",
    ),
    (
        "WORD_RE",
        WORD_RE,
        "Eitt talað orð: enskir bókstafir, með einni úrfellingu leyfðri (`don't`). "
        "Fjöldi samsvarana er orðafjöldi tilsvarsins.",
        "Tölur (`2`) og bandstrikuð orð telja sem tvö (`well-known` → `well`, "
        "`known`). Það hefur sömu áhrif á allar persónur og skekkir ekki hlutföll.",
    ),
)
