#!/usr/bin/env bash
# HANFIS paired runner v4.2.2 -- NodePort, >=5-minute workload, node utilization,
# external Prometheus, and fail-closed reproducibility gates.
set -euo pipefail

if [ "$#" -ne 2 ]; then echo "Usage: $0 RUN_NUMBER on-off|off-on" >&2; exit 2; fi

RUN_NO="$1"
ORDER="${2,,}"
RUN_ATTEMPT="${RUN_ATTEMPT:-1}"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SERVER_COLLECTOR="${SERVER_COLLECTOR:-$SCRIPT_DIR/server_collector_v4.sh}"
CLIENT_COLLECTOR="${CLIENT_COLLECTOR:-$SCRIPT_DIR/jetson_capture_v4.sh}"
JETSON_HOST="${JETSON_HOST:-jetson@10.176.68.96}"
TARGET_URL="${TARGET_URL:-http://10.176.68.126:30080/}"
LOCAL_NODEPORT_URL="${LOCAL_NODEPORT_URL:-http://127.0.0.1:30080/}"
NODEPORT_SERVICE="${NODEPORT_SERVICE:-p0-baseline-nodeport-v4}"
NAMESPACE="${NAMESPACE:-hanfis-research}"
GATEWAY_CONTAINER="${GATEWAY_CONTAINER:-hanfis-nodeport-gateway-v4}"
EXPECTED_TARGET_PORT="${EXPECTED_TARGET_PORT:-8080}"
EXPECTED_NODE_PORT="${EXPECTED_NODE_PORT:-30080}"
REMOTE_SCRIPT="${REMOTE_SCRIPT:-/home/jetson/hanfis/scripts/jetson_capture_v4.sh}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV4}"
REQUESTS="${REQUESTS:-1500}"
REQUEST_INTERVAL_SECONDS="${REQUEST_INTERVAL_SECONDS:-0.21}"
SERVER_INTERVAL_SECONDS="${SERVER_INTERVAL_SECONDS:-5}"
PROM_URL="${PROM_URL:-http://127.0.0.1:29090}"
SERVER_INSTANCE_REGEX="${SERVER_INSTANCE_REGEX:-desktop-worker.*}"
NODE_RATE_WINDOW_SECONDS="${NODE_RATE_WINDOW_SECONDS:-30}"
EXPECTED_ENVIRONMENT_NAME="${EXPECTED_ENVIRONMENT_NAME:-anfis}"
WASHOUT_SECONDS="${WASHOUT_SECONDS:-120}"
START_DELAY_SECONDS="${START_DELAY_SECONDS:-20}"
CONFIRM_RUN17="${CONFIRM_RUN17:-NO}"
PAIR_ID="run${RUN_NO}-${ORDER}-$(date +%Y%m%dT%H%M%S%z)"
PAIR_DIR="$OUTPUT_ROOT/$PAIR_ID"
CONTROL_DIR=$(mktemp -d /tmp/hanfis-ssh.XXXXXX)
CONTROL_PATH="$CONTROL_DIR/control"

case "$ORDER" in on-off) FIRST=on; SECOND=off;; off-on) FIRST=off; SECOND=on;; *) echo "Order must be on-off or off-on" >&2; exit 2;; esac
[[ "$RUN_NO" =~ ^[0-9]+$ ]] || { echo "RUN_NUMBER must be a non-negative integer" >&2; exit 2; }
[[ "$RUN_ATTEMPT" =~ ^[1-9][0-9]*$ ]] || { echo "RUN_ATTEMPT must be a positive integer" >&2; exit 2; }
if [ "$RUN_NO" = 17 ] && [ "$CONFIRM_RUN17" != YES_RUN17 ]; then
  echo "STATUS=HOLD_RUN17_NOT_AUTHORIZED"
  echo "Run 17 requires CONFIRM_RUN17=YES_RUN17 after all preregistration gates pass."
  exit 1
fi

