"""Leit að handritslínum í byggðu gömlu síðunni (`docs/vidmid/vefur/`).

Hluti af handritsleitinni (`handritsleit.py`). Talnaskrárnar eru skannaðar reit
fyrir reit; hér er hins vegar leitað í **öllum** HTML- og JSON-skrám byggðu
síðunnar — texta, `<pre>`/`<code>`, `<script>` og eigindagildum — að einu
mynstri: **tilsvari í handritasniði**, `Nafn: texti`, sem er á ensku.

Ákvörðun (b) í issue #3 (28.9.2026): orðréttu línurnar úr þætti 0101 sem gamla
síðan birtir sem dæmi um þáttarann mega standa sem stutt tilvitnun. Þær eru
undanþegnar **ein og ein**, auðkenndar með skrá og SHA-256 af línunni sjálfri
og með fjölda tilvika (`handritsreitir.VEFUNDANTEKNINGAR`). Textinn sjálfur er
hvergi afritaður í kóðann. Hver ný lína — og hver undanþegin lína sem breytist
um eitt orð — fær nýja summu og fellir leitina.

**Hvað telst tilsvar.** `Nafn:` (eitt til fjögur hástafsorð, t.d.
`Monica and Phoebe:`) og á eftir textinn fram að næsta `Nafn:` eða enda
einingar. Textinn er skorinn við fyrsta orð með íslenskum staf, svo að
íslenskur meginmálstexti á eftir tilvitnun (algengt í `search.json`) teljist
ekki með. Tilsvarið telst **enskt** ef það geymir minnst eitt algengt enskt
kerfisorð (`ENSK_KERFISORD`) eftir að svigainnskot eru fjarlægð — sama regla
og þáttarinn: `(hlær)` er sviðsleiðbeining, ekki talað orð. Íslensku
merkingarnar á síðunni (`Heimild: …`, `Nafn: texti`) standast því.

**Afmörkun.** Tilsvar án nokkurs ensks kerfisorðs (t.d. tveggja orða upphrópun)
finnst ekki, og ekki heldur handritstexti sem er birtur án `Nafn:`. Sjá
docs/adferdafraedi.md, kafla 1.5.2.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterator

VEF_VIDAUKAR = (".html", ".json")

# Merki sem brjóta texta í einingar: blokkir, línuskil og <code>, svo innfelld
# tilvitnun (`<code>All: …</code>` inni í málsgrein) verði sín eigin eining.
BLOKKAMERKI = frozenset({
    "address", "article", "blockquote", "br", "code", "dd", "div", "dl", "dt",
    "figcaption", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li",
    "main", "nav", "ol", "p", "pre", "script", "section", "style", "table",
    "td", "th", "tr", "ul",
})

# Ræðumaður: eitt hástafsorð, mögulega með punkti (`Mrs.`), og allt að þrjú í
# viðbót tengd með `and`, `&`, kommu eða bili.
RAEDUMADUR = re.compile(
    r"(?<![\w'’])(?P<nafn>[A-Z][a-z]+\.?(?:(?: and | & |, | )[A-Z][a-z]+\.?){0,3})"
    r":[ \t]+(?=\S)"
)
ISLENSKUR_STAFUR = re.compile(r"[áðéíóúýþæöÁÐÉÍÓÚÝÞÆÖ]")
SVIGAINNSKOT = re.compile(r"\([^()]*\)")
# Slóðir eru ekki tal: `vedur.is` myndi annars gefa enska orðið „is“.
SLOD = re.compile(r"\S+://\S+")
ENSKT_ORD = re.compile(r"[a-z][a-z'’]*")
BIL = re.compile(r"\s+")

# Algeng ensk kerfisorð sem eru ekki íslensk orð án kommu. Eitt nægir: markmiðið
# er að greina enskt tilsvar frá íslenskri merkingu, ekki að meta enskuna.
ENSK_KERFISORD = frozenset({
    "a", "about", "all", "and", "are", "be", "but", "can", "did", "do", "does",
    "don't", "for", "going", "gonna", "got", "had", "has", "have", "he", "her",
    "him", "his", "i", "i'm", "is", "it", "it's", "just", "know", "like", "me",
    "my", "no", "not", "of", "oh", "okay", "on", "she", "so", "that", "the",
    "there", "there's", "they", "this", "to", "was", "we", "what", "with",
    "yeah", "yes", "you", "you're", "your",
})


class _Einingalesari(HTMLParser):
    """Safnar textaeiningum úr HTML: texta milli blokkamerkja og eigindagildum."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._bidminni: list[str] = []
        self.einingar: list[str] = []

    def _tæma(self) -> None:
        self.einingar.extend("".join(self._bidminni).split("\n"))
        self._bidminni = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOKKAMERKI:
            self._tæma()
        for _, gildi in attrs:
            if gildi:
                self.einingar.extend(gildi.split("\n"))

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOKKAMERKI:
            self._tæma()

    def handle_data(self, data: str) -> None:
        self._bidminni.append(data)

    def close(self) -> None:
        super().close()
        self._tæma()


