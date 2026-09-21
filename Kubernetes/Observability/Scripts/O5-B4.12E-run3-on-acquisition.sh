#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# O5-B4.12E
# Run 3 — Monitoring ON Data Acquisition
#
# Frozen reconstructed protocol:
# - 300 standalone HTTP samples
# - 30 resource snapshots
# - nominal sleep 2 seconds
# - 300 HTTP samples during resource collection
# ============================================================

OBS="/mnt/c/Research/ANFIS/Kubernetes/Observability"
RESULT_ROOT="$OBS/Results"

RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$RESULT_ROOT/O5-B4.12E-run3-on-$RUN_ID"

HTTP_MAIN="$OUT/http-samples.csv"
HTTP_RESOURCE="$OUT/http-under-resource-test.csv"
RESOURCE_DATA="$OUT/resource-snapshots.txt"
SYSTEM_STATE="$OUT/system-state.txt"
SUMMARY="$OUT/collection-summary.txt"
CHECKSUM="$OUT/run3-on-sha256.txt"

NAMESPACE="hanfis-research"
MON_NAMESPACE="monitoring"
LOADGEN_POD="p0-loadgen"
SERVICE_URL="http://p0-baseline-service/"

HTTP_SAMPLES=300
RESOURCE_SNAPSHOTS=30
RESOURCE_SLEEP=2
STABILIZATION_SECONDS=60

mkdir -p "$OUT"

echo "=== O5-B4.12E: RUN 3 MONITORING ON ACQUISITION ==="
echo "Output: $OUT"

# ------------------------------------------------------------
# 1. Safety gate
# ------------------------------------------------------------

READY_NODES=$(
  kubectl get nodes --no-headers |
    awk '$2 == "Ready" {count++} END {print count+0}'
)

P0_READY=$(
  kubectl get deployment p0-baseline \
    -n "$NAMESPACE" \
    -o jsonpath='{.status.readyReplicas}' 2>/dev/null
)

MON_PODS=$(
  kubectl get pods -n "$MON_NAMESPACE" \
    --no-headers 2>/dev/null |
    wc -l |
    tr -d ' '
)

HTTP_GATE=$(
  kubectl exec -n "$NAMESPACE" "$LOADGEN_POD" -- \
    curl -sS --max-time 5 \
    -o /dev/null \
    -w '%{http_code}' \
    "$SERVICE_URL" 2>/dev/null
)

METRICS_OK=0
if kubectl top nodes >/dev/null 2>&1; then
  METRICS_OK=1
fi

{
  echo "Timestamp UTC     : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Ready nodes       : $READY_NODES/2"
  echo "P0 ready replicas : ${P0_READY:-0}/2"
  echo "Monitoring pods   : $MON_PODS/5"
  echo "HTTP gate         : ${HTTP_GATE:-000}"
  echo "Metrics API       : $METRICS_OK/1"
  echo
  kubectl get nodes -o wide
  echo
  kubectl get deployment,pods -n "$NAMESPACE" -o wide
  echo
  kubectl get deployment,statefulset,daemonset \
    -n "$MON_NAMESPACE" 2>/dev/null || true
} | tee "$SYSTEM_STATE"

if [ "$READY_NODES" -ne 2 ] ||
   [ "${P0_READY:-0}" != "2" ] ||
   [ "$MON_PODS" -ne 5 ] ||
   [ "${HTTP_GATE:-000}" != "200" ] ||
   [ "$METRICS_OK" -ne 1 ]; then

  echo "STATUS O5-B4.12E: HOLD — SAFETY GATE FAILED" |
    tee "$SUMMARY"

  exit 1
fi

# ------------------------------------------------------------
# 2. Controlled stabilization
# ------------------------------------------------------------

echo
echo "Safety gate PASS."
echo "Stabilisasi selama $STABILIZATION_SECONDS detik..."

sleep "$STABILIZATION_SECONDS"

# ------------------------------------------------------------
# 3. HTTP collection function
# ------------------------------------------------------------

collect_http()
{
  local OUTPUT_FILE="$1"
  local SAMPLE_COUNT="$2"

  printf '%s\n' \
    "seq,timestamp_utc,http_code,time_total_seconds,size_download_bytes" \
    > "$OUTPUT_FILE"

  for SEQ in $(seq 1 "$SAMPLE_COUNT"); do
    TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

    if RESULT=$(
      kubectl exec -n "$NAMESPACE" "$LOADGEN_POD" -- \
        curl -sS --max-time 5 \
        -o /dev/null \
        -w '%{http_code},%{time_total},%{size_download}' \
        "$SERVICE_URL" 2>/dev/null
    ); then
      :
    else
      RESULT="000,5.000000,0"
    fi

    printf '%s,%s,%s\n' \
      "$SEQ" "$TIMESTAMP" "$RESULT" \
      >> "$OUTPUT_FILE"
  done
}

# ------------------------------------------------------------
# 4. Standalone HTTP test
# ------------------------------------------------------------

echo
echo "Mengambil $HTTP_SAMPLES sampel HTTP utama..."

collect_http "$HTTP_MAIN" "$HTTP_SAMPLES"

echo "HTTP utama selesai."

# ------------------------------------------------------------
# 5. HTTP under resource collection
# ------------------------------------------------------------

echo
echo "Menjalankan HTTP dan resource sampling secara bersamaan..."

collect_http "$HTTP_RESOURCE" "$HTTP_SAMPLES" &
HTTP_PID=$!

: > "$RESOURCE_DATA"

