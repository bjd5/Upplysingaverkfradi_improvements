"""Lýsing á beiðni og provenance-sniðið sem hún skrifar (reglur 4 og 8).

Þessi eining veit ekkert um net eða disk. Hún svarar einni spurningu: **hvað
var beðið um, og hvernig er það skráð svo það sé rekjanlegt?**

Sniðið er ekki nýtt. Lyklarnir eru þeir sömu og í frosnu skránni
``data/raw/vedur-quakes/provenance.json`` sem kom úr upprunaverkefninu, og þeir
eru á ensku þess vegna: gögnin sem þegar eru fryst eiga að vera samanburðarhæf
við það sem þetta lag skrifar héðan í frá.

Fingrafar beiðni er reiknað úr provenance-reitunum sjálfum en ekki úr sérstökum
reit. Þess vegna þekkjast líka frosnu skrárnar, sem voru skrifaðar löngu áður en
þetta lag varð til, og sömu gögn eru ekki sótt tvisvar (regla 4).

Leyndarmál eiga ekki heima í ``Beidni``. ``sofnun.http`` tekur við þeim
sérstaklega og þau komast aldrei hingað inn; hulan hér að neðan er seinni
varnarlínan, ekki sú fyrsta.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlencode

SNID_UTGAFA = 1

# Reitirnir sem segja hvaða beiðni var gerð. Breytist einhver þeirra er þetta
# önnur beiðni og svarið er sótt upp á nýtt.
FINGRAFARSREITIR = ("provider", "endpoint", "method", "parameters", "request_body_sha256")

# Haus- og breytuheiti sem bera leyndarmál. Samanburður er á lágstöfum.
VIDKVAEM_HEITI = frozenset({
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "api-key", "api_key", "apikey", "key", "token",
    "access_token", "auth_token", "secret", "client_secret", "password",
})
HULID = "<fjarlægt: leyndarmál>"


@dataclass(frozen=True)
class Beidni:
    """Lýsing á einni beiðni — það sem provenance skráir og fingrafarið byggir á."""

    thjonusta: str                 # mappan undir data/raw/ (ASCII, kebab-case)
    veitandi: str                  # nafn þjónustunnar eins og það birtist í heimildum
    slod: str                      # endapunktur án fyrirspurnarstrengs
    heiti: str = "svar"            # stofn skráarheitisins undir data/raw/<þjónusta>/
    adferd: str = "GET"
    breytur: Mapping[str, object] = field(default_factory=dict)
    hausar: Mapping[str, str] = field(default_factory=dict)
    gagnastofn: bytes | None = None   # POST-líkami, t.d. json-stat2 fyrirspurn
    skjolun: str | None = None        # slóð á skjölun þjónustunnar
    leyfi: str | None = None          # t.d. "CC BY 4.0"
    leyfisslod: str | None = None


def nuna_utc() -> str:
    """Skilar núverandi tíma sem ISO-8601 streng í UTC."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_af(baeti: bytes) -> str:
    """Reiknar SHA-256 af bætum."""
    return hashlib.sha256(baeti).hexdigest()


def hulid(kort: Mapping[str, object]) -> dict[str, object]:
    """Skilar afriti þar sem gildi undir viðkvæmum heitum eru hulin."""
    return {
        nafn: (HULID if str(nafn).lower() in VIDKVAEM_HEITI else gildi)
        for nafn, gildi in kort.items()
    }


def full_slod(slod: str, breytur: Mapping[str, object]) -> str:
    """Setur saman slóð og fyrirspurnarstreng.

    ``doseq=True`` þýðir að listi verður að endurteknu nafni
    (``station_id=1&station_id=2``), sem er formið sem þjónusturnar búast við.
    """
    if not breytur:
        return slod
    return f"{slod}?{urlencode(breytur, doseq=True)}"


def lysing(beidni: Beidni) -> dict:
    """Byggir þann hluta provenance sem lýsir beiðninni sjálfri.

    Öll gildi eru hulin áður en þau eru skrifuð, svo lykill sem slæddist inn í
    ``breytur`` eða ``hausar`` rati hvorki í skrána né í slóðina sem er skráð.
    """
    breytur = hulid(beidni.breytur)
    skjal: dict = {
        "schema_version": SNID_UTGAFA,
        "provider": beidni.veitandi,
        "endpoint": beidni.slod,
    }
    if beidni.skjolun:
        skjal["documentation"] = beidni.skjolun
    skjal["method"] = beidni.adferd
    skjal["parameters"] = breytur
    skjal["request_url"] = full_slod(beidni.slod, breytur)
    skjal["request_headers"] = hulid(beidni.hausar)
    if beidni.gagnastofn is not None:
        skjal["request_body_sha256"] = sha256_af(beidni.gagnastofn)
    return skjal


def _stodludu_breytur(breytur: object) -> object:
    """Gerir breytugildi að texta eins og þau verða í slóðinni.

    Án þessa teldist ``{"size_min": 3}`` önnur beiðni en ``{"size_min": "3"}``
    og sama svarið væri sótt tvisvar.
    """
    if not isinstance(breytur, Mapping):
        return breytur
    stodlud: dict[str, object] = {}
    for nafn, gildi in breytur.items():
        if isinstance(gildi, (list, tuple)):
            stodlud[str(nafn)] = [str(stak) for stak in gildi]
        else:
            stodlud[str(nafn)] = str(gildi)
    return stodlud


def fingrafar(skjal: Mapping[str, object]) -> str:
    """Reiknar fingrafar beiðni úr provenance-reitum hennar.

    Sama fall er notað á nýja beiðni og á provenance sem þegar er á diski, svo
    frosnar skrár úr upprunaverkefninu þekkist líka.
    """
    kjarni = {reitur: skjal.get(reitur) for reitur in FINGRAFARSREITIR}
    kjarni["parameters"] = _stodludu_breytur(kjarni.get("parameters") or {})
    return sha256_af(json.dumps(kjarni, ensure_ascii=False, sort_keys=True).encode("utf-8"))