def _strengir(hlutur: object) -> Iterator[str]:
    """Öll strengjagildi JSON-trés."""
    if isinstance(hlutur, dict):
        for gildi in hlutur.values():
            yield from _strengir(gildi)
    elif isinstance(hlutur, list):
        for gildi in hlutur:
            yield from _strengir(gildi)
    elif isinstance(hlutur, str):
        yield hlutur


def einingar(slod: Path) -> list[str]:
    """Textaeiningar skráar: línur texta, kóða og eigindagilda."""
    texti = slod.read_text(encoding="utf-8")
    if slod.suffix == ".html":
        lesari = _Einingalesari()
        lesari.feed(texti)
        lesari.close()
        return lesari.einingar
    if slod.suffix == ".json":
        return [lina for s in _strengir(json.loads(texti)) for lina in s.split("\n")]
    raise ValueError(f"Óþekkt skráarsnið: {slod}")


def _skera_vid_islensku(texti: str) -> str:
    """Texti fram að fyrsta orði með íslenskum staf."""
    ord_ = texti.split()
    for visir, eitt in enumerate(ord_):
        if ISLENSKUR_STAFUR.search(eitt):
            return " ".join(ord_[:visir])
    return " ".join(ord_)


def enskt(texti: str) -> bool:
    """Geymir textinn — án svigainnskota og slóða — enskt kerfisorð?"""
    hreinn = SLOD.sub(" ", SVIGAINNSKOT.sub(" ", texti))
    ord_ = ENSKT_ORD.findall(hreinn.lower())
    return any(eitt in ENSK_KERFISORD for eitt in ord_)


def tilsvor(eining: str) -> list[str]:
    """Ensk tilsvör í handritasniði í einni textaeiningu, með stöðluðum bilum."""
    samsvaranir = list(RAEDUMADUR.finditer(eining))
    fundin: list[str] = []
    for visir, samsvorun in enumerate(samsvaranir):
        endir = samsvaranir[visir + 1].start() if visir + 1 < len(samsvaranir) else None
        texti = _skera_vid_islensku(eining[samsvorun.end():endir])
        if texti and enskt(texti):
            fundin.append(BIL.sub(" ", f"{samsvorun['nafn']}: {texti}").strip())
    return fundin


def sha_linu(lina: str) -> str:
    """SHA-256 tilsvars eins og `tilsvor` skilar því."""
    return hashlib.sha256(lina.encode("utf-8")).hexdigest()


def skrar(mappa: Path) -> list[Path]:
    """Allar HTML- og JSON-skrár í möppunni og undirmöppum hennar."""
    return sorted(p for p in mappa.rglob("*") if p.is_file() and p.suffix in VEF_VIDAUKAR)


def fundin_tilsvor(
    rot: Path, mappa: str
) -> tuple[Counter[tuple[str, str]], dict[tuple[str, str], int], int]:
    """Tilsvör í möppunni: tilvik á (slóð, SHA-256), orðafjöldi hvers, fjöldi skráa."""
    fundin: Counter[tuple[str, str]] = Counter()
    lengd: dict[tuple[str, str], int] = {}
    skannadar = skrar(rot / mappa)
    for slod in skannadar:
        birt = slod.relative_to(rot).as_posix()
        for eining in einingar(slod):
            for lina in tilsvor(eining):
                lykill = (birt, sha_linu(lina))
                fundin[lykill] += 1
                lengd[lykill] = len(lina.split())
    return fundin, lengd, len(skannadar)


def leita(
    rot: Path, mappa: str, undantekningar: dict[tuple[str, str], tuple[int, str]]
) -> tuple[list[tuple[str, str, str]], dict[str, int]]:
    """Skannar möppuna og ber fundin tilsvör við frystu undanþágurnar.

    Skilar frávikum sem (slóð, staður, skýring) — aldrei textanum sjálfum — og
    talningu. Frávik er: tilsvar sem er ekki undanþegið, undanþegið tilsvar sem
    kemur fyrir oftar eða sjaldnar en skráð er, eða undanþága sem finnst ekki.
    """
    if not (rot / mappa).is_dir():
        return [("(staðsetning)", "-", f"Mappa sem á að skanna er ekki til: {mappa}")], {}

    fundin, lengd, fjoldi_skraa = fundin_tilsvor(rot, mappa)
    fravik: list[tuple[str, str, str]] = []
    for lykill, fjoldi in sorted(fundin.items()):
        skrad = undantekningar.get(lykill)
        if skrad is None:
            fravik.append((lykill[0], f"sha256 {lykill[1][:16]}",
                           f"handritslína í tilsvarasniði: {lengd[lykill]} orð, "
                           f"{fjoldi} tilvik (ekkert undanþegið)"))
        elif skrad[0] != fjoldi:
            fravik.append((lykill[0], f"sha256 {lykill[1][:16]}",
                           f"undanþegin lína kemur fyrir {fjoldi} sinnum en "
                           f"skráð er {skrad[0]}"))
    for lykill in sorted(set(undantekningar) - set(fundin)):
        fravik.append((lykill[0], f"sha256 {lykill[1][:16]}",
                       "undanþegin lína finnst ekki — dauð færsla eða breytt lína"))

    talning = {
        "vefskrar": fjoldi_skraa,
        "tilsvor": sum(fundin.values()),
        "vefundantekningar": len(undantekningar),
    }
    return fravik, talning
