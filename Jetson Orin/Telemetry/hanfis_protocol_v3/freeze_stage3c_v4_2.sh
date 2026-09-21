#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="${PROJECT:-/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3}"
LIVE_DRY_DIR="${LIVE_DRY_DIR:-$PROJECT/collector_v4_2_live_dry_20260911T115431+0700}"
WORKLOAD_LOG="${WORKLOAD_LOG:-${LIVE_DRY_DIR}_workload.csv}"
COLLECTOR_LOG="${COLLECTOR_LOG:-${LIVE_DRY_DIR}_collector.log}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PREREG_SOURCE="$SCRIPT_DIR/PREREGISTRATION_STAGE3C_V4_2.md"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
FREEZE_DIR="$PROJECT/stage3c_v4_2_freeze_$TIMESTAMP"
ARCHIVE="$PROJECT/STAGE3C_V4_2_FREEZE_$TIMESTAMP.tar.gz"

fail() {
    printf 'STATUS=HOLD_STAGE3C_V4_2_FREEZE\nHOLD_REASON=%s\nRUN17_EXECUTED=NO\n' "$1" >&2
    exit 1
}

meta() {
    local key="$1"
    sed -n "s/^${key}=//p" "$LIVE_DRY_DIR/metadata.txt" | tail -n 1
}

require_equal() {
    local label="$1" observed="$2" expected="$3"
    [[ "$observed" == "$expected" ]] || fail "${label}_EXPECTED_${expected}_OBSERVED_${observed:-MISSING}"
    printf 'PASS %s=%s\n' "$label" "$observed"
}

printf '=== STAGE3C V4.2 PREREGISTRATION FREEZE ===\n'
printf 'PROJECT=%s\nLIVE_DRY_DIR=%s\n' "$PROJECT" "$LIVE_DRY_DIR"

[[ -d "$PROJECT" ]] || fail PROJECT_NOT_FOUND
cd "$PROJECT"

if [[ "${VIRTUAL_ENV:-}" != */anfis ]]; then
    [[ -f /home/hafiz/.venvs/anfis/bin/activate ]] || fail ANFIS_ENVIRONMENT_NOT_FOUND
    # shellcheck disable=SC1091
    source /home/hafiz/.venvs/anfis/bin/activate
fi
ENVIRONMENT_NAME="$(basename -- "${VIRTUAL_ENV:-missing}")"
require_equal ENVIRONMENT_NAME "$ENVIRONMENT_NAME" anfis

[[ -d "$LIVE_DRY_DIR" ]] || fail LIVE_DRY_DIRECTORY_NOT_FOUND
[[ -f "$WORKLOAD_LOG" ]] || fail WORKLOAD_LOG_NOT_FOUND
[[ -f "$COLLECTOR_LOG" ]] || fail COLLECTOR_LOG_NOT_FOUND
[[ -f "$PREREG_SOURCE" ]] || fail PREREGISTRATION_DOCUMENT_NOT_FOUND

required_output=(
    metadata.txt errors.log cpu_counter_delta.csv cpu_summary.csv
    node_cpu_counter_delta.csv utilization_samples.csv utilization_summary.csv
    memory_samples.csv memory_aggregate_samples.csv memory_summary.csv
    target_samples.csv sha256.txt
)
for file in "${required_output[@]}"; do
    [[ -f "$LIVE_DRY_DIR/$file" ]] || fail "LIVE_DRY_FILE_MISSING_${file}"
done

printf '\n=== LIVE-DRY INTEGRITY ===\n'
(cd "$LIVE_DRY_DIR" && sha256sum -c sha256.txt) || fail LIVE_DRY_SHA256_FAILED
[[ ! -s "$LIVE_DRY_DIR/errors.log" ]] || fail COLLECTOR_ERRORS_LOG_NOT_EMPTY

require_equal METADATA_STATUS "$(meta STATUS)" PASS
require_equal RUN17_EXECUTED "$(meta RUN17_EXECUTED)" NO
require_equal METADATA_ENVIRONMENT "$(meta ENVIRONMENT_NAME)" anfis
require_equal REQUESTED_SAMPLES "$(meta REQUESTED_SAMPLES)" 64
require_equal TARGET_CONTINUITY "$(meta TARGET_CONTINUITY)" PASS
require_equal SERIES_CONTINUITY "$(meta SERIES_CONTINUITY)" PASS
require_equal COUNTER_RESET_CHECK "$(meta COUNTER_RESET_CHECK)" PASS
require_equal BOUNDARY_SETTLEMENT "$(meta BOUNDARY_SETTLEMENT)" PASS
require_equal SNAPSHOT_EXACT_CROSSCHECK "$(meta SNAPSHOT_EXACT_CROSSCHECK)" PASS
require_equal RATE_INCREASE_COHERENCE "$(meta RATE_INCREASE_COHERENCE)" PASS
require_equal PROMQL_CROSSCHECK "$(meta PROMQL_CROSSCHECK)" PASS_STRICT
require_equal NODE_UTILIZATION_STATUS "$(meta NODE_UTILIZATION_STATUS)" PASS

