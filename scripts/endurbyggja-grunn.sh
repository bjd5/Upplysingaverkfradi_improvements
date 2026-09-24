#!/usr/bin/env bash
#
# Endurbyggir SQL-grunninn frá grunni: eyðir honum og býr hann til aftur úr
# src/sql/migrations/ og data/raw/.
#
# Þetta er PRÓFIÐ á reglu 5 — grunnurinn er afleiða, ekki frumgagn. Gangi
# þetta ekki upp er eitthvað í grunninum sem hvergi á sér heimild, og þá er
# rannsóknin ekki endurtekjanleg.
#
# Skýrslur fara á stderr, fingrafar grunnsins eitt á stdout, svo bera megi
# tvær byggingar saman:
#
#   fyrri=$(scripts/endurbyggja-grunn.sh)
#   seinni=$(scripts/endurbyggja-grunn.sh)
#   [ "$fyrri" = "$seinni" ]
#
# Notkun:
#   scripts/endurbyggja-grunn.sh
#   RANNSOKN_GRUNNUR=/slod/a/prof.sqlite scripts/endurbyggja-grunn.sh

set -euo pipefail

ROT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRUNNUR="${RANNSOKN_GRUNNUR:-$ROT/data/db/rannsokn.sqlite}"
PYTHON="${PYTHON:-python3}"

# Varnagli: skriftan eyðir skrá, svo hún neitar öllu sem lítur ekki út fyrir
# að vera SQLite-grunnur verkefnisins.
case "$GRUNNUR" in
    *.sqlite) ;;
    *)
        echo "Neita að eyða '$GRUNNUR' — slóðin endar ekki á .sqlite." >&2
        exit 1
        ;;
esac

if [ -d "$GRUNNUR" ]; then
    echo "Neita að eyða '$GRUNNUR' — þetta er mappa, ekki gagnagrunnur." >&2
    exit 1
fi

echo "==> Eyði grunni: $GRUNNUR" >&2
rm -f -- "$GRUNNUR" "$GRUNNUR-wal" "$GRUNNUR-shm" "$GRUNNUR-journal"
mkdir -p -- "$(dirname -- "$GRUNNUR")"

echo "==> Keyri migrations úr src/sql/migrations/" >&2
RANNSOKN_GRUNNUR="$GRUNNUR" "$PYTHON" "$ROT/src/python/main.py" --skref hlada

echo "==> Fingrafar grunnsins (án tímastimpla):" >&2
RANNSOKN_GRUNNUR="$GRUNNUR" PYTHONPATH="$ROT/src/python" \
    "$PYTHON" -m gagnagrunnur.fingrafar
