"""Staðfestir að frosna viðmiðið sé ósnert (docs/vidmid/provenance.json).

Skrárnar sem provenance.json telur upp eru **afrit** af gögnum sem voru aðeins
til á einni vél. Þær eru sönnunargagn: nýja síðan á að sýna sömu tölur og sú
gamla (docs/endurbygging.md, kafli 2). Þessi eining reiknar SHA-256 hverrar
skráar upp á nýtt og ber saman við það sem var skráð við frystinguna.

Skráin er ekki endurskrifuð héðan. Breytingartímarnir í henni komu með `cp -p`
við afritunina og tapast við hvert `git clone`; endurskrifuð skrá væri því röng.
Söfn sem voru tekin úr trénu (`geymt_i_tagi`) eru staðfest í git-taginu sem
geymir þau, ekki hér.

Keyrsla:
    python3 src/python/vidmid/provenance.py stadfesta
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
PROVENANCE = ROT / "docs" / "vidmid" / "provenance.json"
BUFFER_BAET = 1 << 20  # 1 MiB í einu — stórar skrár fara ekki allar í minni

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("provenance")


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


def frabrigdi_safns(safn: dict) -> list[str]:
    """Ber eitt safn úr provenance.json saman við diskinn og skilar frávikum."""
    mappa = ROT / safn["mappa"]
    skradar = {skra["slod"] for skra in safn["skrar"]}
    a_diski = {skra.relative_to(mappa).as_posix() for skra in skrar_i(mappa)}

    frabrigdi = [f"{safn['heiti']}: skrá horfin af diski — {s}" for s in sorted(skradar - a_diski)]
    frabrigdi += [
        f"{safn['heiti']}: skrá á diski sem er ekki í provenance — {s}"
        for s in sorted(a_diski - skradar)
    ]
    for skra in safn["skrar"]:
        slod = mappa / skra["slod"]
        if not slod.is_file():
            continue  # þegar skráð hér að ofan
        if slod.stat().st_size != skra["staerd_baet"]:
            frabrigdi.append(f"{safn['heiti']}: stærð hefur breyst — {skra['slod']}")
        elif sha256_af(slod) != skra["sha256"]:
            frabrigdi.append(f"{safn['heiti']}: SHA-256 stemmir ekki — {skra['slod']}")
    return frabrigdi


def stadfesta() -> int:
    """Ber provenance.json saman við diskinn. Skilar 1 ef nokkuð stemmir ekki."""
    skjal = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    frabrigdi = [lina for safn in skjal["sofn"] for lina in frabrigdi_safns(safn)]

    if frabrigdi:
        # Regla 6: villur eru aldrei þaggaðar.
        for lina in frabrigdi:
            log.error("%s", lina)
        log.error("%d frábrigði — viðmiðið er EKKI ósnert", len(frabrigdi))
        return 1

    log.info("Allar %d skrár stemma við provenance.json", skjal["fjoldi_skraa"])
    return 0


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("adgerd", choices=["stadfesta"])
    thattari.parse_args(rok)
    return stadfesta()


if __name__ == "__main__":
    sys.exit(main())
