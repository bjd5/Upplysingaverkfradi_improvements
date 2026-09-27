"""Sannreyning á frosnu skjálftasvari Veðurstofunnar (issue #6).

Hrágögnin eru ``data/raw/vedur-quakes/events.json`` — GeoJSON FeatureCollection
með 334 atburðum. Þau eru lesin, aldrei skrifuð (regla 10).

Hver færsla er sannreynd **áður en** hún fer í grunninn:

* byggingin er gilt GeoJSON-``Feature`` með ``Point``-hnitum
  (``jardskjalftar_geojson.py`` sér um sniðið),
* öll gildi eru innan þeirra sía sem provenance segir að beiðnin hafi beðið um,
* tímastimpillinn er gildur UTC-tími innan tímabilsins,
* auðkennið er einkvæmt og á SIL-forminu,
* stærðarkvarðinn er skráður.

Frávik **stöðva keyrsluna** með ``SkjalftaVilla``. Færsla má aldrei hverfa
hljóðlega: úrtak sem þegir yfir því sem það sleppti er ekki rannsóknargagn
(regla 6).

Tveir afleiddir lyklar eru dregnir út með reglulegum segðum, eins og í
upprunaverkefninu — sömu mynstur, sami ``fullmatch``. Frumgildin (``event_id``,
``occurred_at``) geymast áfram við hlið þeirra.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

try:  # keyrt sem eining innan pakkans
    from .jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, lesa_afmorkun
    from .jardskjalftar_geojson import hlutur, hnit, lesa_features, tala, texti
except ImportError:  # keyrt beint úr möppunni
    from jardskjalftar_afmorkun import Afmorkun, SkjalftaVilla, lesa_afmorkun
    from jardskjalftar_geojson import hlutur, hnit, lesa_features, tala, texti

ROT = Path(__file__).resolve().parents[3]
ATBURDIR = ROT / "data" / "raw" / "vedur-quakes" / "events.json"

# Regex 1 — UTC-tímastimpill verður daglykill. Nafngreindi hópurinn gefur
# daginn; sekúndubrot mega hafa mismargar tölur. fullmatch krefst alls textans.
DAGSMYNSTUR = re.compile(
    r"(?P<utc_day>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
)

# Regex 2 — SIL-auðkenni klofnar í kerfisheiti og atburðanúmer. Númerið er
# texti, ekki dagsetning, og byrjar aldrei á núlli.
AUDKENNISMYNSTUR = re.compile(r"(?P<source_system>SIL)(?P<event_number>[1-9][0-9]*)")

FEATURE_LYKLAR = frozenset({"type", "geometry", "properties"})
EIGINLEIKAR = frozenset(
    {
        "time",
        "type",
        "depth",
        "event_id",
        "magnitude",
        "magnitude_type",
        "evaluation_mode",
    }
)


@dataclass(frozen=True)
class Skjalfti:
    """Einn sannreyndur atburður, tilbúinn í töfluna ``earthquakes``."""

    event_id: str  # frumgildi úr svarinu
    source_system: str  # afleitt úr event_id
    event_number: str  # afleitt úr event_id
    occurred_at: str  # frumgildi úr svarinu
    utc_day: str  # afleitt úr occurred_at
    magnitude: float
    magnitude_type: str
    depth_km: float
    latitude: float
    longitude: float
    event_type: str
    evaluation_mode: str


def lesa_skjalfta(
    slod: Path | str | None = None, afmorkun: Afmorkun | None = None
) -> list[Skjalfti]:
    """Les og sannreynir alla atburði frosna svarsins, í tímaröð.

    Skilar listanum aðeins ef **hver einasta** færsla stenst afmörkun
    beiðninnar; annars fellur ``SkjalftaVilla``.
    """
    slod = Path(slod) if slod is not None else ATBURDIR
    afmorkun = afmorkun if afmorkun is not None else lesa_afmorkun()

    sedh: dict[str, int] = {}
    skjalftar: list[Skjalfti] = []

    for staeti, faersla in enumerate(lesa_features(slod)):
        skjalfti = _thatta_faerslu(faersla, afmorkun, f"{slod.name} #{staeti}")
        fyrra = sedh.get(skjalfti.event_id)
        if fyrra is not None:
            raise SkjalftaVilla(
                f"{slod.name} #{staeti}: auðkennið {skjalfti.event_id} kom líka "
                f"fyrir í færslu #{fyrra}. Auðkenni verða að vera einkvæm."
            )
        sedh[skjalfti.event_id] = staeti
        skjalftar.append(skjalfti)

    skjalftar.sort(key=lambda s: (s.occurred_at, s.event_id))
    return skjalftar


def talning_eftir_degi(
    skjalftar: list[Skjalfti], dagalisti: list[str]
) -> dict[str, int]:
    """Telur atburði á hvern UTC-dag tímabilsins — dagar án atburðar fá núll."""
    talning = dict.fromkeys(dagalisti, 0)
    for skjalfti in skjalftar:
        if skjalfti.utc_day not in talning:
            raise SkjalftaVilla(
                f"Atburður {skjalfti.event_id} er á {skjalfti.utc_day} sem er utan "
                "tímabils beiðninnar. Dagurinn á sér enga línu í earthquake_days."
            )
        talning[skjalfti.utc_day] += 1
    return talning


def _thatta_faerslu(faersla: object, afmorkun: Afmorkun, hvar: str) -> Skjalfti:
    """Sannreynir eina GeoJSON-færslu og skilar henni sem ``Skjalfti``."""
    ytra = hlutur(faersla, FEATURE_LYKLAR, hvar)
    if ytra.get("type") != "Feature":
        raise SkjalftaVilla(f"{hvar}: type={ytra.get('type')!r}, á að vera 'Feature'.")

    lengd, breidd = hnit(ytra["geometry"], hvar)
    eiginleikar = hlutur(ytra["properties"], EIGINLEIKAR, f"{hvar} properties")

    audkenni = texti(eiginleikar["event_id"], f"{hvar} event_id")
    hlutar = _audkennishlutar(audkenni, afmorkun, hvar)

    stimpill = texti(eiginleikar["time"], f"{hvar} time")
    dagur = _utc_dagur(stimpill, hvar, afmorkun)

    staerd = tala(eiginleikar["magnitude"], f"{hvar} magnitude")
    _innan(staerd, afmorkun.staerd_min, afmorkun.staerd_max, f"{hvar} magnitude")

    dypt = tala(eiginleikar["depth"], f"{hvar} depth")
    _innan(dypt, afmorkun.dypt_min, afmorkun.dypt_max, f"{hvar} depth")

    _innan(lengd, afmorkun.lengd_min, afmorkun.lengd_max, f"{hvar} lengdargráða")
    _innan(breidd, afmorkun.breidd_min, afmorkun.breidd_max, f"{hvar} breiddargráða")

    kvardi = texti(eiginleikar["magnitude_type"], f"{hvar} magnitude_type")
    if not kvardi.strip():
        raise SkjalftaVilla(
            f"{hvar}: magnitude_type er tómur. Stærð án skráðs kvarða er ekki "
            "samanburðarhæf og fer ekki í grunninn."
        )

    tegund = texti(eiginleikar["type"], f"{hvar} type")
    _jafnt(tegund, afmorkun.atburdategund, f"{hvar} type")

    matsadferd = texti(eiginleikar["evaluation_mode"], f"{hvar} evaluation_mode")
    _jafnt(matsadferd, afmorkun.matsadferd, f"{hvar} evaluation_mode")

    return Skjalfti(
        event_id=audkenni,
        source_system=hlutar[0],
        event_number=hlutar[1],
        occurred_at=stimpill,
        utc_day=dagur,
        magnitude=staerd,
        magnitude_type=kvardi,
        depth_km=dypt,
        latitude=breidd,
        longitude=lengd,
        event_type=tegund,
        evaluation_mode=matsadferd,
    )


def _audkennishlutar(audkenni: str, afmorkun: Afmorkun, hvar: str) -> tuple[str, str]:
    """Klýfur SIL-auðkennið í kerfisheiti og atburðanúmer (regex 2)."""
    samsvorun = AUDKENNISMYNSTUR.fullmatch(audkenni)
    if samsvorun is None:
        raise SkjalftaVilla(
            f"{hvar}: auðkennið {audkenni!r} er ekki á forminu SIL<númer>."
        )
    kerfi = samsvorun.group("source_system")
    if kerfi.lower() != afmorkun.kerfi.lower():
        raise SkjalftaVilla(
            f"{hvar}: auðkennið {audkenni!r} kemur ekki úr kerfinu "
            f"{afmorkun.kerfi!r} sem beiðnin bað um."
        )
    return kerfi, samsvorun.group("event_number")


def _utc_dagur(stimpill: str, hvar: str, afmorkun: Afmorkun) -> str:
    """Dregur UTC-daginn út með regex og staðfestir hann með ``datetime``.

    Regex sér um formið, ``datetime`` um að dagurinn og klukkan séu til, og
    afmörkunin um að atburðurinn tilheyri því tímabili sem beðið var um.
    """
    samsvorun = DAGSMYNSTUR.fullmatch(stimpill)
    if samsvorun is None:
        raise SkjalftaVilla(
            f"{hvar}: tímastimpillinn {stimpill!r} er ekki á forminu "
            "YYYY-MM-DDThh:mm:ss[.sss]Z."
        )
    dagur = samsvorun.group("utc_day")

    try:
        tim = datetime.fromisoformat(stimpill.replace("Z", "+00:00"))
    except ValueError as villa:
        raise SkjalftaVilla(
            f"{hvar}: tímastimpillinn {stimpill!r} er ekki til sem dagsetning."
        ) from villa

    tim = tim.astimezone(UTC)
    if tim.date().isoformat() != dagur:
        raise SkjalftaVilla(
            f"{hvar}: daglykillinn {dagur} stemmir ekki við tímastimpilinn "
            f"{stimpill!r}."
        )
    if not afmorkun.upphaf <= tim < afmorkun.endir:
        raise SkjalftaVilla(
            f"{hvar}: {stimpill} er utan tímabils beiðninnar "
            f"({afmorkun.upphaf.isoformat()} til {afmorkun.endir.isoformat()}, "
            "endir undanskilinn)."
        )
    return dagur


def _innan(gildi: float, lagmark: float, hamark: float, hvar: str) -> None:
    """Krefst þess að gildi sé innan þeirra marka sem beiðnin bað um."""
    if not lagmark <= gildi <= hamark:
        raise SkjalftaVilla(
            f"{hvar}: {gildi} er utan marka beiðninnar ({lagmark} til {hamark})."
        )


def _jafnt(gildi: str, vaent: str, hvar: str) -> None:
    """Krefst þess að gildi sé nákvæmlega það sem beiðnin síaði á."""
    if gildi != vaent:
        raise SkjalftaVilla(f"{hvar}: {gildi!r}, beiðnin bað um {vaent!r}.")
