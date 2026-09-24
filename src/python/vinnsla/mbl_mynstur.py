"""Mynstrin fimm sem regex-æfingin á mbl.is byggir á (issue #9).

Æfingin svarar **fimm afmörkuðum spurningum** úr vistuðu HTML-svari frá
``https://www.mbl.is/frettir/``. Mynstrin eru sérhæfð fyrir þekkt slóða-, veður-
og JavaScript-brot; þau eru ekki almennur HTML-þáttari og niðurstöðurnar lýsa
aðeins því eintaki sem var lesið, ekki mbl.is almennt.

Mynstrin eru geymd hér — og afrituð inn í grunninn með hverri niðurstöðu — því
regla 8 krefst rekjanleika: án mynstursins er ekki hægt að sjá hvers vegna talan
varð þessi.

Finnist mynstur ekki er kastað :class:`UtdrattarVilla`. Þögult núll eða tómur
listi er ekki í boði (regla 6): breyting á HTML-sniði mbl.is á að verða sýnileg
strax í stað þess að framleiða trúverðuga en ranga tölu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class UtdrattarVilla(RuntimeError):
    """Væntanlegt mynstur fannst ekki eða gaf ósamræmda niðurstöðu.

    Heitir ``ExtractionError`` í upprunaverkefninu; hlutverkið er hið sama.
    """


# --- 1. Einstakar fréttir -------------------------------------------------
# Fangar fasta upphafshlutann, flokk, dagsetningu og mislangt slóðarnafn.
# Bæði afstæðar og algildar mbl.is-slóðir eru leyfðar. Fyrirsögn og mynd eru
# ekki hluti af mynstrinu, svo frétt án myndar telst með — en leiðsögu- og
# flokkahlekkir án dagsetningar teljast ekki.
MYNSTUR_FRETTASLOD = re.compile(
    r"""
    href\s*=\s*["']
    (?:https?://(?:www\.)?mbl\.is)?
    (?P<path>/frettir/[a-z][a-z0-9_-]*/\d{4}/\d{2}/\d{2}/[a-z0-9_-]+/)
    (?=["'?\#])
    """,
    re.VERBOSE,
)

# --- 2. Hitastig í Reykjavík ----------------------------------------------
# Byrjar á valinni Reykjavík í veðurkassanum og leitar aðeins innan
# HITAGLUGGI stafa að value og unit. Sú afmörkun minnkar hættuna á að hiti
# annarrar borgar verði tekinn. -? leyfir frost og aukastafurinn má vera
# punktur eða komma; gráðumerkið má vera bókstaflegt eða HTML-tákn.
HITAGLUGGI = 2000

MYNSTUR_HITI_REYKJAVIK = re.compile(
    rf"""
    <option\b(?=[^>]*\bselected\b)[^>]*>\s*Reykjavík\s*</option>
    [\s\S]{{0,{HITAGLUGGI}}}?
    <span\b(?=[^>]*\bclass\s*=\s*["'][^"']*\bvalue\b[^"']*["'])[^>]*>
    \s*(?P<temperature>-?\d+(?:[.,]\d+)?)\s*</span>
    \s*
    <span\b(?=[^>]*\bclass\s*=\s*["'][^"']*\bunit\b[^"']*["'])[^>]*>
    \s*(?:&deg;|&\#176;|°)\s*</span>
    """,
    re.VERBOSE,
)

# --- 3. Gengi Bandaríkjadals ----------------------------------------------
# Sýnilegi USD-innsláttarreiturinn er tómur í HTML-svarinu; raungildið liggur
# neðar í JavaScript. Því eru script-blokkir afmarkaðar fyrst og aðeins leitað
# innan þeirra.
MYNSTUR_SCRIPT_BLOKK = re.compile(r"<script\b[^>]*>(?P<body>[\s\S]*?)</script\s*>")

# Array-vísirinn er ekki festur við ákveðna tölu, því röð gjaldmiðla getur
# breyst. Gæsalappir verða að vera þær sömu beggja vegna gildisins.
MYNSTUR_USD_GENGI = re.compile(
    r"""
    \barrCurrency\s*\[\s*\d+\s*\]\s*=\s*
    new\s+MakeItem\s*\(\s*
    (?P<code_quote>["'])USD(?P=code_quote)\s*,\s*
    (?P<rate_quote>["'])(?P<rate>-?\d+(?:\.\d+)?)(?P=rate_quote)
    \s*\)\s*;?
    """,
    re.VERBOSE,
)

# --- 4. Sýnileg orð --------------------------------------------------------
# Blokkir sem skila engum sýnilegum texta eru fjarlægðar með innihaldinu, í
# þessari röð. Röðin skiptir máli: <head> er tekið á undan <script> svo
# script-blokk inni í hausnum slíti ekki hausinn í sundur.
OSYNILEGAR_BLOKKIR = ("head", "script", "style", "template", "noscript")

MYNSTUR_ATHUGASEMD = re.compile(r"<!--[\s\S]*?-->")

# Ólokið tagg nær til enda skjalsins — annars læki forritskóði inn í textann.
MYNSTUR_OSYNILEGT = (MYNSTUR_ATHUGASEMD,) + tuple(
    re.compile(rf"<{tag}\b[^>]*>[\s\S]*?(?:</{tag}\s*>|$)", re.IGNORECASE)
    for tag in OSYNILEGAR_BLOKKIR
)

MYNSTUR_TAGG = re.compile(r"<[^>]*>")

# Leyfir íslenska stafi og innri bandstrik en hvorki tölur né undirstrik.
MYNSTUR_ORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")

# --- 5. Auglýsingareitir ---------------------------------------------------
# Auðkennið er fangað í JavaScript-renderbeiðninni; tvítekin auðkenni eru
# aðeins talin einu sinni.
MYNSTUR_AUGLYSINGAREITUR = re.compile(
    r"""
    \bAds\.renderSlot\s*\(\s*
    ["'](?P<slot>\d+(?:-\d+)*)["']\s*,
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Spurning:
    """Ein af spurningunum fimm: auðkenni, texti, eining og takmarkanir."""

    numer: int
    lykill: str
    texti: str
    eining: str | None
    takmarkanir: str


SPURNINGAR: tuple[Spurning, ...] = (
    Spurning(
        numer=1,
        lykill="einstakar-frettir",
        texti="Hversu margar einstakar fréttir eru á síðunni?",
        eining="fréttir",
        takmarkanir=(
            "Sama grein getur tengst bæði úr mynd og fyrirsögn, svo slóðirnar "
            "eru afritahreinsaðar í birtingarröð. Leiðsögu- og flokkahlekkir án "
            "dagsetningar teljast ekki með."
        ),
    ),
    Spurning(
        numer=2,
        lykill="hitastig-reykjavik",
        texti="Hvert er hitastigið í Reykjavík?",
        eining="°C",
        takmarkanir=(
            "Talan er lesin úr veðurkassa forsíðunnar á sóknarstundu og lýsir "
            "aðeins því augnabliki. Leitin er bundin við "
            f"{HITAGLUGGI} stafa glugga eftir valinni Reykjavík svo hiti "
            "annarrar borgar slæðist ekki með."
        ),
    ),
    Spurning(
        numer=3,
        lykill="gengi-usd",
        texti="Hvert er gengi Bandaríkjadals?",
        eining="ISK á USD",
        takmarkanir=(
            "Sýnilegi innsláttarreiturinn í HTML-svarinu er tómur; gildið kemur "
            "úr JavaScript-blokk og er gengi mbl.is á sóknarstundu, ekki "
            "opinbert miðgengi."
        ),
    ),
    Spurning(
        numer=4,
        lykill="synileg-ord",
        texti="Hversu mörg sýnileg orð eru á síðunni?",
        eining="orð",
        takmarkanir=(
            "„Sýnilegt“ merkir hér texta sem stendur eftir í kyrrstæða "
            "HTML-svarinu. Regluleg segð reiknar hvorki CSS-sýnileika á "
            "ákveðinni skjástærð né breytingar sem JavaScript gerir á DOM-inu. "
            "Flokkaheiti úr leiðsögn eru talin eins og fréttatexti."
        ),
    ),
    Spurning(
        numer=5,
        lykill="auglysingareitir",
        texti="Hversu margir auglýsingareitir eru skilgreindir?",
        eining="reitir",
        takmarkanir=(
            "Talan er fjöldi skilgreindra eða umbeðinna reita, ekki staðfestur "
            "fjöldi auglýsinga sem birtust: reitirnir eru tómir í kyrrstæða "
            "svarinu og skjástærð, samþykki, auglýsingavörn og val "
            "auglýsingakerfisins ráða því hvað birtist."
        ),
    ),
)

SPURNING_EFTIR_LYKLI: dict[str, Spurning] = {s.lykill: s for s in SPURNINGAR}


def flaggaheiti(mynstur: re.Pattern[str]) -> str:
    """Skilar flöggum þýdds mynsturs sem lesanlegum texta, t.d. ``UNICODE|VERBOSE``.

    Flöggin fara í grunninn með mynstrinu því sama mynstur gefur aðra
    niðurstöðu undir öðrum flöggum — án þeirra er talan ekki endurreiknanleg.
    """
    nofn = [flagg.name for flagg in re.RegexFlag if flagg.name and mynstur.flags & flagg]
    return "|".join(sorted(nofn))
