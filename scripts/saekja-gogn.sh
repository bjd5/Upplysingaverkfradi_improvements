#!/usr/bin/env bash
#
# Sækir hrágögn rannsóknarinnar í data/raw/ gegnum sameiginlega HTTP-lagið
# (src/python/sofnun/).
#
# SJÁLFGEFIÐ SENDIR ÞETTA EKKERT NETKALL. Hvert safn sem þegar liggur í
# data/raw/ er skilað úr geymslunni — regla 4 bannar að sækja sömu gögn tvisvar
# að óþörfu, og síðan á að byggjast eins í hvert sinn. --thvinga er meðvituð
# ákvörðun um að sækja nýtt eintak þrátt fyrir það.
#
# Skriftan keyrir söfnunina sem PYTHON-EININGU (-m) og aldrei skrána beint.
# Ástæðan er að src/python/sofnun/http.py heitir eins og http úr staðalsafninu:
# væri mappan fremst á sys.path fyndi urllib okkar skrá í staðinn.
#
# Notkun:
#   scripts/saekja-gogn.sh listi              # telur upp söfnin
#   scripts/saekja-gogn.sh allt               # öll söfn, engin netkall
#   scripts/saekja-gogn.sh skjalftar
#   scripts/saekja-gogn.sh mbl --thvinga      # sækir NÝTT eintak
#
# Umhverfisbreytur (sjá config/.env.example — aldrei lyklar í kóða, regla 4):
#   NOTANDA_AUDKENNI   tengiliður í User-Agent; skylda þegar sótt er
#   BID_MILLI_KALLA    lágmarksbið milli kalla á sömu þjónustu, sekúndur
#   TMDB_TOKEN         lykill TMDB; vanti hann er safnið skráð óvirkt

set -euo pipefail

ROT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

PYTHONPATH="$ROT/src/python${PYTHONPATH:+:$PYTHONPATH}" \
    exec "$PYTHON" -m sofnun.saekja_allt "$@"
