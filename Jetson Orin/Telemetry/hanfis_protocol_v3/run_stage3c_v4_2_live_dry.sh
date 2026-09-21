#!/usr/bin/env bash
# Live-dry validation for HANFIS Stage 3C v4.2.2. Never executes Run 17.
set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RUN=0
CONDITION="${CONDITION:-on}"
PROM_URL="${PROM_URL:-http://127.0.0.1:29090}"
LOCAL_NODEPORT_URL="${LOCAL_NODEPORT_URL:-http://127.0.0.1:30080/}"
REQUESTS="${REQUESTS:-1500}"
REQUEST_INTERVAL_SECONDS="${REQUEST_INTERVAL_SECONDS:-0.21}"
COLLECTOR_SAMPLES="${COLLECTOR_SAMPLES:-64}"
COLLECTOR_INTERVAL_SECONDS="${COLLECTOR_INTERVAL_SECONDS:-5}"
SERVER_INSTANCE_REGEX="${SERVER_INSTANCE_REGEX:-desktop-worker.*}"
NODE_RATE_WINDOW_SECONDS="${NODE_RATE_WINDOW_SECONDS:-30}"
EXPECTED_ENVIRONMENT_NAME="${EXPECTED_ENVIRONMENT_NAME:-anfis}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$SCRIPT_DIR}"
STAMP=$(date +%Y%m%dT%H%M%S%z)
OUT="$OUTPUT_ROOT/collector_v4_2_2_live_dry_$STAMP"
WORKLOAD_LOG="$OUTPUT_ROOT/collector_v4_2_2_live_dry_${STAMP}_workload.csv"
COLLECTOR_LOG="$OUTPUT_ROOT/collector_v4_2_2_live_dry_${STAMP}_collector.log"

actual_environment=$(basename "${VIRTUAL_ENV:-unknown}")
[ "$actual_environment" = "$EXPECTED_ENVIRONMENT_NAME" ] || {
  printf 'ENVIRONMENT_NAME=%s\nSTATUS=HOLD_WRONG_PYTHON_ENVIRONMENT\n' "$actual_environment"
  exit 1
}
[[ "$CONDITION" = on || "$CONDITION" = off ]] || { echo "STATUS=HOLD_INVALID_CONDITION"; exit 1; }
[ "$RUN" -ne 17 ] || { echo "STATUS=HOLD_RUN17_NOT_AUTHORIZED"; exit 1; }

ready=$(curl -fsS --max-time 5 "$PROM_URL/-/ready")
targets=$(curl -fsS --get --max-time 10 "$PROM_URL/api/v1/query" --data-urlencode 'query=count(up{job=~"external-cadvisor-.*"} == 1)' | python3 -c 'import json,sys; r=json.load(sys.stdin).get("data",{}).get("result",[]); print(r[0]["value"][1] if r else "0")')
local_code=$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$LOCAL_NODEPORT_URL" || true)
printf 'RUN=%s\nRUN17_EXECUTED=NO\nENVIRONMENT_NAME=%s\nLOCAL_NODEPORT_HTTP=%s\nEXTERNAL_PROMETHEUS_READY=%s\nEXTERNAL_ACTIVE_TARGETS=%s/2\n' "$RUN" "$actual_environment" "$local_code" "$ready" "$targets"
[ "$local_code" = 200 ] && [ "$targets" = 2 ] || { echo "STATUS=HOLD_LIVE_DRY_PREFLIGHT"; exit 1; }

mkdir -p "$OUT"
start_epoch=$(( $(date -u +%s) + 10 ))
PROM_URL="$PROM_URL" SAMPLES="$COLLECTOR_SAMPLES" INTERVAL_SECONDS="$COLLECTOR_INTERVAL_SECONDS" SERVER_INSTANCE_REGEX="$SERVER_INSTANCE_REGEX" NODE_RATE_WINDOW_SECONDS="$NODE_RATE_WINDOW_SECONDS" PROM_QUERY_SETTLE_SECONDS=5 "$SCRIPT_DIR/server_collector_v4.sh" "$RUN" "$CONDITION" "$start_epoch" "$OUT" >"$COLLECTOR_LOG" 2>&1 &
collector_pid=$!

delay=$(( start_epoch - $(date -u +%s) ))
[ "$delay" -gt 0 ] && sleep "$delay"
printf 'seq,http_code\n' > "$WORKLOAD_LOG"
for seq in $(seq 1 "$REQUESTS"); do
  scheduled_epoch=$(awk -v start="$start_epoch" -v idx="$((seq-1))" -v interval="$REQUEST_INTERVAL_SECONDS" 'BEGIN {printf "%.6f", start + idx*interval}')
  request_delay=$(awk -v target="$scheduled_epoch" -v now="$EPOCHREALTIME" 'BEGIN {d=target-now; if(d<0)d=0; printf "%.6f",d}')
  awk -v d="$request_delay" 'BEGIN {exit !(d>0)}' && sleep "$request_delay"
  code=$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$LOCAL_NODEPORT_URL" || true)
  [ -n "$code" ] || code=000
  printf '%s,%s\n' "$seq" "$code" >> "$WORKLOAD_LOG"
  if [ $((seq % 150)) -eq 0 ]; then printf 'WORKLOAD_PROGRESS=%s/%s\n' "$seq" "$REQUESTS"; fi
done

set +e
wait "$collector_pid"
collector_rc=$?
set -e
cat "$COLLECTOR_LOG"

http_rows=$(( $(wc -l < "$WORKLOAD_LOG") - 1 ))
http_ok=$(awk -F, 'NR>1 && $2==200{n++} END{print n+0}' "$WORKLOAD_LOG")
server_status=$(awk -F= '$1=="SERVER_STATUS"{v=$2} END{print v}' "$COLLECTOR_LOG")
utilization_samples=$(awk -F= '$1=="SERVER_UTILIZATION_SAMPLES"{v=$2} END{print v}' "$COLLECTOR_LOG")

(cd "$OUT" && sha256sum -c sha256.txt)
for required in node_cpu_counter_delta.csv utilization_samples.csv utilization_summary.csv metadata.txt; do
  [ -s "$OUT/$required" ] || { echo "MISSING_OUTPUT=$required"; exit 1; }
done

printf 'COLLECTOR_RC=%s\nSERVER_STATUS=%s\nWORKLOAD_ROWS=%s\nWORKLOAD_HTTP_200=%s\nUTILIZATION_SAMPLES=%s\nDRY_OUTPUT=%s\nWORKLOAD_LOG=%s\n' "$collector_rc" "$server_status" "$http_rows" "$http_ok" "$utilization_samples" "$OUT" "$WORKLOAD_LOG"
[ "$collector_rc" -eq 0 ] && [ "$server_status" = PASS ] && [ "$http_rows" -eq "$REQUESTS" ] && [ "$http_ok" -eq "$REQUESTS" ] && [ "$utilization_samples" -eq "$COLLECTOR_SAMPLES" ] || {
  echo "STATUS=HOLD_STAGE3C_V4_2_2_LIVE_DRY_VALIDATION"
  exit 1
}
echo "RUN17_EXECUTED=NO"
echo "STATUS=PASS_STAGE3C_V4_2_2_LIVE_DRY_VALIDATION"
