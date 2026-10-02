"""Sameiginleg grunnvirkni fyrir frystingu hrágagna í ``data/raw/`` (regla 4).

Regla 4 gerir sömu kröfur til hvers gagnasafns: svarið vistað óbreytt áður en
nokkuð er unnið úr því, provenance með SHA-256, og auðkennandi User-Agent sem
ber ekki persónulegt netfang. Þær kröfur eiga því heima á einum stað og ekki
afritaðar inn í hverja söfnunarskriftu.

Einingin gerir þrennt:

* reiknar SHA-256 og lýsir skrám safns,
* les provenance sem fylgdi safni og skilar væntum SHA-256 per skrá,
* skrifar ``data/raw/frysting.json`` — skrána yfir hvað var fryst, hvenær,
  hvaðan og hvað stemmdi.

Staðfestingin sjálf er í ``vidmid.provenance`` (``stadfesta``), sem ber bæði
``frysting.json`` og ``docs/vidmid/provenance.json`` við diskinn.

``frysting.json`` er **ekki** í stað provenance hvers safns. Provenance svarar
„hvaðan komu gögnin?"; frysting.json svarar „hvenær komust þau hingað og eru
þau enn ósnert?".
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
HRAGOGN = ROT / "data" / "raw"
FRYSTING = HRAGOGN / "frysting.json"

SNID_UTGAFA = 1
VERK = "P0.3 — frysting hrágagna (issue #2)"
BUFFER_BAET = 1 << 20  # 1 MiB í einu — stór svör fara ekki öll í minni

# Auðkenni gagnvart vefþjónustu (regla 4). Sjálfgefna gildið vísar á repo-ið en
# ekki á netfang: repo-ið er opið og persónulegt netfang á ekkert erindi í
# opinberan User-Agent. Tengiliður sem þolir birtingu má koma úr umhverfinu.
AUDKENNIS_BREYTA = "NOTANDA_AUDKENNI"
SJALFGEFID_AUDKENNI = (
    "Upplysingaverkfradi-rannsokn/1.0 "
    "(+https://github.com/bjd5/Upplysingaverkfradi_improvements)"
)

PROVENANCE_HEITI = "provenance.json"

# Söfn sem liggja líka í data/raw/ en eru tryggð annars staðar. Þau eru skráð
# hér sem TILVÍSUN en ekki afrituð inn: tvær summur fyrir sömu skrá geta ekki
# annað en farið á skjön með tímanum. mbl-eintakið var fryst í P0.1 og er
# tryggt í docs/vidmid/provenance.json.
SKRAD_ANNARS_STADAR = (
    {
        "heiti": "mbl",
        "mappa": "data/raw/mbl",
        "fryst_i": "P0.1 (issue #30)",
        "provenance": "docs/vidmid/provenance.json",
        "stadfest_med": "python3 src/python/vidmid/provenance.py stadfesta",
    },
    # Friends-handritin eru EKKI fryst hér og mega ekki vera það: þau eru
    # höfundarréttarvarin og þetta repo er opið (issue #3). Þau eru git
    # submodule — git geymir aðeins slóð og commit-SHA (gitlink), og venjulegt
    # `git clone` sækir þau ekki. Commit-SHA-ið í gitlink er frystingin.
    {
        "heiti": "friends-handrit",
        "mappa": "data/raw/friends-handrit",
        "fryst_i": "issue #3, ákvörðun (a) 28.9.2026 — git submodule, ekki efni í git",
        "upprunarepo": "https://github.com/delvinso/friends-tv-show-analysis",
        "commit": "a4641fed3d95bb9d9c7ba23681604c692f9b392a",
        "commit_dagsetning": "2019-02-21T14:44:22-05:00",
        "provenance": "docs/heimildir.md, kafli 2.1",
        "stadfest_med": "git submodule status data/raw/friends-handrit",
    },
)

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("frysting")


def stutt_slod(slod: Path) -> str:
    """Slóð afstæð við rót verkefnisins þegar hún liggur þar, annars full slóð.

    Villuboð eiga að vera læsileg án þess að falla sjálf: ``relative_to`` kastar
    villu á slóð utan rótarinnar og þá hyrfi upprunalega villan.
    """
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)


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
        skra for skra in mappa.rglob("*") if skra.is_file() and not skra.name.startswith(".")
    )


def notandi_audkenni() -> str:
    """Skilar User-Agent sem auðkennir verkefnið (regla 4).

    Gildi úr umhverfinu er tekið fram yfir sjálfgefna gildið, en aðvörun fylgir
    ef það inniheldur netfang — repo-ið er opið og netfangið birtist þá bæði í
    provenance og í aðgangsskrám þjónustunnar.
    """
    audkenni = os.environ.get(AUDKENNIS_BREYTA, "").strip() or SJALFGEFID_AUDKENNI
    if "@" in audkenni:
        log.warning(
            "%s inniheldur netfang (%s). Það fer í provenance sem er í opnu "
            "repo-i — notaðu tengilið sem þolir birtingu.",
            AUDKENNIS_BREYTA,
            audkenni,
        )
    return audkenni


def vaentar_summur(mappa: Path) -> dict[str, str]:
    """Les SHA-256 sem provenance safnsins lofar, sem {skráarheiti: summa}.

    Tvö snið eru í notkun og bæði eru lesin:

    * ``"sha256": {"skra.json": "..."}`` — summa per skrá (hagstofan).
    * ``"sha256": "..."`` — ein summa fyrir svarskrána (vedur-quakes). Skráin
      sem hún á við er ``response_file`` ef hún er skráð, annars eina skráin í
      möppunni sem er ekki provenance sjálft.

    Skilar tómu mappingi ef ekkert provenance fylgdi. Óskiljanlegt snið stöðvar
    keyrsluna (regla 6) — þögult tómt mapping myndi láta staðfestinguna líta út
    fyrir að hafa heppnast.
    """
    slod = mappa / PROVENANCE_HEITI
    if not slod.is_file():
        return {}

    skjal = json.loads(slod.read_text(encoding="utf-8"))
    summur = skjal.get("sha256")
    if summur is None:
        return {}
    if isinstance(summur, dict):
        return dict(summur)
    if not isinstance(summur, str):
        raise ValueError(f"{slod}: sha256 er hvorki strengur né mapping heldur {type(summur).__name__}")

    nefnd = skjal.get("response_file")
    if nefnd:
        return {str(nefnd): summur}

    gagnaskrar = [skra.name for skra in skrar_i(mappa) if skra.name != PROVENANCE_HEITI]
    if len(gagnaskrar) != 1:
        raise ValueError(
            f"{slod}: ein sha256-summa en {len(gagnaskrar)} gagnaskrár í möppunni "
            f"({', '.join(gagnaskrar) or 'engin'}). Skráðu response_file svo ljóst "
            "sé við hvaða skrá summan á."
        )
    return {gagnaskrar[0]: summur}


def lysa_skrar(mappa: Path, vaentar: dict[str, str] | None = None) -> list[dict]:
    """Lýsir hverri skrá safnsins: slóð, stærð, SHA-256 og hvort hún var sannreynd.

    ``vaentar`` er summur sem provenance lofaði. Stemmi summa ekki er það villa
    sem stöðvar keyrsluna: afritið er þá ekki afrit (regla 4).
    """
    vaentar = vaentar or {}
    lysing: list[dict] = []
    for skra in skrar_i(mappa):
        afstaed = skra.relative_to(mappa).as_posix()
        summa = sha256_af(skra)
        vaent = vaentar.get(afstaed)
        if vaent is not None and vaent != summa:
            raise ValueError(
                f"{stutt_slod(mappa)}/{afstaed}: SHA-256 stemmir ekki við "
                f"provenance. Vænt {vaent}, reiknað {summa}."
            )
        lysing.append(
            {
                "slod": afstaed,
                "staerd_baet": skra.stat().st_size,
                "sha256": summa,
                # Skrá sem provenance nefnir ekki (provenance.json sjálft, t.d.)
                # er skráð en ekki sannreynd. Munurinn þarf að vera sýnilegur.
                "stadfest_vid_provenance": vaent is not None,
            }
        )
    return lysing


def lesa_frystingu() -> dict:
    """Les ``data/raw/frysting.json``, eða skilar tómri beinagrind ef hún er ekki til."""
    if FRYSTING.is_file():
        return json.loads(FRYSTING.read_text(encoding="utf-8"))
    return {
        "snid_utgafa": SNID_UTGAFA,
        "verk": VERK,
        "sofn": {},
        "ofryst": [],
        "skrad_annars_stadar": list(SKRAD_ANNARS_STADAR),
    }


def skrifa_frystingu(skjal: dict) -> None:
    """Skrifar ``data/raw/frysting.json`` með uppfærðum tímastimpli."""
    skjal["uppfaert_utc"] = nuna_utc()
    skjal["skrad_annars_stadar"] = list(SKRAD_ANNARS_STADAR)
    skjal["fjoldi_skraa"] = sum(safn["fjoldi_skraa"] for safn in skjal["sofn"].values())
    skjal["staerd_baet"] = sum(safn["staerd_baet"] for safn in skjal["sofn"].values())
    FRYSTING.parent.mkdir(parents=True, exist_ok=True)
    FRYSTING.write_text(json.dumps(skjal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def skra_safn(faersla: dict) -> None:
    """Bætir safni (eða uppfærir það) í ``frysting.json``."""
    skjal = lesa_frystingu()
    skjal["sofn"][faersla["heiti"]] = faersla
    skrifa_frystingu(skjal)
