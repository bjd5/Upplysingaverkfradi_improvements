"""Hleðsla stöðvaskrár Veðurstofunnar í ``weather_stations`` (issue #8).

Flæðið er einstefna (kafli 0 í CLAUDE.md): frosna svarið í ``data/raw/`` er
lesið, hver færsla sannreynd og niðurstaðan sett í grunninn. Hrágögnin eru
aldrei snert (regla 10) og grunnurinn er hrein afleiða — hann má eyða og byggja
aftur með ``scripts/endurbyggja-grunn.sh``.

**Frosið eintak, ekki lifandi staða.** Gamla verkefnið sótti stöðvalistann upp
á nýtt í hverri CI-byggingu og vistaði svarið aldrei, svo síðan gat birt aðrar
tölur í dag en í gær. Hér er hlaðið úr einu eintaki með tiltekinni
sóknardagsetningu og SHA-256 summan úr ``provenance.json`` er staðfest áður en
nokkuð fer inn: víki skráin frá summunni er hún ekki lengur það sem var fryst
og hleðslan stöðvast.

Hleðslan er endurkeyranleg: hún hreinsar það sem hún setti inn síðast og setur
eintakið inn á ný. Sama eintak gefur því alltaf sama grunn.

Keyrsla frá rót verkefnisins (tenging við ``main.py`` kemur í issue #11)::

    PYTHONPATH=src/python python3 -m vinnsla.vedurstodvar_hledsla

Netlaust — les aðeins frosin gögn. Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur.keyrari import keyra
from gagnagrunnur.tenging import ROT, tenging

from .vedurstodvar_faersla import Stod, sannreyna_svar

log = logging.getLogger(__name__)

FROSID = ROT / "data" / "raw" / "vedurstodvar"
PROVENANCE = "provenance.json"

# Heiti safnsins í fetch_log. Hleðslan á þessa færslu ein og hreinsar hana
# áður en hún skrifar nýja, svo endurkeyrsla safni ekki upp sögu.
THJONUSTA = "vedurstofa-stodvar"

# Reitir sem provenance verður að hafa til að hleðslan sé rekjanleg (regla 4).
PROVENANCE_REITIR = ("endpoint", "fetched_at_utc", "response_file", "sha256", "station_count")

INNSETNING = """
INSERT INTO weather_stations (
    station_id, name, abbr, station_type, lat, lon,
    elevation_m, wigos_id, owner, start_year, end_year
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SOFNUNARSKRANING = """
INSERT INTO fetch_log (service, endpoint, params, fetched_at, record_count, raw_file, notes)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SKRANINGARSKYRING = (
    "Frosið eintak, ekki lifandi staða. Gamla verkefnið sótti stöðvalistann í "
    "hverri CI-byggingu og vistaði svarið aldrei; hér er hlaðið úr einu eintaki "
    "sem var sótt á tímastimplinum að ofan. Samanburður við gömlu síðuna er í "
    "docs/vedurstodvar-samanburdur.md."
)


class HledsluVilla(RuntimeError):
    """Hleðslan er ekki framkvæmanleg eða eintakið er ekki það sem var fryst."""


@dataclass(frozen=True)
class Nidurstada:
    """Yfirlit yfir eina hleðslu, notað í skýrslur og próf."""

    eintak: str
    sott_utc: str
    fjoldi: int
    virkar: int

    @property
    def aflagdar(self) -> int:
        return self.fjoldi - self.virkar


def stutt_slod(slod: Path) -> str:
    """Slóð afstæð við rót verkefnisins þegar hún liggur þar, annars full slóð."""
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)


def lesa_provenance(mappa: Path = FROSID) -> dict:
    """Les provenance safnsins og staðfestir að reitirnir sem þarf séu til staðar.

    Hrágagn án uppruna er ónothæft (regla 4): án slóðar, sóknartíma og summu er
    ekkert sem tengir töluna í grunninum við það sem þjónustan sagði.
    """
    slod = mappa / PROVENANCE
    if not slod.is_file():
        raise HledsluVilla(
            f"Vantar {stutt_slod(slod)} — hrágagn án uppruna fer ekki í grunninn "
            "(regla 4). Keyrðu src/python/sofnun/frysta_vedurstodvar.py fyrst."
        )
    skjal = json.loads(slod.read_text(encoding="utf-8"))
    vantar = [reitur for reitur in PROVENANCE_REITIR if not skjal.get(reitur)]
    if vantar:
        raise HledsluVilla(
            f"{stutt_slod(slod)} vantar reitina {', '.join(vantar)}; hleðslan yrði "
            "þá ekki rekjanleg aftur í svarið sem var fryst."
        )
    return skjal


def stadfesta_summu(slod: Path, vaent: str) -> None:
    """Ber SHA-256 skrárinnar við summuna í provenance.

    Þetta er eina vörnin gegn því að frosna eintakið hafi breyst eftir
    frystinguna — handvirk breyting á ``data/raw/`` er bönnuð (regla 10) en
    hleðslan treystir því ekki, hún mælir það.
    """
    summa = hashlib.sha256(slod.read_bytes()).hexdigest()
    if summa != vaent:
        raise HledsluVilla(
            f"{stutt_slod(slod)} stemmir ekki við provenance.\n"
            f"  skráð SHA-256:   {vaent}\n"
            f"  á diski SHA-256: {summa}\n"
            "Eintakið er ekki lengur það sem var fryst og fer því ekki í grunninn."
        )


def lesa_eintak(mappa: Path = FROSID) -> tuple[dict, Path, list[Stod]]:
    """Les frosna eintakið sem provenance lýsir og sannreynir hverja færslu.

    Skráin er valin eftir ``response_file`` í provenance en ekki eftir dagsetningu
    í skráarheiti: provenance er heimildin um hvaða eintak var fryst.
    """
    skjal = lesa_provenance(mappa)
    slod = mappa / str(skjal["response_file"])
    if not slod.is_file():
        raise HledsluVilla(
            f"Provenance nefnir eintakið {skjal['response_file']} en það finnst "
            f"ekki í {stutt_slod(mappa)}."
        )
    stadfesta_summu(slod, str(skjal["sha256"]))

    stodvar = sannreyna_svar(json.loads(slod.read_text(encoding="utf-8")))
    vaentur_fjoldi = int(skjal["station_count"])
    if len(stodvar) != vaentur_fjoldi:
        raise HledsluVilla(
            f"Provenance segir {vaentur_fjoldi} stöðvar en {len(stodvar)} lásust "
            f"úr {stutt_slod(slod)}."
        )
    return skjal, slod, stodvar


def _skra_sofnun(samband: Connection, skjal: dict, slod: Path, fjoldi: int) -> None:
    """Skráir sóknina í ``fetch_log`` svo hver tala eigi sér rekjanlega leið (regla 8).

    Fyrri skráning þessa safns er fjarlægð svo endurkeyrsla safni ekki upp
    tvítekinni sögu; önnur söfn í töflunni eru ósnert.
    """
    samband.execute("DELETE FROM fetch_log WHERE service = ?", (THJONUSTA,))
    samband.execute(
        SOFNUNARSKRANING,
        (
            THJONUSTA,
            str(skjal["endpoint"]),
            json.dumps(skjal.get("parameters", {}), ensure_ascii=False, sort_keys=True),
            str(skjal["fetched_at_utc"]),
            fjoldi,
            stutt_slod(slod),
            SKRANINGARSKYRING,
        ),
    )


def hlada(samband: Connection, mappa: Path = FROSID) -> Nidurstada:
    """Hleður frosnu stöðvaskránni í ``weather_stations`` og skilar yfirliti.

    Fallið stýrir ekki færslunni sjálft: kallandinn opnar grunninn með
    ``gagnagrunnur.tenging.tenging`` og hún sér um commit eða rollback. Þannig
    situr grunnurinn aldrei með hálfa stöðvaskrá.

    Allar fyrirspurnir eru með breytum (regla 5) — engin gildi eru límd í SQL.
    """
    skjal, slod, stodvar = lesa_eintak(mappa)

    # Taflan geymir eitt eintak í senn; hleðslan er endurkeyranleg.
    samband.execute("DELETE FROM weather_stations")
    samband.executemany(INNSETNING, [stod.sem_rad() for stod in stodvar])

    innsettar = samband.execute("SELECT COUNT(*) FROM weather_stations").fetchone()[0]
    if innsettar != len(stodvar):
        raise HledsluVilla(
            f"{len(stodvar)} stöðvar voru sendar í grunninn en {innsettar} komust "
            "inn. Hleðslan er ekki heil og er rúllað til baka."
        )

    _skra_sofnun(samband, skjal, slod, innsettar)
    virkar = samband.execute(
        "SELECT COUNT(*) FROM weather_stations WHERE end_year IS NULL"
    ).fetchone()[0]

    return Nidurstada(
        eintak=slod.name,
        sott_utc=str(skjal["fetched_at_utc"]),
        fjoldi=innsettar,
        virkar=virkar,
    )


def main(rok: list[str] | None = None) -> int:
    """Keyrir migrations og hleður stöðvaskránni í grunninn."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    if rok:
        raise SystemExit(f"Þessi eining tekur enga viðbótarröksemd, fékk: {rok}")

    with tenging() as samband:
        keyra(samband)
        nidurstada = hlada(samband)

    log.info(
        "Hlóð %d stöðvum úr %s (sótt %s): %d enn starfræktar, %d aflagðar.",
        nidurstada.fjoldi,
        nidurstada.eintak,
        nidurstada.sott_utc,
        nidurstada.virkar,
        nidurstada.aflagdar,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
