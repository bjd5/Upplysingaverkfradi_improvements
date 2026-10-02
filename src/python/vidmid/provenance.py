"""Staðfestir að frosnu gögnin séu ósnert — hrágögnin og viðmiðið.

Tvær skrár lofa SHA-256 fyrir hverja frosna skrá í repo-inu:

* ``data/raw/frysting.json`` — hrágögnin sem grunnurinn er byggður úr (P0.3).
* ``docs/vidmid/provenance.json`` — gögnin sem P0.1 bjargaði af einni vél:
  viðmiðið sem nýja síðan er borin saman við, og mbl-eintakið.

Þessi eining reiknar summurnar upp á nýtt og ber saman við loforðin. Hún
gerir athugasemd við breytta skrá, horfna skrá **og** skrá sem hefur bæst við
óskráð. Skrárnar eru ekki endurskrifaðar héðan: frystingin var gerð einu sinni
og breytingartímarnir í þeim komu með afrituninni (``cp -p``).

Söfn sem voru tekin úr trénu (``geymt_i_tagi`` í provenance.json) eru
staðfest í git-taginu sem geymir þau, ekki hér.

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
FRYSTING = ROT / "data" / "raw" / "frysting.json"
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


def frabrigdi_safns(safn: dict, rot: Path = ROT) -> list[str]:
    """Ber eitt safn saman við diskinn og skilar frávikum sem læsilegum línum.

    ``safn`` hefur ``heiti``, ``mappa`` (afstæð við ``rot``) og ``skrar`` — lista
    af ``{"slod", "staerd_baet", "sha256"}``. Það er sama snið í báðum skránum.
    """
    heiti, mappa = safn["heiti"], rot / safn["mappa"]
    if not mappa.is_dir():
        return [f"{heiti}: mappan er horfin — {safn['mappa']}"]

    skradar = {skra["slod"] for skra in safn["skrar"]}
    a_diski = {skra.relative_to(mappa).as_posix() for skra in skrar_i(mappa)}
    frabrigdi = [f"{heiti}: skrá horfin af diski — {s}" for s in sorted(skradar - a_diski)]
    frabrigdi += [f"{heiti}: óskráð skrá á diski — {s}" for s in sorted(a_diski - skradar)]

    for skra in safn["skrar"]:
        slod = mappa / skra["slod"]
        if not slod.is_file():
            continue  # þegar skráð hér að ofan
        if slod.stat().st_size != skra["staerd_baet"]:
            frabrigdi.append(f"{heiti}: stærð hefur breyst — {skra['slod']}")
        elif sha256_af(slod) != skra["sha256"]:
            frabrigdi.append(f"{heiti}: SHA-256 stemmir ekki — {skra['slod']}")
    return frabrigdi


def sofn_i(skra: Path) -> list[dict]:
    """Les söfnin úr frysting.json (orðabók) eða provenance.json (listi)."""
    sofn = json.loads(skra.read_text(encoding="utf-8"))["sofn"]
    return list(sofn.values()) if isinstance(sofn, dict) else sofn


def stadfesta(skrar: tuple[Path, ...] = (FRYSTING, PROVENANCE), rot: Path = ROT) -> int:
    """Ber hverja skrá saman við diskinn. Skilar 1 ef nokkuð stemmir ekki."""
    frabrigdi: list[str] = []
    fjoldi = 0
    for skra in skrar:
        for safn in sofn_i(skra):
            fjoldi += len(safn["skrar"])
            frabrigdi += frabrigdi_safns(safn, rot)

    if frabrigdi:
        # Regla 6: villur eru aldrei þaggaðar.
        for lina in frabrigdi:
            log.error("%s", lina)
        log.error("%d frábrigði — frosnu gögnin eru EKKI ósnert", len(frabrigdi))
        return 1

    log.info("Allar %d frosnar skrár stemma", fjoldi)
    return 0


def main(rok: list[str] | None = None) -> int:
    """Handvirk keyrsla: ``stadfesta`` skilar 0 séu frosnu gögnin ósnert, annars 1."""
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("adgerd", choices=["stadfesta"])
    thattari.parse_args(rok)
    return stadfesta()


if __name__ == "__main__":
    sys.exit(main())
