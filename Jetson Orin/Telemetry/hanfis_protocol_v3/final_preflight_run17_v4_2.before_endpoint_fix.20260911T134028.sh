#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="${PROJECT:-/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV4}"
FREEZE_ARCHIVE="${FREEZE_ARCHIVE:-$PROJECT/STAGE3C_V4_2_FREEZE_20260911T130752+0700.tar.gz}"
JETSON_HOST="${JETSON_HOST:-jetson@10.176.68.96}"
TARGET_URL="${TARGET_URL:-http://10.176.68.126:30080/}"
LOCAL_NODEPORT_URL="${LOCAL_NODEPORT_URL:-http://127.0.0.1:30080/}"
PROM_URL="${PROM_URL:-http://127.0.0.1:29090}"
NAMESPACE="${NAMESPACE:-hanfis-research}"
NODEPORT_SERVICE="${NODEPORT_SERVICE:-p0-baseline-nodeport-v4}"
GATEWAY_CONTAINER="${GATEWAY_CONTAINER:-hanfis-nodeport-gateway-v4}"
EXPECTED_TARGET_PORT="${EXPECTED_TARGET_PORT:-8080}"
EXPECTED_NODE_PORT="${EXPECTED_NODE_PORT:-30080}"
MAX_CLOCK_SKEW_SECONDS="${MAX_CLOCK_SKEW_SECONDS:-5}"
MIN_FREE_GIB="${MIN_FREE_GIB:-5}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PREREG="$SCRIPT_DIR/PREREGISTRATION_RUN17_STAGE3C_V4_2.md"
STAMP="$(date +%Y%m%dT%H%M%S%z)"
OUT="$PROJECT/run17_final_preflight_$STAMP"
LOG="$PROJECT/run17_final_preflight_$STAMP.log"
CONTROL_DIR="$(mktemp -d /tmp/hanfis-run17-preflight-ssh.XXXXXX)"
CONTROL_PATH="$CONTROL_DIR/control"

