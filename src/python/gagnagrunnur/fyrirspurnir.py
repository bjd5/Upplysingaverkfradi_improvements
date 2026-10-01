"""Einn lesari fyrir fyrirspurnirnar í ``src/sql/queries/`` (issue #11).

Regla 5 segir að fyrirspurnir eigi að geymast, ekki bara svörin. Þær eiga því
heima í ``.sql``-skrám sem hægt er að lesa, prófa og keyra í hvaða SQL-tóli sem
er — ekki í Python-strengjum þar sem þær fara á skjön við sjálfar sig.

**Ein skrá = ein fyrirspurn.** Skráarheitið (án ``.sql``) er heiti hennar, og
skráin hefst á haus sem lesarinn krefst::

    -- skjalftar-dagleg-talning.sql
    -- Spurning: Hversu margir skjálftar urðu hvern UTC-dag tímabilsins?
    -- Síða: web/sidur/skjalftavaktin.html
    -- Breytur: engar

Með breytum er hver ``?`` talin upp í sinni röð undir ``Breytur:``::

    -- Breytur:
    --   ?1 lágmarks breidd
    --   ?2 hámarks breidd

Lesarinn stöðvast (regla 6) ef hausinn vantar, ef síðan er ekki nefnd eða ef
fjöldi ``?`` í fyrirspurninni er annar en hausinn lýsir — þá er skjölun
fyrirspurnarinnar röng og kallandinn sendir breytur í rangri röð.

**Hvítlisti, aldrei slóð úr inntaki.** ``FYRIRSPURNIR`` er tæmandi listi.
Heiti utan hans er hafnað áður en nokkur slóð er til, og slóðin sjálf er sett
saman úr gildi listans en ekki úr strengnum sem kallandinn sendi. ``../`` eða
algild slóð kemst því hvergi að.

**Námundun.** Fyrirspurnirnar skila ÓNÁMUNDUÐUM gildum; birtingin námundar
(``utflutningur.islenskt_snid``). SQLite ``ROUND`` námundar helminga frá núlli
en Python að sléttri tölu: 99/24 = 4,125 verður 4,13 í SQL en 4,12 í Python og
á gömlu síðunni. Ein venja, á einum stað — sjá ``docs/adferdafraedi.md`` 4.1.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection, Row

from gagnagrunnur.tenging import ROT

FYRIRSPURNAMAPPA = ROT / "src" / "sql" / "queries"
ENDING = ".sql"

# Tæmandi listi. Ný fyrirspurn = ný skrá + ný lína hér; prófið krefst þess að
# listinn og mappan segi sömu sögu, svo hvorugt verði eftir.
FYRIRSPURNIR: frozenset[str] = frozenset({
    # Skjálftavaktin
    "skjalftar-dagleg-talning",
    "skjalftar-dagleg-samantekt",
    "skjalftar-hlaupandi-medaltal",
    "skjalftar-manadartalning",
    "skjalftar-staerd-eftir-kvarda",
    "skjalftar-dypt",
    "skjalftar-syni",
    # Hagstofan
    "hagstofan-hlutfoll",
    "hagstofan-munur",
    "hagstofan-summur",
    "hagstofan-gagnasafn",
    "hagstofan-fyrirspurn",
    "hagstofan-viddir",
    "hagstofan-kodabok",
    # Veðurstöðvar
    "vedurstodvar-allar-stodvar",
    "vedurstodvar-fjoldi-stodva",
    "vedurstodvar-stod-eftir-audkenni",
    "vedurstodvar-virkar-stodvar",
    "vedurstodvar-fjoldi-virkra",
    "vedurstodvar-stodvar-i-marghyrningi",
    "vedurstodvar-virkar-stodvar-i-marghyrningi",
    "vedurstodvar-naesta-virka-stod",
    "vedurstodvar-naesta-aflagda-stod",
    "vedurstodvar-naesta-virka-langtimastod",
    "vedurstodvar-kassi-eftir-fjarlaegd",
    "vedurstodvar-sokn",
    # mbl.is
    "mbl-eintok",
    "mbl-svor",
    # Friends / Phoebe
    "friends-uppruni",
    "friends-umfang",
    "friends-thattunargaedi",
    "friends-plass-alls",
    "friends-plass-eftir-thattarod",
    "friends-interaction-lift",
    "friends-nafntilvik-eftir-thattarod",
    # Central Perk (migration 007)
    "central-perk-samantekt",
    "central-perk-hopar",
    "central-perk-handrit",
    "central-perk-songhandrit",
    "central-perk-segdir",
})

# Skráarheiti hvers leyfðs heitis, reiknað úr listanum sjálfum (aldrei úr inntaki).
_SKRAARHEITI: dict[str, str] = {heiti: heiti + ENDING for heiti in FYRIRSPURNIR}

HEITISMYNSTUR = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SPURNING = re.compile(r"^--\s*Spurning:\s*(?P<texti>\S.*)$")
SIDA = re.compile(r"^--\s*Síða:\s*(?P<texti>\S.*)$")
BREYTUR = re.compile(r"^--\s*Breytur:\s*(?P<texti>.*)$")
BREYTA = re.compile(r"^--\s+\?(?P<numer>[0-9]+)\s+(?P<lysing>\S.*)$")
ENGAR_BREYTUR = "engar"

# Það sem er ekki staðgengill þótt það innihaldi ``?``: athugasemdir og
# strengjafastar. Fjarlægt áður en staðgenglarnir eru taldir.
_ATHUGASEMD_EDA_STRENGUR = re.compile(r"--[^\n]*|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
# Aðeins ónúmeraðir ``?``. ``?1``, ``:heiti`` og ``@heiti`` eru bannaðir svo
# röð breytnanna sé alltaf sú sama og röðin í hausnum.
_NUMERADUR_EDA_NEFNDUR = re.compile(r"\?[0-9]|[:@$][A-Za-z_]")


class FyrirspurnaVilla(RuntimeError):
    """Fyrirspurnin er ekki á hvítlistanum, finnst ekki eða er ranglega skjalfest."""


@dataclass(frozen=True)
class Fyrirspurn:
    """Ein fyrirspurn úr ``src/sql/queries/`` ásamt hausnum sem lýsir henni."""

    heiti: str
    spurning: str
    sida: str
    breytur: tuple[str, ...]
    sql: str


def slod(heiti: str, mappa: Path = FYRIRSPURNAMAPPA) -> Path:
    """Slóð fyrirspurnarskrárinnar — aðeins fyrir heiti á hvítlistanum."""
    skraarheiti = _SKRAARHEITI.get(heiti)
    if skraarheiti is None:
        raise FyrirspurnaVilla(
            f"Fyrirspurnin {heiti!r} er ekki á hvítlistanum. Leyfðar eru: "
            + ", ".join(sorted(FYRIRSPURNIR))
        )
    return mappa / skraarheiti


def lesa(heiti: str, mappa: Path = FYRIRSPURNAMAPPA) -> Fyrirspurn:
    """Les og sannreynir eina fyrirspurn; villa ef hausinn eða breyturnar stemma ekki."""
    skra = slod(heiti, mappa)
    if not skra.is_file():
        raise FyrirspurnaVilla(f"Fyrirspurnin {heiti!r} er á hvítlistanum en {skra} finnst ekki.")
    texti = skra.read_text(encoding="utf-8")
    linur = texti.splitlines()

    if not linur or linur[0].strip() != f"-- {skra.name}":
        raise FyrirspurnaVilla(f"{skra.name}: fyrsta línan á að vera '-- {skra.name}'.")
    haus = _haus(linur)
    spurning = _eitt(haus, SPURNING, skra.name, "Spurning")
    sida = _eitt(haus, SIDA, skra.name, "Síða")
    breytur = _breytur(haus, skra.name)

    sql = texti.strip()
    fjoldi = stadgenglar(sql)
    if fjoldi != len(breytur):
        raise FyrirspurnaVilla(
            f"{skra.name}: fyrirspurnin hefur {fjoldi} ?-staðgengla en hausinn lýsir "
            f"{len(breytur)} breytum. Skjölunin og fyrirspurnin verða að stemma."
        )
    return Fyrirspurn(heiti=heiti, spurning=spurning, sida=sida, breytur=breytur, sql=sql)


def keyra(samband: Connection, heiti: str, breytur: tuple = ()) -> list[Row]:
    """Keyrir nefnda fyrirspurn með breytum (regla 5) og skilar öllum röðum."""
    fyrirspurn = lesa(heiti)
    if len(breytur) != len(fyrirspurn.breytur):
        raise FyrirspurnaVilla(
            f"{heiti} tekur {len(fyrirspurn.breytur)} breytur "
            f"({'; '.join(fyrirspurn.breytur) or 'engar'}) en fékk {len(breytur)}."
        )
    sql = fyrirspurn.sql
    return samband.execute(sql, breytur).fetchall()


def stadgenglar(sql: str) -> int:
    """Fjöldi ``?``-staðgengla utan athugasemda og strengjafasta."""
    hreint = _ATHUGASEMD_EDA_STRENGUR.sub(" ", sql)
    if _NUMERADUR_EDA_NEFNDUR.search(hreint):
        raise FyrirspurnaVilla(
            "Aðeins ónúmeraðir ?-staðgenglar eru leyfðir; röð þeirra er skjalfest í hausnum."
        )
    return hreint.count("?")


def skrar_i_moppu(mappa: Path = FYRIRSPURNAMAPPA) -> frozenset[str]:
    """Heiti allra ``.sql``-skráa í möppunni — til að bera við hvítlistann."""
    return frozenset(skra.stem for skra in mappa.glob("*" + ENDING))


def _haus(linur: list[str]) -> list[str]:
    """Samfelldu athugasemdalínurnar efst í skránni."""
    haus = []
    for lina in linur:
        if not lina.startswith("--"):
            break
        haus.append(lina.rstrip())
    return haus


def _eitt(haus: list[str], mynstur: re.Pattern[str], skra: str, reitur: str) -> str:
    """Einn reitur hausins; enginn eða tveir eru villa."""
    fundid = [m["texti"].strip() for lina in haus if (m := mynstur.match(lina))]
    if len(fundid) != 1:
        raise FyrirspurnaVilla(
            f"{skra}: hausinn á að hafa nákvæmlega eina '-- {reitur}:'-línu, fann {len(fundid)}."
        )
    return fundid[0]


def _breytur(haus: list[str], skra: str) -> tuple[str, ...]:
    """Breyturnar í hausnum, í röð ``?1, ?2, …`` — gat eða víxl er villa."""
    stadir = [i for i, lina in enumerate(haus) if BREYTUR.match(lina)]
    if len(stadir) != 1:
        raise FyrirspurnaVilla(
            f"{skra}: hausinn á að hafa nákvæmlega eina '-- Breytur:'-línu, fann {len(stadir)}."
        )
    fyrsta = BREYTUR.match(haus[stadir[0]])["texti"].strip()
    if fyrsta == ENGAR_BREYTUR:
        return ()
    if fyrsta:
        raise FyrirspurnaVilla(
            f"{skra}: 'Breytur:' er annaðhvort '{ENGAR_BREYTUR}' eða listi ?1, ?2 … á næstu línum."
        )
    breytur: list[str] = []
    for lina in haus[stadir[0] + 1:]:
        samsvorun = BREYTA.match(lina)
        if samsvorun is None:
            break
        if int(samsvorun["numer"]) != len(breytur) + 1:
            raise FyrirspurnaVilla(
                f"{skra}: breyta ?{samsvorun['numer']} kemur þar sem ?{len(breytur) + 1} á að vera."
            )
        breytur.append(samsvorun["lysing"].strip())
    if not breytur:
        raise FyrirspurnaVilla(f"{skra}: 'Breytur:' er tómt en ekki '{ENGAR_BREYTUR}'.")
    return tuple(breytur)
