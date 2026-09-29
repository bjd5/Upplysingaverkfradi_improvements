"""Hjálpargögn mbl-prófanna: gervieintök, viðmiðstölur og prófgrunnur (issue #9).

**Gervieintökin** eru tilbúið HTML, aldrei hrágögnin sjálf. Frosna eintakið í
``data/raw/mbl/`` er eina afritið sem til er og er aðeins lesið (regla 10);
jaðartilvik — týnt mynstur, tvíræð niðurstaða, tvö eintök í sömu töflu — eru
prófuð á gervieintökum sem herma aðeins eftir brotunum sem mynstrin leita að.

**Viðmiðstölurnar** eru ekki handskrifaðar: þær eru lesnar úr
``docs/vidmid/vidmid.json``. Breytist viðmiðið fellur prófið — það er
tilgangurinn (breytist tala er það villa þar til annað er sannað).

**Prófgrunnurinn** (``GrunnProf``) er byggður úr sömu migrations og
alvörugrunnurinn, aldrei handskrifuðu ``CREATE TABLE``. ``SVOR_SQL`` er lesin
úr ``src/sql/queries/mbl-svor.sql`` og er staðfestingin á kröfunni um að öll
fimm svörin fáist úr SQL; breytur fara alltaf inn sem ``?`` (regla 5).

Hjálpareining, ekki prófskrá (``unittest discover`` leitar að ``test*.py``).
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from gagnagrunnur import fyrirspurnir  # noqa: E402
from gagnagrunnur.keyrari import MIGRATIONS_MAPPA, keyra  # noqa: E402
from gagnagrunnur.tenging import opna  # noqa: E402
from vinnsla.mbl_eintak import Eintak, finna_eintok  # noqa: E402


# --- Gervieintök ---------------------------------------------------------------

# Tvöföld fréttaslóð og tvöfalt auglýsingaauðkenni eru viljandi: þannig prófast
# afritahreinsunin, ekki bara talningin.
GERVI_HTML = """<!DOCTYPE html>
<html lang="is"><head><title>Hausinn telst ekki með</title>
<script>var leyniord = "ekki synilegt";</script>
<style>.falid { display: none; }</style></head>
<body>
<nav><a href="/frettir/">Fréttir</a><a href="/frettir/innlent/">Innlent</a></nav>
<a href="/frettir/innlent/2026/09/16/fyrsta_frettin/"><img alt="mynd"></a>
<a href="/frettir/innlent/2026/09/16/fyrsta_frettin/">Fyrsta fréttin</a>
<a href="https://www.mbl.is/frettir/erlent/2026/09/16/onnur_frett/">Önnur frétt</a>
<select>
<option value="1">Akureyri</option>
<option value="2" selected>Reykjavík</option>
</select>
<div class="vedur"><span class="value">11</span><span class="unit">&deg;</span></div>
<p>Sýnilegur texti með&nbsp;íslenskum stöfum.</p>
<!-- athugasemd sem telst ekki -->
<script>arrCurrency[3] = new MakeItem("USD", "121.33");</script>
<script>
Ads.renderSlot("1234-5678", {});
Ads.renderSlot("1234-5678", {});
Ads.renderSlot("9999-1", {});
</script>
</body></html>
"""

# Það sem GERVI_HTML á að gefa. Fast hér svo prófin lýsi væntingunni á einum stað.
GERVI_SVOR: dict[str, float] = {
    "einstakar-frettir": 2.0,
    "hitastig-reykjavik": 11.0,
    "gengi-usd": 121.33,
    "synileg-ord": 13.0,
    "auglysingareitir": 2.0,
}

GERVI_UPPRUNASLOD = "https://www.mbl.is/frettir/"


def iso_stund(stund: str) -> str:
    """Breytir ``20260916T120851Z`` í ``2026-09-16T12:08:51Z``."""
    dagur, klukka = stund.split("T")
    ar, manudur, dagsetning = dagur[:4], dagur[4:6], dagur[6:8]
    klst, minuta, sekunda = klukka[:2], klukka[2:4], klukka[4:6]
    return f"{ar}-{manudur}-{dagsetning}T{klst}:{minuta}:{sekunda}Z"


def skrifa_eintak(
    mappa: Path,
    sotta_stund: str,
    html_texti: str = GERVI_HTML,
    *,
    stada: int = 200,
    md5: str | None = None,
    staerd: int | None = None,
) -> Path:
    """Skrifar gervieintak — HTML og samnefnd lýsigögn — og skilar HTML-slóðinni.

    ``sotta_stund`` er á forminu ``20260916T120851Z`` og ræður skráarheitinu.
    ``md5``, ``staerd`` og ``stada`` má setja vísvitandi röng til að prófa að
    sannreyningin í ``mbl_eintak`` stöðvi keyrslu (regla 6).
    """
    mappa.mkdir(parents=True, exist_ok=True)
    html_slod = mappa / f"mbl-{sotta_stund}.html"
    baeti = html_texti.encode("utf-8")
    html_slod.write_bytes(baeti)

    lysigogn = {
        "schema_version": 1,
        "source_url": GERVI_UPPRUNASLOD,
        "fetched_at_utc": iso_stund(sotta_stund),
        "status_code": stada,
        "content_type": "text/html; charset=UTF-8",
        "content_length_bytes": len(baeti) if staerd is None else staerd,
        "md5": hashlib.md5(baeti).hexdigest() if md5 is None else md5,
        "user_agent": "prófun",
    }
    html_slod.with_suffix(".json").write_text(
        json.dumps(lysigogn, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return html_slod


# --- Viðmiðstölur --------------------------------------------------------------

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


# --- Prófgrunnur ---------------------------------------------------------------

# Keyrarinn varar við götum í migration-númerum (002–004 eru á greinum hinna
# agentanna) og hleðslan skráir hvert eintak. Hvorugt er villa og hvorugt er
# það sem þessi próf mæla — þögnin er aðeins hér, ekki í keyrslunni sjálfri.
THOGGUD_LOG = ("gagnagrunnur.keyrari", "vinnsla.mbl_hledsla")

for heiti in THOGGUD_LOG:
    logging.getLogger(heiti).setLevel(logging.ERROR)

# Ein fyrirspurn sem svarar öllum fimm spurningunum eða einni, og sýnir um
# leið hvaðan hvert svar kemur. Hún er í src/sql/queries/mbl-svor.sql (#11) og
# er lesin þaðan — sama skrá og hleðslan (mbl_hledsla.stadfesta_svor) notar.
SVOR_SQL = fyrirspurnir.lesa("mbl-svor").sql

# Lesið sem „allar spurningar" í SVOR_SQL.
ALLAR_SPURNINGAR = None


class GrunnProf(unittest.TestCase):
    """Tómur grunnur með raunverulegu migration-unum, einn á hvert próf."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.samband = opna(self.mappa / "prof.sqlite")
        self.addCleanup(self.samband.close)
        keyra(self.samband, MIGRATIONS_MAPPA)

    def svor(self, sott: str) -> list[sqlite3.Row]:
        """Öll fimm svörin fyrir eitt eintak — alltaf með breytu, aldrei f-streng."""
        breytur = (sott, ALLAR_SPURNINGAR, ALLAR_SPURNINGAR)
        return self.samband.execute(SVOR_SQL, breytur).fetchall()

    def eitt_svar(self, sott: str, lykill: str) -> sqlite3.Row:
        """Eitt svar úr SQL. Finnist það ekki fellur prófið með læsilegri villu."""
        rad = self.samband.execute(SVOR_SQL, (sott, lykill, lykill)).fetchone()
        self.assertIsNotNone(
            rad, f"Spurningin {lykill!r} er ekki svaranleg úr grunninum fyrir {sott}."
        )
        return rad

    def frosna_eintakid(self) -> Eintak:
        """Frosna eintakið úr ``data/raw/mbl/`` — lesið, aldrei skrifað."""
        eintok = [
            e for e in finna_eintok() if e.skraarheiti.startswith(FROSNA_EINTAKID)
        ]
        self.assertTrue(
            eintok,
            f"{FROSNA_EINTAKID}.html finnst ekki í data/raw/mbl/. Það er eina "
            "eintakið sem til er — sjá data/raw/README.md.",
        )
        return eintok[0]
