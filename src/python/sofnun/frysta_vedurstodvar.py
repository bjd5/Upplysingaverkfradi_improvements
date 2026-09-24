"""Sækir EITT eintak af stöðvalista Veðurstofunnar og frystir það (regla 4).

Þetta safn er annars eðlis en hin: **ekkert eldra eintak er til.** Gamla
verkefnið sótti stöðvalistann upp á nýtt í hverri byggingu og vistaði svarið
aldrei, svo gamla veðurstöðvasíðan sýndi aðrar tölur í dag en í gær. Tölurnar
sem þetta eintak gefur víkja því frá gömlu síðunni — það er vænt niðurstaða,
ekki villa. Samanburðurinn er í ``src/python/vinnsla/vedurstodvar_samanburdur.py``.

Ein beiðni er send, ósíuð. Gamla skriftan sendi fimm — ósíaða og fjórar síaðar
— en síurnar (``active``, ``polygon``, ``station_id``) velja allar úr sama
mengi, svo ósíaða svarið er yfirmengi þeirra allra og hinar fjórar má reikna
staðbundið. Fjórar beiðnir sem engu bæta við eru álag á þjónustu sem gefur
gögnin frítt (regla 4).

Keyrsla frá rót verkefnisins::

    python3 src/python/sofnun/frysta_vedurstodvar.py

Skriftan sækir ekki neitt sé eintak þegar til — regla 4 bannar að sækja sömu
gögn tvisvar að óþörfu. Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

try:  # keyrt beint: python3 src/python/sofnun/frysta_vedurstodvar.py
    from hragogn import (
        ROT, PROVENANCE_HEITI, log, lysa_skrar, notandi_audkenni, nuna_utc,
        skra_safn, timastimpill,
    )
except ImportError:  # flutt inn sem eining innan pakkans
    from .hragogn import (
        ROT, PROVENANCE_HEITI, log, lysa_skrar, notandi_audkenni, nuna_utc,
        skra_safn, timastimpill,
    )

HEITI = "vedurstodvar"
MAPPA = "data/raw/vedurstodvar"

ENDAPUNKTUR = "https://api.vedur.is/weather/stations"
SKJOLUN = "https://api.vedur.is/weather/openapi.json"
# Leyfið er ekki ágiskun: openapi.json þjónustunnar (info.license) skráir
# CC BY 4.0 fyrir Weather API, staðfest við söfnun.
LEYFI = "CC BY 4.0"
LEYFI_SLOD = "https://creativecommons.org/licenses/by/4.0/"

BID_SEKUNDUR = 60  # þolinmæði gagnvart þjónustunni, ekki hraðatakmörkun
# Svarhausar sem eru skráðir í provenance. Þeir segja hvað þjónustan sjálf
# sagði um svarið og eru sjálfstæð heimild á móti því sem við skráum.
SKRADIR_HAUSAR = ("content-type", "date", "last-modified", "etag")


class VedurstofuVilla(RuntimeError):
    """Skýr villa þegar ekki tekst að sækja nothæfan stöðvalista."""


def saekja(audkenni: str) -> tuple[bytes, dict[str, str]]:
    """Sendir eina GET-beiðni og skilar svarinu ÓBREYTTU sem bætum.

    Svarið er ekki þáttað hér: regla 4 krefst þess að það sem vistað er sé
    nákvæmlega það sem þjónustan sendi, ekki endurritun þess.
    """
    beidni = urllib.request.Request(
        ENDAPUNKTUR, headers={"User-Agent": audkenni, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(beidni, timeout=BID_SEKUNDUR) as svar:
            baet = svar.read()
            hausar = {
                heiti: svar.headers[heiti]
                for heiti in SKRADIR_HAUSAR
                if svar.headers.get(heiti) is not None
            }
    except urllib.error.HTTPError as villa:  # þjónustan svaraði, en með villu
        raise VedurstofuVilla(
            f"{ENDAPUNKTUR} svaraði HTTP {villa.code} ({villa.reason})."
        ) from villa
    except (urllib.error.URLError, TimeoutError) as villa:  # ekkert samband
        raise VedurstofuVilla(
            f"Náði ekki sambandi við {ENDAPUNKTUR}: {villa}. "
            "Ekkert var vistað; reyndu aftur síðar."
        ) from villa
    if not baet:
        raise VedurstofuVilla(f"{ENDAPUNKTUR} skilaði tómu svari.")
    return baet, hausar


def sannreyna(baet: bytes) -> int:
    """Þáttar vistaða svarið og skilar fjölda stöðva.

    Kallað EFTIR að svarið er vistað: hráa svarið er heimildin og það á að
    liggja á disknum líka þótt innihaldið bregðist (regla 4). Frávik stöðva
    keyrsluna með skýringu — þögult tómt safn er verra en engin frysting.
    """
    try:
        gogn = json.loads(baet)
    except json.JSONDecodeError as villa:
        raise VedurstofuVilla(
            f"Svarið frá {ENDAPUNKTUR} er ekki gilt JSON: {villa}. "
            "Hráa svarið var samt vistað — skoðaðu það."
        ) from villa
    if not isinstance(gogn, list) or not gogn:
        raise VedurstofuVilla(
            f"Bjóst við ótæmdu fylki frá {ENDAPUNKTUR} en fékk "
            f"{type(gogn).__name__} með {len(gogn) if hasattr(gogn, '__len__') else '?'} stökum."
        )
    return len(gogn)


def skrifa_provenance(skraarheiti: str, baet: bytes, hausar: dict, audkenni: str,
                      fjoldi_stodva: int, sha256: str) -> None:
    """Skrifar ``data/raw/vedurstodvar/provenance.json`` í sama sniði og vedur-quakes."""
    skjal = {
        "provider": "Veðurstofa Íslands",
        "endpoint": ENDAPUNKTUR,
        "documentation": SKJOLUN,
        "method": "GET",
        "parameters": {},
        "request_url": ENDAPUNKTUR,
        "request_headers": {"Accept": "application/json", "User-Agent": audkenni},
        "response_file": skraarheiti,
        "response_headers": hausar,
        "fetched_at_utc": nuna_utc(),
        "sha256": sha256,
        "response_bytes": len(baet),
        "station_count": fjoldi_stodva,
        "license": LEYFI,
        "license_url": LEYFI_SLOD,
        "collection_method": "ny_sofnun",
        "note_is": (
            "NÝ SÖFNUN. Ekkert eldra eintak er til: gamla verkefnið sótti "
            "stöðvalistann upp á nýtt í hverri byggingu og vistaði svarið aldrei. "
            "Tölurnar hér víkja því frá þeim sem gamla síðan birti, og gamla síðan "
            "var sjálf aldrei stöðug milli bygginga. Samanburðurinn við frosna "
            "viðmiðið er í docs/vedurstodvar-samanburdur.md."
        ),
        "note_filters_is": (
            "Ósíað svar. Síurnar active, polygon og station_id velja úr þessu "
            "sama mengi, svo síuðu svörin fjögur sem gamla síðan sótti eru "
            "reiknuð staðbundið úr þessu eintaki."
        ),
    }
    (ROT / MAPPA / PROVENANCE_HEITI).write_text(
        json.dumps(skjal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def frysta() -> int:
    """Sækir stöðvalistann einu sinni, vistar hann óbreyttan og skráir frystinguna."""
    mappa = ROT / MAPPA
    fyrri = sorted(mappa.glob("stations-*.json")) if mappa.is_dir() else []
    if fyrri:
        # Regla 4: sömu gögn eru ekki sótt tvisvar að óþörfu.
        log.info(
            "Eintak er þegar til (%s) — sæki ekki aftur. Eyddu möppunni viljandi "
            "ef nýtt eintak er ætlunin.",
            fyrri[-1].relative_to(ROT),
        )
        return 0

    audkenni = notandi_audkenni()
    baet, hausar = saekja(audkenni)

    mappa.mkdir(parents=True, exist_ok=True)
    skraarheiti = f"stations-{timastimpill()}.json"
    (mappa / skraarheiti).write_bytes(baet)  # óbreytt, ÁÐUR en nokkuð er unnið
    log.info("Vistaði %s — %d bæti", f"{MAPPA}/{skraarheiti}", len(baet))

    fjoldi_stodva = sannreyna(baet)
    skrar = lysa_skrar(mappa)
    sha256 = next(skra["sha256"] for skra in skrar if skra["slod"] == skraarheiti)
    skrifa_provenance(skraarheiti, baet, hausar, audkenni, fjoldi_stodva, sha256)

    skrar = lysa_skrar(mappa, {skraarheiti: sha256})
    skra_safn(
        {
            "heiti": HEITI,
            "mappa": MAPPA,
            "adferd": "ny_sofnun",
            "skyring": (
                f"Ósíaður stöðvalisti Veðurstofunnar, {fjoldi_stodva} stöðvar, sóttur "
                "einu sinni af api.vedur.is/weather/stations. NÝ SÖFNUN — ekkert eldra "
                "eintak er til, svo tölurnar víkja frá gömlu síðunni. Leyfi: CC BY 4.0."
            ),
            "les_skrifta": "src/python/vinnsla/vedurstodvar_samanburdur.py; P1.4 (issue #8)",
            "uppruni": ENDAPUNKTUR,
            "upprunarepo": None,
            "frosid_utc": nuna_utc(),
            "fjoldi_skraa": len(skrar),
            "staerd_baet": sum(skra["staerd_baet"] for skra in skrar),
            "fjoldi_sannreyndra": sum(1 for skra in skrar if skra["stadfest_vid_provenance"]),
            "fjoldi_stodva": fjoldi_stodva,
            "skrar": skrar,
        }
    )
    log.info("%s: %d stöðvar frystar", MAPPA, fjoldi_stodva)
    return 0


def main(rok: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(rok)
    return frysta()


if __name__ == "__main__":
    sys.exit(main())
