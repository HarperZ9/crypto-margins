#!/usr/bin/env bash
# Each arg: "M NR K ROUNDS THREADS SEED".
set -u
PY="$HOME/cm/g6kenv/bin/python"
cd "$(dirname "$0")/.."
status=0
for spec in "$@"; do
  read -r m nr k r th sd <<<"$spec"
  "$PY" src/rerandomize_check.py "$m" "$nr" "$k" "$r" "$th" "$sd" 2>/dev/null
  rc=$?
  echo "m=$m nr=$nr seed=$sd exit=$rc"
  [ "$rc" -ne 0 ] && status=1
done
exit $status