ACTUAL_ENVIRONMENT_NAME=$(basename "${VIRTUAL_ENV:-unknown}")
if [ "$ACTUAL_ENVIRONMENT_NAME" != "$EXPECTED_ENVIRONMENT_NAME" ]; then
  echo "ENVIRONMENT_NAME=$ACTUAL_ENVIRONMENT_NAME"
  echo "STATUS=HOLD_WRONG_PYTHON_ENVIRONMENT"
  exit 1
fi

WORKLOAD_SPAN_SECONDS=$(awk -v n="$REQUESTS" -v i="$REQUEST_INTERVAL_SECONDS" 'BEGIN {printf "%.3f",(n-1)*i}')
awk -v span="$WORKLOAD_SPAN_SECONDS" 'BEGIN {exit !(span>=300)}' || { echo "STATUS=HOLD_WORKLOAD_UNDER_300S"; exit 1; }
SERVER_SAMPLES=$(awk -v span="$WORKLOAD_SPAN_SECONDS" -v i="$SERVER_INTERVAL_SECONDS" 'BEGIN {print int(span/i)+2}')

for required in kubectl docker curl ssh scp sha256sum tar awk mktemp date tee find python3; do command -v "$required" >/dev/null 2>&1 || { echo "Missing command: $required" >&2; exit 1; }; done
for script in "$SERVER_COLLECTOR" "$CLIENT_COLLECTOR"; do [ -f "$script" ] || { echo "Missing script: $script" >&2; exit 1; }; bash -n "$script"; done

cleanup() { ssh -S "$CONTROL_PATH" -O exit "$JETSON_HOST" >/dev/null 2>&1 || true; rm -f "$CONTROL_PATH"; rmdir "$CONTROL_DIR" >/dev/null 2>&1 || true; }
trap cleanup EXIT
last_value() { awk -F= -v key="$1" '$1==key {v=$2} END{print v}' "$2"; }
http_code() { curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "$1"; }

