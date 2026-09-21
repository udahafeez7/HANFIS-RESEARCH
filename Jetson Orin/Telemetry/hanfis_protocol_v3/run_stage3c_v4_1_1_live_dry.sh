#!/usr/bin/env bash
# HANFIS Stage 3C v4.1.1 live dry validation. This script never runs Run 17.
set -Eeuo pipefail

PROJECT="${PROJECT:-/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3}"
PROM_URL="${PROM_URL:-http://127.0.0.1:29090}"
NODEPORT_URL="${NODEPORT_URL:-http://127.0.0.1:30080/}"
GATEWAY_CONTAINER="${GATEWAY_CONTAINER:-hanfis-nodeport-gateway-v4}"
REQUESTS="${REQUESTS:-1500}"
REQUEST_INTERVAL_SECONDS="${REQUEST_INTERVAL_SECONDS:-0.21}"
SAMPLES="${SAMPLES:-64}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-5}"
START_DELAY_SECONDS="${START_DELAY_SECONDS:-10}"
EXPECTED_EXTERNAL_TARGETS="${EXPECTED_EXTERNAL_TARGETS:-2}"
COLLECTOR="$PROJECT/server_collector_v4.sh"
RUN17_EXECUTED="NO"
WORKLOAD_PID=""
COLLECTOR_PID=""

fail() {
    local message="$1"
    echo "STATUS=HOLD_STAGE3C_V4_1_1_LIVE_DRY"
    echo "HOLD_REASON=$message"
    exit 1
}

cleanup() {
    if [[ -n "${COLLECTOR_PID:-}" ]] && kill -0 "$COLLECTOR_PID" 2>/dev/null; then
        kill "$COLLECTOR_PID" 2>/dev/null || true
        wait "$COLLECTOR_PID" 2>/dev/null || true
    fi
    if [[ -n "${WORKLOAD_PID:-}" ]] && kill -0 "$WORKLOAD_PID" 2>/dev/null; then
        kill "$WORKLOAD_PID" 2>/dev/null || true
        wait "$WORKLOAD_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "=== STAGE3C V4.1.1 LIVE DRY VALIDATION ==="
echo "RUN=0"
echo "RUN17_EXECUTED=$RUN17_EXECUTED"
echo "PROJECT=$PROJECT"

[[ -d "$PROJECT" ]] || fail "PROJECT_NOT_FOUND"
cd "$PROJECT"
[[ -f /home/hafiz/.venvs/anfis/bin/activate ]] || fail "ANFIS_ENV_NOT_FOUND"
# shellcheck disable=SC1091
source /home/hafiz/.venvs/anfis/bin/activate
echo "ENVIRONMENT=$(basename "${VIRTUAL_ENV:-NOT_ACTIVE}")"
[[ "${VIRTUAL_ENV:-}" == /home/hafiz/.venvs/anfis ]] || fail "ANFIS_ENV_NOT_ACTIVE"

for command_name in curl docker kubectl python3 sha256sum awk date; do
    command -v "$command_name" >/dev/null 2>&1 || fail "MISSING_COMMAND_$command_name"
done
[[ -x "$COLLECTOR" ]] || fail "COLLECTOR_NOT_EXECUTABLE"

echo
echo "=== PREFLIGHT ==="
GATEWAY_RUNNING="$(docker inspect -f '{{.State.Running}}' "$GATEWAY_CONTAINER" 2>/dev/null || true)"
echo "GATEWAY_RUNNING=${GATEWAY_RUNNING:-false}"
[[ "$GATEWAY_RUNNING" == true ]] || fail "NODEPORT_GATEWAY_NOT_RUNNING"

NODEPORT_HTTP="$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$NODEPORT_URL" || true)"
echo "LOCAL_NODEPORT_HTTP=${NODEPORT_HTTP:-000}"
[[ "$NODEPORT_HTTP" == 200 ]] || fail "LOCAL_NODEPORT_HTTP_NOT_200"

PROM_READY="$(curl -fsS --max-time 5 "$PROM_URL/-/ready" 2>/dev/null || true)"
echo "EXTERNAL_PROMETHEUS_READY=${PROM_READY:-NO}"
[[ "${PROM_READY,,}" == *ready* ]] || fail "EXTERNAL_PROMETHEUS_NOT_READY"

