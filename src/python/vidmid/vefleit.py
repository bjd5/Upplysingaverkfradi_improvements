"""Leit að handritslínum í HTML- og JSON-skrám — trénu og frosna viðmiðinu.

Hluti af handritsleitinni (`handritsleit.py`). Talnaskrárnar eru skannaðar reit
fyrir reit; hér er hins vegar leitað í **öllum** HTML- og JSON-skrám — texta,
`<pre>`/`<code>`, `<script>` og eigindagildum — að einu mynstri: **tilsvari í
handritasniði**, `Nafn: texti`, sem er á ensku. Leitað er á tveimur stöðum:

1. **Í trénu** (`handritsreitir.VEFMOPPUR`: `web/`, `docs/`, `data/processed/`).
   Þar er **ekkert** undanþegið: hvert tilsvar fellir leitina.
2. **Í frosna viðmiðinu** — byggðu gömlu síðunni sem var tekin úr trénu
   28.9.2026 og er aðeins í commit `handritsreitir.FROSID_COMMIT` (git-tagið
   `vidmid-frosid`). Ákvörðun (b) í issue #3 (28.9.2026): orðréttu línurnar úr
   þætti 0101 sem síðan birtir sem dæmi um þáttarann standa sem stutt
   tilvitnun. Þær eru undanþegnar **ein og ein** með skrá, SHA-256 línunnar og
   fjölda tilvika (`handritsreitir.VEFUNDANTEKNINGAR`); textinn sjálfur er
   hvergi afritaður í kóðann. Hver ný lína — og hver undanþegin lína sem
   breytist um eitt orð — fær nýja summu og fellir leitina.

**Hvað telst tilsvar.** `Nafn:` (eitt til fjögur hástafsorð, t.d.
`Monica and Phoebe:`) og á eftir textinn fram að næsta `Nafn:` eða enda
einingar. Textinn er skorinn við fyrsta orð með íslenskum staf, svo að
íslenskur meginmálstexti á eftir tilvitnun (algengt í `search.json`) teljist
ekki með. Tilsvarið telst **enskt** ef það geymir minnst eitt algengt enskt
kerfisorð (`ENSK_KERFISORD`) eftir að svigainnskot og slóðir eru fjarlægð —
sama regla og þáttarinn: `(hlær)` er sviðsleiðbeining, ekki talað orð.
Íslenskar merkingar (`Heimild: …`, `Nafn: texti`) standast því.

**Afmörkun.** Tilsvar án nokkurs ensks kerfisorðs (t.d. tveggja orða upphrópun)
finnst ekki, og ekki heldur handritstexti sem er birtur án `Nafn:`. Sjá
docs/adferdafraedi.md, kafla 1.5.2.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
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


def einingar_texta(texti: str, vidauki: str) -> list[str]:
    """Textaeiningar: línur texta, kóða og eigindagilda (HTML) eða strengja (JSON)."""
    if vidauki == ".html":
        lesari = _Einingalesari()
        lesari.feed(texti)
        lesari.close()
        return lesari.einingar
    if vidauki == ".json":
        return [lina for s in _strengir(json.loads(texti)) for lina in s.split("\n")]
    raise ValueError(f"Óþekkt skráarsnið: {vidauki}")


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


# (birt slóð, viðauki, texti) — sama hvort skráin er á diski eða í git-commiti.
Heimild = tuple[str, str, str]
Frava = tuple[str, str, str]


def skrar(mappa: Path) -> list[Path]:
    """Allar HTML- og JSON-skrár í möppunni og undirmöppum hennar."""
    return sorted(p for p in mappa.rglob("*") if p.is_file() and p.suffix in VEF_VIDAUKAR)


def ur_trenu(rot: Path, moppur: tuple[str, ...]) -> tuple[list[Heimild], list[str]]:
    """HTML- og JSON-skrár í möppunum, og möppur sem vantar."""
    heimildir: list[Heimild] = []
    vantar: list[str] = []
    for mappa in moppur:
        if not (rot / mappa).is_dir():
            vantar.append(mappa)
            continue
        for slod in skrar(rot / mappa):
            heimildir.append((slod.relative_to(rot).as_posix(), slod.suffix,
                              slod.read_text(encoding="utf-8")))
    return heimildir, vantar


def ur_commiti(rot: Path, commit: str, slodir: list[str]) -> list[Heimild] | None:
    """Skrárnar eins og þær eru í git-commiti; None ef commit-ið er ekki tiltækt.

    Grunnt klón (`--depth`) geymir ekki frosna commit-ið. Það er ekki merki um
    handritstexta, svo kallandinn skráir það sem viðvörun, ekki frávik.
    """
    if shutil.which("git") is None:
        return None
    til = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                         cwd=rot, capture_output=True, check=False)
    if til.returncode != 0:
        return None
    heimildir: list[Heimild] = []
    for slod in slodir:
        texti = subprocess.run(["git", "show", f"{commit}:{slod}"], cwd=rot,
                               capture_output=True, check=True).stdout.decode("utf-8")
        heimildir.append((slod, Path(slod).suffix, texti))
    return heimildir


def fundin_tilsvor(
    heimildir: list[Heimild],
) -> tuple[Counter[tuple[str, str]], dict[tuple[str, str], int]]:
    """Tilsvör: tilvik á (slóð, SHA-256) og orðafjöldi hvers."""
    fundin: Counter[tuple[str, str]] = Counter()
    lengd: dict[tuple[str, str], int] = {}
    for birt, vidauki, texti in heimildir:
        for eining in einingar_texta(texti, vidauki):
            for lina in tilsvor(eining):
                lykill = (birt, sha_linu(lina))
                fundin[lykill] += 1
                lengd[lykill] = len(lina.split())
    return fundin, lengd


def bera_saman(
    heimildir: list[Heimild], undantekningar: dict[tuple[str, str], tuple[int, str]]
) -> tuple[list[Frava], int]:
    """Ber fundin tilsvör við frystar undanþágur; skilar frávikum og fjölda tilsvara.

    Frávik eru (slóð, staður, skýring) — aldrei textinn sjálfur. Frávik er:
    tilsvar sem er ekki undanþegið, undanþegið tilsvar sem kemur fyrir oftar eða
    sjaldnar en skráð er, eða undanþága sem finnst ekki.
    """
    fundin, lengd = fundin_tilsvor(heimildir)
    fravik: list[Frava] = []
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
    return fravik, sum(fundin.values())


def leita(
    rot: Path,
    moppur: tuple[str, ...],
    commit: str,
    undantekningar: dict[tuple[str, str], tuple[int, str]],
) -> tuple[list[Frava], dict[str, int]]:
    """Tréð án undanþágu, og frosna commit-ið með frystu undanþágunum."""
    heimildir, vantar = ur_trenu(rot, moppur)
    fravik: list[Frava] = [("(staðsetning)", "-", f"Mappa sem á að skanna er ekki til: {m}")
                           for m in vantar]
    tre_fravik, tre_tilsvor = bera_saman(heimildir, {})
    fravik.extend(tre_fravik)

    frosnar = ur_commiti(rot, commit, sorted({slod for slod, _ in undantekningar}))
    frosin_tilsvor = 0
    if frosnar is not None:
        frosin_fravik, frosin_tilsvor = bera_saman(frosnar, undantekningar)
        fravik.extend(frosin_fravik)

    talning = {
        "vefskrar": len(heimildir),
        "tilsvor_i_trenu": tre_tilsvor,
        "frosid_tiltaekt": int(frosnar is not None),
        "frosin_tilsvor": frosin_tilsvor,
        "vefundantekningar": len(undantekningar),
    }
    return fravik, talning


def lysing(talning: dict[str, int], commit: str) -> list[tuple[bool, str]]:
    """Skilaboð um niðurstöðuna: (allt tiltækt?, texti) — án fundins texta."""
    skilabod = [(True, f"{talning.get('vefskrar', 0)} HTML/JSON-skrár í trénu — "
                       "ekkert tilsvar í handritasniði")]
    if talning.get("frosid_tiltaekt"):
        skilabod.append((True, f"Frosna viðmiðið ({commit[:7]}): "
                               f"{talning['frosin_tilsvor']} tilsvör, öll "
                               f"{talning['vefundantekningar']} frystar undanþágur "
                               "(issue #3, ákvörðun b), engin ný"))
    else:
        skilabod.append((False, f"Frosna commit-ið {commit[:7]} er ekki í klóninu — "
                                "undanþágurnar úr ákvörðun (b) voru ekki bornar við "
                                "það (sæktu fulla sögu: git fetch --unshallow)"))
    return skilabod
