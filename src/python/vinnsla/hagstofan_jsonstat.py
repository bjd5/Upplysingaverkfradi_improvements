"""Lestur og sannreyning á json-stat2-svari Hagstofunnar.

json-stat2 skilar marghliða töflu sem **flötum** gildalista: víddalýsingin í
``dimension`` segir hvernig á að lesa hann. Rangur lestur gefur tölur sem líta
rétt út en eiga við annað — brautskráningarhlutfall kvenna endar á karlalínunni.
Þess vegna sannreynir þessi eining bygginguna áður en nokkurt gildi er notað:

* SHA-256 frystu skránna stemmir við ``provenance.json`` (reglur 4 og 8),
* víddaröð, víddastærðir og ``category.index`` mynda heila og gatalausa röð,
* heiti valinna kóða eru þau sömu í svarinu og lýsigögnunum,
* **fjöldi gilda er nákvæmlega margfeldi víddastærðanna.**

Bregðist eitthvað af þessu er kastað :class:`JsonstatVilla` og engin lína fer
í grunninn (regla 6: villur eru aldrei þaggaðar, hálf tafla er verri en engin).

Einingin snertir hvorki gagnagrunn né net — hún les eingöngu frystu skrárnar í
``data/raw/hagstofan/`` og breytir þeim aldrei (regla 4).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SVARSKRA = "response.json"
LYSIGAGNASKRA = "metadata.json"
UPPRUNASKRA = "provenance.json"
FYRIRSPURNARSKRA = "query.json"

# Einingin les aðeins þá útgáfu json-stat sem hún kann. Ný útgáfa getur breytt
# merkingu `size` eða `category.index` og fengi þá að lesast rangt í þögn.
STUDD_UTGAFA = "2.0"


class JsonstatVilla(ValueError):
    """Frystu gögnin eru ekki það json-stat2 sem hleðslan gerir ráð fyrir."""


@dataclass(frozen=True)
class Viddargildi:
    """Eitt leyft gildi einnar víddar, með íslensku heiti sínu."""

    kodi: str
    heiti: str
    valid: bool
    # Staða innan víddarinnar í svarinu (`category.index`); None sé gildið
    # leyft í lýsigögnum en ekki valið í frystu fyrirspurninni.
    stada: int | None


@dataclass(frozen=True)
class Vidd:
    """Ein vídd töflunnar ásamt allri kóðabók sinni."""

    kodi: str
    heiti: str
    rod: int
    staerd: int
    er_timi: bool
    gildi: tuple[Viddargildi, ...]

    @property
    def valin_gildi(self) -> tuple[Viddargildi, ...]:
        """Valin gildi í þeirri röð sem svarið raðar þeim."""
        valin = [g for g in self.gildi if g.valid]
        return tuple(sorted(valin, key=lambda g: g.stada or 0))


@dataclass(frozen=True)
class Maeling:
    """Eitt gildi úr flata listanum ásamt samsetningu víddanna sem á við það."""

    flat_stada: int
    kodar: tuple[tuple[str, str], ...]
    gildi: float


@dataclass(frozen=True)
class Gagnasafn:
    """Frysta json-stat2-svarið, lesið og sannreynt."""

    audkenni: str
    heiti: str
    heimild: str
    endapunktur: str
    sott_kl: str
    uppfaert: str | None
    utgafa: str
    aukastafir: int | None
    hraskra: str
    viddir: tuple[Vidd, ...]
    maelingar: tuple[Maeling, ...]


def lesa_gagnasafn(mappa: Path) -> Gagnasafn:
    """Les og sannreynir frysta svarið í ``mappa`` og skilar því lesnu.

    Kastar :class:`JsonstatVilla` víki nokkuð frá væntri byggingu.
    """
    upprunagogn = _lesa_json(mappa / UPPRUNASKRA)
    _sannreyna_summur(mappa, upprunagogn)

    svar = _lesa_json(mappa / SVARSKRA)
    lysigogn = _lesa_json(mappa / LYSIGAGNASKRA)

    _sannreyna_utgafu(svar)
    viddir = _lesa_viddir(svar, lysigogn)
    maelingar = _lesa_maelingar(svar, viddir)

    endapunktur = _krefjast_strengs(upprunagogn, "endpoint", UPPRUNASKRA)
    return Gagnasafn(
        audkenni=_audkenni_ur_endapunkti(endapunktur),
        heiti=_krefjast_strengs(svar, "label", SVARSKRA),
        heimild=_krefjast_strengs(svar, "source", SVARSKRA),
        endapunktur=endapunktur,
        sott_kl=_krefjast_strengs(upprunagogn, "fetched_at_utc", UPPRUNASKRA),
        uppfaert=svar.get("updated"),
        utgafa=str(svar["version"]),
        aukastafir=svar.get("extension", {}).get("px", {}).get("decimals"),
        hraskra=str(mappa / SVARSKRA),
        viddir=viddir,
        maelingar=maelingar,
    )


def _lesa_json(slod: Path) -> dict[str, Any]:
    """Les JSON-skrá og kastar skiljanlegri villu finnist hún ekki."""
    if not slod.is_file():
        raise JsonstatVilla(f"Frysta skráin finnst ekki: {slod}")
    try:
        innihald = json.loads(slod.read_text(encoding="utf-8"))
    except json.JSONDecodeError as villa:
        raise JsonstatVilla(f"{slod} er ekki gilt JSON: {villa}") from villa
    if not isinstance(innihald, dict):
        raise JsonstatVilla(f"{slod} átti að geyma hlut en geymir {type(innihald)}.")
    return innihald


def _sannreyna_summur(mappa: Path, upprunagogn: dict[str, Any]) -> None:
    """Ber SHA-256 frystu skránna saman við ``provenance.json`` (reglur 4 og 8)."""
    skradar = upprunagogn.get("sha256")
    if not isinstance(skradar, dict) or not skradar:
        raise JsonstatVilla(
            f"{mappa / UPPRUNASKRA} geymir engar SHA-256 gátsummur. Án þeirra er "
            "ekki hægt að staðfesta að frystu gögnin séu ósnert."
        )
    for skraarheiti, vaent in sorted(skradar.items()):
        slod = mappa / skraarheiti
        if not slod.is_file():
            raise JsonstatVilla(f"{slod} er skráð í provenance en finnst ekki.")
        raun = hashlib.sha256(slod.read_bytes()).hexdigest()
        if raun != vaent:
            raise JsonstatVilla(
                f"{slod} hefur breyst frá frystingu.\n"
                f"  skráð SHA-256:   {vaent}\n"
                f"  á diski SHA-256: {raun}\n"
                "Hrágögnum er aldrei breytt eftir á (regla 4); sæktu óbreyttu "
                "skrána úr git."
            )


def _sannreyna_utgafu(svar: dict[str, Any]) -> None:
    """Stöðvar sé svarið ekki json-stat2 af þeirri útgáfu sem einingin kann."""
    if svar.get("class") != "dataset":
        raise JsonstatVilla(
            f"Svarið er af gerðinni {svar.get('class')!r} en verður að vera 'dataset'."
        )
    utgafa = str(svar.get("version", ""))
    if utgafa != STUDD_UTGAFA:
        raise JsonstatVilla(
            f"Svarið er json-stat útgáfa {utgafa!r}; einingin les aðeins "
            f"{STUDD_UTGAFA!r}. Ný útgáfa getur breytt merkingu `size` og "
            "`category.index` og yrði þá lesin rangt."
        )


def _lesa_viddir(svar: dict[str, Any], lysigogn: dict[str, Any]) -> tuple[Vidd, ...]:
    """Les víddirnar í röð `id` og parar þær við kóðabókina í lýsigögnunum."""
    kodar = svar.get("id")
    staerdir = svar.get("size")
    if not isinstance(kodar, list) or not isinstance(staerdir, list):
        raise JsonstatVilla(f"{SVARSKRA} vantar `id` eða `size` sem lista.")
    if len(kodar) != len(staerdir):
        raise JsonstatVilla(
            f"`id` telur {len(kodar)} víddir en `size` {len(staerdir)}. "
            "Þá er ekki hægt að vita hvaða stærð á við hvaða vídd."
        )

    ur_lysigognum = _kodabok(lysigogn)
    timaviddir = set(svar.get("role", {}).get("time", []))
    return tuple(
        _lesa_vidd(kodi, rod, staerdir[rod], svar, ur_lysigognum, kodi in timaviddir)
        for rod, kodi in enumerate(kodar)
    )


def _kodabok(lysigogn: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Kóði -> heiti fyrir hverja breytu í ``metadata.json``."""
    breytur = lysigogn.get("variables")
    if not isinstance(breytur, list):
        raise JsonstatVilla(f"{LYSIGAGNASKRA} vantar `variables` sem lista.")

    bok: dict[str, dict[str, str]] = {}
    for breyta in breytur:
        kodi = breyta.get("code")
        gildi = breyta.get("values")
        heiti = breyta.get("valueTexts")
        if not kodi or not isinstance(gildi, list) or not isinstance(heiti, list):
            raise JsonstatVilla(
                f"Breytan {kodi!r} í {LYSIGAGNASKRA} vantar `values` eða `valueTexts`."
            )
        if len(gildi) != len(heiti):
            raise JsonstatVilla(
                f"Breytan {kodi!r} í {LYSIGAGNASKRA} hefur {len(gildi)} kóða en "
                f"{len(heiti)} heiti; pörunin er ótvíræð aðeins séu þau jafnmörg."
            )
        bok[kodi] = dict(zip(gildi, heiti, strict=True))
    return bok


