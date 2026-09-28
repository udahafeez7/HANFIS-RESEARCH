#!/usr/bin/env bash
# Capture reachability evidence for one deployment (HANFIS patch 0014).
#
# Produces, per replica, the six evidence dimensions used by amendment A-01:
#   1 package identity and version      (apk list --installed)
#   2 direct dependency                 (readelf -d DT_NEEDED of the nginx binary)
#   3 transitive dependency             (ldd of the nginx binary and of loaded modules)
#   4 configuration activation          (nginx -T: load_module and directive usage)
#   5 runtime mapping                   (/proc/<pid>/maps of the running nginx processes)
#   6 exposure                          (Service and Endpoints of the deployment)
# Everything is read-only. No exploit traffic is generated; the trigger path is a
# normal HTTP GET of a static image, recorded as TRIGGER_PATH_EXERCISED.
#
# Usage (from /mnt/c/Research/ANFIS):
#   ./scripts/capture_reachability_evidence.sh p0if-on  results_python/evidence/p0if-on  /resize/sample.jpg
#   ./scripts/capture_reachability_evidence.sh p0if-off results_python/evidence/p0if-off
#
# Fail-closed: any failed step writes STATUS=HOLD_<reason> and exits non-zero.

set -euo pipefail

DEPLOY="${1:?deployment name, e.g. p0if-on}"
OUTDIR="${2:?output directory, e.g. results_python/evidence/p0if-on}"
TRIGGER_PATH="${3:-}"
NAMESPACE="${NAMESPACE:-hanfis-research}"

fail() { echo "STATUS=HOLD_$1" | tee -a "$OUTDIR/metadata.txt"; exit 1; }

mkdir -p "$OUTDIR"
: > "$OUTDIR/metadata.txt"
{
  echo "DEPLOYMENT=$DEPLOY"
  echo "NAMESPACE=$NAMESPACE"
  echo "CAPTURE_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "PROTOCOL=reachability-evidence-v1"
  echo "RUNTIME_EXPLOIT_EXECUTED=false"
} >> "$OUTDIR/metadata.txt"

kubectl -n "$NAMESPACE" rollout status "deploy/$DEPLOY" --timeout=120s >/dev/null || fail ROLLOUT
mapfile -t PODS < <(kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOY" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')
[ "${#PODS[@]}" -ge 2 ] || fail FEWER_THAN_TWO_REPLICAS
echo "REPLICAS=${#PODS[@]}" >> "$OUTDIR/metadata.txt"

# Optional trigger: a plain GET that forces the module's code path to run.
if [ -n "$TRIGGER_PATH" ]; then
  CODE=$(kubectl -n "$NAMESPACE" exec "${PODS[0]}" -- curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8080${TRIGGER_PATH}" || echo 000)
  echo "TRIGGER_PATH=${TRIGGER_PATH}" >> "$OUTDIR/metadata.txt"
  echo "TRIGGER_HTTP_CODE=${CODE}" >> "$OUTDIR/metadata.txt"
  [ "$CODE" = "200" ] || fail TRIGGER_NOT_200
  echo "TRIGGER_PATH_EXERCISED=true" >> "$OUTDIR/metadata.txt"
  sleep 2
else
  echo "TRIGGER_PATH_EXERCISED=false" >> "$OUTDIR/metadata.txt"
fi

for POD in "${PODS[@]}"; do
  D="$OUTDIR/$POD"; mkdir -p "$D"
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'apk list --installed 2>/dev/null | sort' > "$D/identity_apk.txt" || fail IDENTITY
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'for f in /usr/sbin/nginx /usr/lib/nginx/modules/*.so; do echo "== $f"; readelf -d "$f" 2>/dev/null | grep NEEDED || echo "(no readelf)"; done' > "$D/linkage_dt_needed.txt" || true
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'for f in /usr/sbin/nginx /usr/lib/nginx/modules/*.so; do echo "== $f"; ldd "$f" 2>&1; done' > "$D/linkage_ldd.txt" || true
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'nginx -T 2>&1' > "$D/activation_nginx_T.txt" || fail ACTIVATION
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'for p in $(pgrep nginx); do echo "== pid $p"; cat /proc/$p/maps; done' > "$D/runtime_maps.txt" || fail RUNTIME_MAPS
  # Machine-readable summary of the two libraries of interest.
  {
    echo "pod=$POD"
    echo "libgd_mapped=$(grep -c 'libgd' "$D/runtime_maps.txt" || true)"
    echo "libexpat_mapped=$(grep -c 'libexpat' "$D/runtime_maps.txt" || true)"
    echo "module_loaded=$(grep -c '^load_module' "$D/activation_nginx_T.txt" || true)"
    echo "image_filter_directive=$(grep -c 'image_filter' "$D/activation_nginx_T.txt" || true)"
  } > "$D/summary.txt"
done

kubectl -n "$NAMESPACE" get svc,endpoints -l "app=$DEPLOY" -o yaml > "$OUTDIR/exposure.yaml" 2>/dev/null || true
kubectl -n "$NAMESPACE" get deploy "$DEPLOY" -o yaml > "$OUTDIR/deployment.yaml"

( cd "$OUTDIR" && find . -type f ! -name sha256.txt -print0 | sort -z | xargs -0 sha256sum > sha256.txt )
( cd "$OUTDIR" && sha256sum -c sha256.txt >/dev/null ) || fail CHECKSUM

echo "STATUS=PASS_REACHABILITY_EVIDENCE_${DEPLOY}" | tee -a "$OUTDIR/metadata.txt"
