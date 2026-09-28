"""Skilgreiningar fyrir handritsleitina: hvað er skannað og hvað er undanþegið.

Aðskilið frá `handritsleit.py` af sömu ástæðu og `sofn.py` er aðskilið frá
`provenance.py`: leitarreglan er kóði sem má lesa í einu, en undanþágurnar eru
**skjalfest ákvörðun** sem verður að vera hægt að lesa og vefengja eina og sér.

Sjá docs/adferdafraedi.md, kafla 1.5.2, fyrir röksemdina að baki þröskuldunum
og afmörkun leitarinnar.
"""

from __future__ import annotations

from dataclasses import dataclass

# Allar Friends-TALNASKRÁR sem eru í git. Þrjú afrit af tölfræðinni eru í
# repo-inu: vinnugagnið, frosna viðmiðið, og eintakið inni í byggðu gömlu
# síðunni sem Observable Plot las. Leitin nær til allra þriggja.
#
# Byggðu síðurnar í docs/vidmid/vefur/ (HTML og search.json) eru skannaðar
# sérstaklega eftir tilsvörum í handritasniði — sjá `VEFMAPPA` neðst og
# `vefleit.py`.
MOPPUR = (
    "data/processed/phoebe-stats",
    "docs/vidmid/phoebe-stats",
    "docs/vidmid/vefur/friends/phoebe-stats",
)
STAKAR_SKRAR = ("docs/vidmid/generated/phoebe-central-perk-summary.json",)

VIDAUKAR = (".json", ".csv")

# Þröskuldurinn fyrir gagnareiti: strengur með fleiri en fimm orðum er ekki
# talning heldur texti. Fimm er mælt hámark þeirra gagnareita sem eru í
# skránum (hæst `.units.share_pct` í phoebe-screentime-by-season.json og
# `.question` í phoebe-extra-stats.json),
# og lengsti strengurinn í `signature-phrases.csv` — reitnum sem er næst því
# að vera tilvitnun — er þrjú orð. Til samanburðar er meðaltilsvar í
# handritunum 11,2 orð (Phoebe) og 10,7 orð (hinir fimm), skv. `summary.json`.
# Þakið er því **undir hálfu** meðaltilsvari: brot úr tilsvari fellir prófið.
ORDATHAK_GAGNAREITS = 5


@dataclass(frozen=True)
class Undantekning:
    """Reitur sem má brjóta almennu regluna, með ástæðu og frystu innihaldi.

    `sha256` er reiknað af öllum gildum reitsins í skránni, skeytt saman með
    línuskilum. Undanþágan er þannig **fryst**: reitur sem er undanþeginn í dag
    getur ekki orðið felustaður á morgun án þess að prófið falli.
    """

    flokkur: str  # "skjolun" eða "titill"
    astaeda: str
    sha256: str


# Undanþágurnar eru auðkenndar með (skráarnafni, reit) en ekki fullri slóð:
# afritin þrjú geyma sömu gildi í þessum reitum og prófið staðfestir það
# sérstaklega. Tvær skrár eru ólíkar milli afrita (`_meta.json` í tímastimpli,
# `phoebe-top-talkers.json` í röðun — skjalfest í docs/vidmid/README.md,
# kafla 2), en hvorugur munurinn er í undanþegnum reit.
SKJOLUN = "skjolun"
TITILL = "titill"

_AST_ADFERD = "Aðferðarlýsing verkefnisins sjálfs, á íslensku — ekki úr handriti."
_AST_TITILL = "Þáttatitlar. Heiti verks, ekki texti úr því."