cleanup() {
    ssh -S "$CONTROL_PATH" -O exit "$JETSON_HOST" >/dev/null 2>&1 || true
    rm -f -- "$CONTROL_PATH"
    rmdir -- "$CONTROL_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

fail() {
    printf 'STATUS=HOLD_RUN17_FINAL_PREFLIGHT\nHOLD_REASON=%s\nRUN17_EXECUTED=NO\n' "$1" | tee -a "$LOG" >&2
    exit 1
}

pass() { printf 'PASS %s\n' "$1" | tee -a "$LOG"; }

abs_diff() {
    awk -v a="$1" -v b="$2" 'BEGIN {d=a-b; if(d<0)d=-d; print d}'
}

for tool in bash kubectl docker curl ssh sha256sum tar python3 awk date df find sort cmp tee grep tr tail xargs powershell.exe mktemp rmdir; do
    command -v "$tool" >/dev/null 2>&1 || { echo "Missing command: $tool"; exit 1; }
done

[[ -d "$PROJECT" ]] || { echo "STATUS=HOLD_PROJECT_NOT_FOUND"; exit 1; }
cd "$PROJECT"
: > "$LOG"
[[ -d "$OUTPUT_ROOT" ]] || fail OUTPUT_ROOT_NOT_FOUND

printf '=== RUN 17 FINAL PREFLIGHT STAGE3C V4.2 ===\n' | tee -a "$LOG"
printf 'RUN=17\nORDER=ON-OFF\nRUN17_EXECUTED=NO\nPROJECT=%s\n' "$PROJECT" | tee -a "$LOG"

if [[ "${VIRTUAL_ENV:-}" != */anfis ]]; then
    [[ -f /home/hafiz/.venvs/anfis/bin/activate ]] || fail ANFIS_ENVIRONMENT_NOT_FOUND
    # shellcheck disable=SC1091
    source /home/hafiz/.venvs/anfis/bin/activate
fi
[[ "$(basename -- "${VIRTUAL_ENV:-missing}")" == anfis ]] || fail WRONG_PYTHON_ENVIRONMENT
pass ENVIRONMENT_ANFIS

[[ -f "$FREEZE_ARCHIVE" ]] || fail FREEZE_ARCHIVE_NOT_FOUND
[[ -f "$FREEZE_ARCHIVE.sha256" ]] || fail FREEZE_ARCHIVE_SHA256_NOT_FOUND
(cd "$(dirname -- "$FREEZE_ARCHIVE")" && sha256sum -c "$(basename -- "$FREEZE_ARCHIVE").sha256") | tee -a "$LOG" || fail FREEZE_ARCHIVE_SHA256_FAILED
tar -tzf "$FREEZE_ARCHIVE" >/dev/null || fail FREEZE_ARCHIVE_INVALID
FREEZE_MANIFEST="$(tar -xOf "$FREEZE_ARCHIVE" ./FREEZE_MANIFEST.txt)"
grep -qx 'PREREGISTRATION_STATUS=FROZEN' <<<"$FREEZE_MANIFEST" || fail FREEZE_PREREGISTRATION_NOT_FROZEN
grep -qx 'RUN17_EXECUTED=NO' <<<"$FREEZE_MANIFEST" || fail FREEZE_RUN17_STATE_INVALID
grep -qx 'STATUS=PASS_STAGE3C_V4_2_PREREGISTRATION_FREEZE' <<<"$FREEZE_MANIFEST" || fail FREEZE_STATUS_INVALID
pass FREEZE_ARCHIVE_AND_MANIFEST

required_code=(run_pair_v4.sh jetson_capture_v4.sh server_collector_v4.sh server_collector_v4.py test_server_collector_v4_mock.py test_run_pair_v4_static.sh run_stage3c_v4_2_live_dry.sh)
for file in "${required_code[@]}"; do
    [[ -f "$PROJECT/$file" ]] || fail "INSTALLED_CODE_MISSING_${file}"
    tar -xOf "$FREEZE_ARCHIVE" "./code/$file" | cmp -s - "$PROJECT/$file" || fail "INSTALLED_CODE_DIFFERS_FROM_FREEZE_${file}"
done
bash -n run_pair_v4.sh jetson_capture_v4.sh server_collector_v4.sh test_run_pair_v4_static.sh run_stage3c_v4_2_live_dry.sh || fail SHELL_SYNTAX_FAILED
python3 -m py_compile server_collector_v4.py test_server_collector_v4_mock.py || fail PYTHON_SYNTAX_FAILED
grep -q 'CONFIRM_RUN17' run_pair_v4.sh || fail RUN17_AUTHORIZATION_GATE_MISSING
pass INSTALLED_CODE_MATCHES_FREEZE

EXISTING_RUN17="$(find "$OUTPUT_ROOT" -maxdepth 1 -mindepth 1 -iname 'run17-*' -print -quit 2>/dev/null || true)"
[[ -z "$EXISTING_RUN17" ]] || fail "RUN17_OUTPUT_ALREADY_EXISTS_${EXISTING_RUN17}"
pass RUN17_OUTPUT_ABSENT

ssh -M -S "$CONTROL_PATH" -o ControlPersist=600 -fN "$JETSON_HOST" || fail JETSON_SSH_CONTROL_CONNECTION_FAILED
pass JETSON_SSH_CONTROL_CONNECTION

SERVICE_TYPE="$(kubectl get service "$NODEPORT_SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.type}')"
TARGET_PORT="$(kubectl get service "$NODEPORT_SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].targetPort}')"
NODE_PORT="$(kubectl get service "$NODEPORT_SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}')"
ENDPOINTS="$(kubectl get endpointslice -n "$NAMESPACE" -l "kubernetes.io/service-name=$NODEPORT_SERVICE" -o jsonpath='{range .items[*].endpoints[*]}{range .addresses[*]}{.}{"\n"}{end}{end}' | awk 'NF{n++} END{print n+0}')"
GATEWAY_RUNNING="$(docker inspect -f '{{.State.Running}}' "$GATEWAY_CONTAINER" 2>/dev/null || echo false)"
LOCAL_HTTP="$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$LOCAL_NODEPORT_URL" || true)"
REMOTE_HTTP="$(ssh -S "$CONTROL_PATH" "$JETSON_HOST" "curl -sS --max-time 10 -o /dev/null -w '%{http_code}' '$TARGET_URL'" || true)"
printf 'SERVICE_TYPE=%s\nTARGET_PORT=%s\nNODE_PORT=%s\nENDPOINTS=%s\nGATEWAY_RUNNING=%s\nLOCAL_NODEPORT_HTTP=%s\nJETSON_NODEPORT_HTTP=%s\n' "$SERVICE_TYPE" "$TARGET_PORT" "$NODE_PORT" "$ENDPOINTS" "$GATEWAY_RUNNING" "$LOCAL_HTTP" "$REMOTE_HTTP" | tee -a "$LOG"
[[ "$SERVICE_TYPE" == NodePort && "$TARGET_PORT" == "$EXPECTED_TARGET_PORT" && "$NODE_PORT" == "$EXPECTED_NODE_PORT" && "$ENDPOINTS" -ge 1 && "$GATEWAY_RUNNING" == true && "$LOCAL_HTTP" == 200 && "$REMOTE_HTTP" == 200 ]] || fail NODEPORT_PATH_FAILED
pass NODEPORT_PATH

