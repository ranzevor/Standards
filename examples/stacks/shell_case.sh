#!/usr/bin/env bash
set -euo pipefail
if (( $# != 1 )); then printf '%s\n' 'one argument required' >&2; exit 64; fi
printf '%s\n' "$1"
