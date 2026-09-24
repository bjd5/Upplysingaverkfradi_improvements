"""Geymsla hrágagna undir ``data/raw/`` (reglur 4, 5 og 6).

Hvert svar frá vefþjónustu er vistað **óbreytt** undir ``data/raw/<þjónusta>/``
ásamt provenance-skrá, áður en nokkuð er unnið úr því. Sniðið á provenance er í
``sofnun.beidni``; þessi eining á diskinn.

Tvennt sem hún tryggir:

* **Ekkert hálfskrifað.** Bæði svarið og provenance fara í gegnum tímabundnar
  skrár sem eru færðar á sinn stað í einu lagi. Falli keyrslan í miðju kafi er
  ekkert nýtt komið í ``data/raw/``.
* **Ekkert ósannreynt.** Áður en áður vistað svar er endurnotað er SHA-256 þess
  borið saman við provenance. Stemmi það ekki stöðvast keyrslan; þögult
  skemmt hrágagn væri verra en ekkert (regla 6).
"""

from __future__ import annotations

import json
import logging
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .beidni import Beidni, fingrafar, lysing, nuna_utc, sha256_af

log = logging.getLogger(__name__)

ROT = Path(__file__).resolve().parents[3]
HRAGOGN = ROT / "data" / "raw"

# Regla 1.2: möppu- og skráaheiti eru ASCII, lágstafir og bandstrik. Mynstrið
# er líka varnagli: heitið kemur frá kallanda og ræður slóð undir data/raw/.
HEITAMYNSTUR = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

VIDSKEYTI_PROVENANCE = ".provenance.json"
ARFUR_PROVENANCE = "provenance.json"   # sniðið á frosnu skránum úr upprunaverkefninu

# Skráarending eftir efnistegund svarsins. Óþekkt tegund fer í .bin — svarið er
# geymt óbreytt hvort sem er.
ENDINGAR = {
    "application/json": "json",
    "application/geo+json": "json",
    "text/json": "json",
    "text/html": "html",
    "text/csv": "csv",
    "text/plain": "txt",
    "application/xml": "xml",
    "text/xml": "xml",
}


class HragagnaVilla(RuntimeError):
    """Hrágögn og provenance eiga ekki saman, eða geymslan er ónothæf."""


@dataclass(frozen=True)
class Svar:
    """Vistað svar: bætin sjálf, skráin sem geymir þau og provenance þeirra."""

    baeti: bytes
    slod_skrar: Path
    provenance: dict
    ur_safni: bool   # True: kom úr data/raw/, engin beiðni var send


def stadfesta_heiti(heiti: str, hlutverk: str) -> str:
    """Staðfestir að heiti sé ASCII-kebab-case og því óhætt í slóð (regla 1.2)."""
    if not HEITAMYNSTUR.fullmatch(heiti):
        raise HragagnaVilla(
            f"{hlutverk} '{heiti}' þarf að vera lágstafir, tölustafir og bandstrik "
            f"(regla 1.2) — það ræður slóð undir data/raw/."
        )
    return heiti


def mappa_safns(thjonusta: str, rot: Path = HRAGOGN) -> Path:
    """Skilar möppu þjónustunnar undir ``data/raw/``."""
    return rot / stadfesta_heiti(thjonusta, "Þjónustuheiti")


def provenance_skrar(mappa: Path) -> list[Path]:
    """Skilar provenance-skrám möppunnar í stafrófsröð."""
    if not mappa.is_dir():
        return []
    return sorted(
        skra for skra in mappa.iterdir()
        if skra.is_file()
        and (skra.name.endswith(VIDSKEYTI_PROVENANCE) or skra.name == ARFUR_PROVENANCE)
    )


def _lesa_provenance(slod: Path) -> dict | None:
    """Les provenance-skrá; skilar ``None`` og segir frá sé hún ónýt.

    Ein ónýt skrá stöðvar ekki leitina að hinum, en hún er aldrei þögguð
    (regla 6).
    """
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as villa:
        log.warning("Hunsa ónýta provenance-skrá %s: %s", slod.name, villa)
        return None
    if not isinstance(skjal, dict):
        log.warning("Hunsa %s: provenance á að vera JSON-hlutur.", slod.name)
        return None
    return skjal


def _hragagnaskra(slod_provenance: Path, skjal: Mapping[str, object]) -> Path:
    """Finnur skrána sem provenance lýsir og staðfestir SHA-256 hennar.

    ``raw_file`` er notað þegar það er til staðar. Frosnu skrárnar úr
    upprunaverkefninu hafa það ekki, svo þá er leitað að skrá í möppunni sem ber
    skráðu summuna. Finnist hún ekki er það villa (regla 6).
    """
    mappa = slod_provenance.parent
    summa = skjal.get("sha256")
    if not isinstance(summa, str):
        raise HragagnaVilla(f"{slod_provenance.name} skráir enga SHA-256 summu.")

    nefnd = skjal.get("raw_file")
    if isinstance(nefnd, str):
        kandidat = mappa / Path(nefnd).name
        if kandidat.is_file():
            if sha256_af(kandidat.read_bytes()) != summa:
                raise HragagnaVilla(
                    f"SHA-256 stemmir ekki fyrir {kandidat.name}; hrágögnin hafa "
                    f"breyst frá því þau voru sótt."
                )
            return kandidat

    for skra in sorted(mappa.iterdir()):
        if not skra.is_file() or skra.name.endswith(VIDSKEYTI_PROVENANCE):
            continue
        if skra.name == ARFUR_PROVENANCE:
            continue
        if sha256_af(skra.read_bytes()) == summa:
            return skra

    raise HragagnaVilla(
        f"{slod_provenance.name} lýsir svari sem finnst ekki í {mappa.name}/ — "
        f"engin skrá ber skráðu SHA-256 summuna."
    )