UTILIZATION_ROWS="$(( $(wc -l < "$LIVE_DRY_DIR/utilization_samples.csv") - 1 ))"
TARGET_ROWS="$(( $(wc -l < "$LIVE_DRY_DIR/target_samples.csv") - 1 ))"
WORKLOAD_ROWS="$(( $(wc -l < "$WORKLOAD_LOG") - 1 ))"
WORKLOAD_HTTP_200="$(awk -F, 'NR > 1 && $2 == 200 {n++} END {print n+0}' "$WORKLOAD_LOG")"
require_equal UTILIZATION_ROWS "$UTILIZATION_ROWS" 64
require_equal TARGET_ROWS "$TARGET_ROWS" 64
require_equal WORKLOAD_ROWS "$WORKLOAD_ROWS" 1500
require_equal WORKLOAD_HTTP_200 "$WORKLOAD_HTTP_200" 1500

printf '\n=== INSTALLED CODE GATES ===\n'
required_code=(
    run_pair_v4.sh jetson_capture_v4.sh server_collector_v4.sh
    server_collector_v4.py test_server_collector_v4_mock.py
    test_run_pair_v4_static.sh run_stage3c_v4_2_live_dry.sh
)
for file in "${required_code[@]}"; do
    [[ -f "$PROJECT/$file" ]] || fail "CODE_FILE_MISSING_${file}"
done
bash -n run_pair_v4.sh jetson_capture_v4.sh server_collector_v4.sh \
    test_run_pair_v4_static.sh run_stage3c_v4_2_live_dry.sh || fail SHELL_SYNTAX_FAILED
python3 -m py_compile server_collector_v4.py test_server_collector_v4_mock.py || fail PYTHON_SYNTAX_FAILED
if grep -R -n -E -- '-v[[:space:]]+index=' run_stage3c_v4_2_live_dry.sh server_collector_v4.py; then
    fail GNU_AWK_RESERVED_INDEX_REGRESSION
fi
grep -q 'CONFIRM_RUN17' run_pair_v4.sh || fail RUN17_CONFIRMATION_GATE_MISSING
printf 'PASS CODE_AND_RUN17_GATES\n'

[[ ! -e "$FREEZE_DIR" && ! -e "$ARCHIVE" && ! -e "$ARCHIVE.sha256" ]] || fail FREEZE_TARGET_ALREADY_EXISTS
mkdir -p "$FREEZE_DIR/code" "$FREEZE_DIR/live_dry" "$FREEZE_DIR/evidence"
cp -p -- "${required_code[@]}" "$FREEZE_DIR/code/"
cp -p -- "$PREREG_SOURCE" "$FREEZE_DIR/"
cp -p -- "$LIVE_DRY_DIR"/* "$FREEZE_DIR/live_dry/"
cp -p -- "$WORKLOAD_LOG" "$COLLECTOR_LOG" "$FREEZE_DIR/evidence/"

cat > "$FREEZE_DIR/FREEZE_MANIFEST.txt" <<EOF
PROTOCOL=HANFIS_STAGE3C_V4_2_UTILIZATION_GATED
FREEZE_TIMESTAMP=$TIMESTAMP
PROJECT=$PROJECT
LIVE_DRY_SOURCE=$LIVE_DRY_DIR
WORKLOAD_LOG=$WORKLOAD_LOG
ENVIRONMENT_NAME=$ENVIRONMENT_NAME
WORKLOAD_ROWS=$WORKLOAD_ROWS
WORKLOAD_HTTP_200=$WORKLOAD_HTTP_200
UTILIZATION_SAMPLES=$UTILIZATION_ROWS
TARGET_SAMPLES=$TARGET_ROWS
CPU_UTILIZATION_PERCENT_MEAN=$(meta CPU_UTILIZATION_PERCENT_MEAN)
CPU_UTILIZATION_PERCENT_P95=$(meta CPU_UTILIZATION_PERCENT_P95)
CPU_UTILIZATION_PERCENT_MAX=$(meta CPU_UTILIZATION_PERCENT_MAX)
UTILIZATION_REGIME=$(meta UTILIZATION_REGIME)
PREREGISTRATION_STATUS=FROZEN
RUN17_EXECUTED=NO
STATUS=PASS_STAGE3C_V4_2_PREREGISTRATION_FREEZE
EOF

(
    cd "$FREEZE_DIR"
    find . -type f ! -name FREEZE_SHA256.txt -print0 | sort -z | xargs -0 sha256sum > FREEZE_SHA256.txt
    sha256sum -c FREEZE_SHA256.txt
) || fail FREEZE_SHA256_FAILED

tar -C "$FREEZE_DIR" -czf "$ARCHIVE" .
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
tar -tzf "$ARCHIVE" >/dev/null || fail ARCHIVE_VALIDATION_FAILED

printf '\nFREEZE_DIR=%s\nARCHIVE=%s\nARCHIVE_SHA256=%s\n' "$FREEZE_DIR" "$ARCHIVE" "$ARCHIVE.sha256"
printf 'PREREGISTRATION_STATUS=FROZEN\nRUN17_EXECUTED=NO\n'
printf 'STATUS=PASS_STAGE3C_V4_2_PREREGISTRATION_FREEZE\n'
