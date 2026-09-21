#!/usr/bin/env bash

echo "=== O5-B4.11A: RUN 2 PREFLIGHT ==="

set -uo pipefail

BASE="/mnt/c/research/ANFIS/Kubernetes/Observability/Results"
SNAP="$(cat "$BASE/O5-B4-latest-preflight-path.txt")"

PREP="$SNAP/O5-B4.10-replication-preparation"
RUN2="$PREP/Run-2"
OUT="$RUN2/00-preflight"

mkdir -p "$OUT"

REPORT="$OUT/run2-preflight-report.txt"
PLAN="$PREP/replication-plan.csv"
B410_REPORT="$PREP/b4.10-preparation-report.txt"
B410_SHA="$PREP/b4.10-sha256.txt"
SHA_RESULT="$OUT/b4.10-checksum-revalidation.txt"

# 1. Validasi checkpoint sebelumnya
if grep -q \
  "STATUS O5-B4.10: PASS - READY FOR RUN 2" \
  "$B410_REPORT" 2>/dev/null; then
  B410_PASS=1
else
  B410_PASS=0
fi

# 2. Pastikan urutan Run 2 adalah OFF-ON
if grep -q '^2,OFF-ON,PREPARED' "$PLAN" 2>/dev/null; then
  SEQUENCE_PASS=1
  RUN2_SEQUENCE="OFF-ON"
else
  SEQUENCE_PASS=0
  RUN2_SEQUENCE="UNKNOWN"
fi

# 3. Validasi ulang checksum B4.10
if sha256sum -c "$B410_SHA" > "$SHA_RESULT" 2>&1; then
  SHA_PASS=1
else
  SHA_PASS=0
fi

# 4. Periksa node Kubernetes
NODE_TOTAL=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)

NODE_READY=$(kubectl get nodes --no-headers 2>/dev/null |
  awk '$2=="Ready" {n++} END {print n+0}')

# 5. Periksa workload P0
P0_READY=$(kubectl get deployment p0-baseline \
  -n hanfis-research \
  -o jsonpath='{.status.readyReplicas}' 2>/dev/null)

HTTP_CODE=$(kubectl exec -n hanfis-research p0-loadgen -- \
  curl -sS --max-time 5 \
  -o /dev/null \
  -w '%{http_code}' \
  http://p0-baseline-service/ 2>/dev/null)

# 6. Periksa stack monitoring
MON_PODS=$(kubectl get pods -n monitoring \
  --no-headers 2>/dev/null | wc -l)

MON_RUNNING=$(kubectl get pods -n monitoring \
  --no-headers 2>/dev/null |
  awk '$3=="Running" {n++} END {print n+0}')

MON_NOT_READY=$(kubectl get pods -n monitoring \
  --no-headers 2>/dev/null |
  awk '{
    split($2,a,"/")
    if (a[1] != a[2]) n++
  }
  END {print n+0}')

PROM_READY=$(kubectl get statefulset \
  prometheus-hanfis-monitoring-kube-pro-prometheus \
  -n monitoring \
  -o jsonpath='{.status.readyReplicas}' 2>/dev/null)

# 7. Tentukan status gate
if [ "$B410_PASS" -eq 1 ] &&
   [ "$SEQUENCE_PASS" -eq 1 ] &&
   [ "$SHA_PASS" -eq 1 ] &&
   [ "$NODE_TOTAL" -eq 2 ] &&
   [ "$NODE_READY" -eq 2 ] &&
   [ "${P0_READY:-0}" = "2" ] &&
   [ "$HTTP_CODE" = "200" ] &&
   [ "$MON_PODS" -eq 5 ] &&
   [ "$MON_RUNNING" -eq 5 ] &&
   [ "$MON_NOT_READY" -eq 0 ] &&
   [ "${PROM_READY:-0}" = "1" ]; then
  STATUS="PASS - READY FOR RUN 2 OFF CONDITION"
else
  STATUS="HOLD"
fi

# 8. Tulis laporan
{
  echo "Gate                       : O5-B4.11A"
  echo "Tahap                      : RUN 2 PREFLIGHT"
  echo "Snapshot                   : $SNAP"
  echo
  echo "--- PROTOCOL INTEGRITY ---"
  echo "B4.10 valid                : $B410_PASS/1"
  echo "Checksum B4.10             : $SHA_PASS/1"
  echo "Urutan Run 2               : $RUN2_SEQUENCE"
  echo "Urutan tervalidasi         : $SEQUENCE_PASS/1"
  echo
  echo "--- KUBERNETES HEALTH ---"
  echo "Node tersedia              : $NODE_TOTAL/2"
  echo "Node Ready                 : $NODE_READY/2"
  echo
  echo "--- P0 SAFETY ---"
  echo "P0 Ready                   : ${P0_READY:-0}/2"
  echo "HTTP Service P0            : ${HTTP_CODE:-000}"
  echo
  echo "--- MONITORING BASELINE ---"
  echo "Pod monitoring             : $MON_PODS/5"
  echo "Pod Running                : $MON_RUNNING/5"
  echo "Pod tidak sepenuhnya Ready : $MON_NOT_READY"
  echo "Prometheus Ready           : ${PROM_READY:-0}/1"
  echo
  echo "STATUS O5-B4.11A: $STATUS"
} | tee "$REPORT"

sha256sum \
  "$REPORT" \
  "$SHA_RESULT" \
  > "$OUT/run2-preflight-sha256.txt"

echo "=== O5-B4.11A SELESAI ==="