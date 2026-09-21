#!/usr/bin/env bash

echo "=== O5-B4.12M: RUN 4 TRANSITION TO MONITORING OFF ==="

set -uo pipefail

BASE="/mnt/c/Research/ANFIS/Kubernetes/Observability/Results"
SNAP="$(cat "$BASE/O5-B4-latest-preflight-path.txt")"

PREP="$SNAP/O5-B4.10-replication-preparation"
RUN3="$PREP/Run-4"
PREFLIGHT="$RUN3/run4-execution-manifest.txt"
OUT="$RUN3/03-transition-validation"

mkdir -p "$OUT"

REPORT="$OUT/run4-transition-off-report.txt"
BACKUP="$OUT/monitoring-state-before-off.yaml"
SCALE_STATE="$OUT/monitoring-original-replicas.txt"
EVENTS="$OUT/monitoring-off-events.txt"

# ----------------------------------------------------------
# 1. Pastikan preflight Run 4 telah PASS
# ----------------------------------------------------------

if grep -q \
  "FIRST_CONDITION=MONITORING_OFF" \
  "$PREFLIGHT" 2>/dev/null; then
  PREFLIGHT_PASS=1
else
  PREFLIGHT_PASS=0
fi

if [ "$PREFLIGHT_PASS" -ne 1 ]; then
  echo "HOLD: manifest Run 4 belum tervalidasi."
  exit 1
fi

# ----------------------------------------------------------
# 2. Periksa kondisi awal monitoring
# ----------------------------------------------------------

MON_INITIAL=$(kubectl get pods -n monitoring \
  --no-headers 2>/dev/null | wc -l)

MON_INITIAL_RUNNING=$(kubectl get pods -n monitoring \
  --no-headers 2>/dev/null |
  awk '$3=="Running" {n++} END {print n+0}')

if [ "$MON_INITIAL" -ne 5 ] ||
   [ "$MON_INITIAL_RUNNING" -ne 5 ]; then
  echo "HOLD: kondisi awal monitoring bukan 5/5 Running."
  exit 1
fi

# ----------------------------------------------------------
# 3. Simpan konfigurasi sebelum monitoring dimatikan
# ----------------------------------------------------------

kubectl get deployment,statefulset,daemonset \
  -n monitoring -o yaml > "$BACKUP"

OPERATOR_REPLICAS=$(kubectl get deployment \
  hanfis-monitoring-kube-pro-operator \
  -n monitoring \
  -o jsonpath='{.spec.replicas}')

KSM_REPLICAS=$(kubectl get deployment \
  hanfis-monitoring-kube-state-metrics \
  -n monitoring \
  -o jsonpath='{.spec.replicas}')

PROM_REPLICAS=$(kubectl get statefulset \
  prometheus-hanfis-monitoring-kube-pro-prometheus \
  -n monitoring \
  -o jsonpath='{.spec.replicas}')

{
  echo "operator_replicas=$OPERATOR_REPLICAS"
  echo "kube_state_metrics_replicas=$KSM_REPLICAS"
  echo "prometheus_replicas=$PROM_REPLICAS"
  echo "node_exporter_mode=daemonset"
} > "$SCALE_STATE"

# ----------------------------------------------------------
# 4. Matikan stack monitoring secara terkontrol
# ----------------------------------------------------------

kubectl scale deployment \
  hanfis-monitoring-kube-pro-operator \
  -n monitoring --replicas=0

kubectl scale deployment \
  hanfis-monitoring-kube-state-metrics \
  -n monitoring --replicas=0

kubectl scale statefulset \
  prometheus-hanfis-monitoring-kube-pro-prometheus \
  -n monitoring --replicas=0

kubectl patch daemonset \
  hanfis-monitoring-prometheus-node-exporter \
  -n monitoring \
  --type=merge \
  -p '{"spec":{"template":{"spec":{"nodeSelector":{"hanfis.monitoring/off":"true"}}}}}'

# ----------------------------------------------------------
# 5. Tunggu seluruh pod monitoring berhenti
# ----------------------------------------------------------

echo "Menunggu seluruh pod monitoring berhenti..."

for ATTEMPT in $(seq 1 36); do
  MON_REMAINING=$(kubectl get pods -n monitoring \
    --no-headers 2>/dev/null | wc -l)

  if [ "$MON_REMAINING" -eq 0 ]; then
    break
  fi

  echo "Pemeriksaan $ATTEMPT/36: masih ada $MON_REMAINING pod."
  sleep 5
done

# ----------------------------------------------------------
# 6. Validasi kondisi OFF dan kesehatan P0
# ----------------------------------------------------------

MON_FINAL=$(kubectl get pods -n monitoring \
  --no-headers 2>/dev/null | wc -l)

P0_READY=$(kubectl get deployment p0-baseline \
  -n hanfis-research \
  -o jsonpath='{.status.readyReplicas}' 2>/dev/null)

HTTP_CODE=$(kubectl exec -n hanfis-research p0-loadgen -- \
  curl -sS --max-time 5 \
  -o /dev/null \
  -w '%{http_code}' \
  http://p0-baseline-service/ 2>/dev/null)

kubectl get events -n monitoring \
  --sort-by=.lastTimestamp > "$EVENTS"

# ----------------------------------------------------------
# 7. Tentukan status gate
# ----------------------------------------------------------

if [ "$PREFLIGHT_PASS" -eq 1 ] &&
   [ "$MON_INITIAL" -eq 5 ] &&
   [ "$MON_INITIAL_RUNNING" -eq 5 ] &&
   [ "$MON_FINAL" -eq 0 ] &&
   [ "${P0_READY:-0}" = "2" ] &&
   [ "$HTTP_CODE" = "200" ]; then
  STATUS="PASS - RUN 4 OFF CONDITION READY"
else
  STATUS="HOLD"
fi

# ----------------------------------------------------------
# 8. Tulis laporan dan checksum
# ----------------------------------------------------------

{
  echo "Gate                       : O5-B4.12M"
  echo "Tahap                      : RUN 4 TRANSITION TO MONITORING OFF"
  echo "Snapshot                   : $SNAP"
  echo
  echo "--- PREREQUISITE ---"
  echo "B4.11A valid              : $PREFLIGHT_PASS/1"
  echo
  echo "--- INITIAL MONITORING ---"
  echo "Pod monitoring awal       : $MON_INITIAL/5"
  echo "Pod Running awal          : $MON_INITIAL_RUNNING/5"
  echo
  echo "--- OFF CONDITION ---"
  echo "Pod monitoring tersisa    : $MON_FINAL/0"
  echo
  echo "--- P0 SAFETY ---"
  echo "P0 Ready                  : ${P0_READY:-0}/2"
  echo "HTTP Service P0           : ${HTTP_CODE:-000}"
  echo
  echo "STATUS O5-B4.12M: $STATUS"
} | tee "$REPORT"

sha256sum \
  "$BACKUP" \
  "$SCALE_STATE" \
  "$EVENTS" \
  "$REPORT" \
  > "$OUT/run4-transition-off-sha256.txt"

echo "=== O5-B4.12M SELESAI ==="