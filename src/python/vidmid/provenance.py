"""Provenance fyrir frosna viðmiðið í docs/vidmid/ og data/raw/mbl/.

Skrárnar í þessum möppum eru **afrit** af gögnum sem voru aðeins til á einni
vél og hvergi í git. Þær eru sönnunargagn: nýja síðan á að sýna sömu tölur og
sú gamla (sjá docs/endurbygging.md, kafli 2). Þess vegna þarf að vera hægt að
sanna hvenær sem er að afritið sé ósnert.

Þessi eining reiknar SHA-256 fyrir hverja skrá og skrifar docs/vidmid/provenance.json,
og les svo sömu skrá aftur til að staðfesta að ekkert hafi breyst.

Keyrsla:
    python3 src/python/vidmid/provenance.py skrifa      # býr til provenance.json
    python3 src/python/vidmid/provenance.py stadfesta   # ber saman við diskinn
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

try:  # keyrt beint: python3 src/python/vidmid/provenance.py
    from sofn import BYGGINGARLOTUR, SOFN, VIDMIDSREPO
except ImportError:  # flutt inn sem eining innan pakkans
    from .sofn import BYGGINGARLOTUR, SOFN, VIDMIDSREPO

ROT = Path(__file__).resolve().parents[3]
PROVENANCE = ROT / "docs" / "vidmid" / "provenance.json"
SNID_UTGAFA = 1
BUFFER_BAET = 1 << 20  # 1 MiB í einu — 4,3 MB af HTML fer ekki allt í minni



logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("provenance")


def nuna_utc() -> str:
    """Skilar núverandi tíma sem ISO-8601 streng í UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_af(skra: Path) -> str:
    """Reiknar SHA-256 af skrá, lesinni í bútum svo stórar skrár rúmist í minni."""
    summa = hashlib.sha256()
    with skra.open("rb") as opin:
        for butur in iter(lambda: opin.read(BUFFER_BAET), b""):
            summa.update(butur)
    return summa.hexdigest()


def skrar_i(mappa: Path) -> list[Path]:
    """Skilar öllum skrám undir möppu í stafrófsröð, án .DS_Store og sambærilegs."""
    return sorted(
        skra
        for skra in mappa.rglob("*")
        if skra.is_file() and not skra.name.startswith(".")
    )