INTERNAL_JSON="$(kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus -o json)"
INTERNAL_STATUS="$(python3 -c 'import json,sys; d=json.load(sys.stdin); pods=d.get("items",[]); ok=len(pods)==1 and pods[0].get("status",{}).get("phase")=="Running" and all(x.get("ready") for x in pods[0].get("status",{}).get("containerStatuses",[])) and len(pods[0].get("status",{}).get("containerStatuses",[]))>0; print("PASS" if ok else "FAIL")' <<<"$INTERNAL_JSON")"
printf 'INTERNAL_PROMETHEUS=%s\n' "$INTERNAL_STATUS" | tee -a "$LOG"
[[ "$INTERNAL_STATUS" == PASS ]] || fail INTERNAL_PROMETHEUS_NOT_READY
pass INTERNAL_PROMETHEUS

READY="$(curl -fsS --max-time 5 "$PROM_URL/-/ready" || true)"
[[ "$READY" == *Ready* ]] || fail EXTERNAL_PROMETHEUS_NOT_READY
TARGET_JSON="$(curl -fsS --max-time 10 "$PROM_URL/api/v1/targets")" || fail EXTERNAL_TARGET_QUERY_FAILED
TARGET_DIAGNOSTIC="$(python3 -c 'import json,sys; d=json.load(sys.stdin); t=[x for x in d.get("data",{}).get("activeTargets",[]) if x.get("labels",{}).get("job","").startswith("external-cadvisor-")]; good=[x for x in t if x.get("health")=="up" and not x.get("lastError")]; print(f"DISCOVERED={len(t)} HEALTHY={len(good)}"); raise SystemExit(0 if len(t)==2 and len(good)==2 else 1)' <<<"$TARGET_JSON")" || fail EXTERNAL_TARGET_HEALTH_FAILED
printf 'EXTERNAL_PROMETHEUS_READY=%s\nEXTERNAL_TARGETS=%s\n' "$READY" "$TARGET_DIAGNOSTIC" | tee -a "$LOG"
pass EXTERNAL_PROMETHEUS_2_OF_2

