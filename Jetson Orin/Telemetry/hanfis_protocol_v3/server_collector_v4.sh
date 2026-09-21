#!/usr/bin/env bash
# HANFIS server collector v4.2 -- external Prometheus, explicit pod/node CPU
# deltas, five-second utilization/memory gauges, fail-closed continuity/reset.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "Missing Python interpreter: $PYTHON_BIN" >&2
  echo "SERVER_STATUS=HOLD"
  exit 1
}

exec "$PYTHON_BIN" "$SCRIPT_DIR/server_collector_v4.py" "$@"