def _lesa_vidd(
    kodi: str,
    rod: int,
    staerd: int,
    svar: dict[str, Any],
    ur_lysigognum: dict[str, dict[str, str]],
    er_timi: bool,
) -> Vidd:
    """Les eina vídd: stöðu hvers valins gildis og heiti allra leyfðra gilda."""
    lysing = svar.get("dimension", {}).get(kodi)
    if not isinstance(lysing, dict):
        raise JsonstatVilla(f"Víddin {kodi!r} er í `id` en vantar í `dimension`.")

    flokkur = lysing.get("category", {})
    stodur = flokkur.get("index")
    heiti = flokkur.get("label")
    if not isinstance(stodur, dict) or not isinstance(heiti, dict):
        raise JsonstatVilla(
            f"Víddin {kodi!r} vantar `category.index` eða `category.label`."
        )
    if len(stodur) != staerd:
        raise JsonstatVilla(
            f"Víddin {kodi!r} segist vera af stærð {staerd} en `category.index` "
            f"telur {len(stodur)} gildi."
        )
    if sorted(stodur.values()) != list(range(staerd)):
        raise JsonstatVilla(
            f"`category.index` fyrir {kodi!r} er ekki heil röð 0..{staerd - 1}: "
            f"{sorted(stodur.values())}. Þá er staða gilda í flata listanum óþekkt."
        )

    leyfd = ur_lysigognum.get(kodi)
    if leyfd is None:
        raise JsonstatVilla(
            f"Víddin {kodi!r} er í svarinu en finnst ekki í {LYSIGAGNASKRA}."
        )

    for valinn in stodur:
        if valinn not in leyfd:
            raise JsonstatVilla(
                f"Kóðinn {valinn!r} í vídd {kodi!r} er í svarinu en ekki meðal "
                f"leyfðra kóða í {LYSIGAGNASKRA}. Skrárnar lýsa ekki sömu töflu."
            )
        if heiti.get(valinn) != leyfd[valinn]:
            raise JsonstatVilla(
                f"Kóðinn {valinn!r} í vídd {kodi!r} heitir {heiti.get(valinn)!r} í "
                f"svarinu en {leyfd[valinn]!r} í {LYSIGAGNASKRA}."
            )

    gildi = tuple(
        Viddargildi(
            kodi=gildiskodi,
            heiti=gildisheiti,
            valid=gildiskodi in stodur,
            stada=stodur.get(gildiskodi),
        )
        for gildiskodi, gildisheiti in leyfd.items()
    )
    return Vidd(
        kodi=kodi,
        heiti=str(lysing.get("label") or kodi),
        rod=rod,
        staerd=staerd,
        er_timi=er_timi,
        gildi=gildi,
    )