def finna_fyrra_svar(beidni: Beidni, rot: Path = HRAGOGN) -> Svar | None:
    """Skilar áður vistuðu svari við sömu beiðni, annars ``None`` (regla 4).

    Svarið er ekki endurnotað nema SHA-256 þess stemmi við provenance.
    """
    mappa = mappa_safns(beidni.thjonusta, rot)
    leitad = fingrafar(lysing(beidni))

    samsvarandi: list[tuple[str, Path, dict]] = []
    for slod in provenance_skrar(mappa):
        skjal = _lesa_provenance(slod)
        if skjal is None or fingrafar(skjal) != leitad:
            continue
        samsvarandi.append((str(skjal.get("fetched_at_utc") or ""), slod, skjal))

    if not samsvarandi:
        return None

    # Nýjasta sóknin ræður. Skráarheitið segir ekki til um aldur: frosnu
    # skrárnar heita einfaldlega provenance.json.
    _, slod, skjal = max(samsvarandi, key=lambda faersla: faersla[0])
    hragagnaskra = _hragagnaskra(slod, skjal)
    return Svar(
        baeti=hragagnaskra.read_bytes(),
        slod_skrar=hragagnaskra,
        provenance=skjal,
        ur_safni=True,
    )


def _skrifa_atomiskt(skrar: list[tuple[Path, bytes]]) -> None:
    """Skrifar skrár gegnum tímabundnar skrár svo hálfskrifuð gögn verði ekki til."""
    bidstada: list[tuple[Path, Path]] = []
    try:
        for afangastadur, innihald in skrar:
            with tempfile.NamedTemporaryFile(dir=afangastadur.parent, delete=False) as handfang:
                bidstada.append((Path(handfang.name), afangastadur))
                handfang.write(innihald)
        for timabundin, afangastadur in bidstada:
            timabundin.replace(afangastadur)
    finally:
        for timabundin, _ in bidstada:
            timabundin.unlink(missing_ok=True)


def _laus_stofn(mappa: Path, stofn: str) -> str:
    """Skilar skráarstofni sem er ekki þegar í notkun.

    Tvær sóknir á sömu sekúndu fengju annars sama heiti og sú seinni myndi
    yfirskrifa hrágögn þeirrar fyrri (regla 4).
    """
    if not any(mappa.glob(f"{stofn}.*")):
        return stofn
    teljari = 2
    while any(mappa.glob(f"{stofn}-{teljari}.*")):
        teljari += 1
    return f"{stofn}-{teljari}"


def vista_svar(
    beidni: Beidni,
    baeti: bytes,
    *,
    stada: int,
    efnistegund: str | None,
    rot: Path = HRAGOGN,
) -> Svar:
    """Vistar svarið óbreytt ásamt provenance og skilar því (regla 4).

    Skrárnar tvær bera sama stofn og tímastimpil sóknarinnar, svo eldra eintak
    er aldrei yfirskrifað.
    """
    stadfesta_heiti(beidni.heiti, "Skráarstofn")
    mappa = mappa_safns(beidni.thjonusta, rot)
    mappa.mkdir(parents=True, exist_ok=True)

    sott = nuna_utc()
    stimpill = sott.replace("-", "").replace(":", "")
    stofn = _laus_stofn(mappa, f"{beidni.heiti}-{stimpill}")
    ending = ENDINGAR.get((efnistegund or "").split(";")[0].strip().lower(), "bin")
    slod_gagna = mappa / f"{stofn}.{ending}"
    slod_provenance = mappa / f"{stofn}{VIDSKEYTI_PROVENANCE}"

    skjal = lysing(beidni)
    skjal.update({
        "fetched_at_utc": sott,
        "sha256": sha256_af(baeti),
        "response_bytes": len(baeti),
        "status_code": stada,
        "content_type": efnistegund,
        "raw_file": slod_gagna.name,
    })
    if beidni.leyfi:
        skjal["license"] = beidni.leyfi
    if beidni.leyfisslod:
        skjal["license_url"] = beidni.leyfisslod

    _skrifa_atomiskt([
        (slod_gagna, baeti),
        (slod_provenance,
         (json.dumps(skjal, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
    ])
    log.info("Vistaði %d bæti í %s/%s", len(baeti), mappa.name, slod_gagna.name)
    return Svar(baeti=baeti, slod_skrar=slod_gagna, provenance=skjal, ur_safni=False)
