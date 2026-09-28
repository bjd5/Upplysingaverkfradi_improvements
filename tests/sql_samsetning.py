"""AST-leit að SQL sem er sett saman úr strengjum (regla 5).

Upphaflega í ``test_friends_sannreyning.py`` (P1.6, #10), þar sem hún náði yfir
fimm hleðslueiningar. Flutt hingað í #11 svo sama leit nái yfir **allan**
Python-kóðann í ``src/python/`` og prófin tvö noti eina útgáfu hennar.

``brot(kodi)`` skilar stöðunum þar sem SQL er sett saman — f-strengur,
``+``/``%``, ``+=`` eða ``.format`` á streng sem inniheldur SQL-orð, og
keyrslukall (``execute`` o.fl.) þar sem fyrirspurnin er reiknuð en ekki fast
nafn eða fasti — ásamt fjölda keyrslukalla. Kall í sameiginlega lesarann
(``fyrirspurnir.keyra``) telst keyrslukall: fyrirspurnin kemur þá úr
``src/sql/queries/`` og heitið fer í gegnum hvítlista, ekki inn í SQL.

Þetta er hjálpareining, ekki prófskrá.
"""

from __future__ import annotations

import ast

SQL_ORD = ("SELECT ", "INSERT ", "DELETE ", "UPDATE ", " FROM ", " WHERE ", "PRAGMA ")
KEYRSLUFOLL = {"execute", "executemany", "executescript"}
LESARAKALL = "keyra"
LESARAEINING = "fyrirspurnir"


def _er_sql(hnutur: ast.AST) -> bool:
    texti = " ".join(h.value for h in ast.walk(hnutur)
                     if isinstance(h, ast.Constant) and isinstance(h.value, str))
    return any(ord_ in f" {texti.upper()} " for ord_ in SQL_ORD)


def _er_lesarakall(hnutur: ast.Call) -> bool:
    """``fyrirspurnir.keyra(...)`` — keyrsla fyrirspurnar úr src/sql/queries/."""
    fall = hnutur.func
    return (isinstance(fall, ast.Attribute) and fall.attr == LESARAKALL
            and isinstance(fall.value, ast.Name) and fall.value.id == LESARAEINING)


def brot(kodi: str) -> tuple[list[str], int]:
    """Staðir í ``kodi`` þar sem SQL er sett saman, og fjöldi keyrslukalla."""
    fundid: list[str] = []
    kollin = 0
    for hnutur in ast.walk(ast.parse(kodi)):
        if isinstance(hnutur, ast.JoinedStr) and _er_sql(hnutur):
            fundid.append(f"f-strengur í línu {hnutur.lineno}")
        elif (isinstance(hnutur, ast.BinOp) and isinstance(hnutur.op, (ast.Add, ast.Mod))
              and _er_sql(hnutur)):
            fundid.append(f"+/% í línu {hnutur.lineno}")
        elif (isinstance(hnutur, ast.AugAssign) and isinstance(hnutur.op, ast.Add)
              and _er_sql(hnutur.value)):
            fundid.append(f"+= í línu {hnutur.lineno}")
        elif isinstance(hnutur, ast.Call) and isinstance(hnutur.func, ast.Attribute):
            if hnutur.func.attr == "format" and _er_sql(hnutur.func.value):
                fundid.append(f".format í línu {hnutur.lineno}")
            if _er_lesarakall(hnutur):
                kollin += 1
            elif hnutur.func.attr in KEYRSLUFOLL:
                kollin += 1
                if hnutur.args and not isinstance(hnutur.args[0], (ast.Name, ast.Constant)):
                    fundid.append(f"reiknuð fyrirspurn í línu {hnutur.lineno}")
    return fundid, kollin
