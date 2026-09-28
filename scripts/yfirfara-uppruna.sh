#!/usr/bin/env bash
#
# Sækir nýjustu stöðu upprunarepo-sins og flokkar það sem hefur breyst síðan
# síðast var yfirfarið (docs/uppruni/stada.json). Verklagið er í
# docs/uppruni.md.
#
# Klónið fer utan repo-sins: það er afrit af öðru verkefni, ekki gögn þessa.
#
# Notkun:
#   scripts/yfirfara-uppruna.sh              # prentar skýrsluna
#   scripts/yfirfara-uppruna.sh --skrifa     # vistar hana og færir stöðuna
#   UPPRUNI_KLON=/slod scripts/yfirfara-uppruna.sh

set -euo pipefail

ROT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
KLON="${UPPRUNI_KLON:-${TMPDIR:-/tmp}/uppruni-friends-phoebe}"

lesa_stillingu() {
    "$PYTHON" -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' \
        "$ROT/config/uppruni.json" "$1"
}
REPO="$(lesa_stillingu repo)"
GREIN="$(lesa_stillingu grein)"

if [ -d "$KLON/.git" ]; then
    echo "==> Uppfæri klón: $KLON" >&2
    git -C "$KLON" fetch --quiet origin "$GREIN"
else
    echo "==> Klóna $REPO í $KLON" >&2
    git clone --quiet --no-checkout "https://github.com/$REPO.git" "$KLON"
    git -C "$KLON" fetch --quiet origin "$GREIN"
fi

PYTHONPATH="$ROT/src/python" exec "$PYTHON" -m uppruni.yfirfara \
    --klon "$KLON" --til FETCH_HEAD "$@"