def _lesa_maelingar(
    svar: dict[str, Any], viddir: tuple[Vidd, ...]
) -> tuple[Maeling, ...]:
    """Flettir flata gildalistanum út í eina mælingu á hverja samsetningu vídda.

    Síðasta víddin breytist hraðast — það er röðunin sem json-stat2 skilgreinir
    og ``itertools.product`` gefur beint.
    """
    gildi = svar.get("value")
    if not isinstance(gildi, list):
        raise JsonstatVilla(f"{SVARSKRA} vantar `value` sem lista.")

    vaentur_fjoldi = math.prod(vidd.staerd for vidd in viddir)
    if len(gildi) != vaentur_fjoldi:
        staerdir = " x ".join(f"{v.kodi}={v.staerd}" for v in viddir)
        raise JsonstatVilla(
            f"Fjöldi gilda stemmir ekki við víddastærðirnar: `value` telur "
            f"{len(gildi)} gildi en {staerdir} gefur {vaentur_fjoldi}. "
            "Lestur á json-stat2 hefur farið úrskeiðis og engin lína er skrifuð."
        )

    asar = [[(vidd.kodi, g.kodi) for g in vidd.valin_gildi] for vidd in viddir]
    maelingar = []
    for flat_stada, samsetning in enumerate(product(*asar)):
        talan = gildi[flat_stada]
        if isinstance(talan, bool) or not isinstance(talan, (int, float)):
            raise JsonstatVilla(
                f"Gildi nr. {flat_stada} í `value` er {talan!r} en ekki tala. "
                "Eyður í json-stat2 eru ekki studdar hér — samsetningin "
                f"{samsetning} ætti sér þá ekkert gildi."
            )
        maelingar.append(
            Maeling(flat_stada=flat_stada, kodar=samsetning, gildi=float(talan))
        )
    return tuple(maelingar)


def _audkenni_ur_endapunkti(endapunktur: str) -> str:
    """Dregur töfluauðkennið (t.d. ``SKO04208b``) út úr slóð endapunktsins."""
    audkenni = Path(urlsplit(endapunktur).path).stem
    if not audkenni:
        raise JsonstatVilla(
            f"Ekkert töfluauðkenni verður lesið úr endapunktinum {endapunktur!r}."
        )
    return audkenni


def _krefjast_strengs(gogn: dict[str, Any], lykill: str, skra: str) -> str:
    """Sækir strengjareit og stöðvar sé hann tómur eða af rangri gerð."""
    gildi = gogn.get(lykill)
    if not isinstance(gildi, str) or not gildi.strip():
        raise JsonstatVilla(f"{skra} vantar reitinn {lykill!r} sem texta.")
    return gildi
