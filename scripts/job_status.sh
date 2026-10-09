#!/usr/bin/env bash
# Show detached job units, log tails and done markers.
cd "$(dirname "$0")/../results/logs" || exit 1
systemctl list-units 'cm-*' --all --no-legend
for f in *; do
  [ -f "$f" ] || continue
  echo "== $f"
  tail -3 "$f"
done
for u in "$@"; do journalctl -u "cm-$u" --no-pager -n 8; done
