#!/usr/bin/env bash
# HANFIS Jetson client capture v4 -- NodePort path and >=5-minute workload.
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 RUN CONDITION START_EPOCH TARGET_URL" >&2
  exit 2
fi

RUN_NO="$1"
CONDITION="${2,,}"
START_EPOCH="$3"
TARGET_URL="$4"
REQUESTS="${REQUESTS:-1500}"
REQUEST_INTERVAL_SECONDS="${REQUEST_INTERVAL_SECONDS:-0.21}"
TEGRSTATS_INTERVAL_MS="${TEGRSTATS_INTERVAL_MS:-2000}"
WARMUP_REQUESTS="${WARMUP_REQUESTS:-10}"
MIN_WORKLOAD_SECONDS="${MIN_WORKLOAD_SECONDS:-300}"

[[ "$RUN_NO" =~ ^[0-9]+$ ]] || { echo "RUN must be a non-negative integer" >&2; exit 2; }
[[ "$CONDITION" = on || "$CONDITION" = off ]] || { echo "CONDITION must be on or off" >&2; exit 2; }
[[ "$START_EPOCH" =~ ^[0-9]+$ ]] || { echo "START_EPOCH must be an integer" >&2; exit 2; }
[[ "$REQUESTS" =~ ^[1-9][0-9]*$ ]] || { echo "REQUESTS must be positive" >&2; exit 2; }
[[ "$REQUEST_INTERVAL_SECONDS" =~ ^[0-9]+([.][0-9]+)?$ ]] || { echo "Invalid REQUEST_INTERVAL_SECONDS" >&2; exit 2; }
[[ "$TEGRSTATS_INTERVAL_MS" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid TEGRSTATS_INTERVAL_MS" >&2; exit 2; }

WORKLOAD_SPAN_SECONDS=$(awk -v n="$REQUESTS" -v i="$REQUEST_INTERVAL_SECONDS" 'BEGIN {printf "%.3f", (n-1)*i}')
awk -v span="$WORKLOAD_SPAN_SECONDS" -v minimum="$MIN_WORKLOAD_SECONDS" 'BEGIN {exit !(span>=minimum)}' || {
  echo "CLIENT_STATUS=HOLD_WORKLOAD_UNDER_${MIN_WORKLOAD_SECONDS}s"
  exit 1
}
MIN_TEGRA_ROWS=$(awk -v span="$WORKLOAD_SPAN_SECONDS" -v ms="$TEGRSTATS_INTERVAL_MS" 'BEGIN {v=int((span*1000/ms)*0.90); print (v<1 ? 1 : v)}')

for required in curl awk date hostname sha256sum timedatectl tegrastats; do
  command -v "$required" >/dev/null 2>&1 || { echo "Missing command: $required" >&2; exit 1; }
done

NTP_SYNC=$(timedatectl show -p NTPSynchronized --value)
if [ "$NTP_SYNC" != yes ]; then
  echo "CLIENT_STATUS=HOLD_NTP"
  exit 1
fi

WARMUP_OK=0
for _ in $(seq 1 "$WARMUP_REQUESTS"); do
  code=$(curl -sS --connect-timeout 5 --max-time 10 -o /dev/null -w '%{http_code}' "$TARGET_URL" || true)
  [ "$code" = 200 ] && WARMUP_OK=$((WARMUP_OK + 1))
  sleep 0.1
done
echo "CLIENT_WARMUP_HTTP_200=$WARMUP_OK/$WARMUP_REQUESTS"
[ "$WARMUP_OK" -eq "$WARMUP_REQUESTS" ] || { echo "CLIENT_STATUS=HOLD_EXTERNAL_NODEPORT_PATH"; exit 1; }

delay=$(awk -v target="$START_EPOCH" -v now="$EPOCHREALTIME" 'BEGIN {d=target-now; if(d<0)d=0; printf "%.3f",d}')
awk -v d="$delay" 'BEGIN {exit !(d>0)}' && sleep "$delay"

RUN_ID=$(date +%Y%m%dT%H%M%S%z)
OUT="$HOME/hanfis/data/raw/O5-V4-run${RUN_NO}-${CONDITION}-${RUN_ID}"
mkdir -p "$OUT"
SCRIPT_SHA256=$(sha256sum "$0" | awk '{print $1}')

cat > "$OUT/metadata.txt" <<EOF
RUN=$RUN_NO
CONDITION=${CONDITION^^}
PROTOCOL=external-v4-nodeport
COLLECTOR=client-jetson
ACCESS_PATH=JETSON_TO_WINDOWS_DOCKER_GATEWAY_TO_NODEPORT
REQUEST_PACING=ABSOLUTE_DEADLINE
COLLECTOR_SHA256=$SCRIPT_SHA256
START_EPOCH_UTC=$START_EPOCH
TARGET=$TARGET_URL
HTTP_REQUESTS=$REQUESTS
REQUEST_INTERVAL_SECONDS=$REQUEST_INTERVAL_SECONDS
WORKLOAD_SPAN_SECONDS=$WORKLOAD_SPAN_SECONDS
TEGRSTATS_INTERVAL_MS=$TEGRSTATS_INTERVAL_MS
MIN_TEGRA_ROWS=$MIN_TEGRA_ROWS
WARMUP_REQUESTS=$WARMUP_REQUESTS
NTP_SYNCHRONIZED=$NTP_SYNC
HOSTNAME=$(hostname)
JETSON_IP=$(hostname -I | awk '{print $1}')
KERNEL=$(uname -r)
START_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

tegrastats --interval "$TEGRSTATS_INTERVAL_MS" > "$OUT/tegrastats.log" &
TEGRA_PID=$!
stop_tegrastats() {
  kill "$TEGRA_PID" >/dev/null 2>&1 || true
  wait "$TEGRA_PID" 2>/dev/null || true
}
trap stop_tegrastats EXIT

printf '%s\n' 'seq,timestamp_utc,http_code,time_namelookup,time_connect,time_starttransfer,time_total,size_bytes' > "$OUT/http.csv"
for seq in $(seq 1 "$REQUESTS"); do
  scheduled_epoch=$(awk -v start="$START_EPOCH" -v idx="$((seq-1))" -v interval="$REQUEST_INTERVAL_SECONDS" 'BEGIN {printf "%.6f", start + idx*interval}')
  request_delay=$(awk -v target="$scheduled_epoch" -v now="$EPOCHREALTIME" 'BEGIN {d=target-now; if(d<0)d=0; printf "%.6f",d}')
  awk -v d="$request_delay" 'BEGIN {exit !(d>0)}' && sleep "$request_delay"
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  curl -sS --connect-timeout 5 --max-time 10 -o /dev/null \
    -w "$seq,$timestamp,%{http_code},%{time_namelookup},%{time_connect},%{time_starttransfer},%{time_total},%{size_download}\n" \
    "$TARGET_URL" >> "$OUT/http.csv"
done
stop_tegrastats
trap - EXIT

HTTP_ROWS=$(( $(wc -l < "$OUT/http.csv") - 1 ))
HTTP_OK=$(awk -F, 'NR>1 && $3==200 {n++} END{print n+0}' "$OUT/http.csv")
DUPLICATES=$(awk -F, 'NR>1 {n[$1]++} END{for(i in n)if(n[i]>1)d++; print d+0}' "$OUT/http.csv")
TEGRA_ROWS=$(wc -l < "$OUT/tegrastats.log")

cat >> "$OUT/metadata.txt" <<EOF
END_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OBSERVED_HTTP_ROWS=$HTTP_ROWS
OBSERVED_HTTP_200=$HTTP_OK
OBSERVED_TEGRA_ROWS=$TEGRA_ROWS
EOF
(cd "$OUT" && sha256sum metadata.txt http.csv tegrastats.log > sha256.txt)

echo "CLIENT_HTTP_ROWS=$HTTP_ROWS/$REQUESTS"
echo "CLIENT_HTTP_200=$HTTP_OK/$REQUESTS"
echo "CLIENT_DUPLICATE_SEQ=$DUPLICATES"
echo "CLIENT_TEGRA_ROWS=$TEGRA_ROWS/$MIN_TEGRA_ROWS"
echo "OUTPUT=$OUT"
if [ "$HTTP_ROWS" -eq "$REQUESTS" ] && [ "$HTTP_OK" -eq "$REQUESTS" ] && [ "$DUPLICATES" -eq 0 ] && [ "$TEGRA_ROWS" -ge "$MIN_TEGRA_ROWS" ]; then
  echo "CLIENT_STATUS=PASS"
else
  echo "CLIENT_STATUS=HOLD"
  exit 1
fi