UNDANTEKNINGAR: dict[tuple[str, str], Undantekning] = {
    ("_meta.json", ".conventions.group_lines_note"): Undantekning(
        SKJOLUN,
        "Skilgreining á hóplínum; nefnir tvö talnaheiti í gæsalöppum.",
        "3d8cecd19835c846a1fc0dfa7ac006ab14ff97ce5e3856f087411d2b75b9d26b",
    ),
    ("_meta.json", ".conventions.word_definition"): Undantekning(
        SKJOLUN,
        "Skilgreining á orði: reglulega segðin sem talningin notar.",
        "959db4aa4af02508b752c59737c113fe5875fbcdf72d9bcdcf96f2b4ee5f59b8",
    ),
    ("_meta.json", ".source_note"): Undantekning(
        SKJOLUN,
        "Af hverju delvinso-safnið var valið fram yfir fangj.",
        "c75a67a73db1226441920d719fc3a77ed1a80a29754821273aa930fc34d0a6e8",
    ),
    ("phoebe-extra-stats.json", ".bottom_episodes_by_lines[].title"): Undantekning(
        TITILL, _AST_TITILL,
        "61f4baaac6e62b50ce9a98bb8ed214684c98ed7b5244b7b6baffc053b33ca95c",
    ),
    ("phoebe-extra-stats.json", ".distinctive_words_note"): Undantekning(
        SKJOLUN,
        "Aðferð z-gildanna með tilvísun í Monroe, Colaresi & Quinn (2008).",
        "bc0281d665f23e0a2248af84d342e82a9533fb2e2cd72a3c0e8c332f7747b823",
    ),
    ("phoebe-extra-stats.json", ".top_episodes_by_lines[].title"): Undantekning(
        TITILL, _AST_TITILL,
        "142749d4932fd33aec11ee753fb26809c8eca808922cd77ee3b6ace51137176e",
    ),
    ("phoebe-extra-stats.json", ".top_episodes_by_share[].title"): Undantekning(
        TITILL, _AST_TITILL,
        "40b53e2afce35fa367690e362003bc26f181fdaa323bd4fb19f78853d1a26a87",
    ),
    ("phoebe-mentions-by-season.json", ".method"): Undantekning(
        SKJOLUN, _AST_ADFERD,
        "b1ff9322569e618803f13b6c73a7373110532752fb09c7c17a96d6fe750028c8",
    ),
    ("phoebe-mentions-by-season.json", ".question"): Undantekning(
        SKJOLUN, "Rannsóknarspurning greiningarinnar, á íslensku.",
        "5b604ea45859b5f5019a60946efc493f125faae32c4caa773457615ba2bd3cc8",
    ),
    ("phoebe-per-episode.csv", "title"): Undantekning(
        TITILL,
        "Þáttatitlar, 227 raðir — fínasta upplausn gagnanna. Heiti verka.",
        "2edec7bfc0078fd0e323a8eb9d0a1b1c74930c2fcdf7c5917d744ceaba13c369",
    ),
    ("phoebe-screentime-by-season.json", ".method"): Undantekning(
        SKJOLUN, _AST_ADFERD,
        "549161848ac2810e76a5fa95db5aa6fcf8f961525979c97aebfa93a4eeea514d",
    ),
    ("phoebe-screentime-by-season.json", ".question"): Undantekning(
        SKJOLUN, "Rannsóknarspurning greiningarinnar, á íslensku.",
        "febdb8a67291b15f751af4640f8be240aa05c055f141536dc5657255255669ea",
    ),
    ("phoebe-screentime-by-season.json", ".units.speaking_scenes"): Undantekning(
        SKJOLUN, "Einingaskýring fyrir senutalninguna.",
        "eb02c4a6a1ae0e5c7b3dae39146992bc54c537d4995e5d67ee1aec91ac207207",
    ),
    ("phoebe-top-talkers.json", ".headline.tie_note"): Undantekning(
        SKJOLUN,
        "Varnaðarorð um að Monica og Rachel séu innan skekkjumarka.",
        "c911814f8e375d3e8e0399ff75e5e630bde437a1e77945afbd1c192a4b40c5c3",
    ),
    ("phoebe-top-talkers.json", ".method"): Undantekning(
        SKJOLUN, _AST_ADFERD,
        "d5d3faae7777fb498ebc97abb808cf3e737613133e787eb4e3d7f823ca1e2bf9",
    ),
    ("phoebe-top-talkers.json", ".question"): Undantekning(
        SKJOLUN, "Rannsóknarspurning greiningarinnar, á íslensku.",
        "4215e162d8fe4aacd4a90b10bdb1c9090e2a38f0b7288318a5376e48f2c5a1d1",
    ),
    ("summary.json", ".note"): Undantekning(
        SKJOLUN, "Athugasemd um að tölurnar séu raunniðurstöður.",
        "b80f49d8a77a7576129d2f1ebc3092b108f0fb08624b5f0ad4c0e1cef78b415a",
    ),
    ("summary.json", ".source"): Undantekning(
        SKJOLUN, "Stutt lýsing á gagnagrunni greiningarinnar.",
        "933816da3f87e83059478ecffa0491ede9394a60745e391e0363a9a3f502e57a",
    ),
}


