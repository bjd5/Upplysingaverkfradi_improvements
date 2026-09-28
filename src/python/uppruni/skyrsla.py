"""Skrifar yfirferð á upprunanum sem stutta Markdown-skýrslu."""

from __future__ import annotations

from dataclasses import dataclass, field

from .flokkun import FLOKKAR, FLYTJA, OFLOKKAD, Regla
from .saga import Breyting


@dataclass(frozen=True)
class Lidur:
    """Ein breytt skrá, reglan sem á við hana og athugasemdir um hana."""

    breyting: Breyting
    regla: Regla | None
    athugasemdir: tuple[str, ...] = ()

    @property
    def flokkur(self) -> str:
        """Flokkur reglunnar, eða „óflokkað“ ef engin regla passaði."""
        return self.regla.flokkur if self.regla else OFLOKKAD

    @property
    def athuga(self) -> str:
        """Athugasemd reglunnar og sjálfvirku athugasemdirnar í einum streng."""
        allar = [self.regla.athugasemd] if self.regla and self.regla.athugasemd else []
        return "; ".join(a.rstrip(".") for a in [*allar, *self.athugasemdir])


@dataclass(frozen=True)
class Yfirferd:
    """Allt sem ein skýrsla segir frá."""

    repo: str
    fra: str
    til: str
    dagur: str
    fjoldi_commita: int
    lidir: tuple[Lidur, ...]
    titlar: dict[str, str] = field(default_factory=dict)

    def i_flokki(self, *flokkar: str) -> list[Lidur]:
        """Liðir í gefnum flokkum, í flokkaröð og svo stafrófsröð."""
        rod = list(FLOKKAR) + [OFLOKKAD]
        valdir = [lidur for lidur in self.lidir if lidur.flokkur in flokkar]
        return sorted(valdir, key=lambda l: (rod.index(l.flokkur), l.breyting.slod))


def _reitur(texti: str) -> str:
    return texti.replace("|", "\\|") or "—"


def _tafla(haus: list[str], radir: list[list[str]]) -> list[str]:
    linur = ["| " + " | ".join(haus) + " |", "|" + "---|" * len(haus)]
    linur += ["| " + " | ".join(_reitur(r) for r in rod) + " |" for rod in radir]
    return linur + [""]


def _flytja(y: Yfirferd) -> list[str]:
    lidir = y.i_flokki(*FLYTJA)
    if not lidir:
        return []
    linur = ["## Flytja", ""]
    for rannsokn in sorted({l.regla.rannsokn for l in lidir}):
        titill = y.titlar.get(rannsokn, rannsokn)
        linur += [f"### {titill} — `web/sidur/{rannsokn}.html`", ""]
        radir = [
            [f"`{l.breyting.slod}`", l.breyting.lysing, FLOKKAR[l.flokkur],
             f"`{l.regla.markmid}`", l.athuga]
            for l in lidir if l.regla.rannsokn == rannsokn
        ]
        linur += _tafla(["Skrá", "Breyting", "Flokkur", "Á heima í", "Athuga"], radir)
    return linur


def _einfold(y: Yfirferd, flokkur: str, titill: str, skyring: str) -> list[str]:
    lidir = y.i_flokki(flokkur)
    if not lidir:
        return []
    radir = [[f"`{l.breyting.slod}`", l.breyting.lysing, l.athuga] for l in lidir]
    return [f"## {titill}", "", skyring, "", *_tafla(["Skrá", "Breyting", "Athuga"], radir)]


def skrifa(y: Yfirferd) -> str:
    """Skilar skýrslunni sem Markdown-texta."""
    samanburdur = f"https://github.com/{y.repo}/compare/{y.fra[:7]}...{y.til[:7]}"
    fjoldi = {f: len(y.i_flokki(f)) for f in (*FLOKKAR, OFLOKKAD)}
    linur = [
        f"# Yfirferð uppruna — {y.dagur}",
        "",
        f"`{y.fra[:7]}` → `{y.til[:7]}` · {y.fjoldi_commita} commit · "
        f"{len(y.lidir)} skrár · [bera saman á GitHub]({samanburdur})",
        "",
        *_tafla(
            ["Flytja", "Ákvörðun", "Bannað", "Óflokkað", "Utan umfangs"],
            [[str(sum(fjoldi[f] for f in FLYTJA)), str(fjoldi["akvordun"]),
              str(fjoldi["bannad"]), str(fjoldi[OFLOKKAD]), str(fjoldi["utan"])]],
        ),
        *_flytja(y),
        *_einfold(y, "akvordun", "Þarf ákvörðun",
                  "Nýtt efni utan umfangs síðunnar. Björn ákveður hvort það flyst."),
        *_einfold(y, "bannad", "Bannað", "Þessar skrár fara aldrei í þetta repo."),
        *_einfold(y, OFLOKKAD, "Óflokkað",
                  "Engin regla passar. Bættu reglu í `config/uppruni.json` og keyrðu aftur."),
    ]
    utan = y.i_flokki("utan")
    if utan:
        slodir = ", ".join(f"`{l.breyting.slod}`" for l in utan)
        linur += ["## Utan umfangs", "", f"Flyst ekki (endurbygging.md §3): {slodir}.", ""]
    linur += ["---", "", "Skrifað af `src/python/uppruni/yfirfara.py`. "
              "Verklag: [`docs/uppruni.md`](../uppruni.md)."]
    return "\n".join(linur) + "\n"
