#!/usr/bin/env bash
# Block until every named job has a .done marker, then print the markers.
cd "$(dirname "$0")/.."
for name in "$@"; do
  until [ -f "results/logs/$name.done" ]; do sleep 20; done
  echo "$name $(cat "results/logs/$name.done")"
done
