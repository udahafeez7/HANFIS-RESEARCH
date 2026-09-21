#!/usr/bin/env bash
# Non-cluster structural tests for run_pair_v3_2.sh.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RUNNER="$SCRIPT_DIR/run_pair_v3_2.sh"
FAIL=0

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; FAIL=1; }

bash -n "$RUNNER" && pass syntax || fail syntax

required_patterns=(
  'server_collector_v3_2.sh'
  'SERVER_STATUS'
  'CLIENT_STATUS'
  'SERVER_MONITORING_ROWS'
  'TREATMENT_INTEGRITY'
  'RESOURCE_COMPLETENESS'
  'CLIENT_COMPLETENESS'
  'STATUS=HOLD_INVALID_PAIR'
  'STATUS=LOCKED_VALID_PAIR'
  'mktemp -d'
  'GIT_COMMIT'
  'pair-content.sha256'
)

for pattern in "${required_patterns[@]}"; do
  if grep -Fq "$pattern" "$RUNNER"; then
    pass "gate_${pattern//[^A-Za-z0-9]/_}"
  else
    fail "gate_${pattern//[^A-Za-z0-9]/_}"
  fi
done

if grep -Fq 'mktemp -u' "$RUNNER"; then
  fail unsafe_mktemp_u_absent
else
  pass unsafe_mktemp_u_absent
fi

if grep -Eq '^SERVER_COLLECTOR=.*server_collector_v3\.sh' "$RUNNER"; then
  fail legacy_collector_not_default
else
  pass legacy_collector_not_default
fi

if [ "$FAIL" -eq 0 ]; then
  echo "STATUS=PASS_RUN_PAIR_V3_2_STATIC_TESTS"
else
  echo "STATUS=FAIL_RUN_PAIR_V3_2_STATIC_TESTS"
  exit 1
fi