WSL_EPOCH="$(date -u +%s)"
JETSON_EPOCH="$(ssh -S "$CONTROL_PATH" "$JETSON_HOST" 'date -u +%s')" || fail JETSON_CLOCK_UNAVAILABLE
WINDOWS_EPOCH="$(powershell.exe -NoProfile -Command '[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()' 2>/dev/null | tr -d '\r' | tail -n 1)" || fail WINDOWS_CLOCK_UNAVAILABLE
CONTROL_EPOCH="$(docker exec desktop-control-plane date -u +%s)" || fail CONTROL_PLANE_CLOCK_UNAVAILABLE
WORKER_EPOCH="$(docker exec desktop-worker date -u +%s)" || fail WORKER_CLOCK_UNAVAILABLE
for item in "JETSON:$JETSON_EPOCH" "WINDOWS:$WINDOWS_EPOCH" "CONTROL_PLANE:$CONTROL_EPOCH" "WORKER:$WORKER_EPOCH"; do
    NAME="${item%%:*}"; VALUE="${item#*:}"; SKEW="$(abs_diff "$WSL_EPOCH" "$VALUE")"
    printf '%s_EPOCH=%s %s_SKEW_SECONDS=%s\n' "$NAME" "$VALUE" "$NAME" "$SKEW" | tee -a "$LOG"
    awk -v x="$SKEW" -v m="$MAX_CLOCK_SKEW_SECONDS" 'BEGIN{exit !(x<=m)}' || fail "CLOCK_SKEW_${NAME}_${SKEW}_SECONDS"
done
pass CLOCK_SYNCHRONIZATION

FREE_KIB="$(df -Pk "$OUTPUT_ROOT" | awk 'NR==2{print $4}')"
FREE_GIB="$(awk -v k="$FREE_KIB" 'BEGIN{printf "%.2f",k/1024/1024}')"
printf 'OUTPUT_ROOT=%s\nFREE_SPACE_GIB=%s\n' "$OUTPUT_ROOT" "$FREE_GIB" | tee -a "$LOG"
awk -v g="$FREE_GIB" -v m="$MIN_FREE_GIB" 'BEGIN{exit !(g>=m)}' || fail INSUFFICIENT_FREE_SPACE
pass STORAGE_CAPACITY

mkdir -p "$OUT"
cp -p -- "$PREREG" "$OUT/"
cp -p -- "$LOG" "$OUT/preflight.log"
printf '%s\n' "$FREEZE_MANIFEST" > "$OUT/freeze_manifest_snapshot.txt"
kubectl get pods -A -o wide > "$OUT/kubernetes_pods_snapshot.txt"
docker ps --no-trunc > "$OUT/docker_snapshot.txt"
printf 'RUN=17\nORDER=ON-OFF\nPROTOCOL=external-prometheus-v4.2-utilization-gated\nFREEZE_ARCHIVE=%s\nENVIRONMENT_NAME=anfis\nNODEPORT_HTTP=200\nJETSON_NODEPORT_HTTP=200\nEXTERNAL_ACTIVE_TARGETS=2/2\nMAX_CLOCK_SKEW_SECONDS=%s\nFREE_SPACE_GIB=%s\nAUTHORIZATION_STATUS=NOT_GRANTED\nRUN17_EXECUTED=NO\nSTATUS=PASS_RUN17_FINAL_PREFLIGHT\n' "$FREEZE_ARCHIVE" "$MAX_CLOCK_SKEW_SECONDS" "$FREE_GIB" > "$OUT/PREFLIGHT_MANIFEST.txt"
(cd "$OUT" && find . -type f ! -name PREFLIGHT_SHA256.txt -print0 | sort -z | xargs -0 sha256sum > PREFLIGHT_SHA256.txt && sha256sum -c PREFLIGHT_SHA256.txt) | tee -a "$LOG" || fail PREFLIGHT_EVIDENCE_SHA256_FAILED
ARCHIVE="$PROJECT/RUN17_FINAL_PREFLIGHT_$STAMP.tar.gz"
tar -C "$OUT" -czf "$ARCHIVE" .
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
tar -tzf "$ARCHIVE" >/dev/null || fail PREFLIGHT_ARCHIVE_INVALID

printf '\nPREFLIGHT_OUTPUT=%s\nPREFLIGHT_ARCHIVE=%s\nAUTHORIZATION_STATUS=NOT_GRANTED\nRUN17_EXECUTED=NO\nSTATUS=PASS_RUN17_FINAL_PREFLIGHT\n' "$OUT" "$ARCHIVE" | tee -a "$LOG"
printf 'NEXT_COMMAND_HELD=CONFIRM_RUN17=YES_RUN17 ./run_pair_v4.sh 17 on-off\n' | tee -a "$LOG"
