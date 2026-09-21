#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 RUN CONDITION START_EPOCH OUTPUT_DIR" >&2
  exit 2
fi

RUN_NO="$1"
CONDITION="${2,,}"
START_EPOCH="$3"
OUT="$4"
SAMPLES=32
INTERVAL_SECONDS=2

if [[ "$CONDITION" != "on" && "$CONDITION" != "off" ]]; then
  echo "CONDITION must be on or off" >&2
  exit 2
fi

mkdir -p "$OUT"
SCRIPT_SHA256=$(sha256sum "$0" | awk '{print $1}')

cat > "$OUT/metadata.txt" <<EOF
RUN=$RUN_NO
CONDITION=${CONDITION^^}
PROTOCOL=external-v3.0
COLLECTOR=server-wsl
COLLECTOR_SHA256=$SCRIPT_SHA256
START_EPOCH_UTC=$START_EPOCH
SAMPLES=$SAMPLES
INTERVAL_SECONDS=$INTERVAL_SECONDS
HOSTNAME=$(hostname)
KUBECTL_VERSION=$(kubectl version --client -o json 2>/dev/null | tr -d '\n' || true)
EOF

printf '%s\n' 'seq,timestamp_utc,node,cpu_cores,cpu_pct,memory_bytes,memory_pct' > "$OUT/nodes.csv"
printf '%s\n' 'seq,timestamp_utc,pod,container,cpu,memory' > "$OUT/p0_containers.csv"
printf '%s\n' 'seq,timestamp_utc,pod,container,cpu,memory' > "$OUT/monitoring_containers.csv"
: > "$OUT/errors.log"

wait_until() {
  local target="$1"
  local delay
  delay=$(awk -v target="$target" -v now="$EPOCHREALTIME" 'BEGIN { d=target-now; if (d<0) d=0; printf "%.3f", d }')
  if awk -v d="$delay" 'BEGIN { exit !(d>0) }'; then
    sleep "$delay"
  fi
}

for seq in $(seq 1 "$SAMPLES"); do
  target_time=$(awk -v start="$START_EPOCH" -v sample_idx="$seq" -v interval="$INTERVAL_SECONDS" 'BEGIN { printf "%.3f", start+(sample_idx-1)*interval }')
  wait_until "$target_time"
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  kubectl top nodes --no-headers 2>>"$OUT/errors.log" \
    | awk -v s="$seq" -v ts="$timestamp" 'BEGIN{OFS=","} NF>=5 {print s,ts,$1,$2,$3,$4,$5}' \
    >> "$OUT/nodes.csv" || true

  kubectl top pods -n hanfis-research --containers --no-headers 2>>"$OUT/errors.log" \
    | awk -v s="$seq" -v ts="$timestamp" 'BEGIN{OFS=","} NF>=4 {print s,ts,$1,$2,$3,$4}' \
    >> "$OUT/p0_containers.csv" || true

  kubectl top pods -n monitoring --containers --no-headers 2>>"$OUT/errors.log" \
    | awk -v s="$seq" -v ts="$timestamp" 'BEGIN{OFS=","} NF>=4 {print s,ts,$1,$2,$3,$4}' \
    >> "$OUT/monitoring_containers.csv" || true
done

NODE_ROWS=$(( $(wc -l < "$OUT/nodes.csv") - 1 ))
P0_ROWS=$(( $(wc -l < "$OUT/p0_containers.csv") - 1 ))
MONITORING_ROWS=$(( $(wc -l < "$OUT/monitoring_containers.csv") - 1 ))

(
  cd "$OUT"
  sha256sum metadata.txt nodes.csv p0_containers.csv monitoring_containers.csv errors.log > sha256.txt
)

echo "SERVER_NODE_ROWS=$NODE_ROWS"
echo "SERVER_P0_ROWS=$P0_ROWS"
echo "SERVER_MONITORING_ROWS=$MONITORING_ROWS"
echo "SERVER_OUTPUT=$OUT"

if [ "$NODE_ROWS" -ge 60 ] && [ "$P0_ROWS" -ge 60 ]; then
  echo "SERVER_STATUS=PASS"
else
  echo "SERVER_STATUS=HOLD"
  exit 1
fi
