"""Lestur víddalýsingarinnar: hvaða víddir taflan hefur og hvað þær innihalda.

json-stat2 lýsir víddunum á tveimur stöðum og hvorugur dugir einn:

* ``response.json`` segir hvaða kóðar RÖTUÐU inn í frystu fyrirspurnina og á
  hvaða stað hver þeirra er (``category.index``) — það er lykillinn að flata
  gildalistanum,
* ``metadata.json`` segir hvaða kóðar STÓÐU TIL BOÐA og hvað þeir heita.

Einingin parar þetta tvennt saman í :class:`~.hagstofan_snid.Vidd`, sem geymir
hvort tveggja: án valinna kóða er taflan ólesanleg, án hinna sést ekki hvaða
sneið af töflunni var tekin.

Athuganirnar hér varða eina vídd í einu. Þær sem ná yfir gagnasafnið í heild
eru í ``hagstofan_sannreyning``.
"""

from __future__ import annotations

from typing import Any

from .hagstofan_snid import LYSIGAGNASKRA, SVARSKRA, JsonstatVilla, Vidd, Viddargildi

# Kóðabók: víddarkóði -> {gildiskóði: íslenskt heiti} eins og lýsigögnin gefa.
Kodabok = dict[str, dict[str, str]]


def lesa_viddir(svar: dict[str, Any], lysigogn: dict[str, Any]) -> tuple[Vidd, ...]:
    """Les víddirnar í röð ``id`` og parar þær við kóðabókina í lýsigögnunum.

    Röðin er efnisleg: hún ræður því hvernig flati gildalistinn er lesinn.
    """
    kodar, staerdir = _viddarod(svar)
    kodabok = lesa_kodabok(lysigogn)
    timaviddir = set(svar.get("role", {}).get("time", []))
    return tuple(
        _lesa_vidd(kodi, rod, staerdir[rod], svar, kodabok, kodi in timaviddir)
        for rod, kodi in enumerate(kodar)
    )


def _viddarod(svar: dict[str, Any]) -> tuple[list[str], list[int]]:
    """Sækir ``id`` og ``size`` og stöðvar séu þau ekki jafnlöng."""
    kodar = svar.get("id")
    staerdir = svar.get("size")
    if not isinstance(kodar, list) or not isinstance(staerdir, list):
        raise JsonstatVilla(f"{SVARSKRA} vantar `id` eða `size` sem lista.")
    if len(kodar) != len(staerdir):
        raise JsonstatVilla(
            f"`id` telur {len(kodar)} víddir en `size` {len(staerdir)}. "
            "Þá er ekki hægt að vita hvaða stærð á við hvaða vídd."
        )
    return kodar, staerdir


def lesa_kodabok(lysigogn: dict[str, Any]) -> Kodabok:
    """Kóði -> heiti fyrir hverja breytu í ``metadata.json``."""
    breytur = lysigogn.get("variables")
    if not isinstance(breytur, list):
        raise JsonstatVilla(f"{LYSIGAGNASKRA} vantar `variables` sem lista.")
    return {breyta.get("code"): _breytuheiti(breyta) for breyta in breytur}


def _breytuheiti(breyta: dict[str, Any]) -> dict[str, str]:
    """Parar ``values`` við ``valueTexts`` fyrir eina breytu lýsigagnanna."""
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
    return dict(zip(gildi, heiti, strict=True))


def _lesa_vidd(
    kodi: str,
    rod: int,
    staerd: int,
    svar: dict[str, Any],
    kodabok: Kodabok,
    er_timi: bool,
) -> Vidd:
    """Setur saman eina vídd úr stöðum svarsins og kóðabók lýsigagnanna."""
    lysing = _viddarlysing(svar, kodi)
    stodur = _stodur(lysing, kodi)
    _sannreyna_stodur(kodi, stodur, staerd)

    leyfd = _leyfdir_kodar(kodabok, kodi)
    _sannreyna_heiti(kodi, stodur, _heiti_i_svari(lysing, kodi), leyfd)

    return Vidd(
        kodi=kodi,
        heiti=str(lysing.get("label") or kodi),
        rod=rod,
        staerd=staerd,
        er_timi=er_timi,
        gildi=_byggja_gildi(leyfd, stodur),
    )


def _viddarlysing(svar: dict[str, Any], kodi: str) -> dict[str, Any]:
    """Sækir ``dimension[kodi]`` úr svarinu."""
    lysing = svar.get("dimension", {}).get(kodi)
    if not isinstance(lysing, dict):
        raise JsonstatVilla(f"Víddin {kodi!r} er í `id` en vantar í `dimension`.")
    return lysing


def _stodur(lysing: dict[str, Any], kodi: str) -> dict[str, int]:
    """Sækir ``category.index``: valinn kóði -> staða hans innan víddarinnar."""
    stodur = lysing.get("category", {}).get("index")
    if not isinstance(stodur, dict):
        raise JsonstatVilla(f"Víddin {kodi!r} vantar `category.index`.")
    return stodur


def _heiti_i_svari(lysing: dict[str, Any], kodi: str) -> dict[str, str]:
    """Sækir ``category.label``: valinn kóði -> heiti eins og svarið gefur það."""
    heiti = lysing.get("category", {}).get("label")
    if not isinstance(heiti, dict):
        raise JsonstatVilla(f"Víddin {kodi!r} vantar `category.label`.")
    return heiti


def _sannreyna_stodur(kodi: str, stodur: dict[str, int], staerd: int) -> None:
    """Stöðvar sé ``category.index`` ekki heil og gatalaus röð ``0..staerd-1``."""
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


def _leyfdir_kodar(kodabok: Kodabok, kodi: str) -> dict[str, str]:
    """Sækir leyfða kóða víddarinnar og heiti þeirra úr lýsigögnunum."""
    leyfd = kodabok.get(kodi)
    if leyfd is None:
        raise JsonstatVilla(
            f"Víddin {kodi!r} er í svarinu en finnst ekki í {LYSIGAGNASKRA}."
        )
    return leyfd


def _sannreyna_heiti(
    kodi: str,
    stodur: dict[str, int],
    i_svari: dict[str, str],
    leyfd: dict[str, str],
) -> None:
    """Stöðvar lýsi svarið og lýsigögnin ekki sömu töflu.

    Beri valinn kóði annað heiti á stöðunum tveimur er ekki vitað hvor lýsingin
    á við gildin — og þar með ekki hvað taflan sýnir.
    """
    for valinn in stodur:
        if valinn not in leyfd:
            raise JsonstatVilla(
                f"Kóðinn {valinn!r} í vídd {kodi!r} er í svarinu en ekki meðal "
                f"leyfðra kóða í {LYSIGAGNASKRA}. Skrárnar lýsa ekki sömu töflu."
            )
        if i_svari.get(valinn) != leyfd[valinn]:
            raise JsonstatVilla(
                f"Kóðinn {valinn!r} í vídd {kodi!r} heitir {i_svari.get(valinn)!r} í "
                f"svarinu en {leyfd[valinn]!r} í {LYSIGAGNASKRA}."
            )


def _byggja_gildi(
    leyfd: dict[str, str], stodur: dict[str, int]
) -> tuple[Viddargildi, ...]:
    """Býr til eitt :class:`Viddargildi` á hvern leyfðan kóða víddarinnar."""
    return tuple(
        Viddargildi(kodi=kodi, heiti=heiti, stada=stodur.get(kodi))
        for kodi, heiti in leyfd.items()
    )
