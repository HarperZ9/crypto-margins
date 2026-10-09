#!/usr/bin/env bash
# Launch a runner as a systemd transient unit so neither a Claude Code restart
# nor wsl.exe exiting kills it. setsid+nohup was not enough: WSL reaped the
# children before they opened their logs (observed 2026-10-09).
# Usage: launch_detached.sh NAME RUNNER [ARGS...]
#   -> results/logs/NAME.log and results/logs/NAME.done ("exit=N")
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$root/results/logs"
name="$1"; shift
log="$root/results/logs/$name.log"; done_f="$root/results/logs/$name.done"
rm -f "$done_f"
systemd-run --quiet --unit="cm-$name" --collect --working-directory="$root" \
  --setenv=HOME="$HOME" \
  bash -c 'log=$0; done_f=$1; shift; "$@" > "$log" 2>&1; echo "exit=$?" > "$done_f"' \
  "$log" "$done_f" "$@"
echo "launched cm-$name"
