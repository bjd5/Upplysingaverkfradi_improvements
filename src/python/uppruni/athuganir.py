"""Sjálfvirkar athuganir á nýjum skrám úr upprunanum, miðað við CLAUDE.md.

Athugasemdirnar eru ábendingar, ekki dómar: þær segja hvað þarf að laga
þegar skráin er flutt yfir. Leyndarmál eru aldrei endurtekin í skýrslunni.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import PurePosixPath

HAMARKSLINUR = 300  # regla 6
HAMARKSSTAERD = 1_000_000  # regla 7: stór hrágögn fara ekki í git
SKRAARHEITI = re.compile(r"^[a-z0-9][a-z0-9._-]*$")  # regla 1.2
SQL_KOLL = {"execute", "executemany", "executescript"}

LEYNDARMAL = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"'](?=[^\"']*\d)[A-Za-z0-9._\-]{20,}[\"']"
    r"|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}"  # JWT, t.d. TMDB-lykill
    r"|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"
)
INLINE = re.compile(
    r"<style\b|\sstyle\s*=\s*[\"']|\son[a-z]+\s*=\s*[\"']|<script\b(?![^>]*\bsrc=)",
    re.IGNORECASE,
)
CDN = re.compile(r"https?://(?:cdn\.|unpkg\.com|cdnjs\.)", re.IGNORECASE)
VEFENDINGAR = {".html", ".qmd", ".js", ".css"}


def _python(texti: str, stadbundnar: frozenset[str]) -> list[str]:
    try:
        tre = ast.parse(texti)
    except SyntaxError as villa:
        return [f"Python þáttast ekki (lína {villa.lineno})"]

    athugasemdir: list[str] = []
    pakkar: set[str] = set()
    for hnutur in ast.walk(tre):
        if isinstance(hnutur, ast.Import):
            pakkar.update(heiti.name.split(".")[0] for heiti in hnutur.names)
        elif isinstance(hnutur, ast.ImportFrom) and hnutur.module and not hnutur.level:
            pakkar.add(hnutur.module.split(".")[0])
        elif isinstance(hnutur, ast.ExceptHandler) and all(
            isinstance(s, ast.Pass) for s in hnutur.body
        ):
            athugasemdir.append(f"Villa þögguð í línu {hnutur.lineno} (regla 6)")
        elif (
            isinstance(hnutur, ast.Call)
            and isinstance(hnutur.func, ast.Attribute)
            and hnutur.func.attr in SQL_KOLL
            and hnutur.args
            and _er_samsettur_strengur(hnutur.args[0])
        ):
            athugasemdir.append(f"SQL sett saman úr streng í línu {hnutur.lineno} (regla 5)")

    utan = sorted(pakkar - set(sys.stdlib_module_names) - stadbundnar)
    if utan:
        athugasemdir.append(f"Pakkar utan staðalsafns: {', '.join(utan)} (regla 10 — spyrja)")
    return athugasemdir


def _er_samsettur_strengur(hnutur: ast.expr) -> bool:
    if isinstance(hnutur, ast.JoinedStr):
        return True
    if isinstance(hnutur, ast.BinOp) and isinstance(hnutur.op, (ast.Mod, ast.Add)):
        return True
    return (
        isinstance(hnutur, ast.Call)
        and isinstance(hnutur.func, ast.Attribute)
        and hnutur.func.attr == "format"
    )


def athuga(
    slod: str, innihald: bytes, flokkur: str, stadbundnar: frozenset[str] = frozenset()
) -> list[str]:
    """Skilar athugasemdum um eina skrá; tómur listi ef ekkert fannst.

    `stadbundnar` eru heiti Python-eininga í upprunanum sjálfum, svo innflutningur
    á milli skráa þar teljist ekki utanaðkomandi pakki.
    """
    skra = PurePosixPath(slod)
    athugasemdir: list[str] = []

    if len(innihald) > HAMARKSSTAERD:
        athugasemdir.append(f"{len(innihald) / 1e6:.1f} MB — á hún heima í git? (regla 7)")
    if flokkur == "hragogn" and not SKRAARHEITI.match(skra.name):
        athugasemdir.append("Skráarheiti ekki ASCII-lágstafir (regla 1.2)")

    try:
        texti = innihald.decode("utf-8")
    except UnicodeDecodeError:
        return athugasemdir  # tvíundaskrá: aðeins stærð og heiti eiga við

    if LEYNDARMAL.search(texti):
        athugasemdir.append("Mögulegt leyndarmál — ALDREI afrita (regla 4)")
    if skra.suffix == ".py":
        linur = len(texti.splitlines())
        if linur > HAMARKSLINUR:
            athugasemdir.append(f"{linur} línur — kljúfa (regla 6)")
        athugasemdir.extend(_python(texti, stadbundnar))
    if skra.suffix in VEFENDINGAR:
        if skra.suffix in {".html", ".qmd"} and INLINE.search(texti):
            athugasemdir.append("Inline CSS/JS — aðskilja (regla 2)")
        if CDN.search(texti):
            athugasemdir.append("CDN-tengill (regla 3.4)")
    return athugasemdir
