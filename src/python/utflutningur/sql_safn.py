"""Lítill lesari fyrir nefndar SQL-fyrirspurnir útflutningsins (issue #15).

SQL-ið býr í ``src/sql/queries/*.sql`` og hver fyrirspurn hefst á
``-- @fyrirspurn: <heiti>`` — sama snið og ``vedurstodvar-siur.sql``. Þáttunin
sjálf er endurnýtt úr :func:`vinnsla.vedurstodvar_fyrirspurnir.lesa_fyrirspurnir`
(hún tekur slóð sem breytu) svo sniðið sé skilgreint á einum stað.

Þetta er einkalesari útflutningsins, ekki almennt fyrirspurnalag:
``gagnagrunnur/fyrirspurnir.py`` er annað verk.

Allar breytur fara inn sem gildi (``cur.execute(sql, breytur)``), aldrei með
strengjasamsetningu (regla 5).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from sqlite3 import Connection, Row

from gagnagrunnur.tenging import ROT
from vinnsla.vedurstodvar_fyrirspurnir import lesa_fyrirspurnir

from .json_skrif import UtflutningsVilla

FYRIRSPURNAMAPPA = ROT / "src" / "sql" / "queries"


class Fyrirspurnasafn:
    """Nefndar fyrirspurnir úr einni SQL-skrá, lesnar einu sinni."""

    def __init__(self, slod: Path) -> None:
        self.slod = slod
        self._safn: dict[str, str] | None = None

    def sql(self, heiti: str) -> str:
        """Skilar SQL nefndrar fyrirspurnar; óþekkt heiti er villa, ekki tómur strengur."""
        if self._safn is None:
            self._safn = lesa_fyrirspurnir(self.slod)
        if heiti not in self._safn:
            raise UtflutningsVilla(
                f"Fyrirspurnin {heiti!r} er ekki í {self.slod.name}. Til eru: "
                + ", ".join(sorted(self._safn))
            )
        return self._safn[heiti]

    def radir(
        self, samband: Connection, heiti: str, breytur: Mapping[str, object] | None = None
    ) -> list[Row]:
        """Keyrir fyrirspurnina með nefndum breytum og skilar öllum röðum."""
        return samband.execute(self.sql(heiti), dict(breytur or {})).fetchall()

    def ein_rod(
        self, samband: Connection, heiti: str, breytur: Mapping[str, object] | None = None
    ) -> Row:
        """Eins og :meth:`radir` en krefst nákvæmlega einnar raðar.

        Engin röð þýðir að grunnurinn hefur ekki verið hlaðinn; fleiri en ein að
        eitthvað sé tvískráð. Hvorugt má enda sem tala á vefsíðunni (regla 6).
        """
        radir = self.radir(samband, heiti, breytur)
        if len(radir) != 1:
            raise UtflutningsVilla(
                f"Fyrirspurnin {heiti!r} ({self.slod.name}) skilaði {len(radir)} "
                "röðum en átti að skila einni. Er búið að hlaða gagnasafnið í grunninn?"
            )
        return radir[0]