EXTERNAL_TARGETS="$(
    curl -fsS --get --max-time 10 "$PROM_URL/api/v1/query" \
        --data-urlencode 'query=count(up{job=~"external-cadvisor-.*"} == 1)' |
    python3 -c 'import json,sys; r=json.load(sys.stdin).get("data",{}).get("result",[]); print(r[0]["value"][1] if r else "0")'
)"
echo "EXTERNAL_ACTIVE_TARGETS=$EXTERNAL_TARGETS/$EXPECTED_EXTERNAL_TARGETS"
[[ "$EXTERNAL_TARGETS" == "$EXPECTED_EXTERNAL_TARGETS" ]] || fail "EXTERNAL_TARGET_COUNT_MISMATCH"

INTERNAL_PROM_READY="$(
    kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus --no-headers 2>/dev/null |
    awk '$2=="2/2" && $3=="Running"{n++} END{print n+0}'
)"
echo "INTERNAL_PROMETHEUS_READY_PODS=$INTERNAL_PROM_READY"
[[ "$INTERNAL_PROM_READY" -ge 1 ]] || fail "INTERNAL_PROMETHEUS_NOT_READY"

echo
echo "=== SYNCHRONIZED 315-SECOND COLLECTION ==="
OUT="$PROJECT/collector_v4_1_1_live_dry_$(date +%Y%m%dT%H%M%S%z)"
WORKLOAD_LOG="${OUT}_workload.csv"
START_EPOCH=$(( $(date -u +%s) + START_DELAY_SECONDS ))
echo "START_EPOCH_UTC=$START_EPOCH"
echo "REQUESTS=$REQUESTS"
echo "REQUEST_INTERVAL_SECONDS=$REQUEST_INTERVAL_SECONDS"
echo "COLLECTOR_SAMPLES=$SAMPLES"
echo "COLLECTOR_INTERVAL_SECONDS=$INTERVAL_SECONDS"

python3 - "$START_EPOCH" "$WORKLOAD_LOG" "$REQUESTS" "$REQUEST_INTERVAL_SECONDS" "$NODEPORT_URL" <<'PY' &
import csv
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

start = float(sys.argv[1])
output = sys.argv[2]
request_count = int(sys.argv[3])
interval = float(sys.argv[4])
url = sys.argv[5]