for SAMPLE in $(seq 1 "$RESOURCE_SNAPSHOTS"); do
  {
    echo "=== SAMPLE $SAMPLE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

    echo "-- NODES --"
    if ! kubectl top nodes --no-headers; then
      echo "ERROR: kubectl top nodes failed"
    fi

    echo "-- P0 --"
    if ! kubectl top pods \
      -n "$NAMESPACE" \
      --no-headers; then
      echo "ERROR: kubectl top P0 failed"
    fi

    echo "-- MONITORING --"
    kubectl top pods \
      -n "$MON_NAMESPACE" \
      --no-headers 2>/dev/null || true

    echo
  } >> "$RESOURCE_DATA"

  if [ "$SAMPLE" -lt "$RESOURCE_SNAPSHOTS" ]; then
    sleep "$RESOURCE_SLEEP"
  fi
done

wait "$HTTP_PID"

echo "Resource sampling selesai."

# ------------------------------------------------------------
# 6. Validation and descriptive summary
# ------------------------------------------------------------

HTTP_MAIN_ROWS=$(awk 'NR > 1 {count++} END {print count+0}' "$HTTP_MAIN")
HTTP_MAIN_OK=$(awk -F',' 'NR > 1 && $3 == 200 {count++}
  END {print count+0}' "$HTTP_MAIN")

HTTP_RESOURCE_ROWS=$(awk 'NR > 1 {count++} END {print count+0}' "$HTTP_RESOURCE")
HTTP_RESOURCE_OK=$(awk -F',' 'NR > 1 && $3 == 200 {count++}
  END {print count+0}' "$HTTP_RESOURCE")

SNAPSHOT_COUNT=$(grep -c '^=== SAMPLE ' "$RESOURCE_DATA" || true)
RESOURCE_ERRORS=$(grep -c '^ERROR:' "$RESOURCE_DATA" || true)

HTTP_MAIN_MEAN=$(awk -F',' '
  NR > 1 {sum += $4; count++}
  END {
    if (count > 0) printf "%.9f", sum/count;
    else print "NA"
  }' "$HTTP_MAIN")

HTTP_RESOURCE_MEAN=$(awk -F',' '
  NR > 1 {sum += $4; count++}
  END {
    if (count > 0) printf "%.9f", sum/count;
    else print "NA"
  }' "$HTTP_RESOURCE")

P0_FINAL=$(
  kubectl get deployment p0-baseline \
    -n "$NAMESPACE" \
    -o jsonpath='{.status.readyReplicas}' 2>/dev/null
)

HTTP_FINAL=$(
  kubectl exec -n "$NAMESPACE" "$LOADGEN_POD" -- \
    curl -sS --max-time 5 \
    -o /dev/null \
    -w '%{http_code}' \
    "$SERVICE_URL" 2>/dev/null
)

MON_FINAL=$(
  kubectl get pods -n "$MON_NAMESPACE" \
    --no-headers 2>/dev/null |
    wc -l |
    tr -d ' '
)

STATUS="HOLD"

if [ "$HTTP_MAIN_ROWS" -eq 300 ] &&
   [ "$HTTP_MAIN_OK" -eq 300 ] &&
   [ "$HTTP_RESOURCE_ROWS" -eq 300 ] &&
   [ "$HTTP_RESOURCE_OK" -eq 300 ] &&
   [ "$SNAPSHOT_COUNT" -eq 30 ] &&
   [ "$RESOURCE_ERRORS" -eq 0 ] &&
   [ "${P0_FINAL:-0}" = "2" ] &&
   [ "${HTTP_FINAL:-000}" = "200" ] &&
   [ "$MON_FINAL" -eq 5 ]; then

  STATUS="PASS — RUN 3 ON DATA ACQUIRED"
fi

{
  echo "Gate                         : O5-B4.12E"
  echo "Run                          : 2"
  echo "Condition                    : Monitoring ON"
  echo "Protocol                     : Reconstructed and frozen"
  echo "Output                       : $OUT"
  echo
  echo "--- STANDALONE HTTP ---"
  echo "Samples                      : $HTTP_MAIN_ROWS/300"
  echo "HTTP 200                     : $HTTP_MAIN_OK/300"
  echo "Mean latency, seconds        : $HTTP_MAIN_MEAN"
  echo
  echo "--- RESOURCE TEST ---"
  echo "Resource snapshots           : $SNAPSHOT_COUNT/30"
  echo "Nominal sleep                : $RESOURCE_SLEEP seconds"
  echo "Resource collection errors   : $RESOURCE_ERRORS/0"
  echo "Concurrent HTTP samples      : $HTTP_RESOURCE_ROWS/300"
  echo "Concurrent HTTP 200          : $HTTP_RESOURCE_OK/300"
  echo "Concurrent mean latency      : $HTTP_RESOURCE_MEAN"
  echo
  echo "--- FINAL SAFETY ---"
  echo "P0 Ready                     : ${P0_FINAL:-0}/2"
  echo "HTTP Service                 : ${HTTP_FINAL:-000}"
  echo "Monitoring pods              : $MON_FINAL/5"
  echo
  echo "STATUS O5-B4.12E: $STATUS"
} | tee "$SUMMARY"

# ------------------------------------------------------------
# 7. Integrity checksum
# ------------------------------------------------------------

sha256sum \
  "$HTTP_MAIN" \
  "$HTTP_RESOURCE" \
  "$RESOURCE_DATA" \
  "$SYSTEM_STATE" \
  "$SUMMARY" \
  > "$CHECKSUM"

echo
echo "=== O5-B4.12E SELESAI ==="