"""Hleðsla Hagstofugagnanna í SQL-grunninn (migration 003).

Les frysta json-stat2-svarið í ``data/raw/hagstofan/`` og skrifar það í löngu
töfluna ``hagstofan_observations`` ásamt kóðabókinni sem gerir hana læsilega.

Tvennt er ófrávíkjanlegt:

* **Allt eða ekkert.** Sannreyningin fer öll fram áður en fyrsta lína er
  skrifuð, og skrifin gerast innan færslu kallandans. Stemmi fjöldi gilda ekki
  við margfeldi víddastærðanna hefur lestur á json-stat2 farið úrskeiðis og
  keyrslan stöðvast — hálf tafla er verri en engin (regla 6).
* **Fyrirspurnir með breytum.** Engin SQL-setning hér er sett saman úr
  strengjum; dálkarnir eru fastir í migration 003 og skrifaðir út óbreyttir
  (regla 5).

Fallið :func:`hlada` er endurkeyranlegt: það hreinsar fyrri hleðslu sama
gagnasafns út áður en það skrifar, svo grunnurinn verði sá sami hversu oft sem
hann er byggður.
"""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur.tenging import ROT

from .hagstofan_jsonstat import FYRIRSPURNARSKRA, Gagnasafn, lesa_gagnasafn

log = logging.getLogger(__name__)

HRAGOGN = ROT / "data" / "raw" / "hagstofan"

# Heiti þjónustunnar eins og það er skráð í fetch_log (migration 001).
THJONUSTA = "Hagstofa Íslands (PxWeb)"

# Víddakóði Hagstofunnar -> dálkaforskeyti í hagstofan_observations.
# Kóðaheiti eru á ensku (regla 1.2); kóðarnir sjálfir eru gögn og standa
# óbreyttir. Röðin hér verður að vera sú sama og í migration 003 og í `id`
# svarsins — breytist afmörkun fyrirspurnarinnar stöðvar _sannreyna_viddir().
VIDDADALKAR: dict[str, str] = {
    "Innritunarár": "enrolment_year",
    "Tími": "time_point",
    "Nemendur": "student_status",
    "Fjöldi/Hlutfall": "measure",
    "Námssvið": "field",
    "Kyn": "sex",
}

SQL_GAGNASAFN = """
INSERT INTO hagstofan_datasets (
    id, label, source, endpoint, fetched_at, updated,
    jsonstat_version, decimals, value_count, raw_file, loaded_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SQL_VIDD = """
