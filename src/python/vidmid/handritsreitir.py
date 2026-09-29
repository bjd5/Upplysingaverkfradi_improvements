"""Skilgreiningar fyrir handritsleitina: hvað er skannað og hvað er undanþegið.

Aðskilið frá `handritsleit.py` af því að leitarreglan er kóði sem má lesa í
einu, en undanþágurnar eru
**skjalfest ákvörðun** sem verður að vera hægt að lesa og vefengja eina og sér.

Sjá docs/adferdafraedi.md, kafla 1.5.2, fyrir röksemdina að baki þröskuldunum
og afmörkun leitarinnar.
"""

from __future__ import annotations

from dataclasses import dataclass

# Allar Friends-TALNASKRÁR sem eru í git.
#
# Byggða gamla síðan (docs/vidmid/vefur/), sem geymdi orðréttar handritslínur,
# var tekin úr trénu 28.9.2026 og er aðeins í git-taginu vidmid-frosid
# (docs/adferdafraedi.md, kafli 1.5.2).
MOPPUR = (
    "data/processed/phoebe-stats",
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
