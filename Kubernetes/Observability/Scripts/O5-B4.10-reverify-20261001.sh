#!/usr/bin/env bash
# O5-B4.10 re-verification (2026-10-01), written to close F4 in
# claude/HANFIS-review-status.md and HANFIS_RESEARCH_MEMORY.md.
#
# SCOPE -- read this before trusting the PASS/HOLD line below.
# The original O5-B4.10 gate (2026-08-07) was run as a transient terminal
# session: no O5-B4.10-*.sh script and no console log for it exist anywhere
# in this repository or its git history (checked 2026-10-01 against the sole
# commit touching Kubernetes/Observability/Scripts/, 1033c09, whose message
# states that generated evidence and transient output were excluded from the
# curated checkpoint). The two "unexpected EOF" errors the review notes
# describe cannot be verified or refuted by this script: there is nothing
# left to inspect from that session. This script does NOT reproduce that
# live-cluster run.
#
# What this script DOES do: re-verify, today, that the frozen artifacts the
# original gate produced are still present, byte-for-byte unchanged since
# 2026-08-07 (checksum), and structurally well-formed (valid YAML, a
# replication plan with the expected row shape) -- the only parts of the
# original B4.10 claim that remain checkable now. A PASS below means
# "the frozen evidence is intact and well-formed as of today," not
# "the original live preflight is now independently confirmed."
#
# Usage: Kubernetes/Observability/Scripts/O5-B4.10-reverify-20261001.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SNAP="$REPO_ROOT/Kubernetes/Observability/Results/O5-B4-preflight-20260807-095253"
PREP="$SNAP/O5-B4.10-replication-preparation"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$PREP/reverify-$STAMP"
mkdir -p "$OUT"

REPORT="$OUT/b4.10-reverify-report.txt"
SHA_RESULT="$OUT/b4.10-checksum-reverification.txt"
YAML_RESULT="$OUT/b4.10-yaml-validation.txt"

# 1. Required artefacts present
REQUIRED_FILES=(
  "$PREP/frozen-experiment-protocol.txt"
  "$PREP/frozen-kubernetes-controllers.yaml"
  "$PREP/frozen-kubernetes-services.yaml"
  "$PREP/system-fingerprint.txt"
  "$PREP/replication-plan.csv"
  "$PREP/b4.10-sha256.txt"
)
MISSING=0
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    MISSING=$((MISSING + 1))
    echo "MISSING: $f" >> "$OUT/missing-files.txt"
  fi
done
if [ "$MISSING" -eq 0 ]; then
  FILES_PASS=1
else
  FILES_PASS=0
fi

# 2. Checksum re-verification against the original manifest (fail-closed:
# explicitly count FAILED lines rather than trusting sha256sum's exit code
# alone, since a missing input file also yields a non-zero exit code that
# would otherwise be indistinguishable from a genuine mismatch in the report)
if [ "$FILES_PASS" -eq 1 ]; then
  ( cd "$PREP" && sha256sum -c "b4.10-sha256.txt" > "$SHA_RESULT" 2>&1 )
  SHA_EXIT=$?
  # grep -c prints "0" to stdout even when it matches nothing (exit 1 in that
  # case); do NOT add "|| echo 0" here, or a genuine zero count gets doubled
  # into "0\n0" and breaks the numeric test below. ${VAR:-0} alone correctly
  # covers the case where $SHA_RESULT is missing entirely (empty capture).
  SHA_FAILED_COUNT="$(grep -c "FAILED" "$SHA_RESULT" 2>/dev/null)"
  SHA_OK_COUNT="$(grep -c ": OK$" "$SHA_RESULT" 2>/dev/null)"
  if [ "$SHA_EXIT" -eq 0 ] && [ "${SHA_FAILED_COUNT:-0}" -eq 0 ] && [ "${SHA_OK_COUNT:-0}" -gt 0 ]; then
    SHA_PASS=1
  else
    SHA_PASS=0
  fi
else
  SHA_OK_COUNT=0
  SHA_FAILED_COUNT="N/A (prerequisite files missing)"
  SHA_PASS=0
fi

# 3. YAML structural validity (requires PyYAML; if unavailable, this check
# is reported as CANNOT_VERIFY rather than silently skipped or assumed PASS)
YAML_FILES=("frozen-kubernetes-controllers.yaml" "frozen-kubernetes-services.yaml")
: > "$YAML_RESULT"
if python3 -c "import yaml" 2>/dev/null; then
  YAML_PASS=1
  for f in "${YAML_FILES[@]}"; do
    if [ -f "$PREP/$f" ]; then
      if python3 -c "
