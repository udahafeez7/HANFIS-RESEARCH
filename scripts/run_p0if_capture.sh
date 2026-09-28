#!/usr/bin/env bash
# One command to rebuild the P0-IF image, roll out both conditions and capture the evidence.
# Run it from the VS Code terminal (WSL), from the repository root:
#
#   cd /mnt/c/Research/ANFIS && ./scripts/run_p0if_capture.sh v3
#
# The single argument is a label for the output directory; results are written to
#   /mnt/c/Research/ANFIS/results_python/evidence/p0if-off-<label>/
#   /mnt/c/Research/ANFIS/results_python/evidence/p0if-on-<label>/
# Nothing is overwritten: pick a new label for every attempt.

set -uo pipefail

LABEL="${1:?usage: ./scripts/run_p0if_capture.sh <label>, e.g. v3}"
ROOT="/mnt/c/Research/ANFIS"
NAMESPACE="${NAMESPACE:-hanfis-research}"
OUT="$ROOT/results_python/evidence"
cd "$ROOT"

step() { printf '\n=== %s\n' "$1"; }

step "1/6 build image"
docker build -t hanfis/p0if:1.0 "$ROOT/kubernetes/p0if" || { echo "STATUS=HOLD_BUILD"; exit 1; }

step "2/6 ELF tooling inside the image"
docker run --rm hanfis/p0if:1.0 sh -c 'command -v readelf; command -v objdump; command -v scanelf' \
  || { echo "STATUS=HOLD_NO_ELF_TOOL_IN_IMAGE"; exit 1; }

step "3/6 rollout both conditions"
kubectl -n "$NAMESPACE" rollout restart deploy/p0if-off deploy/p0if-on
kubectl -n "$NAMESPACE" rollout status deploy/p0if-off --timeout=180s || { echo "STATUS=HOLD_ROLLOUT_OFF"; exit 1; }
kubectl -n "$NAMESPACE" rollout status deploy/p0if-on  --timeout=180s || { echo "STATUS=HOLD_ROLLOUT_ON"; exit 1; }

step "4/6 wait for terminated pods to disappear"
for i in $(seq 1 20); do
  LEFT=$(kubectl -n "$NAMESPACE" get pods -l hanfis.role=positive-control --no-headers 2>/dev/null | grep -vc ' Running ' || true)
  [ "${LEFT:-1}" -eq 0 ] && break
  sleep 3
done
kubectl -n "$NAMESPACE" get pods -l hanfis.role=positive-control -o wide

step "5/6 capture evidence"
RC=0
./scripts/capture_reachability_evidence.sh p0if-off "$OUT/p0if-off-$LABEL" || RC=1
./scripts/capture_reachability_evidence.sh p0if-on  "$OUT/p0if-on-$LABEL" /resize/sample.jpg || RC=1

step "6/6 summaries"
for d in "$OUT/p0if-off-$LABEL" "$OUT/p0if-on-$LABEL"; do
  echo "--- $d"
  [ -f "$d/metadata.txt" ] && tail -6 "$d/metadata.txt"
  cat "$d"/*/summary.txt 2>/dev/null || echo "(no summary.txt: the capture stopped at a gate)"
done

echo
echo "Files to send back:"
echo "  $OUT/p0if-off-$LABEL/metadata.txt and */summary.txt"
echo "  $OUT/p0if-on-$LABEL/metadata.txt and */summary.txt"
echo "  $OUT/p0if-on-$LABEL/*/linkage_dt_needed.txt"
exit "$RC"
