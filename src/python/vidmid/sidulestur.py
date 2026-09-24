"""Les textablokkir með samhengi úr byggðri Quarto-síðu.

Gamla síðan er Quarto-úttak: efnið liggur inni í <main id="quarto-document-content">
og umgjörðin (valmynd, brauðmylsna, leitarform, fótur) utan um það. Þess vegna er
aðeins lesið innan <main> — það heldur dagsetningum í fæti og hnappatextum úti án
þess að þurfa svartan lista.

Hver blokk sem kemur út veit hvar hún stóð: fyrirsagnakeðjuna fyrir ofan sig og,
ef hún er töflusella, heiti töflunnar, röðina og dálkinn. Það samhengi er það sem
gerir tölu að niðurstöðu fremur en að tölustaf (verklýsing P0.2).

Eingöngu html.parser úr staðalsafninu — engin bs4, engin lxml (regla 10).
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import NamedTuple

# Tóm merki senda aldrei lokamerki; dýptartalningin má ekki telja þau.
TOM_MERKI = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})

# Umgjörð Quarto sem er ekki efni: brauðmylsna, afritunarhnappar, táknmyndir,
# og <script>/<style> sem geyma kóða en ekki texta til lestrar.
HUNSA_MERKI = frozenset({"script", "style", "nav", "button", "i", "svg"})

# Merki sem loka textablokk. Allt annað (strong, em, a, code, span) er innlínu
# og safnast í sömu blokk — annars klofnaði „334 yfirfarna skjálfta" í þrennt.
BLOKKARMERKI = frozenset({
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "dt", "dd", "caption",
    "pre", "blockquote", "figcaption", "div", "td", "th", "tr", "table",
    "section", "header", "ul", "ol", "dl", "details", "summary", "figure",
})

FYRIRSAGNIR = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
EFNISMERKI = "quarto-document-content"


class Blokk(NamedTuple):
    """Ein textablokk með öllu samhengi sem HTML-ið gefur um hana."""

    flokkur: str                 # fyrirsogn|malsgrein|listi|tafla|kodi|mynd|uttak
    texti: str
    kafli: tuple[str, ...]       # fyrirsagnakeðjan fyrir ofan blokkina
    tafla: str | None = None     # heiti töflunnar (caption eða undanfari)
    lina: str | None = None      # merking röðarinnar
    sulka: str | None = None     # merking dálksins


class _Tafla:
    """Söfnunarstaða einnar töflu á meðan parsarinn gengur gegnum hana."""

    def __init__(self, undanfari: str | None) -> None:
        self.heiti = undanfari
        self.caption: list[str] = []
        self.sulkur: list[str] = []
        self.radir: list[list[tuple[str, str]]] = []
        self.rod: list[tuple[str, str]] = []
        self.i_haus = False

    def nafn(self) -> str | None:
        if self.caption:
            return " ".join(" ".join(self.caption).split())
        return self.heiti


def _radarmerking(rod: list[tuple[str, str]]) -> str | None:
    """Merking röðar: fyrsti reitur, auk þeirra næstu sem eru merkingar en tölur.

    Töflur hafa oft tvo merkingardálka (Námssvið + Kyn). Væri aðeins fyrsti
    reiturinn notaður yrðu „Karlar 70,3" og „Konur 75,9" bæði merkt „Alls" og
    tölurnar óaðgreinanlegar.
    """
    if not rod:
        return None
    merkingar = [rod[0][1]]
    for _, texti in rod[1:]:
        if any(c.isdigit() for c in texti):
            break
        merkingar.append(texti)
    return " · ".join(m for m in merkingar if m)


class Sidulesari(HTMLParser):
    """Gengur gegnum eina HTML-síðu og safnar textablokkum úr <main>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blokkir: list[Blokk] = []
        self.titill: str | None = None
        self._inni = False
        self._dypt = 0
        self._hunsa = 0
        self._bidminni: list[str] = []
        self._flokkur = "malsgrein"
        self._fyrirsagnastig: int | None = None
        self._kafli: dict[int, str] = {}
        self._toflur: list[_Tafla] = []
        self._sella: str | None = None
        self._sidasta_malsgrein: str | None = None

    # — opinbert —

    def lesa(self, html: str) -> list[Blokk]:
        """Skilar öllum textablokkum síðunnar í þeirri röð sem þær stóðu."""
        self.feed(html)
        self.close()
        self._skola()
        return self.blokkir

    # — innri vinnsla —

    def _kedja(self) -> tuple[str, ...]:
        return tuple(self._kafli[s] for s in sorted(self._kafli))

    def _skola(self) -> None:
        """Lokar yfirstandandi textablokk og skráir hana ef hún hefur innihald."""
        texti = " ".join(" ".join(self._bidminni).split())
        self._bidminni = []
        if not texti:
            return
        if self._toflur and self._sella:
            self._toflur[-1].rod.append((self._sella, texti))
            return
        if self._toflur:
            self._toflur[-1].caption.append(texti)
            return
        if self._fyrirsagnastig is not None:
            stig = self._fyrirsagnastig
            self._kafli = {s: t for s, t in self._kafli.items() if s < stig}
            self._kafli[stig] = texti
            if stig == 1 and self.titill is None:
                self.titill = texti
            self.blokkir.append(Blokk("fyrirsogn", texti, self._kedja()))
            return
        if self._flokkur == "malsgrein":
            self._sidasta_malsgrein = texti
        self.blokkir.append(Blokk(self._flokkur, texti, self._kedja()))

    def _loka_toflu(self) -> None:
        tafla = self._toflur.pop()
        nafn = tafla.nafn()
        for rod in tafla.radir:
            merking = _radarmerking(rod)
            for i, (merki, texti) in enumerate(rod):
                sulka = tafla.sulkur[i] if i < len(tafla.sulkur) else None
                if merki == "th" and not tafla.sulkur:
                    continue
                self.blokkir.append(Blokk(
                    "tafla", texti, self._kedja(), nafn,
                    None if i == 0 else merking, sulka,
                ))

    # — HTMLParser —

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        eig = {k: (v or "") for k, v in attrs}
        if not self._inni:
            if eig.get("id") == EFNISMERKI:
                self._inni, self._dypt = True, 1
            return
        if self._hunsa:
            if tag not in TOM_MERKI:
                self._hunsa += 1
            return
        if tag in HUNSA_MERKI:
            self._skola()
            self._hunsa = 1
            return
        if tag not in TOM_MERKI:
            self._dypt += 1

        if tag in BLOKKARMERKI:
            self._skola()
        klasar = eig.get("class", "").split()
        if tag == "table":
            self._toflur.append(_Tafla(self._sidasta_malsgrein))
        elif tag == "thead" and self._toflur:
            self._toflur[-1].i_haus = True
        elif tag == "tr" and self._toflur:
            self._toflur[-1].rod = []
        elif tag in ("td", "th") and self._toflur:
            self._sella = tag
        elif tag in FYRIRSAGNIR:
            self._fyrirsagnastig = FYRIRSAGNIR[tag]
        elif tag == "pre":
            self._flokkur = "uttak" if "cell-output" in klasar else "kodi"
        elif tag == "li":
            self._flokkur = "listi"
        elif tag == "figcaption":
            self._flokkur = "mynd"
        elif tag in ("p", "div", "blockquote", "dd", "dt"):
            if "cell-output" in klasar:
                self._flokkur = "uttak"
            elif self._flokkur in ("kodi", "uttak", "listi", "mynd"):
                self._flokkur = "malsgrein"

    def handle_endtag(self, tag: str) -> None:
        if not self._inni:
            return
        if self._hunsa:
            self._hunsa -= 1
            return
        if tag in BLOKKARMERKI:
            self._skola()
        if tag in ("td", "th"):
            self._sella = None
        elif tag == "tr" and self._toflur:
            tafla = self._toflur[-1]
            if tafla.i_haus and not tafla.sulkur:
                tafla.sulkur = [t for _, t in tafla.rod]
            elif tafla.rod:
                tafla.radir.append(tafla.rod)
            tafla.rod = []
        elif tag == "thead" and self._toflur:
            self._toflur[-1].i_haus = False
        elif tag == "table" and self._toflur:
            self._loka_toflu()
        elif tag in FYRIRSAGNIR:
            self._fyrirsagnastig = None
        elif tag in ("pre", "li", "figcaption"):
            self._flokkur = "malsgrein"

        if tag not in TOM_MERKI:
            self._dypt -= 1
            if self._dypt <= 0:
                self._skola()
                self._inni = False

    def handle_data(self, data: str) -> None:
        if self._inni and not self._hunsa and data.strip():
            self._bidminni.append(data.strip())