import sys, yaml
try:
    docs = list(yaml.safe_load_all(open('$PREP/$f')))
    n = len([d for d in docs if d is not None])
    print(f'$f: OK ({n} document(s))')
except Exception as e:
    print(f'$f: PARSE_ERROR ({e})')
    sys.exit(1)
" >> "$YAML_RESULT" 2>&1; then
        :
      else
        YAML_PASS=0
      fi
    else
      echo "$f: FILE_MISSING" >> "$YAML_RESULT"
      YAML_PASS=0
    fi
  done
else
  YAML_PASS="CANNOT_VERIFY"
  echo "python3 + PyYAML not available in this environment -- YAML structural validity not checked" >> "$YAML_RESULT"
fi

# 4. Replication plan shape: header + exactly 5 run rows, run 2 is OFF-ON
# (matches the pattern O5-B4.11A-run2-preflight.sh itself relies on)
PLAN="$PREP/replication-plan.csv"
if [ -f "$PLAN" ]; then
  PLAN_ROWS=$(($(wc -l < "$PLAN") - 1))
  if grep -q '^2,OFF-ON,PREPARED' "$PLAN" 2>/dev/null; then
    PLAN_RUN2_OK=1
  else
    PLAN_RUN2_OK=0
  fi
else
  PLAN_ROWS=0
  PLAN_RUN2_OK=0
fi
if [ "${PLAN_ROWS:-0}" -eq 5 ] && [ "$PLAN_RUN2_OK" -eq 1 ]; then
  PLAN_PASS=1
else
  PLAN_PASS=0
fi

# 5. Overall status -- fail-closed: YAML "CANNOT_VERIFY" does NOT count as
# passing; it holds the gate open and says why, rather than defaulting to
# either PASS or FAIL on a check that did not actually run.
if [ "$FILES_PASS" -eq 1 ] && [ "$SHA_PASS" -eq 1 ] && [ "$YAML_PASS" = "1" ] && [ "$PLAN_PASS" -eq 1 ]; then
  STATUS="PASS - frozen B4.10 artefacts intact and well-formed as of $STAMP"
elif [ "$YAML_PASS" = "CANNOT_VERIFY" ] && [ "$FILES_PASS" -eq 1 ] && [ "$SHA_PASS" -eq 1 ] && [ "$PLAN_PASS" -eq 1 ]; then
  STATUS="HOLD - checksum and file-presence checks pass, but YAML structural validity could not be checked (PyYAML unavailable); do not report as PASS until this is resolved"
else
  STATUS="HOLD - one or more re-verification checks failed; see $REPORT"
fi

{
  echo "Gate            : O5-B4.10-REVERIFY"
  echo "Original gate   : O5-B4.10 (2026-08-07), frozen snapshot $SNAP"
  echo "Re-verified     : $STAMP"
  echo "Scope           : re-checks frozen artefacts only; does NOT reproduce the"
  echo "                  original live-cluster run (see script header comment)"
  echo
  echo "--- FILE PRESENCE ---"
  echo "Required files present  : $((${#REQUIRED_FILES[@]} - MISSING))/${#REQUIRED_FILES[@]}"
  echo
  echo "--- CHECKSUM RE-VERIFICATION (vs. b4.10-sha256.txt) ---"
  echo "OK                       : ${SHA_OK_COUNT:-0}"
  echo "FAILED                   : ${SHA_FAILED_COUNT:-N/A}"
  echo
  echo "--- YAML STRUCTURAL VALIDITY ---"
  echo "Result                   : $YAML_PASS"
  cat "$YAML_RESULT" | sed 's/^/  /'
  echo
  echo "--- REPLICATION PLAN SHAPE ---"
  echo "Run rows (expect 5)      : ${PLAN_ROWS:-0}"
  echo "Run 2 = OFF-ON, PREPARED : $PLAN_RUN2_OK"
  echo
  echo "STATUS O5-B4.10-REVERIFY: $STATUS"
} | tee "$REPORT"

sha256sum "$REPORT" "$SHA_RESULT" "$YAML_RESULT" > "$OUT/reverify-sha256.txt" 2>/dev/null

echo
echo "Report written to: $REPORT"
