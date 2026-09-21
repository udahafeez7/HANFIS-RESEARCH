#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/hanfis_protocol_v3"
OUTPUT_ROOT="/mnt/c/Research/ANFIS/Jetson Orin/Telemetry/RunsV4"
RUNNER="$PROJECT/run_pair_v4.sh"
RESTORE_REQUIRED=0

restore_monitoring() {
  kubectl scale deployment hanfis-monitoring-kube-pro-operator hanfis-monitoring-kube-state-metrics -n monitoring --replicas=1 >/dev/null
  kubectl scale statefulset prometheus-hanfis-monitoring-kube-pro-prometheus -n monitoring --replicas=1 >/dev/null
  kubectl patch daemonset hanfis-monitoring-prometheus-node-exporter -n monitoring --type=merge -p='{"spec":{"template":{"spec":{"nodeSelector":{"hanfis.monitoring/off":null}}}}}' >/dev/null
  kubectl rollout status deployment/hanfis-monitoring-kube-pro-operator -n monitoring --timeout=180s
  kubectl rollout status deployment/hanfis-monitoring-kube-state-metrics -n monitoring --timeout=180s
  kubectl rollout status daemonset/hanfis-monitoring-prometheus-node-exporter -n monitoring --timeout=180s
  kubectl rollout status statefulset/prometheus-hanfis-monitoring-kube-pro-prometheus -n monitoring --timeout=180s
}

finish() {
  local rc=$?
  trap - EXIT
  if [ "$RESTORE_REQUIRED" -eq 1 ]; then
    echo '=== RESTORE INTERNAL MONITORING TO ON ==='
    restore_monitoring || rc=1
    echo 'MONITORING_RESTORED=YES'
  fi
  if [ "$rc" -ne 0 ]; then
    echo 'RUN17_ATTEMPT2_VALID_PAIR=NO'
    echo 'RUN17_ATTEMPT2_REPEAT_AUTHORIZED=NO'
    echo 'STATUS=HOLD_RUN17_ATTEMPT2'
    echo "FINAL_RC=$rc"
  fi
  exit "$rc"
}
trap finish EXIT

cd "$PROJECT"
source /home/hafiz/.venvs/anfis/bin/activate
[ "$(basename "${VIRTUAL_ENV:-unknown}")" = anfis ] || { echo 'STATUS=HOLD_WRONG_ENVIRONMENT'; exit 1; }
[ -x "$RUNNER" ] || { echo 'STATUS=HOLD_V4_2_2_RUNNER_MISSING'; exit 1; }
grep -Fq 'external-prometheus-v4.2.2-retained-series-aware' "$RUNNER" || { echo 'STATUS=HOLD_WRONG_RUNNER_VERSION'; exit 1; }

FREEZE_ARCHIVE="$(find "$PROJECT" -maxdepth 1 -type f -name 'STAGE3C_V4_2_2_AMENDED_FREEZE_*.tar.gz' -printf '%T@ %p\n' | sort -nr | sed -n '1s/^[^ ]* //p')"
[ -n "$FREEZE_ARCHIVE" ] && [ -f "$FREEZE_ARCHIVE.sha256" ] || { echo 'STATUS=HOLD_AMENDED_FREEZE_MISSING'; exit 1; }
(cd "$PROJECT" && sha256sum -c "$(basename "$FREEZE_ARCHIVE").sha256")

if find "$OUTPUT_ROOT" -maxdepth 1 -type f -name 'O5-V4-run17-on-off-*-pair.tar.gz' -print -quit | grep -q .; then
  echo 'STATUS=HOLD_VALID_RUN17_ARCHIVE_ALREADY_EXISTS'
  exit 1
fi

STAMP="$(date +%Y%m%dT%H%M%S%z)"
CONSOLE_LOG="$PROJECT/run17_attempt2_on_off_console_$STAMP.log"
echo '=== EXECUTE RUN 17 ATTEMPT 2: ON-OFF ==='
echo 'RUN=17'
echo 'RUN_ATTEMPT=2'
echo 'ATTEMPT1_VALID_PAIR=NO'
echo 'REPEAT_BASIS=PREREGISTERED_INSTRUMENTATION_GATE_AMENDMENT_V4_2_2'
RESTORE_REQUIRED=1

set +e
CONFIRM_RUN17=YES_RUN17 RUN_ATTEMPT=2 \
  JETSON_HOST="${JETSON_HOST:-jetson@10.176.68.96}" \
  TARGET_URL="${TARGET_URL:-http://10.176.68.126:30080/}" \
  LOCAL_NODEPORT_URL="${LOCAL_NODEPORT_URL:-http://127.0.0.1:30080/}" \
  PROM_URL="${PROM_URL:-http://127.0.0.1:29090}" \
  OUTPUT_ROOT="$OUTPUT_ROOT" \
  REQUESTS=1500 REQUEST_INTERVAL_SECONDS=0.21 SERVER_INTERVAL_SECONDS=5 WASHOUT_SECONDS=120 \
  "$RUNNER" 17 on-off 2>&1 | tee "$CONSOLE_LOG"
RUN_RC=${PIPESTATUS[0]}
set -e
[ "$RUN_RC" -eq 0 ] || exit "$RUN_RC"

PAIR_ARCHIVE="$(awk -F= '$1=="PAIR_ARCHIVE"{v=$2} END{print v}' "$CONSOLE_LOG")"
[ -n "$PAIR_ARCHIVE" ] && [ -f "$PAIR_ARCHIVE" ] && [ -f "$PAIR_ARCHIVE.sha256" ] || { echo 'STATUS=HOLD_PAIR_ARCHIVE_MISSING'; exit 1; }
(cd "$OUTPUT_ROOT" && sha256sum -c "$(basename "$PAIR_ARCHIVE").sha256")
tar -tzf "$PAIR_ARCHIVE" >/dev/null

restore_monitoring
RESTORE_REQUIRED=0
echo 'MONITORING_RESTORED=YES'
echo "CONSOLE_LOG=$CONSOLE_LOG"
echo "PAIR_ARCHIVE=$PAIR_ARCHIVE"
echo 'RUN17_ATTEMPT2_VALID_PAIR=YES'
echo 'RUN17_ATTEMPT2_REPEAT_AUTHORIZED=NO'
echo 'STATUS=PASS_RUN17_ATTEMPT2_PAIR_ARCHIVED'