INSERT INTO hagstofan_dimensions (dataset_id, code, label, position, size, is_time)
VALUES (?, ?, ?, ?, ?, ?)
"""

SQL_VIDDARGILDI = """
INSERT INTO hagstofan_dimension_values (
    dataset_id, dimension_code, code, label, selected, value_index
) VALUES (?, ?, ?, ?, ?, ?)
"""

SQL_MAELING = """
INSERT INTO hagstofan_observations (
    dataset_id, flat_index, value,
    enrolment_year_dim, enrolment_year_code,
    time_point_dim, time_point_code,
    student_status_dim, student_status_code,
    measure_dim, measure_code,
    field_dim, field_code,
    sex_dim, sex_code
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SQL_SOFNUN = """
INSERT INTO fetch_log (
    service, endpoint, params, fetched_at, status_code, record_count, raw_file, notes
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

HREINSUN = (
    "DELETE FROM hagstofan_observations WHERE dataset_id = ?",
    "DELETE FROM hagstofan_dimension_values WHERE dataset_id = ?",
    "DELETE FROM hagstofan_dimensions WHERE dataset_id = ?",
    "DELETE FROM hagstofan_datasets WHERE id = ?",
)


class HledsluVilla(RuntimeError):
    """Gögnin stemma ekki við það sem migration 003 gerir ráð fyrir."""


def hlada(samband: Connection, mappa: Path | None = None) -> int:
    """Hleður frysta Hagstofusvarinu í grunninn og skilar fjölda mælinga.

    Kallandinn á færsluna: ``with tenging() as samband: hlada(samband)``.
    Villa hér veldur rollback hjá kallandanum og engin lína situr eftir.
    """
    mappa = mappa or HRAGOGN
    gagnasafn = lesa_gagnasafn(mappa)
    _sannreyna_viddir(gagnasafn)

    _hreinsa(samband, gagnasafn.audkenni)
    _skrifa_gagnasafn(samband, gagnasafn)
    _skrifa_viddir(samband, gagnasafn)
    _skrifa_maelingar(samband, gagnasafn)
    _skrifa_sofnun(samband, gagnasafn, mappa)

    fjoldi = _stadfesta_fjolda(samband, gagnasafn.audkenni)
    log.info(
        "Hlóð %d mælingum úr %s í hagstofan_observations.", fjoldi, gagnasafn.audkenni
    )
    return fjoldi


def _sannreyna_viddir(gagnasafn: Gagnasafn) -> None:
    """Stöðvar víki víddir svarsins frá þeim sex sem migration 003 á dálka fyrir."""
    ur_svari = [vidd.kodi for vidd in gagnasafn.viddir]
    if ur_svari != list(VIDDADALKAR):
        raise HledsluVilla(
            "Víddir svarsins eru ekki þær sem migration 003 gerir ráð fyrir.\n"
            f"  í svarinu:   {ur_svari}\n"
            f"  í schema:    {list(VIDDADALKAR)}\n"
            "Afmörkun fyrirspurnarinnar hefur breyst; það kallar á nýja migration, "
            "ekki á að gögnin séu þvinguð í gamla töflu."
        )


def _hreinsa(samband: Connection, audkenni: str) -> None:
    """Fjarlægir fyrri hleðslu sama gagnasafns svo hleðslan sé endurkeyranleg."""
    for setning in HREINSUN:
        samband.execute(setning, (audkenni,))


def _skrifa_gagnasafn(samband: Connection, gagnasafn: Gagnasafn) -> None:
    """Skrifar lýsigögn töflunnar: heiti, heimild, sóknartíma og snið."""
    samband.execute(
        SQL_GAGNASAFN,
        (
            gagnasafn.audkenni,
            gagnasafn.heiti,
            gagnasafn.heimild,
            gagnasafn.endapunktur,
            gagnasafn.sott_kl,
            gagnasafn.uppfaert,
            gagnasafn.utgafa,
            gagnasafn.aukastafir,
            len(gagnasafn.maelingar),
            _innan_verkefnis(Path(gagnasafn.hraskra)),
            _nuna(),
        ),
    )


def _skrifa_viddir(samband: Connection, gagnasafn: Gagnasafn) -> None:
    """Skrifar víddirnar sex og alla kóðabókina úr metadata.json."""
    for vidd in gagnasafn.viddir:
        samband.execute(
            SQL_VIDD,
            (
                gagnasafn.audkenni,
                vidd.kodi,
                vidd.heiti,
                vidd.rod,
                vidd.staerd,
                int(vidd.er_timi),
            ),
        )
        for gildi in vidd.gildi:
            samband.execute(
                SQL_VIDDARGILDI,
                (
                    gagnasafn.audkenni,
                    vidd.kodi,
                    gildi.kodi,
                    gildi.heiti,
                    int(gildi.valid),
                    gildi.stada,
                ),
            )


def _skrifa_maelingar(samband: Connection, gagnasafn: Gagnasafn) -> None:
    """Skrifar eina línu á hverja samsetningu víddanna sex."""
    for maeling in gagnasafn.maelingar:
        kodar = dict(maeling.kodar)
        radgildi: list[object] = [
            gagnasafn.audkenni,
            maeling.flat_stada,
            maeling.gildi,
        ]
        for viddarkodi in VIDDADALKAR:
            radgildi.append(viddarkodi)
            radgildi.append(kodar[viddarkodi])
        samband.execute(SQL_MAELING, tuple(radgildi))


def _skrifa_sofnun(samband: Connection, gagnasafn: Gagnasafn, mappa: Path) -> None:
    """Skráir söfnunina í ``fetch_log`` (migration 001, regla 4)."""
    hraskra = _innan_verkefnis(Path(gagnasafn.hraskra))
    samband.execute(
        "DELETE FROM fetch_log WHERE service = ? AND raw_file = ?",
        (THJONUSTA, hraskra),
    )
    samband.execute(
        SQL_SOFNUN,
        (
            THJONUSTA,
            gagnasafn.endapunktur,
            (mappa / FYRIRSPURNARSKRA).read_text(encoding="utf-8"),
            gagnasafn.sott_kl,
            None,
            len(gagnasafn.maelingar),
            hraskra,
            "Fryst POST-fyrirspurn, json-stat2. HTTP-staða var ekki skráð við "
            "frystingu; sóknartíminn kemur úr provenance.json.",
        ),
    )


def _stadfesta_fjolda(samband: Connection, audkenni: str) -> int:
    """Ber fjölda lína í grunninum saman við margfeldi víddastærðanna þar.

    Bæði talan og stærðirnar eru lesnar úr grunninum, ekki úr Python-minninu:
    prófið á að segja hvað GRUNNURINN geymir.
    """
    fjoldi = samband.execute(
        "SELECT COUNT(*) FROM hagstofan_observations WHERE dataset_id = ?",
        (audkenni,),
    ).fetchone()[0]

    staerdir = [
        rad[0]
        for rad in samband.execute(
            "SELECT size FROM hagstofan_dimensions WHERE dataset_id = ? "
            "ORDER BY position",
            (audkenni,),
        ).fetchall()
    ]
    vaentur = math.prod(staerdir) if staerdir else 0

    if fjoldi != vaentur:
        raise HledsluVilla(
            f"{fjoldi} línur rötuðu í hagstofan_observations en víddastærðirnar "
            f"{staerdir} gefa {vaentur}. Töflunni er rúllað til baka."
        )
    return fjoldi


def _innan_verkefnis(slod: Path) -> str:
    """Slóð miðað við rót verkefnisins svo skráningin sé óháð vélinni."""
    try:
        return str(slod.resolve().relative_to(ROT))
    except ValueError:
        return str(slod)


def _nuna() -> str:
    """Tímastimpill í ISO 8601, UTC, á sekúndunákvæmni."""
    return datetime.now(UTC).isoformat(timespec="seconds")
