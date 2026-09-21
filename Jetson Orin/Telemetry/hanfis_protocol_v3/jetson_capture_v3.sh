#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 RUN CONDITION START_EPOCH TARGET_URL" >&2
  exit 2
fi

RUN_NO="$1"
CONDITION="${2,,}"
START_EPOCH="$3"
TARGET_URL="$4"
REQUESTS=300
REQUEST_INTERVAL_SECONDS=0.2
TEGRSTATS_INTERVAL_MS=2000
WARMUP_REQUESTS=10

if [[ "$CONDITION" != "on" && "$CONDITION" != "off" ]]; then
  echo "CONDITION must be on or off" >&2
  exit 2
fi

NTP_SYNC=$(timedatectl show -p NTPSynchronized --value)
if [ "$NTP_SYNC" != "yes" ]; then
  echo "CLIENT_STATUS=HOLD_NTP"
  exit 1
fi

WARMUP_OK=0
for _ in $(seq 1 "$WARMUP_REQUESTS"); do
  code=$(curl -sS --connect-timeout 5 --max-time 10 -o /dev/null -w '%{http_code}' "$TARGET_URL" || true)
  [ "$code" = "200" ] && WARMUP_OK=$((WARMUP_OK + 1))
  sleep 0.1
done

echo "CLIENT_WARMUP_HTTP_200=$WARMUP_OK/$WARMUP_REQUESTS"
if [ "$WARMUP_OK" -ne "$WARMUP_REQUESTS" ]; then
  echo "CLIENT_STATUS=HOLD_EXTERNAL_PATH"
  exit 1
fi

delay=$(awk -v target="$START_EPOCH" -v now="$EPOCHREALTIME" 'BEGIN { d=target-now; if (d<0) d=0; printf "%.3f", d }')
if awk -v d="$delay" 'BEGIN { exit !(d>0) }'; then
  sleep "$delay"
fi

RUN_ID=$(date +%Y%m%dT%H%M%S%z)
OUT="$HOME/hanfis/data/raw/O5-V3-run${RUN_NO}-${CONDITION}-${RUN_ID}"
mkdir -p "$OUT"
SCRIPT_SHA256=$(sha256sum "$0" | awk '{print $1}')

cat > "$OUT/metadata.txt" <<EOF
RUN=$RUN_NO
CONDITION=${CONDITION^^}
PROTOCOL=external-v3.0
COLLECTOR=client-jetson
COLLECTOR_SHA256=$SCRIPT_SHA256
START_EPOCH_UTC=$START_EPOCH
TARGET=$TARGET_URL
HTTP_REQUESTS=$REQUESTS
REQUEST_INTERVAL_SECONDS=$REQUEST_INTERVAL_SECONDS
TEGRSTATS_INTERVAL_MS=$TEGRSTATS_INTERVAL_MS
WARMUP_REQUESTS=$WARMUP_REQUESTS
NTP_SYNCHRONIZED=$NTP_SYNC
HOSTNAME=$(hostname)
JETSON_IP=$(hostname -I | awk '{print $1}')
KERNEL=$(uname -r)
START_UTC=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
EOF

timeout 65s tegrastats --interval "$TEGRSTATS_INTERVAL_MS" > "$OUT/tegrastats.log" &
TEGRA_PID=$!

printf '%s\n' 'seq,timestamp_utc,http_code,time_connect,time_total,size_bytes' > "$OUT/http.csv"

for seq in $(seq 1 "$REQUESTS"); do
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  curl -sS --connect-timeout 5 --max-time 10 -o /dev/null \
    -w "$seq,$timestamp,%{http_code},%{time_connect},%{time_total},%{size_download}\n" \
    "$TARGET_URL" >> "$OUT/http.csv"
  sleep "$REQUEST_INTERVAL_SECONDS"
done

wait "$TEGRA_PID" 2>/dev/null || true

HTTP_ROWS=$(( $(wc -l < "$OUT/http.csv") - 1 ))
HTTP_OK=$(awk -F, 'NR>1 && $3==200 {n++} END{print n+0}' "$OUT/http.csv")
DUPLICATES=$(awk -F, 'NR>1 {n[$1]++} END{for(i in n)if(n[i]>1)d++; print d+0}' "$OUT/http.csv")
TEGRA_ROWS=$(wc -l < "$OUT/tegrastats.log")

(
  cd "$OUT"
  sha256sum metadata.txt http.csv tegrastats.log > sha256.txt
)

echo "CLIENT_HTTP_ROWS=$HTTP_ROWS/$REQUESTS"
echo "CLIENT_HTTP_200=$HTTP_OK/$REQUESTS"
echo "CLIENT_DUPLICATE_SEQ=$DUPLICATES"
echo "CLIENT_TEGRA_ROWS=$TEGRA_ROWS"
echo "OUTPUT=$OUT"

if [ "$HTTP_ROWS" -eq "$REQUESTS" ] && [ "$HTTP_OK" -eq "$REQUESTS" ] && [ "$DUPLICATES" -eq 0 ] && [ "$TEGRA_ROWS" -ge 30 ]; then
  echo "CLIENT_STATUS=PASS"
else
  echo "CLIENT_STATUS=HOLD"
  exit 1
fi
