"""Mat á nothæfi veðurstöðva fyrir VR-II (issue #14, pakki P2.4).

Síðasti hluti ``src/vedurstofa_stodvar.py`` í upprunaverkefninu sem enn var
ófluttur: *greiningin* sem velur stöðina sem forritið á að lesa og reiknar
tölurnar í svörum æfingarinnar. Annað úr skriftunni er þegar komið í tréð:

* sókn og vistun hrás svars — ``sofnun/sofn.py`` (#13),
* þáttun og sannreyning svarsins — ``vedurstodvar_faersla.py`` (#8),
* síurnar ``active``, ``polygon`` og ``station_id`` — SQL í
  ``src/sql/queries/vedurstodvar-*.sql`` og ``vedurstodvar_samanburdur.py`` (#8, #11),
* fjarlægð, kassinn og föstu hnitin — ``vedurstodvar_samanburdur.py`` (#8).

Þeir hlutar eru endurnýttir hér en ekki tvíteknir.

Matið fylgir gömlu skriftunni skref fyrir skref, svo sama inntak gefi sömu tölur:

1. Stöðvarnar innan kassans um VR-II eru raðaðar eftir fjarlægð (óúnnaðri).
2. Næsta stöð í kassanum er skoðuð, hvort sem hún er virk eða ekki.
3. Stöðin sem forritið les er næsta **virka** stöð í kassanum.
4. Næsta aflagða stöð í kassanum og fjarlægðarmunurinn á henni og þeirri virku.
5. Hvort valda stöðin nær aftur til viðmiðunarársins — og ef ekki, hver er
   næsta virka stöð í **öllu** eintakinu sem gerir það.

**Eitt frávik frá gömlu skriftunni, af ásettu ráði:** viðmiðunarárið er
``VIDMIDSAR - AR_AFTUR_I_TIMANN`` en ekki ``date.today().year - 50``. Gamla
skriftan gaf aðra niðurstöðu eftir því hvaða ár hún var keyrð; hér er matið
hrein afleiða af frosna eintakinu. Árið 2026 gefa báðar leiðir 1976.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .vedurstodvar_faersla import Stod
from .vedurstodvar_samanburdur import (
    AR_AFTUR_I_TIMANN,
    METRAR_I_KM,
    RADIUS_KM,
    VIDMIDSAR,
    VR_II_BREIDD,
    VR_II_LENGD,
    haversine_km,
    kassi,
)

PROSENT = 100


class MatVilla(RuntimeError):
    """Eintakið býður ekki upp á matið sem æfingin gerir ráð fyrir."""


@dataclass(frozen=True)
class StodIFjarlaegd:
    """Ein stöð með fjarlægð frá viðmiðunarpunktinum, í heilum metrum.

    Metrarnir eru rúnnaðir eins og gamla síðan birti þá. ``km`` er óúnnaða
    fjarlægðin sem röðunin og fjarlægðarmunurinn eru reiknuð á.
    """

    station_id: int
    name: str
    km: float
    metrar: int
    start_year: int
    end_year: int | None

    @property
    def er_virk(self) -> bool:
        """Virk stöð hefur ekkert lokaár — sama skilyrði og ``Stod.er_virk``."""
        return self.end_year is None


@dataclass(frozen=True)
class Mat:
    """Niðurstaða matsins: tölurnar sem svör æfingarinnar eru byggð á."""

    breidd: float
    lengd: float
    radius_km: float
    kassi: tuple[float, float, float, float]
    fjoldi_allra: int
    fjoldi_virkra: int
    hlutfall_virkra_prosent: int
    naestu: tuple[StodIFjarlaegd, ...]
    naesta: StodIFjarlaegd
    valin: StodIFjarlaegd
    naesta_aflogd: StodIFjarlaegd | None
    munur_metrar: int | None
    vidmidunarar: int
    valin_naer_aftur: bool
    langtimastod: StodIFjarlaegd | None


def _i_kassa(stod: Stod, mork: tuple[float, float, float, float]) -> bool:
    """Sama skilyrði og ``polygon``-sían: báðir ásar innan marka, jaðrar meðtaldir."""
    min_lengd, min_breidd, max_lengd, max_breidd = mork
    return min_lengd <= stod.lon <= max_lengd and min_breidd <= stod.lat <= max_breidd


def rada_eftir_fjarlaegd(
    stodvar: Sequence[Stod], breidd: float, lengd: float
) -> list[StodIFjarlaegd]:
    """Raðar stöðvum eftir fjarlægð frá hnitunum, næsta fyrst.

    Röðunin er á óúnnaðri fjarlægð eins og í gömlu skriftunni: tvær stöðvar
    sem rúnnast í sama metrafjölda halda réttri innbyrðis röð. ``sorted`` er
    stöðugt, svo jöfn fjarlægð heldur röð eintaksins.
    """
    med_km = sorted(
        ((haversine_km(breidd, lengd, stod.lat, stod.lon), stod) for stod in stodvar),
        key=lambda par: par[0],
    )
    return [
        StodIFjarlaegd(
            station_id=stod.station_id,
            name=stod.name,
            km=km,
            metrar=round(km * METRAR_I_KM),
            start_year=stod.start_year,
            end_year=stod.end_year,
        )
        for km, stod in med_km
    ]


def _fyrsta(
    stodvar: Sequence[StodIFjarlaegd], skilyrdi: Callable[[StodIFjarlaegd], bool]
) -> StodIFjarlaegd | None:
    """Fyrsta stöðin í röðinni sem stenst skilyrðið, eða ``None``."""
    return next((stod for stod in stodvar if skilyrdi(stod)), None)


def hlutfall_prosent(hluti: int, heild: int) -> int:
    """Hlutfall í heilum prósentum, rúnnað eins og gamla síðan birti það (44 %)."""
    if heild <= 0:
        raise MatVilla(f"Hlutfall af {heild} stöðvum er ekki skilgreint.")
    return round(PROSENT * hluti / heild)


def meta(
    stodvar: Sequence[Stod],
    breidd: float = VR_II_BREIDD,
    lengd: float = VR_II_LENGD,
    radius_km: float = RADIUS_KM,
    vidmidunarar: int = VIDMIDSAR - AR_AFTUR_I_TIMANN,
) -> Mat:
    """Metur hvaða stöð forritið á að lesa og reiknar tölur svaranna.

    Þrjú tilvik stöðva matið með skýrri villu frekar en að skila hálfu svari
    (regla 6) — öll þýða að eintakið er ekki eins og æfingin gerir ráð fyrir:
    tómt eintak, engin stöð í kassanum og engin *virk* stöð í kassanum.
    """
    if not stodvar:
        raise MatVilla("Eintakið er tómt — engin stöð til að meta.")

    mork = kassi(breidd, lengd, radius_km)
    naestu = rada_eftir_fjarlaegd(
        [stod for stod in stodvar if _i_kassa(stod, mork)], breidd, lengd
    )
    if not naestu:
        raise MatVilla(
            f"Engin stöð fannst innan {radius_km:g} km kassans um ({breidd}, {lengd}). "
            "Athugaðu hnitin og kassann áður en matið er notað."
        )

    valin = _fyrsta(naestu, lambda stod: stod.er_virk)
    if valin is None:
        raise MatVilla(
            f"Engin virk stöð (ekkert lokaár) innan {radius_km:g} km kassans. "
            "Stækkaðu radíusinn eða athugaðu hvort stöðvaskráin hafi breyst."
        )

    naesta_aflogd = _fyrsta(naestu, lambda stod: not stod.er_virk)
    munur = None
    if naesta_aflogd is not None:
        # Munurinn er reiknaður á óúnnaðri fjarlægð og rúnnaður í lokin, eins og
        # gamla skriftan gerði — ekki mismunur tveggja rúnnaðra talna.
        munur = round(abs(naesta_aflogd.km - valin.km) * METRAR_I_KM)

    valin_naer_aftur = valin.start_year <= vidmidunarar
    if valin_naer_aftur:
        langtimastod: StodIFjarlaegd | None = valin
    else:
        # Leitað í öllu eintakinu en ekki aðeins í kassanum, eins og gamla
        # skriftan gerði: löng tímaröð getur legið utan 5 km.
        langtimastod = _fyrsta(
            rada_eftir_fjarlaegd(stodvar, breidd, lengd),
            lambda stod: stod.er_virk and stod.start_year <= vidmidunarar,
        )

    fjoldi_virkra = sum(1 for stod in stodvar if stod.er_virk)
    return Mat(
        breidd=breidd,
        lengd=lengd,
        radius_km=radius_km,
        kassi=mork,
        fjoldi_allra=len(stodvar),
        fjoldi_virkra=fjoldi_virkra,
        hlutfall_virkra_prosent=hlutfall_prosent(fjoldi_virkra, len(stodvar)),
        naestu=tuple(naestu),
        naesta=naestu[0],
        valin=valin,
        naesta_aflogd=naesta_aflogd,
        munur_metrar=munur,
        vidmidunarar=vidmidunarar,
        valin_naer_aftur=valin_naer_aftur,
        langtimastod=langtimastod,
    )