def lysa_skra(skra: Path, safn: dict) -> dict:
    """Byggir provenance-færslu fyrir eina skrá."""
    afstaeð = skra.relative_to(ROT / safn["mappa"]).as_posix()
    breytt = datetime.fromtimestamp(skra.stat().st_mtime, timezone.utc)
    return {
        "slod": afstaeð,
        "uppruni": f"{safn['uppruni']}/{afstaeð}",
        "staerd_baet": skra.stat().st_size,
        "sha256": sha256_af(skra),
        # Breytingartími fylgdi með afritinu (cp -p). Fyrir byggðu síðuna er
        # hann byggingartíminn og þar með eina beina vísbendingin um hvaða
        # commit var undir þegar hún var byggð.
        "breytt_utc": breytt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def greina_byggingarlotur(vefsafn: dict) -> dict:
    """Raðar HTML-síðum byggðu síðunnar á byggingarlotur eftir breytingartíma.

    Hver lota svarar til eins commits í upprunarepo-inu (sjá BYGGINGARLOTUR).
    Síða sem fellur utan allra lota er skráð sérstaklega svo hún hverfi ekki.
    """
    lotur = [{**lota, "sidur": []} for lota in BYGGINGARLOTUR]
    oflokkad: list[str] = []

    for skra in vefsafn["skrar"]:
        if not skra["slod"].endswith(".html"):
            continue  # site_libs og myndir fylgja Quarto, ekki efninu
        for lota in lotur:
            if lota["fra_utc"] <= skra["breytt_utc"] <= lota["til_utc"]:
                lota["sidur"].append(skra["slod"])
                break
        else:
            oflokkad.append(skra["slod"])

    return {
        "spurning": "Úr hvaða commit er byggða síðan í docs/vidmid/vefur/?",
        "svar": (
            "Ekki einu — þremur. Quarto endurbyggði aðeins breyttar síður, svo "
            "viðmiðið er samsett úr þremur byggingum á tveimur dögum."
        ),
        "verklysing_sagdi": "2865ed6 (2026-09-20T11:51:21Z)",
        "leidretting": (
            "Rangt. Engin skrá í byggingunni er yngri en 2026-09-17T09:51:40Z, "
            "svo byggingin er ÞREMUR DÖGUM eldri en 2865ed6. Sömuleiðis er "
            "origin/main kominn í fb15d2a — 16 commit á undan 2865ed6 og 22 "
            "á undan yngstu byggingarlotunni."
        ),
        "adferd": (
            "docs/ var gitignored í upprunarepo-inu, svo byggingin á sér ekkert "
            "git-ummerki. Lotugreiningin byggir á breytingartíma hverrar skráar "
            "(varðveittur með cp -p) borinn saman við reflog upprunarepo-sins."
        ),
        "upprunarepo": VIDMIDSREPO,
        "origin_main_vid_afritun": "fb15d2a40457f6f97803699e4a68cd9c39aac72e",
        "lotur": lotur,
        "sidur_utan_lotu": oflokkad,
    }


def byggja() -> dict:
    """Byggir allt provenance-skjalið úr því sem er á disknum núna."""
    sofn = []
    for safn in SOFN:
        mappa = ROT / safn["mappa"]
        if not mappa.is_dir():
            raise FileNotFoundError(f"Vantar möppu sem á að vera til: {safn['mappa']}")
        skrar = [lysa_skra(skra, safn) for skra in skrar_i(mappa)]
        if not skrar:
            raise ValueError(f"Engar skrár í {safn['mappa']} — afritunin brást")
        sofn.append(
            {
                **{lykill: safn[lykill] for lykill in ("heiti", "mappa", "uppruni", "upprunarepo", "skyring")},
                "fjoldi_skraa": len(skrar),
                "staerd_baet": sum(skra["staerd_baet"] for skra in skrar),
                "skrar": skrar,
            }
        )

    return {
        "snid_utgafa": SNID_UTGAFA,
        "afritad_utc": nuna_utc(),
        "verk": "P0.1 — gagnabjörgun (issue #30)",
        "lysing": (
            "Afrit af gögnum sem voru aðeins til á einni vél og hvergi í git. "
            "Afritað óbreytt; SHA-256 hér er sönnunin fyrir því að viðmiðið sé ósnert."
        ),
        "vidmidsbygging": greina_byggingarlotur(
            next(safn for safn in sofn if safn["heiti"] == "vefur")
        ),
        "fjoldi_skraa": sum(safn["fjoldi_skraa"] for safn in sofn),
        "staerd_baet": sum(safn["staerd_baet"] for safn in sofn),
        "sofn": sofn,
    }


def skrifa() -> int:
    """Skrifar docs/vidmid/provenance.json út frá því sem er á disknum."""
    skjal = byggja()
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.write_text(
        json.dumps(skjal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info(
        "Skrifaði %s — %d skrár, %.1f MB",
        PROVENANCE.relative_to(ROT),
        skjal["fjoldi_skraa"],
        skjal["staerd_baet"] / 1_000_000,
    )
    return 0


def stadfesta() -> int:
    """Ber provenance.json saman við diskinn. Skilar 1 ef nokkuð stemmir ekki."""
    if not PROVENANCE.is_file():
        raise FileNotFoundError(f"Vantar {PROVENANCE.relative_to(ROT)} — keyrðu 'skrifa' fyrst")

    skjal = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    frabrigdi: list[str] = []

    for safn in skjal["sofn"]:
        mappa = ROT / safn["mappa"]
        skradar = {skra["slod"] for skra in safn["skrar"]}
        a_diski = {skra.relative_to(mappa).as_posix() for skra in skrar_i(mappa)}

        for slod in sorted(skradar - a_diski):
            frabrigdi.append(f"{safn['heiti']}: skrá horfin af diski — {slod}")
        for slod in sorted(a_diski - skradar):
            frabrigdi.append(f"{safn['heiti']}: skrá á diski sem er ekki í provenance — {slod}")

        for skra in safn["skrar"]:
            adgengileg = mappa / skra["slod"]
            if not adgengileg.is_file():
                continue  # þegar skráð hér að ofan
            if adgengileg.stat().st_size != skra["staerd_baet"]:
                frabrigdi.append(f"{safn['heiti']}: stærð hefur breyst — {skra['slod']}")
            elif sha256_af(adgengileg) != skra["sha256"]:
                frabrigdi.append(f"{safn['heiti']}: SHA-256 stemmir ekki — {skra['slod']}")

    if frabrigdi:
        # Regla 6: villur eru aldrei þaggaðar.
        for lina in frabrigdi:
            log.error("%s", lina)
        log.error("%d frábrigði — viðmiðið er EKKI ósnert", len(frabrigdi))
        return 1

    log.info("Allar %d skrár stemma við provenance.json", skjal["fjoldi_skraa"])
    return 0


AÐGERÐIR = {"skrifa": skrifa, "stadfesta": stadfesta}


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("adgerd", choices=[*AÐGERÐIR], help="skrifa eða stadfesta")
    return AÐGERÐIR[thattari.parse_args(rok).adgerd]()


if __name__ == "__main__":
    sys.exit(main())
