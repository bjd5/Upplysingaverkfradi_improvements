"""Viðmiðstölur gömlu síðunnar fyrir mbl-eintökin (issue #9).

Væntingarnar í mbl-prófunum eru **ekki handskrifaðar**: þær eru lesnar hér úr
``docs/vidmid/vidmid.json``, sem `src/python/vidmid/tolur.py` las út úr byggðu
útgáfu gamla verkefnisins. Breytist viðmiðið fellur prófið — það er tilgangurinn
(regla 5 í docs/endurbygging.md: breytist tala er það villa þar til annað er
sannað).

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py`` og hleður henni því aðeins þegar prófin flytja hana inn.
"""

from __future__ import annotations

import json
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
VIDMIDSSKRA = ROT / "docs" / "vidmid" / "vidmid.json"

# Eintakið sem bæði gamla síðan og þetta verk lesa — sama MD5, sama skrá.
FROSNA_EINTAKID = "mbl-20260916T120851Z"
FROSNA_MD5 = "c2c83bddb8ed41357b7b1b8ab51a6457"
FROSNA_UPPRUNASLOD = "https://www.mbl.is/frettir/"

# Eldra eintakið úr sömu töflu. Prófað til að sýna að viðmiðstölurnar eru
# eintaksbundnar — færu þær saman væri samanburðurinn merkingarlaus.
ELDRA_EINTAKID = "mbl-20260907T103959Z"

VIDMIDSSIDA = "lotur/regex/mbl.html"
VIDMIDSKAFLI = "Samanburður eintaka"

# Dálkur í samanburðartöflu gömlu síðunnar -> lykill spurningarinnar hér.
SULKA_EFTIR_LYKLI = {
    "einstakar-frettir": "Fréttir",
    "hitastig-reykjavik": "Hiti",
    "gengi-usd": "USD",
    "synileg-ord": "Orð",
    "auglysingareitir": "Auglýsingareitir",
}


def vidmidstolur(eintaksheiti: str) -> dict[str, float]:
    """Les tölur gömlu síðunnar fyrir eitt eintak úr ``vidmid.json``.

    Vanti einhverja þeirra er kastað villu en ekki skilað tómu korti: próf sem
    ber saman við ekkert stenst alltaf og sannar ekkert (regla 6).
    """
    skjal = json.loads(VIDMIDSSKRA.read_text(encoding="utf-8"))
    i_tofluni = {
        rad["sulka"]: rad["gildi"]
        for rad in skjal["gogn"]
        if rad.get("sida") == VIDMIDSSIDA
        and rad.get("lina") == eintaksheiti
        and VIDMIDSKAFLI in (rad.get("kafli") or [])
        and rad.get("visst")
    }

    tolur: dict[str, float] = {}
    vantar: list[str] = []
    for lykill, sulka in SULKA_EFTIR_LYKLI.items():
        if sulka in i_tofluni:
            tolur[lykill] = float(i_tofluni[sulka])
        else:
            vantar.append(sulka)
    if vantar:
        raise AssertionError(
            f"Viðmiðið í {VIDMIDSSKRA.name} hefur ekki dálkana "
            f"{', '.join(vantar)} fyrir {eintaksheiti} í kaflanum "
            f"„{VIDMIDSKAFLI}“. Án þeirra er ekkert til að bera saman við."
        )
    return tolur


def vidmidstala(eintaksheiti: str, lykill: str) -> float:
    """Ein viðmiðstala — notað þegar próf ber eitt svar saman í einu."""
    return vidmidstolur(eintaksheiti)[lykill]
