"""Sannreyning á einni færslu úr stöðvaskrá Veðurstofunnar.

Hleðslan í ``vedurstodvar_hledsla`` sannreynir hverja færslu áður en hún fer í
grunninn. Frávik stöðvar keyrsluna — það er ekki sleppt þegjandi og ekki lagað
sjálfkrafa (regla 6). Ástæðan er sú að stöðvaskráin er **frosið eintak**: víki
færsla frá því sem búist var við hefur þjónustan breytt sniðinu, og þá er það
niðurstaða sem á að sjást en ekki galli sem á að fela.

Reiturinn ``ending`` fær sérmeðferð. Tómt lokaár þýðir að stöðin mælir enn og
verður að rata í grunninn sem ``NULL``, aldrei sem tómstrengur: ``end_year IS
NULL`` telur 343 stöðvar en ``end_year = ''`` telur enga. Hér er tómstrengur því
villa en ekki gildi sem er þýtt yfir í NULL í kyrrþey.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import astuple, dataclass
from typing import Any

# Reitirnir sem svarið verður að hafa. Vanti reit er sniðið annað en það sem
# frysta eintakið var sannreynt á og hleðslan stöðvast.
REITIR: tuple[str, ...] = (
    "station", "name", "abbr", "type", "lat", "lon",
    "ele", "wigos", "owner", "start", "ending",
)

# Ártöl utan þessara marka eru ekki ártöl heldur merki um breytt snið.
ELSTA_AR = 1700
YNGSTA_AR = 2100


class FaersluVilla(ValueError):
    """Færsla stenst ekki sniðið sem frosna eintakið var sannreynt á."""


@dataclass(frozen=True)
class Stod:
    """Ein stöð, tilbúin í ``weather_stations``.

    Reitirnir heita eins og dálkarnir í töflunni svo röðin í ``sem_rad`` sé
    lesin á einum stað og fari ekki á skjön við INSERT-setninguna.
    """

    station_id: int
    name: str
    abbr: str
    station_type: str
    lat: float
    lon: float
    elevation_m: float
    wigos_id: str | None
    owner: str | None
    start_year: int
    end_year: int | None

    @property
    def er_virk(self) -> bool:
        """Stöð telst virk hafi hún ekkert lokaár — sama skilyrði og ``active=true``."""
        return self.end_year is None

    def sem_rad(self) -> tuple[Any, ...]:
        """Gildin í dálkaröð töflunnar, tilbúin fyrir fyrirspurn með breytum."""
        return astuple(self)


def _villa(visir: int, reitur: str, skyring: str, gildi: object) -> FaersluVilla:
    """Villa sem segir hvar í svarinu vandinn er og hvað stóð þar."""
    return FaersluVilla(
        f"Færsla {visir}: reiturinn {reitur!r} {skyring}, en þar stóð {gildi!r}."
    )


def _heiltala(faersla: Mapping[str, Any], reitur: str, visir: int) -> int:
    """Les heiltölureit. ``bool`` er heiltala í Python en ekki gild hér."""
    gildi = faersla[reitur]
    if type(gildi) is not int:
        raise _villa(visir, reitur, "á að vera heiltala", gildi)
    return gildi


def _fleytitala(faersla: Mapping[str, Any], reitur: str, visir: int) -> float:
    """Les tölureit sem má vera heiltala eða fleytitala."""
    gildi = faersla[reitur]
    if type(gildi) not in (int, float):
        raise _villa(visir, reitur, "á að vera tala", gildi)
    return float(gildi)


def _texti(faersla: Mapping[str, Any], reitur: str, visir: int) -> str:
    """Les textareit sem verður að vera til staðar og ótómur."""
    gildi = faersla[reitur]
    if not isinstance(gildi, str) or not gildi.strip():
        raise _villa(visir, reitur, "á að vera ótómur texti", gildi)
    return gildi.strip()


def _valfrjals_texti(faersla: Mapping[str, Any], reitur: str, visir: int) -> str | None:
    """Les textareit sem má vanta — en þá sem NULL, ekki sem tómstreng.

    Tómstrengur er ekki þýddur yfir í NULL hér: dálkurinn hafnar honum hvort eð
    er (CHECK í 004) og þögul leiðrétting fæli breytingu á svarinu.
    """
    gildi = faersla[reitur]
    if gildi is None:
        return None
    if not isinstance(gildi, str) or not gildi.strip():
        raise _villa(
            visir, reitur, "á að vera ótómur texti eða vanta alveg (null)", gildi
        )
    return gildi.strip()


def _ar(faersla: Mapping[str, Any], reitur: str, visir: int) -> int:
    """Les ártal og hafnar tölum sem geta ekki verið ártöl."""
    gildi = _heiltala(faersla, reitur, visir)
    if not ELSTA_AR <= gildi <= YNGSTA_AR:
        raise _villa(
            visir, reitur, f"á að vera ártal á bilinu {ELSTA_AR}–{YNGSTA_AR}", gildi
        )
    return gildi


def _lokaar(faersla: Mapping[str, Any], visir: int, upphafsar: int) -> int | None:
    """Les lokaár starfrækslu: ártal, eða ``None`` mæli stöðin enn.

    Tómstrengur er villa en ekki tómt gildi. Þetta er munurinn sem æfingin
    snýst um og hann má ekki jafnast út í hleðslunni.
    """
    gildi = faersla["ending"]
    if gildi is None:
        return None
    if isinstance(gildi, str):
        raise _villa(
            visir,
            "ending",
            "á að vera ártal eða vanta alveg (null) — tómstrengur og texti "
            "gera `end_year IS NULL` ómarktækt",
            gildi,
        )
    lokaar = _ar(faersla, "ending", visir)
    if lokaar < upphafsar:
        raise _villa(
            visir, "ending", f"má ekki vera fyrir upphafsárið {upphafsar}", lokaar
        )
    return lokaar


def sannreyna_faerslu(faersla: object, visir: int) -> Stod:
    """Sannreynir eina færslu úr svarinu og skilar henni sem ``Stod``.

    ``visir`` er staðan í svarinu og fer í villuboðin svo hægt sé að fletta
    færslunni upp í frosna eintakinu.
    """
    if not isinstance(faersla, Mapping):
        raise FaersluVilla(
            f"Færsla {visir}: á að vera hlutur með reitum en er {type(faersla).__name__}."
        )

    vantar = [reitur for reitur in REITIR if reitur not in faersla]
    if vantar:
        raise FaersluVilla(
            f"Færsla {visir}: vantar reitina {', '.join(vantar)}. Snið svarsins er "
            "annað en það sem frosna eintakið var sannreynt á."
        )

    upphafsar = _ar(faersla, "start", visir)
    return Stod(
        station_id=_heiltala(faersla, "station", visir),
        name=_texti(faersla, "name", visir),
        abbr=_texti(faersla, "abbr", visir),
        station_type=_texti(faersla, "type", visir),
        lat=_fleytitala(faersla, "lat", visir),
        lon=_fleytitala(faersla, "lon", visir),
        elevation_m=_fleytitala(faersla, "ele", visir),
        wigos_id=_valfrjals_texti(faersla, "wigos", visir),
        owner=_valfrjals_texti(faersla, "owner", visir),
        start_year=upphafsar,
        end_year=_lokaar(faersla, visir, upphafsar),
    )


def sannreyna_svar(svar: object) -> list[Stod]:
    """Sannreynir allt svarið og skilar stöðvunum í þeirri röð sem þær komu.

    Tvær færslur með sama auðkenni stöðva keyrsluna hér frekar en að lenda á
    frumlyklinum: villuboðin segja þá hvaða auðkenni endurtók sig.
    """
    if not isinstance(svar, list):
        raise FaersluVilla(
            f"Svarið á að vera listi af stöðvum en er {type(svar).__name__}."
        )
    if not svar:
        raise FaersluVilla("Svarið er tómt — engin stöð til að hlaða.")

    stodvar: list[Stod] = []
    sed: set[int] = set()
    for visir, faersla in enumerate(svar):
        stod = sannreyna_faerslu(faersla, visir)
        if stod.station_id in sed:
            raise FaersluVilla(
                f"Færsla {visir}: auðkennið {stod.station_id} kemur oftar en einu "
                "sinni. Frumlykillinn krefst þess að hver stöð sé ein færsla."
            )
        sed.add(stod.station_id)
        stodvar.append(stod)
    return stodvar
