#!/usr/bin/env bash
# Run concrete uSVP experiments. Calls the env's python directly because
# `micromamba run` returned 0 on a Python traceback (observed 2026-10-08).
set -u
PY="$HOME/cm/mamba/envs/sage/bin/python"
cd "$(dirname "$0")/.."
status=0
for spec in "$@"; do
  read -r eta n trials maxb <<<"$spec"
  "$PY" src/usvp_concrete.py "$eta" "$n" "$trials" "$maxb"
  rc=$?
  echo "eta=$eta n=$n exit=$rc"
  [ "$rc" -ne 0 ] && status=1
  ls results/usvp_eta${eta}_n${n}*.json >/dev/null 2>&1 || { echo "missing result for eta=$eta n=$n"; status=1; }
done
exit $status
