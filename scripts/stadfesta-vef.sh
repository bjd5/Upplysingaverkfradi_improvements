#!/usr/bin/env bash
#
# Staðfestir web/ áður en hún er birt á GitHub Pages (issue #28): hver
# gagnaskrá í web/gogn/ er gilt JSON á sniði útflutningsins (regla 5.4), engin
# skrá sem útflutningurinn skrifar vantar, og hver gagnaskrá sem síða vísar í
# er til. Allar villur eru taldar upp; útgangskóði 1 ef einhver fannst.
#
# Birtingin (.github/workflows/pages.yml) keyrir þessa sömu skipun og stöðvast
# ef hún fellur. Keyrðu hana því áður en þú ýtir á main.
#
# Notkun:
#   scripts/stadfesta-vef.sh
#   scripts/stadfesta-vef.sh --vefur /slod/a/afriti/af/web

set -euo pipefail

ROT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

PYTHONPATH="$ROT/src/python${PYTHONPATH:+:$PYTHONPATH}" \
    exec "$PYTHON" -m utflutningur.stadfesta_vef "$@"
