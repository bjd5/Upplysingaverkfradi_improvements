"""Byggir vélleshæft viðmið úr byggðu gömlu síðunni (P0.2, issue #30).

Krafa verkefnisins er að nýja síðan sýni sömu tölur og sú gamla
(docs/endurbygging.md, kafli 2). Í dag eru þær tölur aðeins til sem texti inni í
28 HTML-skrám í docs/vidmid/vefur/; próf geta ekki borið sig saman við HTML.
Þessi eining les síðurnar, flokkar hverja tölu og skrifar:

    docs/vidmid/vidmid.json   vélleshæft viðmið
    docs/vidmid/vidmid.md     sama efni í töflu sem manneskja les

Keyrsla:
    python3 src/python/vidmid/tolur.py skrifa
    python3 src/python/vidmid/tolur.py stadfesta   # ber vidmid.json við síðurnar
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

try:  # keyrt beint: python3 src/python/vidmid/tolur.py
    from osamraemi import OSAMRAEMI
    from sidulestur import Sidulesari
    from stadfestar import GAGNADRIFNAR, STADFESTAR
    from tolugreining import finna_tolur
    from tolusnid import skrifa_markdown
except ImportError:  # flutt inn sem eining innan pakkans
    from .osamraemi import OSAMRAEMI
    from .sidulestur import Sidulesari
    from .stadfestar import GAGNADRIFNAR, STADFESTAR
    from .tolugreining import finna_tolur
    from .tolusnid import skrifa_markdown

ROT = Path(__file__).resolve().parents[3]
VEFUR = ROT / "docs" / "vidmid" / "vefur"
PROVENANCE = ROT / "docs" / "vidmid" / "provenance.json"
VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
VIDMID_MD = ROT / "docs" / "vidmid" / "vidmid.md"
SNID_UTGAFA = 1
SAMHENGI_HAMARK = 400   # löng málsgrein er klippt; rekjanleikinn er í sida+kafli
SAMHENGI_ANNAD = 120    # tala sem er ekki niðurstaða þarf minna samhengi

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("tolur")


def _lotur_per_sidu() -> dict[str, str]:
    """Kortleggur síðu → byggingarlotu úr provenance.json (P0.1 staðfesti þær)."""
    if not PROVENANCE.exists():
        log.warning("provenance.json finnst ekki — byggingarlota ekki skráð")
        return {}
    gogn = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    ut: dict[str, str] = {}
    for lota in gogn.get("vidmidsbygging", {}).get("lotur", []):
        for sida in lota.get("sidur", []):
            ut[sida] = lota["commit"][:7]
    return ut


def _tolur_sidu(
    sida: str, html: str, lota: str | None,
) -> tuple[list[dict], str | None]:
    """Allar tölur einnar síðu, með samhengi, í þeirri röð sem þær stóðu."""
    lesari = Sidulesari()
    blokkir = lesari.lesa(html)
    ut: list[dict] = []
    for blokk in blokkir:
        for tala in finna_tolur(blokk.texti):
            # Tala inni í kóðalistun er ekki niðurstaða heldur bókstafur í kóða.
            # Hún er skráð áfram, en visst=False svo próf geti sniðið hana frá.
            visst = tala.visst and blokk.flokkur != "kodi"
            ut.append({
                "id": f"{sida}#{len(ut):04d}",
                "sida": sida,
                "lota": lota,
                "kafli": list(blokk.kafli),
                "flokkur": blokk.flokkur,
                "tafla": blokk.tafla,
                "lina": blokk.lina,
                "sulka": blokk.sulka,
                "texti": tala.texti,
                "gildi": tala.gildi,
                "bil": list(tala.bil) if tala.bil else None,
                "eining": tala.eining,
                "tegund": tala.tegund,
                "visst": visst,
                "samhengi": blokk.texti[
                    : SAMHENGI_HAMARK if visst else SAMHENGI_ANNAD],
            })
    return ut, lesari.titill


def _ur_meta(leid: str, gogn: dict) -> float | int | None:
    """Sækir tölu úr _meta.json eftir punktaskilinni slóð."""
    hluti: object = gogn
    for lykill in leid.split("."):
        if not isinstance(hluti, dict) or lykill not in hluti:
            return None
        hluti = hluti[lykill]
    return hluti if isinstance(hluti, (int, float)) else None


def _stadfestar_med_leit(tolur: list[dict]) -> list[dict]:
    """Ber staðfestu tölurnar við það sem fannst — og segir hvar þær fundust."""
    meta_skra = VEFUR / "friends" / "phoebe-stats" / "_meta.json"
    meta = (json.loads(meta_skra.read_text(encoding="utf-8"))
            if meta_skra.exists() else {})
    ut = []
    for s in STADFESTAR:
        fundid = [t["id"] for t in tolur
                  if t["visst"] and t["gildi"] == s.gildi and t["sida"] == s.sida]
        ur_gognum = _ur_meta(s.leid, meta) if s.leid else None
        ut.append({
            "heiti": s.heiti,
            "gildi": s.gildi,
            "eining": s.eining,
            "sida": s.sida,
            "i_html": bool(fundid),
            "stadir_i_html": fundid[:6],
            "ur_gagnaskra": ur_gognum,
            "gagnaskra": "friends/phoebe-stats/_meta.json" if s.leid else None,
            "stemmir": (ur_gognum == s.gildi) if s.leid else bool(fundid),
        })
    return ut


def _samrit(tolur: list[dict]) -> list[dict]:
    """Tölur sem birtast á fleiri en einni síðu — báðir staðir skráðir."""
    eftir_gildi: dict[tuple, list[dict]] = {}
    for t in tolur:
        if not t["visst"] or t["gildi"] is None:
            continue
        eftir_gildi.setdefault((t["gildi"], t["eining"]), []).append(t)
    ut = []
    for (gildi, eining), hopur in eftir_gildi.items():
        sidur = sorted({t["sida"] for t in hopur})
        if len(sidur) < 2:
            continue
        ut.append({
            "gildi": gildi,
            "eining": eining,
            "sidur": sidur,
            "stadir": [{"id": t["id"], "sida": t["sida"], "kafli": t["kafli"],
                        "flokkur": t["flokkur"]} for t in hopur],
        })
    return sorted(ut, key=lambda x: (-len(x["sidur"]), -(x["gildi"] or 0)))


def byggja() -> dict:
    """Les allar síður og setur viðmiðið saman."""
    if not VEFUR.is_dir():
        raise FileNotFoundError(
            f"{VEFUR} finnst ekki — P0.2 krefst þess að P0.1 sé komið í tréð")
    lotur = _lotur_per_sidu()
    tolur: list[dict] = []
    sidur: list[dict] = []
    for skra in sorted(VEFUR.rglob("*.html")):
        sida = skra.relative_to(VEFUR).as_posix()
        eigin, titill = _tolur_sidu(
            sida, skra.read_text(encoding="utf-8"), lotur.get(sida))
        tolur.extend(eigin)
        sidur.append({
            "sida": sida,
            "titill": titill,
            "lota": lotur.get(sida),
            "tolur": len(eigin),
            "efnislegar": sum(1 for t in eigin if t["visst"]),
        })
    efnislegar = [t for t in tolur if t["visst"]]
    return {
        "snid_utgafa": SNID_UTGAFA,
        "uppfaert": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verk": "P0.2 — vélleshæft viðmið úr byggðu síðunni (issue #30)",
        "lysing": (
            "Hver tala sem gamla Quarto-síðan birtir, með síðu, kafla og "
            "samhengi. Afleiða af docs/vidmid/vefur/ — aldrei handbreytt."
        ),
        "adferd": (
            "html.parser úr staðalsafninu. Aðeins efnið innan "
            "<main id=quarto-document-content> er lesið, svo valmynd, "
            "brauðmylsna og fótur komast ekki með. Tala inni í kóðalistun er "
            "skráð en fær visst=false."
        ),
        "samantekt": {
            "sidur": len(sidur),
            "sidur_med_tolum": sum(1 for s in sidur if s["tolur"]),
            "sidur_tolulausar": [s["sida"] for s in sidur if not s["tolur"]],
            "sidur_an_efnislegra": [s["sida"] for s in sidur
                                    if s["tolur"] and not s["efnislegar"]],
            "tolur_alls": len(tolur),
            "efnislegar": len(efnislegar),
            "eftir_flokki": _telja(efnislegar, "flokkur"),
            "eftir_tegund": _telja(efnislegar, "tegund"),
            "adrar_eftir_tegund": _telja([t for t in tolur if not t["visst"]],
                                         "tegund"),
        },
        "sidur": sidur,
        "stadfestar": _stadfestar_med_leit(tolur),
        "gagnadrifnar_sidur": [dict(g, gagnaskrar=list(g["gagnaskrar"]))
                               for g in GAGNADRIFNAR],
        "osamraemi": [dict(o._asdict(),
                          stadir=[{"stadur": a, "segir": b}
                                  for a, b in o.stadir])
                     for o in OSAMRAEMI],
        "samrit": _samrit(tolur),
        "gogn": tolur,
    }


def _telja(tolur: list[dict], lykill: str) -> dict[str, int]:
    talning: dict[str, int] = {}
    for t in tolur:
        talning[t[lykill]] = talning.get(t[lykill], 0) + 1
    return dict(sorted(talning.items(), key=lambda kv: -kv[1]))


def _skrifa() -> int:
    vidmid = byggja()
    VIDMID_JSON.write_text(
        json.dumps(vidmid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    skrifa_markdown(vidmid, VIDMID_MD)
    s = vidmid["samantekt"]
    log.info("%d tölur úr %d síðum — %d efnislegar",
             s["tolur_alls"], s["sidur"], s["efnislegar"])
    log.info("tölulausar síður: %s", ", ".join(s["sidur_tolulausar"]) or "engar")
    vantar = [x["heiti"] for x in vidmid["stadfestar"] if not x["stemmir"]]
    if vantar:
        log.error("staðfestar tölur sem stemma ekki: %s", ", ".join(vantar))
        return 1
    log.info("allar %d staðfestar tölur stemma", len(vidmid["stadfestar"]))
    hatt = [o["heiti"] for o in vidmid["osamraemi"]
            if o["alvarleiki"] == "hatt"]
    log.info("ósamræmi milli síðna: %d skráð, %d alvarlegt (%s)",
             len(vidmid["osamraemi"]), len(hatt), "; ".join(hatt))
    log.info("skrifað: %s og %s",
             VIDMID_JSON.relative_to(ROT), VIDMID_MD.relative_to(ROT))
    return 0


def _stadfesta() -> int:
    """Byggir viðmiðið upp á nýtt og ber við skrána á disknum."""
    if not VIDMID_JSON.exists():
        log.error("%s finnst ekki — keyrðu `skrifa` fyrst",
                  VIDMID_JSON.relative_to(ROT))
        return 1
    a = json.loads(VIDMID_JSON.read_text(encoding="utf-8"))
    b = byggja()
    for lykill in ("gogn", "samantekt", "stadfestar", "samrit", "sidur",
                   "osamraemi"):
        if a.get(lykill) != b.get(lykill):
            log.error("%s í vidmid.json stemmir ekki við síðurnar", lykill)
            return 1
    log.info("vidmid.json stemmir við docs/vidmid/vefur/ (%d tölur)",
             len(b["gogn"]))
    return 0


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("skipun", choices=("skrifa", "stadfesta"))
    valid = thattari.parse_args(rok)
    return _skrifa() if valid.skipun == "skrifa" else _stadfesta()


if __name__ == "__main__":
    sys.exit(main())
