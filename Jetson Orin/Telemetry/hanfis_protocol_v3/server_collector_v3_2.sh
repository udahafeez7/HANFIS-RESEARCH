#!/usr/bin/env bash
# HANFIS server collector v3.2
#
# Purpose:
#   Operational, synchronized cross-check of Metrics Server data during the
#   existing ~65-second Jetson workload. Publication-grade resource estimates
#   must be obtained by the out-of-band Prometheus collector developed in the
#   next revision stage.
#
# Key changes from candidate v3.1:
#   * restores a 2-second interval so 32 samples span 62 seconds;
#   * derives expected rows from ready nodes/containers instead of MIN_ROWS=60;
#   * applies condition-aware ON/OFF monitoring gates;
#   * rejects incomplete per-sequence snapshots and any kubectl-top failure;
#   * records safe Git provenance without failing outside a repository;
#   * refuses to overwrite a non-empty output directory.

set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 RUN CONDITION START_EPOCH OUTPUT_DIR" >&2
  exit 2
fi

RUN_NO="$1"
CONDITION="${2,,}"
START_EPOCH="$3"
OUT="$4"
SAMPLES="${SAMPLES:-32}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-2}"
MAX_INCOMPLETE_SEQUENCES="${MAX_INCOMPLETE_SEQUENCES:-0}"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ ! "$RUN_NO" =~ ^[0-9]+$ ]]; then
  echo "RUN must be a non-negative integer" >&2
  exit 2
fi
if [[ "$CONDITION" != "on" && "$CONDITION" != "off" ]]; then
  echo "CONDITION must be on or off" >&2
  exit 2
fi
if [[ ! "$START_EPOCH" =~ ^[0-9]+$ ]]; then
  echo "START_EPOCH must be an integer UTC epoch" >&2
  exit 2
fi
if [[ ! "$SAMPLES" =~ ^[1-9][0-9]*$ ]]; then
  echo "SAMPLES must be a positive integer" >&2
  exit 2
