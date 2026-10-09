#!/usr/bin/env bash
# Launch each "NAME|RUNNER ARGS..." spec as a systemd unit, then stay attached
# until all finish. Staying attached matters: WSL stops the distro (and every
# unit) a few seconds after the last wsl.exe client exits (observed 2026-10-09).
s="$(cd "$(dirname "$0")" && pwd)"
names=()
for spec in "$@"; do
  name="${spec%%|*}"; rest="${spec#*|}"
  read -r runner arg <<<"$rest"
  bash "$s/launch_detached.sh" "$name" bash "$s/$runner" "$arg"
  names+=("$name")
done
bash "$s/wait_done.sh" "${names[@]}"