# --- Byggða gamla síðan (vefleit.py) --------------------------------------
#
# Ákvörðun (b) í issue #3, 28.9.2026: orðréttu línurnar úr þætti 0101 sem gamla
# síðan birtir sem dæmi um þáttarann standa sem stutt tilvitnun, og git-sagan er
# ekki endurskrifuð. Frosna viðmiðið er SHA-staðfest (docs/vidmid/provenance.json)
# og má ekki breyta. Sjá docs/adferdafraedi.md, kafla 1.5.1–1.5.2.
#
# Undanþágan er FRYST lína fyrir línu: (skrá, SHA-256 línunnar) -> (fjöldi
# tilvika, lýsing án texta). Línan er eins og `vefleit.tilsvor` skilar henni.
# Textinn sjálfur er vísvitandi ekki hér — þá væri hann kominn í enn eina skrá.
# Breytist lína um eitt orð breytist summan og leitin fellur.
#
# Níu línur í hvorri skrá: átta úr `<pre>`-dæminu (sviðslýsingin og sjö tilsvör;
# sviðsleiðbeiningin er án `Nafn:` og greinist ekki) og hóplínan `All:` sem er
# dæmi um undanskildar hóplínur. Í search.json nær hóplínan yfir fyrsta orð
# íslenska textans sem fylgir henni, því Quarto skeytti <code> inn í málsgreinina.
VEFMAPPA = "docs/vidmid/vefur"
_STAT = "docs/vidmid/vefur/friends/phoebe-statistics.html"
_LEIT = "docs/vidmid/vefur/search.json"
_0101 = (
    ("d1ab70e82a447018913479895d27559b1049b1c5067fba11387293b3b6b982b6",
     "0101 <pre> lína 1: sviðslýsing, 9 orð"),
    ("8002cc8651888cfcb632e665016618d3362746b8683bbdccf64e9e1f15e325ad",
     "0101 <pre> lína 2: Monica, 11 orð"),
    ("109e2788e3cf2566077c0369a979e7947dd2e41391ded7da453a54a76876fe07",
     "0101 <pre> lína 3: Joey, 14 orð"),
    ("9a229bd59706e582c8f979befde2cb0e53bc0498406ac6cdb6887c31e9ac516c",
     "0101 <pre> lína 4: Chandler, 16 orð"),
    ("960b26642ed9f0b125b3246eb3be3ba9424583830c0833c47c2bdd8c78c6ef2b",
     "0101 <pre> lína 5: Phoebe, 5 orð"),
    ("6a7fc97f6c7a9356cfc7517fba7efaad78b8759890cfddef6cde52a71866b93a",
     "0101 <pre> lína 7: Phoebe, 16 orð"),
    ("792cb4d5c08dbbc01830a1644a0d5f85f0bad6d32a685c1f64415f93a0f3f5dc",
     "0101 <pre> lína 8: Monica, 21 orð"),
    ("d98b01b0388a584c3e441914888711ab0b247faf5b2fdd9966d7b7b5f45d8ec6",
     "0101 <pre> lína 9: Chandler, 6 orð"),
)
VEFUNDANTEKNINGAR: dict[tuple[str, str], tuple[int, str]] = {
    **{(_STAT, sha): (1, lysing) for sha, lysing in _0101},
    **{(_LEIT, sha): (1, lysing) for sha, lysing in _0101},
    (_STAT, "ccd9083216e36d38ee36a7a3991897bb7a58d5b9485129ba99e6481bfc7421fc"): (
        1, "0101 hóplína (All), 5 orð — dæmi um undanskildar hóplínur"),
    (_LEIT, "f06b713529b99c315104efbd9bb0511ce4cd9185901b269f08313ced1c411d73"): (
        1, "0101 hóplína (All), 5 orð + íslenskt „og“ — sama dæmi"),
}
