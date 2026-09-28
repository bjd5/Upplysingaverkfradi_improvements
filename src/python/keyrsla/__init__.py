"""Keyrsluröð gagnaflæðisins: hvaða einingar ``main.py`` kallar í og í hvaða röð.

``main.py`` er aðeins inngangurinn (rök, skref, útgangskóði). Hér er það sem
skrefin gera í raun — ``hledsla`` fyrir ``--skref hlada`` og ``urvinnsla`` fyrir
``--skref vinna`` — svo inngangurinn haldist stuttur (regla 6) og hvert skref
sé prófanlegt án undirferlis (issue #39).
"""
