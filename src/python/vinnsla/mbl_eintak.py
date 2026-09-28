"""Vistuðu mbl.is-eintökin í ``data/raw/mbl/`` og sannreyning þeirra.

Hvert eintak er tvær skrár með sama stofn: HTML-svarið sjálft og samnefnd
JSON-lýsigögn sem festa hvaða svar niðurstöðurnar byggja á (regla 4).

Eintakið ``mbl-20260916T120851Z`` er **eina afritið sem til er** — það var
bjargað af diski í issue #30 og er hvorki til í upprunarepo-inu né hjá mbl.is.
Þess vegna er það lesið, aldrei skrifað, og MD5 og stærð eru borin saman við
lýsigögnin áður en nokkuð er unnið úr því: skemmt hrágagn sem lítur heilt út
væri verra en ekkert (regla 6).

Fleiri en eitt eintak mega liggja hér samtímis; þau eru aðgreind eftir
sóknartíma svo hægt sé að bera saman tvær sóknir án þess að sú eldri glatist.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from sofnun.beidni import sha256_af

ROT = Path(__file__).resolve().parents[3]
MBL_MAPPA = ROT / "data" / "raw" / "mbl"

# Svar sem er ekki 200 lýsir ekki fréttasíðunni og á ekkert erindi í útdrátt.
VAENT_STADA = 200

# Lyklarnir eru á ensku því sniðið kom óbreytt úr upprunaverkefninu.
SKYLDUREITIR = (
    "source_url",
    "fetched_at_utc",
    "status_code",
    "content_length_bytes",
    "md5",
)


class EintakVilla(RuntimeError):
    """Eintakið og lýsigögn þess eiga ekki saman — hrágagnið er ónothæft."""


@dataclass(frozen=True)
class Eintak:
    """Eitt vistað HTML-svar ásamt sannreyndum lýsigögnum sínum."""

    html_slod: Path
    lysigogn_slod: Path
    sotta_stund: str          # fetched_at_utc — aðgreinir eintökin
    upprunaslod: str          # source_url
    sha256: str               # reiknað hér, ekki lesið
    md5: str                  # úr lýsigögnunum, sannreynt hér
    staerd: int
    stada: int
    efnistegund: str | None

    @property
    def skraarheiti(self) -> str:
        """Skráarheitið eitt og sér — það sem fer í ``mbl_snapshots.raw_file``."""
        return self.html_slod.name

    def lesa_html(self) -> str:
        """Skilar HTML-svarinu sem texta. Skráin er aldrei skrifuð."""
        return self.html_slod.read_text(encoding="utf-8")


def _lesa_lysigogn(slod: Path) -> dict:
    """Les og staðfestir JSON-lýsigögn eintaks."""
    if not slod.is_file():
        raise EintakVilla(
            f"Lýsigögn vantar fyrir {slod.stem}: {slod.name} finnst ekki. "
            "HTML-svar án provenance er ekki rekjanlegt (regla 4)."
        )
    try:
        skjal = json.loads(slod.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as villa:
        raise EintakVilla(f"{slod.name} er ekki lesanlegt JSON: {villa}") from villa

    if not isinstance(skjal, dict):
        raise EintakVilla(f"{slod.name} á að vera JSON-hlutur.")

    vantar = [reitur for reitur in SKYLDUREITIR if reitur not in skjal]
    if vantar:
        raise EintakVilla(f"{slod.name} vantar reitina: {', '.join(vantar)}.")
    return skjal


def _stadfesta_innihald(html_slod: Path, skjal: dict, lysigogn_heiti: str) -> str:
    """Ber MD5 og stærð skrárinnar saman við lýsigögnin og skilar SHA-256."""
    baeti = html_slod.read_bytes()

    skrad_staerd = skjal["content_length_bytes"]
    if len(baeti) != skrad_staerd:
        raise EintakVilla(
            f"{html_slod.name} er {len(baeti)} bæti en {lysigogn_heiti} skráir "
            f"{skrad_staerd}. Eintakið hefur breyst frá því það var sótt."
        )

    skrad_md5 = str(skjal["md5"]).lower()
    reiknad_md5 = hashlib.md5(baeti).hexdigest()
    if reiknad_md5 != skrad_md5:
        raise EintakVilla(
            f"MD5 stemmir ekki fyrir {html_slod.name}.\n"
            f"  skráð:    {skrad_md5}\n"
            f"  reiknað:  {reiknad_md5}\n"
            "Hrágögnum er aldrei breytt eftir á (regla 4) — sæktu eintakið "
            "aftur úr git í stað þess að vinna úr því."
        )

    stada = skjal["status_code"]
    if stada != VAENT_STADA:
        raise EintakVilla(
            f"{html_slod.name} var vistað með HTTP-stöðu {stada}, ekki "
            f"{VAENT_STADA}. Svarið lýsir ekki fréttasíðunni."
        )

    return sha256_af(baeti)


def lesa_eintak(html_slod: Path) -> Eintak:
    """Les eitt eintak og sannreynir það gagnvart lýsigögnum sínum."""
    if not html_slod.is_file():
        raise EintakVilla(f"Eintakið finnst ekki: {html_slod}")

    lysigogn_slod = html_slod.with_suffix(".json")
    skjal = _lesa_lysigogn(lysigogn_slod)
    summa = _stadfesta_innihald(html_slod, skjal, lysigogn_slod.name)

    return Eintak(
        html_slod=html_slod,
        lysigogn_slod=lysigogn_slod,
        sotta_stund=str(skjal["fetched_at_utc"]),
        upprunaslod=str(skjal["source_url"]),
        sha256=summa,
        md5=str(skjal["md5"]).lower(),
        staerd=int(skjal["content_length_bytes"]),
        stada=int(skjal["status_code"]),
        efnistegund=skjal.get("content_type"),
    )


def finna_eintok(mappa: Path | None = None) -> list[Eintak]:
    """Les öll eintök möppunnar, elsta fyrst eftir sóknartíma.

    Tóm mappa er villa en ekki tómur listi: útdráttur án eintaks er
    þögult núll (regla 6).
    """
    mappa = mappa or MBL_MAPPA
    if not mappa.is_dir():
        raise EintakVilla(f"Möppan með mbl-eintökum finnst ekki: {mappa}")

    skrar = sorted(mappa.glob("*.html"))
    if not skrar:
        raise EintakVilla(
            f"Ekkert mbl-eintak í {mappa}. Frosna eintakið á að vera í git — "
            "sjá data/raw/README.md."
        )

    eintok = [lesa_eintak(slod) for slod in skrar]
    return sorted(eintok, key=lambda eintak: eintak.sotta_stund)
