"""Villan sem stöðvar skref í flæðinu og nefnir hvað brást (issue #39)."""

from __future__ import annotations


class SkrefVilla(RuntimeError):
    """Skref gat ekki lokið: safn eða vinnsla nefnd, ásamt ástæðunni.

    ``main.py`` breytir henni í útgangskóða 1. Hún er aldrei gleypt: næstu skref
    myndu annars byggja tölur á ófullgerðum gögnum (regla 6).
    """