with open(output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(("seq", "timestamp_utc", "http_code", "elapsed_ms", "error"))
    for seq in range(1, request_count + 1):
        target = start + (seq - 1) * interval
        time.sleep(max(0.0, target - time.time()))
        before = time.perf_counter()
        code = 0
        error = ""
        try:
            request = urllib.request.Request(url, headers={"Connection": "close"})
            with urllib.request.urlopen(request, timeout=5) as response:
                response.read()
                code = response.status
        except urllib.error.HTTPError as exc:
            code = exc.code
            error = type(exc).__name__
        except Exception as exc:  # recorded fail-closed by the shell gate
            error = f"{type(exc).__name__}:{exc}"
        elapsed_ms = (time.perf_counter() - before) * 1000.0
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        writer.writerow((seq, timestamp, code, f"{elapsed_ms:.3f}", error))
        handle.flush()
PY
WORKLOAD_PID=$!

PROM_URL="$PROM_URL" \
SAMPLES="$SAMPLES" \
INTERVAL_SECONDS="$INTERVAL_SECONDS" \
EXPECTED_EXTERNAL_TARGETS="$EXPECTED_EXTERNAL_TARGETS" \
"$COLLECTOR" 0 on "$START_EPOCH" "$OUT" &
COLLECTOR_PID=$!

VALIDATION_STARTED="$(date +%s)"
while kill -0 "$COLLECTOR_PID" 2>/dev/null; do
    sleep 30
    if kill -0 "$COLLECTOR_PID" 2>/dev/null; then
        ELAPSED_NOW=$(( $(date +%s) - VALIDATION_STARTED ))
        echo "VALIDATION_IN_PROGRESS=${ELAPSED_NOW}s"
    fi
done

set +e
wait "$COLLECTOR_PID"
COLLECTOR_RC=$?
set -e
COLLECTOR_PID=""

if [[ "$COLLECTOR_RC" -ne 0 ]]; then
    echo "COLLECTOR_RC=$COLLECTOR_RC"
    [[ ! -f "$OUT/errors.log" ]] || sed -n '1,80p' "$OUT/errors.log"
    fail "COLLECTOR_GATE_FAILED"
fi

set +e
wait "$WORKLOAD_PID"
WORKLOAD_RC=$?
set -e
WORKLOAD_PID=""

echo
echo "=== WORKLOAD AND OUTPUT VALIDATION ==="
WORKLOAD_ROWS="$(awk -F, 'NR>1{n++} END{print n+0}' "$WORKLOAD_LOG")"
WORKLOAD_HTTP_200="$(awk -F, 'NR>1 && $3==200{n++} END{print n+0}' "$WORKLOAD_LOG")"
WORKLOAD_FAILURES=$(( WORKLOAD_ROWS - WORKLOAD_HTTP_200 ))
echo "COLLECTOR_RC=$COLLECTOR_RC"
echo "WORKLOAD_RC=$WORKLOAD_RC"
echo "WORKLOAD_REQUESTS=$WORKLOAD_ROWS"
echo "WORKLOAD_HTTP_200=$WORKLOAD_HTTP_200"
echo "WORKLOAD_FAILURES=$WORKLOAD_FAILURES"

[[ "$WORKLOAD_RC" -eq 0 ]] || fail "WORKLOAD_PROCESS_FAILED"
[[ "$WORKLOAD_ROWS" -eq "$REQUESTS" ]] || fail "WORKLOAD_ROW_COUNT_MISMATCH"
[[ "$WORKLOAD_HTTP_200" -eq "$REQUESTS" ]] || fail "WORKLOAD_HTTP_FAILURE"

(cd "$OUT" && sha256sum -c sha256.txt)

metadata_value() {
    awk -F= -v key="$1" '$1==key{value=$2} END{print value}' "$OUT/metadata.txt"
}

[[ "$(metadata_value STATUS)" == PASS ]] || fail "METADATA_STATUS_NOT_PASS"
[[ "$(metadata_value BOUNDARY_SETTLEMENT)" == PASS ]] || fail "BOUNDARY_SETTLEMENT_FAILED"
[[ "$(metadata_value SNAPSHOT_EXACT_CROSSCHECK)" == PASS ]] || fail "SNAPSHOT_EXACT_CROSSCHECK_FAILED"
[[ "$(metadata_value RATE_INCREASE_COHERENCE)" == PASS ]] || fail "RATE_INCREASE_COHERENCE_FAILED"
[[ "$(metadata_value WINDOW_ESTIMATOR_DIFFERENCE)" == RECORDED_NOT_GATED ]] || fail "WINDOW_ESTIMATOR_STATUS_INVALID"
[[ "$(metadata_value PROMQL_CROSSCHECK)" == PASS_STRICT ]] || fail "PROMQL_CROSSCHECK_NOT_STRICT"
[[ "$(metadata_value RUN17_EXECUTED)" == NO ]] || fail "RUN17_SAFETY_GATE_FAILED"

SUMMARY="$OUT/dry_validation_summary.txt"
{
    echo "PROTOCOL=HANFIS_STAGE3C_V4_1_1_LIVE_DRY"
    echo "RUN=0"
    echo "RUN17_EXECUTED=NO"
    echo "REQUESTS=$WORKLOAD_ROWS"
    echo "HTTP_200=$WORKLOAD_HTTP_200"
    echo "FAILURES=$WORKLOAD_FAILURES"
    grep -E '^(BOUNDARY_SETTLEMENT|PROM_QUERY_SETTLE_SECONDS|SNAPSHOT_EXACT_CROSSCHECK|SNAPSHOT_MAX_ABS_DIFFERENCE_CPU_SECONDS|RATE_INCREASE_COHERENCE|RATE_INCREASE_MAX_ABS_DIFFERENCE_CPU_SECONDS|WINDOW_ESTIMATOR_DIFFERENCE|PROMQL_CROSSCHECK|STATUS)=' "$OUT/metadata.txt"
    echo "CPU_SUMMARY_BEGIN"
    cat "$OUT/cpu_summary.csv"
    echo "CPU_SUMMARY_END"
    echo "MEMORY_SUMMARY_BEGIN"
    cat "$OUT/memory_summary.csv"
    echo "MEMORY_SUMMARY_END"
    echo "STATUS=PASS_STAGE3C_V4_1_1_LIVE_DRY_VALIDATION"
} | tee "$SUMMARY"
sha256sum "$SUMMARY" > "$OUT/dry_validation_summary.sha256"

echo
echo "DRY_OUTPUT=$OUT"
echo "WORKLOAD_LOG=$WORKLOAD_LOG"
echo "RUN17_EXECUTED=NO"
echo "STATUS=PASS_STAGE3C_V4_1_1_LIVE_DRY_VALIDATION"
