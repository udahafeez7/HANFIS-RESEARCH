#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 RUN_NUMBER on-off|off-on" >&2
  exit 2
fi

RUN_NO="$1"
ORDER="${2,,}"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SERVER_COLLECTOR="$SCRIPT_DIR/server_collector_v3.sh"
CLIENT_COLLECTOR="$SCRIPT_DIR/jetson_capture_v3.sh"
JETSON_HOST="${JETSON_HOST:-jetson@10.176.68.250}"
TARGET_URL="${TARGET_URL:-http://10.176.68.28:18080/}"
REMOTE_SCRIPT="/home/jetson/hanfis/scripts/jetson_capture_v3.sh"
OUTPUT_ROOT="${OUTPUT_ROOT:-/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV3}"
PAIR_ID="run${RUN_NO}-${ORDER}-$(date +%Y%m%dT%H%M%S%z)"
PAIR_DIR="$OUTPUT_ROOT/$PAIR_ID"
CONTROL_PATH=$(mktemp -u /tmp/hanfis-ssh-XXXXXX)

case "$ORDER" in
  on-off) FIRST=on; SECOND=off ;;
  off-on) FIRST=off; SECOND=on ;;
  *) echo "Order must be on-off or off-on" >&2; exit 2 ;;
esac

for required in kubectl curl ssh scp sha256sum tar awk; do
  command -v "$required" >/dev/null || { echo "Missing command: $required" >&2; exit 1; }
done

bash -n "$SERVER_COLLECTOR"
bash -n "$CLIENT_COLLECTOR"
awk -v start=100 -v sample_idx=1 -v interval=2 'BEGIN { expected=100; actual=start+(sample_idx-1)*interval; exit !(actual==expected) }'
mkdir -p "$PAIR_DIR"

cleanup() {
  ssh -S "$CONTROL_PATH" -O exit "$JETSON_HOST" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== OPENING PERSISTENT SSH CONNECTION ==="
ssh -M -S "$CONTROL_PATH" -o ControlPersist=900 -fN "$JETSON_HOST"
ssh -S "$CONTROL_PATH" "$JETSON_HOST" 'mkdir -p "$HOME/hanfis/scripts"'
scp -o ControlPath="$CONTROL_PATH" "$CLIENT_COLLECTOR" "$JETSON_HOST:$REMOTE_SCRIPT"
ssh -S "$CONTROL_PATH" "$JETSON_HOST" "chmod +x '$REMOTE_SCRIPT'"

washout() {
  echo "Washout 120 seconds..."
  for remaining in 120 90 60 30; do
    echo "WASHOUT_REMAINING=${remaining}s"
    sleep 30
  done
}

set_condition() {
  local condition="$1"
  echo "=== SET MONITORING ${condition^^} ==="

  if [ "$condition" = "on" ]; then
    kubectl scale deployment hanfis-monitoring-kube-pro-operator hanfis-monitoring-kube-state-metrics -n monitoring --replicas=1
    kubectl scale statefulset prometheus-hanfis-monitoring-kube-pro-prometheus -n monitoring --replicas=1
    kubectl patch daemonset hanfis-monitoring-prometheus-node-exporter -n monitoring --type=merge -p='{"spec":{"template":{"spec":{"nodeSelector":{"hanfis.monitoring/off":null}}}}}'
    kubectl rollout status deployment/hanfis-monitoring-kube-pro-operator -n monitoring --timeout=180s
    kubectl rollout status deployment/hanfis-monitoring-kube-state-metrics -n monitoring --timeout=180s
    kubectl rollout status daemonset/hanfis-monitoring-prometheus-node-exporter -n monitoring --timeout=180s
    kubectl rollout status statefulset/prometheus-hanfis-monitoring-kube-pro-prometheus -n monitoring --timeout=180s
  else
    kubectl scale deployment hanfis-monitoring-kube-pro-operator hanfis-monitoring-kube-state-metrics -n monitoring --replicas=0
    kubectl scale statefulset prometheus-hanfis-monitoring-kube-pro-prometheus -n monitoring --replicas=0
    kubectl patch daemonset hanfis-monitoring-prometheus-node-exporter -n monitoring --type=merge -p='{"spec":{"template":{"spec":{"nodeSelector":{"hanfis.monitoring/off":"true"}}}}}'
    kubectl wait --for=delete pod --all -n monitoring --timeout=180s || true
  fi

  washout

  local p0_ready monitoring_ready http_code
  p0_ready=$(kubectl get pods -n hanfis-research --no-headers | awk '$1~/^p0-baseline-/ && $2=="1/1" && $3=="Running"{n++} END{print n+0}')
  monitoring_ready=$(kubectl get pods -n monitoring --no-headers 2>/dev/null | awk '$3=="Running" && ($2=="1/1" || $2=="2/2"){n++} END{print n+0}')
  http_code=$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:18080/)

  echo "P0_READY=$p0_ready/2"
  echo "MONITORING_READY=$monitoring_ready"
  echo "P0_HTTP=$http_code"

  [ "$p0_ready" -eq 2 ] && [ "$http_code" = "200" ]
  if [ "$condition" = "on" ]; then
    [ "$monitoring_ready" -eq 5 ]
  else
    [ "$monitoring_ready" -eq 0 ]
  fi
}

