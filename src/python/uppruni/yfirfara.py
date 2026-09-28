"""Ber upprunarepo-ið saman við síðustu yfirferð og skrifar skýrslu.

Keyrsla (scripts/yfirfara-uppruna.sh klónar upprunann og kallar í þetta):
    PYTHONPATH=src/python python3 -m uppruni.yfirfara --klon /slod/a/klon
    PYTHONPATH=src/python python3 -m uppruni.yfirfara --klon /slod/a/klon --skrifa

Án --skrifa prentast skýrslan bara. Með --skrifa vistast hún í docs/uppruni/
og staðan færist fram — það er gert í sama PR og skrárnar eru fluttar í.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from . import saga
from .athuganir import athuga
from .flokkun import Stilling, StillingarVilla, finna_reglu, lesa_stillingu
from .saga import SoguVilla
from .skyrsla import Lidur, Yfirferd, skrifa

ROT = Path(__file__).resolve().parents[3]
SKYRSLUMAPPA = ROT / "docs" / "uppruni"
STADA = SKYRSLUMAPPA / "stada.json"
SIDUR = ROT / "web" / "sidur"
FYRIRSOGN = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)
ENGAR_ATHUGANIR = {"utan", "bannad"}


def lesa_stodu(slod: Path = STADA) -> dict:
    """Les docs/uppruni/stada.json: síðasta yfirfarna commit upprunans."""
    try:
        stada = json.loads(slod.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as villa:
        raise StillingarVilla(f"Get ekki lesið {slod}: {villa}") from villa
    if "yfirfarid_til" not in stada:
        raise StillingarVilla(f"{slod}: vantar yfirfarid_til.")
    return stada


def skrifa_stodu(til: str, dagur: str, skyrsla: Path, slod: Path = STADA) -> None:
    """Færir stöðuna fram á `til` og vísar í skýrsluna sem skráði það."""
    stada = lesa_stodu(slod)
    stada.update(
        yfirfarid_til=til,
        dagsetning=dagur,
        skyrsla=skyrsla.relative_to(slod.parent).as_posix(),
    )
    slod.write_text(json.dumps(stada, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def titlar_sidna(mappa: Path = SIDUR) -> dict[str, str]:
    """Kort frá heiti síðu (t.d. „hagstofan“) í <h1> hennar."""
    titlar = {}
    for sida in mappa.glob("*.html"):
        fundur = FYRIRSOGN.search(sida.read_text(encoding="utf-8"))
        if fundur:
            titlar[sida.stem] = " ".join(fundur.group(1).split())
    return titlar


def _lidur(klon: Path, til: str, breyting: saga.Breyting, stilling: Stilling,
           stadbundnar: frozenset[str]) -> Lidur:
    regla = finna_reglu(breyting.slod, stilling.reglur)
    flokkur = regla.flokkur if regla else "oflokkad"
    if breyting.stada == "D" or flokkur in ENGAR_ATHUGANIR:
        return Lidur(breyting, regla)
    try:
        innihald = saga.innihald(klon, til, breyting.slod)
    except SoguVilla as villa:
        return Lidur(breyting, regla, (f"Gat ekki lesið skrána: {villa}",))
    return Lidur(breyting, regla, tuple(athuga(breyting.slod, innihald, flokkur, stadbundnar)))


def yfirfara(klon: Path, stilling: Stilling, fra: str, til: str, dagur: str) -> Yfirferd:
    """Flokkar og athugar hverja skrá sem breyttist milli `fra` og `til`."""
    if not saga.er_forfadir(klon, fra, til):
        raise SoguVilla(
            f"{fra[:7]} er ekki í sögu {til[:7]} — saga upprunans var endurskrifuð. "
            "Berðu saman handvirkt og keyrðu með --fra."
        )
    # Innflutningur milli skráa í upprunanum (t.d. `from src import x`) er
    # ekki utanaðkomandi pakki: heiti eininga og efstu mappa teljast staðbundin.
    skrar = [PurePosixPath(s) for s in saga.skrar(klon, til)]
    stadbundnar = frozenset(
        [s.stem for s in skrar if s.suffix == ".py"] + [s.parts[0] for s in skrar]
    )
    lidir = tuple(
        _lidur(klon, til, breyting, stilling, stadbundnar)
        for breyting in saga.breytingar(klon, fra, til)
    )
    return Yfirferd(
        repo=stilling.repo,
        fra=fra,
        til=til,
        dagur=dagur,
        fjoldi_commita=saga.fjoldi_commita(klon, fra, til),
        lidir=lidir,
        titlar=titlar_sidna(),
    )


def main(argv: list[str] | None = None) -> int:
    """Keyrslupunktur. Skilar 0 ef allt gekk, 1 ef git eða stillingar brugðust."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--klon", type=Path, required=True, help="klón upprunarepo-sins")
    parser.add_argument("--fra", help="commit sem síðast var yfirfarið (sjálfgefið: stada.json)")
    parser.add_argument("--til", default="HEAD", help="commit sem á að yfirfara (sjálfgefið: HEAD)")
    parser.add_argument("--skrifa", action="store_true", help="vista skýrslu og færa stöðuna")
    rok = parser.parse_args(argv)

    try:
        stilling = lesa_stillingu()
        fra = saga.commit(rok.klon, rok.fra or lesa_stodu()["yfirfarid_til"])
        til = saga.commit(rok.klon, rok.til)
        if fra == til:
            print(f"Ekkert nýtt: upprunninn er enn á {til[:7]}.")
            return 0
        dagur = datetime.now(timezone.utc).date().isoformat()
        texti = skrifa(yfirfara(rok.klon, stilling, fra, til, dagur))
    except (SoguVilla, StillingarVilla) as villa:
        print(f"Villa: {villa}", file=sys.stderr)
        return 1

    if not rok.skrifa:
        print(texti, end="")
        return 0
    skyrsla = SKYRSLUMAPPA / f"{dagur}-{til[:7]}.md"
    skyrsla.write_text(texti, encoding="utf-8")
    skrifa_stodu(til, dagur, skyrsla)
    print(f"Skýrsla: {skyrsla.relative_to(ROT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