fi
if [[ ! "$INTERVAL_SECONDS" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "INTERVAL_SECONDS must be non-negative" >&2
  exit 2
fi
if [[ ! "$MAX_INCOMPLETE_SEQUENCES" =~ ^[0-9]+$ ]]; then
  echo "MAX_INCOMPLETE_SEQUENCES must be a non-negative integer" >&2
  exit 2
fi

for required in kubectl awk sha256sum sort wc date hostname find paste seq sleep tr; do
  command -v "$required" >/dev/null 2>&1 || {
    echo "Missing command: $required" >&2
    exit 1
  }
done

mkdir -p "$OUT"
if [ -n "$(find "$OUT" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  echo "Refusing to overwrite non-empty output directory: $OUT" >&2
  exit 1
fi

SCRIPT_SHA256=$(sha256sum "$0" | awk '{print $1}')
if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_COMMIT=$(git -C "$SCRIPT_DIR" rev-parse HEAD)
  GIT_UNCOMMITTED_FILES=$(git -C "$SCRIPT_DIR" status --porcelain | wc -l)
else
  GIT_COMMIT="NOT_A_GIT_CHECKOUT"
  GIT_UNCOMMITTED_FILES="UNKNOWN"
fi

count_ready_nodes() {
  kubectl get nodes --no-headers 2>/dev/null \
    | awk '$2 ~ /^Ready/ {n++} END {print n+0}'
}

count_ready_containers() {
  local namespace="$1"
  kubectl get pods -n "$namespace" \
    -o jsonpath='{range .items[*]}{range .status.containerStatuses[*]}{.ready}{"\n"}{end}{end}' \
    2>/dev/null | awk '$1=="true" {n++} END {print n+0}'
}

NODE_COUNT=$(count_ready_nodes)
P0_CONTAINER_COUNT=$(count_ready_containers hanfis-research)
MONITOR_CONTAINER_COUNT=$(count_ready_containers monitoring)

if [ "$NODE_COUNT" -lt 1 ]; then
  echo "PREFLIGHT_FAIL=NO_READY_NODES" >&2
  exit 1
fi
if [ "$P0_CONTAINER_COUNT" -lt 1 ]; then
  echo "PREFLIGHT_FAIL=NO_READY_P0_CONTAINERS" >&2
  exit 1
fi
if [ "$CONDITION" = "on" ] && [ "$MONITOR_CONTAINER_COUNT" -lt 1 ]; then
  echo "PREFLIGHT_FAIL=NO_READY_MONITORING_CONTAINERS_WHILE_ON" >&2
  exit 1
fi
if [ "$CONDITION" = "off" ] && [ "$MONITOR_CONTAINER_COUNT" -ne 0 ]; then
  echo "PREFLIGHT_FAIL=MONITORING_CONTAINERS_PRESENT_WHILE_OFF" >&2
  exit 1
fi

EXPECTED_NODE_ROWS=$((NODE_COUNT * SAMPLES))
EXPECTED_P0_ROWS=$((P0_CONTAINER_COUNT * SAMPLES))
if [ "$CONDITION" = "on" ]; then
  EXPECTED_MONITORING_ROWS=$((MONITOR_CONTAINER_COUNT * SAMPLES))
else
  EXPECTED_MONITORING_ROWS=0
fi
OBSERVATION_SPAN_SECONDS=$(awk -v n="$SAMPLES" -v i="$INTERVAL_SECONDS" \
  'BEGIN {printf "%.3f", (n-1)*i}')

cat > "$OUT/metadata.txt" <<EOF
RUN=$RUN_NO
CONDITION=${CONDITION^^}
PROTOCOL=external-v3.2-operational
COLLECTOR=server-wsl
COLLECTOR_ROLE=operational-cross-check-not-publication-resource-source
COLLECTOR_SHA256=$SCRIPT_SHA256
GIT_COMMIT=$GIT_COMMIT
GIT_UNCOMMITTED_FILES=$GIT_UNCOMMITTED_FILES
START_EPOCH_UTC=$START_EPOCH
SAMPLES=$SAMPLES
INTERVAL_SECONDS=$INTERVAL_SECONDS
OBSERVATION_SPAN_SECONDS=$OBSERVATION_SPAN_SECONDS
METRICS_SOURCE=metrics-server-via-kubectl-top
METRICS_RESOLUTION_WARNING=aliased-snapshots-do-not-use-for-final-resource-inference
READY_NODE_COUNT=$NODE_COUNT
READY_P0_CONTAINER_COUNT=$P0_CONTAINER_COUNT
READY_MONITORING_CONTAINER_COUNT=$MONITOR_CONTAINER_COUNT
EXPECTED_NODE_ROWS=$EXPECTED_NODE_ROWS
EXPECTED_P0_ROWS=$EXPECTED_P0_ROWS
EXPECTED_MONITORING_ROWS=$EXPECTED_MONITORING_ROWS
MAX_INCOMPLETE_SEQUENCES=$MAX_INCOMPLETE_SEQUENCES
HOSTNAME=$(hostname)
KUBERNETES_CONTEXT=$(kubectl config current-context 2>/dev/null || echo UNKNOWN)
KUBECTL_VERSION=$(kubectl version --client -o json 2>/dev/null | tr -d '\n' || true)
EOF

printf '%s\n' 'seq,timestamp_utc,node,cpu_cores,cpu_pct,memory_bytes,memory_pct' > "$OUT/nodes.csv"
printf '%s\n' 'seq,timestamp_utc,pod,container,cpu,memory' > "$OUT/p0_containers.csv"
printf '%s\n' 'seq,timestamp_utc,pod,container,cpu,memory' > "$OUT/monitoring_containers.csv"
: > "$OUT/errors.log"

TOP_FAILURES=0

collect_pods() {
  local namespace="$1" target="$2" seq="$3" timestamp="$4"
  if ! kubectl top pods -n "$namespace" --containers --no-headers \
      2>>"$OUT/errors.log" \
      | awk -v s="$seq" -v ts="$timestamp" \
          'BEGIN{OFS=","} NF>=4 {print s,ts,$1,$2,$3,$4}' \
      >> "$target"; then
    TOP_FAILURES=$((TOP_FAILURES + 1))
  fi
}

wait_until() {
  local target="$1" delay
  delay=$(awk -v target="$target" -v now="$EPOCHREALTIME" \
    'BEGIN {d=target-now; if (d<0) d=0; printf "%.3f", d}')
  if awk -v d="$delay" 'BEGIN {exit !(d>0)}'; then
    sleep "$delay"
  fi
}

for seq in $(seq 1 "$SAMPLES"); do
  target_time=$(awk -v start="$START_EPOCH" -v idx="$seq" \
    -v interval="$INTERVAL_SECONDS" \
    'BEGIN {printf "%.3f", start+(idx-1)*interval}')
  wait_until "$target_time"
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  if ! kubectl top nodes --no-headers 2>>"$OUT/errors.log" \
      | awk -v s="$seq" -v ts="$timestamp" \
          'BEGIN{OFS=","} NF>=5 {print s,ts,$1,$2,$3,$4,$5}' \
      >> "$OUT/nodes.csv"; then
    TOP_FAILURES=$((TOP_FAILURES + 1))
  fi

  collect_pods hanfis-research "$OUT/p0_containers.csv" "$seq" "$timestamp"
  collect_pods monitoring "$OUT/monitoring_containers.csv" "$seq" "$timestamp"
done

row_count() {
  local path="$1"
  awk 'END {print (NR>0 ? NR-1 : 0)}' "$path"
}

incomplete_sequences() {
  local path="$1" expected_per_sequence="$2"
  awk -F, -v samples="$SAMPLES" -v expected="$expected_per_sequence" '
    NR>1 {count[$1]++}
    END {
      bad=0
      for (i=1; i<=samples; i++) {
        if ((count[i]+0) != expected) bad++
      }
      print bad+0
    }
  ' "$path"
}

NODE_ROWS=$(row_count "$OUT/nodes.csv")
P0_ROWS=$(row_count "$OUT/p0_containers.csv")
MONITORING_ROWS=$(row_count "$OUT/monitoring_containers.csv")
NODE_INCOMPLETE=$(incomplete_sequences "$OUT/nodes.csv" "$NODE_COUNT")
P0_INCOMPLETE=$(incomplete_sequences "$OUT/p0_containers.csv" "$P0_CONTAINER_COUNT")
MONITORING_INCOMPLETE=$(incomplete_sequences \
  "$OUT/monitoring_containers.csv" "$MONITOR_CONTAINER_COUNT")

DISTINCT_NODE_CPU_SUMMARY=$(awk -F, 'NR>1 {print $3 "," $4}' \
  "$OUT/nodes.csv" \
  | sort -u \
  | awk -F, '{count[$1]++} END {for (node in count) print node ":" count[node]}' \
  | sort \
  | paste -sd';' -)

cat >> "$OUT/metadata.txt" <<EOF
OBSERVED_NODE_ROWS=$NODE_ROWS
OBSERVED_P0_ROWS=$P0_ROWS
OBSERVED_MONITORING_ROWS=$MONITORING_ROWS
NODE_INCOMPLETE_SEQUENCES=$NODE_INCOMPLETE
P0_INCOMPLETE_SEQUENCES=$P0_INCOMPLETE
MONITORING_INCOMPLETE_SEQUENCES=$MONITORING_INCOMPLETE
DISTINCT_NODE_CPU_VALUES_BY_NODE=$DISTINCT_NODE_CPU_SUMMARY
TOP_FAILURES=$TOP_FAILURES
EOF

FAIL=0
[ "$NODE_ROWS" -eq "$EXPECTED_NODE_ROWS" ] || {
  echo "GATE_FAIL=NODE_ROWS_EXPECTED_${EXPECTED_NODE_ROWS}_OBSERVED_${NODE_ROWS}"
  FAIL=1
}
[ "$P0_ROWS" -eq "$EXPECTED_P0_ROWS" ] || {
  echo "GATE_FAIL=P0_ROWS_EXPECTED_${EXPECTED_P0_ROWS}_OBSERVED_${P0_ROWS}"
  FAIL=1
}
[ "$NODE_INCOMPLETE" -le "$MAX_INCOMPLETE_SEQUENCES" ] || {
  echo "GATE_FAIL=NODE_INCOMPLETE_SEQUENCES_${NODE_INCOMPLETE}"
  FAIL=1
}
[ "$P0_INCOMPLETE" -le "$MAX_INCOMPLETE_SEQUENCES" ] || {
  echo "GATE_FAIL=P0_INCOMPLETE_SEQUENCES_${P0_INCOMPLETE}"
  FAIL=1
}
[ "$TOP_FAILURES" -eq 0 ] || {
  echo "GATE_FAIL=TOP_FAILURES_${TOP_FAILURES}"
  FAIL=1
}

if [ "$CONDITION" = "on" ]; then
  [ "$MONITORING_ROWS" -eq "$EXPECTED_MONITORING_ROWS" ] || {
    echo "GATE_FAIL=MONITORING_ROWS_EXPECTED_${EXPECTED_MONITORING_ROWS}_OBSERVED_${MONITORING_ROWS}"
    FAIL=1
  }
  [ "$MONITORING_INCOMPLETE" -le "$MAX_INCOMPLETE_SEQUENCES" ] || {
    echo "GATE_FAIL=MONITORING_INCOMPLETE_SEQUENCES_${MONITORING_INCOMPLETE}"
    FAIL=1
  }
else
  [ "$MONITORING_ROWS" -eq 0 ] || {
    echo "GATE_FAIL=MONITORING_PRESENT_WHILE_OFF"
    FAIL=1
  }
fi

(cd "$OUT" && sha256sum \
  metadata.txt nodes.csv p0_containers.csv monitoring_containers.csv errors.log \
  > sha256.txt)

echo "SERVER_NODE_ROWS=$NODE_ROWS/$EXPECTED_NODE_ROWS"
echo "SERVER_P0_ROWS=$P0_ROWS/$EXPECTED_P0_ROWS"
echo "SERVER_MONITORING_ROWS=$MONITORING_ROWS/$EXPECTED_MONITORING_ROWS"
echo "SERVER_NODE_INCOMPLETE_SEQUENCES=$NODE_INCOMPLETE"
echo "SERVER_P0_INCOMPLETE_SEQUENCES=$P0_INCOMPLETE"
echo "SERVER_MONITORING_INCOMPLETE_SEQUENCES=$MONITORING_INCOMPLETE"
echo "SERVER_TOP_FAILURES=$TOP_FAILURES"
echo "SERVER_OUTPUT=$OUT"

if [ "$FAIL" -eq 0 ]; then
  echo "SERVER_STATUS=PASS"
else
  echo "SERVER_STATUS=HOLD"
  exit 1
fi
