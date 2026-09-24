"""Sameiginlegt HTTP-lag fyrir alla gagnasöfnun (regla 4).

Allar vefbeiðnir verkefnisins fara hér í gegn, svo kröfur reglu 4 séu uppfylltar
á einum stað í stað þess að hver söfnunarskrifta útfæri þær upp á eigin spýtur:

* **Auðkenning.** ``User-Agent`` nefnir verkefnið og tengilið. Tengiliðurinn
  kemur úr umhverfinu (``NOTANDA_AUDKENNI``), aldrei úr kóða — repo-ið er opið.
* **Hraðatakmörkun.** Lágmarksbið milli kalla á sömu þjónustu
  (``BID_MILLI_KALLA``, sjálfgefið 1 sekúnda).
* **Endurtilraunir.** Vaxandi bið, fast þak á fjölda tilrauna, og aðeins þegar
  villan getur lagast: tímamörk, netvilla, HTTP 429 eða 5xx. HTTP 404 lagast
  ekki við að spyrja aftur.
* **Engin þögul villa.** Hvert einasta frávik endar í ``HttpVilla`` með skýringu
  (reglur 4 og 6). Ekkert er vistað þegar beiðni bregst.
* **Hrágögn fyrst.** Svarið er vistað óbreytt í ``data/raw/<þjónusta>/`` ásamt
  provenance áður en nokkuð er unnið úr því.
* **Engin tvítekin sókn.** Sé sama beiðni þegar til í ``data/raw/`` er hún ekki
  send aftur (sjá ``sofnun.hragogn.finna_fyrra_svar``).

Lyklar eru aldrei hluti af ``Beidni``. Þeir eru gefnir ``saekja`` sérstaklega
(``leynihausar``, ``leynibreytur``), fara í beiðnina sjálfa og hvergi annað:
hvorki í provenance, logg né villuboð. Slóðin sem er skráð og birt er alltaf
hulda útgáfan.

Eingöngu Python-staðalsafnið (``urllib.request``) — regla 10.

Athugið: einingin heitir ``http`` innan ``sofnun``-pakkans. Flutt inn sem
``sofnun.http`` skyggir hún ekki á ``http`` úr staðalsafninu, en hún er þess
vegna **aldrei keyrð beint** (``python3 src/python/sofnun/http.py``) — þá færi
mappan sjálf fremst á ``sys.path`` og ``urllib`` fyndi þessa skrá.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import stillingar
from .beidni import Beidni, full_slod, lysing
from .hragogn import HRAGOGN, Svar, finna_fyrra_svar, vista_svar

log = logging.getLogger(__name__)

# Verkefnið auðkennir sig sjálft; tengiliðurinn kemur úr umhverfinu.
VERKEFNI = "Upplysingaverkfraedi-rannsokn/1.0"
UMHVERFI_TENGILIDUR = "NOTANDA_AUDKENNI"
UMHVERFI_BID = "BID_MILLI_KALLA"

SJALFGEFIN_BID = 1.0      # sekúndur milli kalla á sömu þjónustu
TILRAUNIR = 3             # þak á fjölda tilrauna, fyrsta tilraun meðtalin
BID_GRUNNUR = 2.0         # sekúndur fyrir fyrstu endurtilraun, tvöfaldast síðan
BID_HAMARK = 60.0         # þak á bið milli tilrauna, líka á Retry-After
TIMAMORK = 30.0           # sekúndur á hverja beiðni
HAMARK_SVARS = 25_000_000  # bæti; stærra svar er ekki það sem beðið var um

# Villur sem geta lagast af sjálfu sér: of margar beiðnir, eða þjónustan í lagi
# en tímabundið óstarfhæf. Allt annað (t.d. 401, 404) lagast ekki við bið.
ENDURTAKANLEG_STODUGILDI = frozenset({408, 425, 429, 500, 502, 503, 504})

# Hvenær síðast var kallað á hverja þjónustu, mælt með monotonic klukku.
_SIDASTA_KALL: dict[str, float] = {}


class HttpVilla(RuntimeError):
    """Beiðni tókst ekki og ekkert var vistað. Ber aldrei lykil í skilaboðum."""


def notandaaudkenni(tengilidur: str | None = None) -> str:
    """Byggir ``User-Agent`` sem auðkennir verkefnið og ber tengilið (regla 4).

    Tengiliðurinn kemur úr ``NOTANDA_AUDKENNI`` (umhverfi eða ``.env``) nema
    hann sé gefinn beint. Vanti hann er beiðnin ekki send: ómerkt umferð á
    vefþjónustu annarra er ekki í boði.
    """
    gildi = tengilidur if tengilidur is not None else stillingar.krefjast(
        UMHVERFI_TENGILIDUR,
        "hún geymir tengiliðinn sem auðkennir verkefnið gagnvart vefþjónustunni",
    )
    gildi = gildi.strip()
    if not gildi:
        raise HttpVilla(f"{UMHVERFI_TENGILIDUR} er tómt; beiðnin væri ómerkt.")
    if any(ord(stafur) < 32 or ord(stafur) == 127 for stafur in gildi):
        # Stýristafur í haus er höfuðlínuinnspýting, ekki tengiliður.
        raise HttpVilla(f"{UMHVERFI_TENGILIDUR} má ekki innihalda stýristafi.")
    return f"{VERKEFNI} ({gildi})"


def bid_milli_kalla() -> float:
    """Skilar lágmarksbið milli kalla á sömu þjónustu, í sekúndum."""
    return max(0.0, stillingar.tala(UMHVERFI_BID, SJALFGEFIN_BID))


def hreinsa_hradaminni() -> None:
    """Gleymir hvenær síðast var kallað. Fyrir próf og langkeyrandi ferli."""
    _SIDASTA_KALL.clear()


def _bida_hradatakmorkun(thjonusta: str, sofa: Callable[[float], None]) -> None:
    """Bíður þar til leyfileg bið frá síðasta kalli á þjónustuna er liðin."""
    sidast = _SIDASTA_KALL.get(thjonusta)
    if sidast is not None:
        eftir = bid_milli_kalla() - (time.monotonic() - sidast)
        if eftir > 0:
            log.debug("Hraðatakmörkun: bíð %.2f s fyrir %s", eftir, thjonusta)
            sofa(eftir)
    _SIDASTA_KALL[thjonusta] = time.monotonic()


def _bid_endurtilraunar(villa: OSError, tilraun: int) -> float | None:
    """Skilar bið fyrir næstu tilraun, eða ``None`` sé villan ekki endurtakanleg.

    Biðin tvöfaldast milli tilrauna. Biðji þjónustan sjálf um ákveðna bið
    (``Retry-After``) er farið eftir henni, þó aldrei lengur en ``BID_HAMARK``.
    """
    if isinstance(villa, HTTPError):
        if villa.code not in ENDURTAKANLEG_STODUGILDI:
            return None
        badst_um = villa.headers.get("Retry-After") if villa.headers else None
        if badst_um is not None:
            try:
                return min(max(0.0, float(badst_um)), BID_HAMARK)
            except ValueError:
                # Retry-After má líka vera dagsetning. Þá gildir okkar eigin bið.
                log.debug("Retry-After var ekki tala; nota eigin bið.")
    return min(BID_GRUNNUR * 2 ** (tilraun - 1), BID_HAMARK)


def _villuskilabod(veitandi: str, skrad_slod: str, villa: OSError, tilraunir: int) -> str:
    """Setur saman villuboð án lykla — slóðin er hulda útgáfan."""
    if isinstance(villa, HTTPError):
        adalatridi = f"{veitandi} svaraði HTTP {villa.code}"
    elif isinstance(villa, URLError):
        adalatridi = f"Náði ekki sambandi við {veitandi}: {villa.reason}"
    else:
        adalatridi = f"Beiðni til {veitandi} brást: {type(villa).__name__}"
    eftir_tilraunir = f" eftir {tilraunir} tilraunir" if tilraunir > 1 else ""
    return f"{adalatridi}{eftir_tilraunir} ({skrad_slod}); ekkert var vistað."


def _senda(
    beidni: Beidni,
    slod: str,
    hausar: Mapping[str, str],
    *,
    opnari: Callable[..., object],
    timamork: float,
    hamark_baeta: int,
) -> tuple[bytes, int, str | None]:
    """Sendir eina beiðni og skilar (bæti, stöðugildi, efnistegund)."""
    hlutur = Request(slod, data=beidni.gagnastofn, headers=dict(hausar), method=beidni.adferd)
    with opnari(hlutur, timeout=timamork) as svar:
        stada = svar.status if hasattr(svar, "status") else svar.getcode()
        efnistegund = svar.headers.get("Content-Type") if svar.headers else None
        # Einu bæti meira en leyfilegt er, svo of stórt svar þekkist án þess að
        # allt sé lesið í minni.
        baeti = svar.read(hamark_baeta + 1)
    return baeti, stada, efnistegund


def saekja(
    beidni: Beidni,
    *,
    leynihausar: Mapping[str, str] | None = None,
    leynibreytur: Mapping[str, object] | None = None,
    thvinga: bool = False,
    rot: Path = HRAGOGN,
    opnari: Callable[..., object] = urlopen,
    sofa: Callable[[float], None] = time.sleep,
    timamork: float = TIMAMORK,
    hamark_baeta: int = HAMARK_SVARS,
) -> Svar:
    """Sækir gögn og vistar svarið óbreytt í ``data/raw/`` ásamt provenance.

    Sé sama beiðni þegar til í ``data/raw/`` er ekkert kall sent og vistaða
    svarið skilað (``Svar.ur_safni`` er þá ``True``). ``thvinga=True`` sækir
    nýtt eintak hvað sem líður geymslunni — notað þegar ætlunin er einmitt að ná
    í ferskt eintak, t.d. nýja forsíðu.

    Lyklar eru gefnir í ``leynihausar``/``leynibreytur``. Þeir fara í beiðnina
    og hvergi annað: ekki í provenance, ekki í logg, ekki í villuboð (regla 4).

    ``opnari`` og ``sofa`` eru stillanleg svo prófin keyri án nets og án biðar.

    Fellur með ``HttpVilla`` ef ekki tekst að ná nothæfu svari; þá er ekkert
    skrifað í ``data/raw/``.
    """
    if not thvinga:
        fyrra = finna_fyrra_svar(beidni, rot)
        if fyrra is not None:
            log.info(
                "Sleppi kalli á %s — sama beiðni er þegar í %s",
                beidni.veitandi, fyrra.slod_skrar.name,
            )
            return fyrra

    hausar = {
        "User-Agent": notandaaudkenni(),
        **dict(beidni.hausar),
        **dict(leynihausar or {}),
    }
    slod = full_slod(beidni.slod, {**dict(beidni.breytur), **dict(leynibreytur or {})})
    skrad_slod = lysing(beidni)["request_url"]   # hulin slóð; óhætt í logg og villuboð

    for tilraun in range(1, TILRAUNIR + 1):
        _bida_hradatakmorkun(beidni.thjonusta, sofa)
        log.info("%s %s (tilraun %d/%d)", beidni.adferd, skrad_slod, tilraun, TILRAUNIR)
        try:
            baeti, stada, efnistegund = _senda(
                beidni, slod, hausar,
                opnari=opnari, timamork=timamork, hamark_baeta=hamark_baeta,
            )
        except (HTTPError, URLError, TimeoutError, OSError) as villa:
            bid = _bid_endurtilraunar(villa, tilraun)
            if bid is None or tilraun == TILRAUNIR:
                raise HttpVilla(
                    _villuskilabod(beidni.veitandi, skrad_slod, villa, tilraun)
                ) from villa
            log.warning(
                "Tilraun %d/%d á %s brást (%s); reyni aftur eftir %.1f s",
                tilraun, TILRAUNIR, beidni.veitandi, type(villa).__name__, bid,
            )
            sofa(bid)
            continue

        if stada != 200:
            raise HttpVilla(
                f"{beidni.veitandi} svaraði HTTP {stada} ({skrad_slod}); ekkert var vistað."
            )
        if len(baeti) > hamark_baeta:
            raise HttpVilla(
                f"Svar frá {beidni.veitandi} er stærra en leyfð {hamark_baeta} bæti "
                f"({skrad_slod}); ekkert var vistað."
            )
        if not baeti:
            raise HttpVilla(
                f"{beidni.veitandi} skilaði tómu svari ({skrad_slod}); ekkert var vistað."
            )
        # Regla 4: hrágögnin fara á disk áður en nokkuð er unnið úr þeim.
        return vista_svar(beidni, baeti, stada=stada, efnistegund=efnistegund, rot=rot)

    # Lykkjan skilar eða fellur alltaf; þetta er varnagli gegn þöglu falli.
    raise HttpVilla(f"Beiðni til {beidni.veitandi} lauk án svars ({skrad_slod}).")