run_condition() {
  local condition="$1"
  local condition_dir="$PAIR_DIR/$condition"
  local server_dir="$condition_dir/server"
  local client_dir="$condition_dir/client"
  local server_log="$condition_dir/server_collector.log"
  local client_log="$condition_dir/client_collector.log"
  local start_epoch

  mkdir -p "$server_dir" "$client_dir"
  start_epoch=$(( $(date -u +%s) + 20 ))

  echo "=== RUN $RUN_NO ${condition^^}; SYNCHRONIZED START=$start_epoch ==="
  "$SERVER_COLLECTOR" "$RUN_NO" "$condition" "$start_epoch" "$server_dir" | tee "$server_log" &
  local server_pid=$!

  ssh -S "$CONTROL_PATH" "$JETSON_HOST" \
    "'$REMOTE_SCRIPT' '$RUN_NO' '$condition' '$start_epoch' '$TARGET_URL'" \
    | tee "$client_log"

  wait "$server_pid"

  local remote_output
  remote_output=$(awk -F= '$1=="OUTPUT"{print $2}' "$client_log" | tail -n 1)
  [ -n "$remote_output" ]

  ssh -S "$CONTROL_PATH" "$JETSON_HOST" "tar -C '$remote_output' -czf - ." \
    | tar -C "$client_dir" -xzf -

  (cd "$server_dir" && sha256sum -c sha256.txt)
  (cd "$client_dir" && sha256sum -c sha256.txt)

  {
    echo "RUN=$RUN_NO"
    echo "CONDITION=${condition^^}"
    echo "ORDER=${ORDER^^}"
    echo "PROTOCOL=external-v3.0"
    echo "START_EPOCH_UTC=$start_epoch"
    echo "TARGET_URL=$TARGET_URL"
    echo "JETSON_HOST=$JETSON_HOST"
    echo "SERVER_COLLECTOR_SHA256=$(sha256sum "$SERVER_COLLECTOR" | awk '{print $1}')"
    echo "CLIENT_COLLECTOR_SHA256=$(sha256sum "$CLIENT_COLLECTOR" | awk '{print $1}')"
    echo "STATUS=LOCKED_CONDITION"
  } > "$condition_dir/condition-manifest.txt"

  (cd "$condition_dir" && sha256sum condition-manifest.txt > condition-manifest.sha256)
  echo "STATUS=PASS_RUN${RUN_NO}_${condition^^}"
}

echo "=== PREFLIGHT ==="
kubectl get nodes
kubectl top nodes
curl -sS --max-time 5 -o /dev/null -w 'LOCAL_P0_HTTP=%{http_code}\n' http://127.0.0.1:18080/
ssh -S "$CONTROL_PATH" "$JETSON_HOST" \
  "curl -sS --max-time 10 -o /dev/null -w 'REMOTE_P0_HTTP=%{http_code}\\n' '$TARGET_URL'"

set_condition "$FIRST"
run_condition "$FIRST"
set_condition "$SECOND"
run_condition "$SECOND"

{
  echo "RUN=$RUN_NO"
  echo "ORDER=${ORDER^^}"
  echo "PROTOCOL=external-v3.0"
  echo "FIRST_CONDITION=${FIRST^^}"
  echo "SECOND_CONDITION=${SECOND^^}"
  echo "STATUS=LOCKED_VALID_PAIR"
} > "$PAIR_DIR/pair-manifest.txt"

ARCHIVE="$OUTPUT_ROOT/O5-V3-run${RUN_NO}-${ORDER}-pair.tar.gz"
tar -czf "$ARCHIVE" -C "$OUTPUT_ROOT" "$PAIR_ID"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

echo "PAIR_DIR=$PAIR_DIR"
echo "PAIR_ARCHIVE=$ARCHIVE"
echo "PAIR_SHA256=$(awk '{print $1}' "$ARCHIVE.sha256")"
echo "STATUS=PASS_RUN${RUN_NO}_PAIR_ARCHIVED"