preflight_nodeport() {
  local service_type target_port node_port slice_json classic_json slice_endpoints classic_endpoints endpoints gateway_state local_code remote_code attempt
  service_type=$(kubectl get service "$NODEPORT_SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.type}')
  target_port=$(kubectl get service "$NODEPORT_SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].targetPort}')
  node_port=$(kubectl get service "$NODEPORT_SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}')
  for attempt in 1 2 3; do
    slice_json=$(kubectl get endpointslice -n "$NAMESPACE" -l "kubernetes.io/service-name=$NODEPORT_SERVICE" -o json 2>/dev/null || printf '{"items":[]}')
    slice_endpoints=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(len(e.get("addresses",[])) for s in d.get("items",[]) for e in s.get("endpoints",[]) if e.get("conditions",{}).get("ready") is not False))' <<<"$slice_json")
    classic_json=$(kubectl get endpoints "$NODEPORT_SERVICE" -n "$NAMESPACE" -o json 2>/dev/null || printf '{"subsets":[]}')
    classic_endpoints=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(len(s.get("addresses",[])) for s in d.get("subsets",[])))' <<<"$classic_json")
    if [ "$slice_endpoints" -ge "$classic_endpoints" ]; then endpoints="$slice_endpoints"; else endpoints="$classic_endpoints"; fi
    gateway_state=$(docker inspect -f '{{.State.Running}}' "$GATEWAY_CONTAINER" 2>/dev/null || echo false)
    local_code=$(http_code "$LOCAL_NODEPORT_URL" || true)
    remote_code=$(ssh -S "$CONTROL_PATH" "$JETSON_HOST" "curl -sS --max-time 10 -o /dev/null -w '%{http_code}' '$TARGET_URL'" || true)
    printf 'NODEPORT_PREFLIGHT_ATTEMPT=%s/3\nSERVICE_TYPE=%s\nTARGET_PORT=%s\nNODE_PORT=%s\nENDPOINTSLICE_READY_ENDPOINTS=%s\nCLASSIC_READY_ENDPOINTS=%s\nEFFECTIVE_ENDPOINTS=%s\nGATEWAY_RUNNING=%s\nLOCAL_NODEPORT_HTTP=%s\nJETSON_NODEPORT_HTTP=%s\n' "$attempt" "$service_type" "$target_port" "$node_port" "$slice_endpoints" "$classic_endpoints" "$endpoints" "$gateway_state" "$local_code" "$remote_code"
    if [ "$service_type" = NodePort ] && [ "$target_port" = "$EXPECTED_TARGET_PORT" ] && [ "$node_port" = "$EXPECTED_NODE_PORT" ] && [ "$endpoints" -ge 1 ] && [ "$gateway_state" = true ] && [ "$local_code" = 200 ] && [ "$remote_code" = 200 ]; then
      echo 'NODEPORT_METADATA_AND_TRAFFIC_GATE=PASS'
      return 0
    fi
    [ "$attempt" -eq 3 ] || sleep 2
  done
  echo 'NODEPORT_METADATA_AND_TRAFFIC_GATE=HOLD'
  return 1
}

preflight_observer() {
  local ready targets cpu_series
  if ready=$(curl -fsS --max-time 5 "$PROM_URL/-/ready" 2>/dev/null); then
    printf 'EXTERNAL_PROMETHEUS_READY=%s\n' "$ready"
  else
    echo "EXTERNAL_PROMETHEUS_READY=NO"
    return 1
  fi
  targets=$(curl -fsS --get --max-time 10 "$PROM_URL/api/v1/query" --data-urlencode 'query=count(up{job=~"external-cadvisor-.*"} == 1)' | python3 -c 'import json,sys; r=json.load(sys.stdin).get("data",{}).get("result",[]); print(r[0]["value"][1] if r else "0")')
  cpu_series=$(curl -fsS --get --max-time 10 "$PROM_URL/api/v1/query" --data-urlencode 'query=count(container_cpu_usage_seconds_total)' | python3 -c 'import json,sys; r=json.load(sys.stdin).get("data",{}).get("result",[]); print(r[0]["value"][1] if r else "0")')
  printf 'EXTERNAL_ACTIVE_TARGETS=%s/2\nEXTERNAL_CPU_COUNTER_SERIES=%s\n' "$targets" "$cpu_series"
  [ "$targets" = 2 ] && awk -v n="$cpu_series" 'BEGIN{exit !(n>0)}'
}

washout() { local elapsed=0 step; while [ "$elapsed" -lt "$WASHOUT_SECONDS" ]; do step=30; [ $((WASHOUT_SECONDS-elapsed)) -lt 30 ] && step=$((WASHOUT_SECONDS-elapsed)); echo "WASHOUT_REMAINING=$((WASHOUT_SECONDS-elapsed))s"; sleep "$step"; elapsed=$((elapsed+step)); done; }

set_condition() {
  local condition="$1" p0_ready monitoring_ready code
  echo "=== SET MONITORING ${condition^^} ==="
  if [ "$condition" = on ]; then
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
    kubectl wait --for=delete pod --all -n monitoring --timeout=180s
  fi
  washout
  p0_ready=$(kubectl get pods -n "$NAMESPACE" --no-headers | awk '$1~/^p0-baseline-/ && $2=="1/1" && $3=="Running"{n++} END{print n+0}')
  monitoring_ready=$(kubectl get pods -n monitoring --no-headers 2>/dev/null | awk '$3=="Running" && ($2=="1/1" || $2=="2/2"){n++} END{print n+0}')
  code=$(http_code "$LOCAL_NODEPORT_URL" || true)
  echo "P0_READY=$p0_ready/2"; echo "MONITORING_READY=$monitoring_ready"; echo "NODEPORT_HTTP=$code"
  [ "$p0_ready" -eq 2 ] && [ "$code" = 200 ] || return 1
  if [ "$condition" = on ]; then [ "$monitoring_ready" -eq 5 ]; else [ "$monitoring_ready" -eq 0 ]; fi
}

run_condition() {
  local condition="$1" condition_dir="$PAIR_DIR/$1" server_dir server_log client_dir client_log start_epoch server_pid server_rc client_rc server_status client_status monitoring_rows settlement_gate snapshot_gate rate_gate window_status utilization_status utilization_regime utilization_samples utilization_mean utilization_p95 utilization_max remote_output post_p0_ready post_monitoring_ready post_http expected_monitoring_ready
  server_dir="$condition_dir/server"; client_dir="$condition_dir/client"; server_log="$condition_dir/server_collector.log"; client_log="$condition_dir/client_collector.log"
  mkdir -p "$server_dir" "$client_dir"
  start_epoch=$(( $(date -u +%s) + START_DELAY_SECONDS ))
  set +e
  PROM_URL="$PROM_URL" SAMPLES="$SERVER_SAMPLES" INTERVAL_SECONDS="$SERVER_INTERVAL_SECONDS" SERVER_INSTANCE_REGEX="$SERVER_INSTANCE_REGEX" NODE_RATE_WINDOW_SECONDS="$NODE_RATE_WINDOW_SECONDS" "$SERVER_COLLECTOR" "$RUN_NO" "$condition" "$start_epoch" "$server_dir" 2>&1 | tee "$server_log" & server_pid=$!
  ssh -S "$CONTROL_PATH" "$JETSON_HOST" "REQUESTS='$REQUESTS' REQUEST_INTERVAL_SECONDS='$REQUEST_INTERVAL_SECONDS' '$REMOTE_SCRIPT' '$RUN_NO' '$condition' '$start_epoch' '$TARGET_URL'" 2>&1 | tee "$client_log"; client_rc=${PIPESTATUS[0]}
  wait "$server_pid"; server_rc=$?; set -e
  post_p0_ready=$(kubectl get pods -n "$NAMESPACE" --no-headers | awk '$1~/^p0-baseline-/ && $2=="1/1" && $3=="Running"{n++} END{print n+0}')
  post_monitoring_ready=$(kubectl get pods -n monitoring --no-headers 2>/dev/null | awk '$3=="Running" && ($2=="1/1" || $2=="2/2"){n++} END{print n+0}')
  post_http=$(http_code "$LOCAL_NODEPORT_URL" || true)
  if [ "$condition" = on ]; then expected_monitoring_ready=5; else expected_monitoring_ready=0; fi
  echo "POST_P0_READY=$post_p0_ready/2"; echo "POST_MONITORING_READY=$post_monitoring_ready/$expected_monitoring_ready"; echo "POST_NODEPORT_HTTP=$post_http"
  server_status=$(last_value SERVER_STATUS "$server_log"); client_status=$(last_value CLIENT_STATUS "$client_log"); monitoring_rows=$(last_value SERVER_MONITORING_ROWS "$server_log")
  settlement_gate=$(last_value SERVER_BOUNDARY_SETTLEMENT "$server_log"); snapshot_gate=$(last_value SERVER_SNAPSHOT_EXACT_CROSSCHECK "$server_log"); rate_gate=$(last_value SERVER_RATE_INCREASE_COHERENCE "$server_log"); window_status=$(last_value SERVER_WINDOW_ESTIMATOR_DIFFERENCE "$server_log")
  utilization_status=$(last_value SERVER_NODE_UTILIZATION_STATUS "$server_log"); utilization_regime=$(last_value SERVER_UTILIZATION_REGIME "$server_log"); utilization_samples=$(last_value SERVER_UTILIZATION_SAMPLES "$server_log"); utilization_mean=$(last_value SERVER_CPU_UTILIZATION_PERCENT_MEAN "$server_log"); utilization_p95=$(last_value SERVER_CPU_UTILIZATION_PERCENT_P95 "$server_log"); utilization_max=$(last_value SERVER_CPU_UTILIZATION_PERCENT_MAX "$server_log")
  {
    echo "RUN=$RUN_NO"; echo "RUN_ATTEMPT=$RUN_ATTEMPT"; echo "CONDITION=${condition^^}"; echo "ORDER=${ORDER^^}"; echo "PROTOCOL=external-prometheus-v4.2.2-retained-series-aware"; echo "ACCESS_PATH=JETSON_TO_WINDOWS_DOCKER_GATEWAY_TO_NODEPORT"; echo "START_EPOCH_UTC=$start_epoch"; echo "JETSON_HOST=$JETSON_HOST"; echo "TARGET_URL=$TARGET_URL"; echo "LOCAL_NODEPORT_URL=$LOCAL_NODEPORT_URL"; echo "PROM_URL=$PROM_URL"; echo "NODEPORT_SERVICE=$NODEPORT_SERVICE"; echo "GATEWAY_CONTAINER=$GATEWAY_CONTAINER"; echo "ENVIRONMENT_NAME=$ACTUAL_ENVIRONMENT_NAME"; echo "SERVER_INSTANCE_REGEX=$SERVER_INSTANCE_REGEX"; echo "NODE_RATE_WINDOW_SECONDS=$NODE_RATE_WINDOW_SECONDS"; echo "REQUESTS=$REQUESTS"; echo "REQUEST_INTERVAL_SECONDS=$REQUEST_INTERVAL_SECONDS"; echo "WORKLOAD_SPAN_SECONDS=$WORKLOAD_SPAN_SECONDS"; echo "POST_P0_READY=$post_p0_ready"; echo "POST_MONITORING_READY=$post_monitoring_ready"; echo "EXPECTED_POST_MONITORING_READY=$expected_monitoring_ready"; echo "POST_NODEPORT_HTTP=$post_http"; echo "SERVER_PROCESS_RC=$server_rc"; echo "CLIENT_TRANSPORT_RC=$client_rc"; echo "SERVER_STATUS=${server_status:-MISSING}"; echo "CLIENT_STATUS=${client_status:-MISSING}"; echo "SERVER_MONITORING_ROWS=${monitoring_rows:-MISSING}"; echo "BOUNDARY_SETTLEMENT=${settlement_gate:-MISSING}"; echo "SNAPSHOT_EXACT_CROSSCHECK=${snapshot_gate:-MISSING}"; echo "RATE_INCREASE_COHERENCE=${rate_gate:-MISSING}"; echo "WINDOW_ESTIMATOR_DIFFERENCE=${window_status:-MISSING}"; echo "NODE_UTILIZATION_STATUS=${utilization_status:-MISSING}"; echo "UTILIZATION_SAMPLES=${utilization_samples:-MISSING}"; echo "UTILIZATION_REGIME=${utilization_regime:-MISSING}"; echo "CPU_UTILIZATION_PERCENT_MEAN=${utilization_mean:-MISSING}"; echo "CPU_UTILIZATION_PERCENT_P95=${utilization_p95:-MISSING}"; echo "CPU_UTILIZATION_PERCENT_MAX=${utilization_max:-MISSING}"
  } > "$condition_dir/condition-manifest.txt"
  [ "$post_p0_ready" -eq 2 ] && [ "$post_monitoring_ready" -eq "$expected_monitoring_ready" ] && [ "$post_http" = 200 ] || { echo "STATUS=HOLD_POST_CONDITION_TREATMENT_GATE" >> "$condition_dir/condition-manifest.txt"; return 1; }
  [ "$server_rc" -eq 0 ] && [ "$server_status" = PASS ] || { echo "STATUS=HOLD_SERVER_RESOURCE_GATE" >> "$condition_dir/condition-manifest.txt"; return 1; }
  [ "$settlement_gate" = PASS ] && [ "$snapshot_gate" = PASS ] && [ "$rate_gate" = PASS ] && [ "$window_status" = RECORDED_NOT_GATED ] || { echo "STATUS=HOLD_NUMERICAL_CROSSCHECK_GATE" >> "$condition_dir/condition-manifest.txt"; return 1; }
  [ "$utilization_status" = PASS ] && [ "$utilization_samples" = "$SERVER_SAMPLES" ] && [ -n "$utilization_regime" ] || { echo "STATUS=HOLD_NODE_UTILIZATION_GATE" >> "$condition_dir/condition-manifest.txt"; return 1; }
  [ "$client_rc" -eq 0 ] && [ "$client_status" = PASS ] || { echo "STATUS=HOLD_CLIENT_GATE" >> "$condition_dir/condition-manifest.txt"; return 1; }
  remote_output=$(last_value OUTPUT "$client_log"); [ -n "$remote_output" ] || { echo "STATUS=HOLD_CLIENT_OUTPUT_MISSING" >> "$condition_dir/condition-manifest.txt"; return 1; }
  ssh -S "$CONTROL_PATH" "$JETSON_HOST" "tar -C '$remote_output' -czf - ." | tar -C "$client_dir" -xzf -
  (cd "$server_dir" && sha256sum -c sha256.txt); (cd "$client_dir" && sha256sum -c sha256.txt)
  echo "STATUS=LOCKED_VALID_CONDITION" >> "$condition_dir/condition-manifest.txt"
  (cd "$condition_dir" && sha256sum condition-manifest.txt > condition-manifest.sha256)
}

mkdir -p "$OUTPUT_ROOT"; [ ! -e "$PAIR_DIR" ] || { echo "Refusing to overwrite $PAIR_DIR" >&2; exit 1; }; mkdir -p "$PAIR_DIR"
echo "=== OPEN PERSISTENT SSH ==="; ssh -M -S "$CONTROL_PATH" -o ControlPersist=1800 -fN "$JETSON_HOST"
ssh -S "$CONTROL_PATH" "$JETSON_HOST" 'mkdir -p "$HOME/hanfis/scripts"'
scp -o ControlPath="$CONTROL_PATH" "$CLIENT_COLLECTOR" "$JETSON_HOST:$REMOTE_SCRIPT"
ssh -S "$CONTROL_PATH" "$JETSON_HOST" "chmod +x '$REMOTE_SCRIPT'"
echo "=== NODEPORT PREFLIGHT ==="; preflight_nodeport || { echo "STATUS=HOLD_NODEPORT_PREFLIGHT"; exit 1; }
echo "=== EXTERNAL OBSERVER PREFLIGHT ==="; preflight_observer || { echo "STATUS=HOLD_EXTERNAL_OBSERVER_PREFLIGHT"; exit 1; }
set_condition "$FIRST" || { echo "STATUS=HOLD_${FIRST^^}_TREATMENT"; exit 1; }
run_condition "$FIRST" || { echo "STATUS=HOLD_${FIRST^^}_CONDITION"; exit 1; }
set_condition "$SECOND" || { echo "STATUS=HOLD_${SECOND^^}_TREATMENT"; exit 1; }
run_condition "$SECOND" || { echo "STATUS=HOLD_${SECOND^^}_CONDITION"; exit 1; }

{
  echo "RUN=$RUN_NO"; echo "RUN_ATTEMPT=$RUN_ATTEMPT"; echo "ORDER=${ORDER^^}"; echo "PROTOCOL=external-prometheus-v4.2.2-retained-series-aware"; echo "PAIR_ID=$PAIR_ID"; echo "ACCESS_PATH=JETSON_TO_WINDOWS_DOCKER_GATEWAY_TO_NODEPORT"; echo "TARGET_URL=$TARGET_URL"; echo "PROM_URL=$PROM_URL"; echo "ENVIRONMENT_NAME=$ACTUAL_ENVIRONMENT_NAME"; echo "SERVER_INSTANCE_REGEX=$SERVER_INSTANCE_REGEX"; echo "NODE_RATE_WINDOW_SECONDS=$NODE_RATE_WINDOW_SECONDS"; echo "WORKLOAD_SPAN_SECONDS=$WORKLOAD_SPAN_SECONDS"; echo "FIRST_CONDITION=${FIRST^^}"; echo "SECOND_CONDITION=${SECOND^^}"; echo "STATUS=LOCKED_VALID_PAIR"
} > "$PAIR_DIR/pair-manifest.txt"
(cd "$PAIR_DIR" && find . -type f ! -name pair-content.sha256 -print0 | sort -z | xargs -0 sha256sum > pair-content.sha256)
ARCHIVE="$OUTPUT_ROOT/O5-V4-${PAIR_ID}-pair.tar.gz"; tar -czf "$ARCHIVE" -C "$OUTPUT_ROOT" "$PAIR_ID"; sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
echo "PAIR_DIR=$PAIR_DIR"; echo "PAIR_ARCHIVE=$ARCHIVE"; echo "STATUS=PASS_RUN${RUN_NO}_PAIR_ARCHIVED"
