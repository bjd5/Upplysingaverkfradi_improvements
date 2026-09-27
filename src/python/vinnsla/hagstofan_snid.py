"""Gagnasniðin sem lestur json-stat2-svarsins skilar — og heiti frystu skránna.

Hér er engin rökvísi: aðeins formin sem hinar einingarnar fylla, og villan sem
þær kasta allar. Ástæðan fyrir sérstakri skrá er að þrjár einingar þurfa sömu
formin — ``hagstofan_viddir`` býr þau til, ``hagstofan_gildi`` les þau og
``hagstofan_sannreyning`` mælir þau — og hringtengdur innflutningur milli
þeirra væri verri en ein hlutlaus skrá.

Sjá ``hagstofan_jsonstat.py`` fyrir hvernig einingarnar raðast saman.
"""

from __future__ import annotations

from dataclasses import dataclass

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
    """Eitt leyft gildi einnar víddar, með íslensku heiti sínu.

    ``stada`` er ``category.index`` úr svarinu: staðan innan víddarinnar og þar
    með lykillinn að því hvar gildið liggur í flata listanum. Hún er ``None``
    fyrir kóða sem lýsigögnin leyfa en frysta fyrirspurnin valdi ekki.
    """

    kodi: str
    heiti: str
    stada: int | None

    @property
    def valid(self) -> bool:
        """Rataði kóðinn inn í frystu fyrirspurnina?

        Leitt af ``stada`` en ekki geymt sér, svo þau geti aldrei stangast á —
        sama krafa og CHECK-skilyrðið í migration 003 setur á töfluna.
        """
        return self.stada is not None


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
        """Valin gildi í þeirri röð sem svarið raðar þeim.

        Röðin er efnisleg: hún ræður því hvaða gildi í flata listanum tilheyrir
        hvaða kóða. Lyklaröð í ``category.index`` er ekki notuð til þess.
        """
        valin = [g for g in self.gildi if g.stada is not None]
        return tuple(sorted(valin, key=lambda g: g.stada))


@dataclass(frozen=True)
class Maeling:
    """Eitt gildi úr flata listanum ásamt samsetningu víddanna sem á við það.

    ``kodar`` er (víddarkóði, gildiskóði) fyrir hverja vídd, í röð ``id``.
    """

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
