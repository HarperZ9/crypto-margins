#!/usr/bin/env bash
# Sweep the dual-hybrid check. Each arg: "M NR K TRIALS THREADS".
set -u
PY="$HOME/cm/g6kenv/bin/python"
cd "$(dirname "$0")/.."
status=0
for spec in "$@"; do
  read -r m nr k t th <<<"$spec"
  "$PY" src/dual_hybrid_check.py "$m" "$nr" "$k" "$t" "$th" 2>/dev/null | grep -v '^wrote'
  rc=${PIPESTATUS[0]}
  echo "m=$m nr=$nr k=$k exit=$rc"
  [ "$rc" -ne 0 ] && status=1
done
exit $status
