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

# Select only pods that are Running, Ready and NOT being deleted. After a rollout restart the
# label selector still returns terminating pods for a few seconds; execing into one of them
# fails with "pods ... not found" (patch 0016).
list_ready_pods() {
  # kubectl jsonpath has no negation operator, so the filter is done with custom-columns + awk:
  # a pod qualifies when it is Running, its container reports ready=true, and it has no
  # deletionTimestamp (printed as <none> when absent).  (patch 0017)
  kubectl -n "$NAMESPACE" get pods -l "app=$DEPLOY" \
    --field-selector=status.phase=Running --no-headers \
    -o custom-columns='NAME:.metadata.name,READY:.status.containerStatuses[0].ready,DEL:.metadata.deletionTimestamp' \
    2>/dev/null | awk '$2=="true" && $3=="<none>" {print $1}'
}
PODS=()
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  mapfile -t PODS < <(list_ready_pods)
  [ "${#PODS[@]}" -ge 2 ] && break
  sleep 3
done
[ "${#PODS[@]}" -ge 2 ] || fail FEWER_THAN_TWO_READY_REPLICAS
echo "REPLICAS=${#PODS[@]}" >> "$OUTDIR/metadata.txt"
echo "PODS=${PODS[*]}" >> "$OUTDIR/metadata.txt"
echo "IMAGE=$(kubectl -n "$NAMESPACE" get pod "${PODS[0]}" -o jsonpath='{.spec.containers[0].image}')" >> "$OUTDIR/metadata.txt"
echo "IMAGE_ID=$(kubectl -n "$NAMESPACE" get pod "${PODS[0]}" -o jsonpath='{.status.containerStatuses[0].imageID}')" >> "$OUTDIR/metadata.txt"

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
  # Direct dependencies (DT_NEEDED). Three tools are tried in order so a missing binutils does
  # not silently empty this evidence dimension; diagnostics are recorded in the same file and the
  # step only fails when none of the tools exists (patch 0016).
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c '
      echo "== tooling"; echo "PATH=$PATH"
      for t in readelf objdump scanelf; do printf "%s=%s\n" "$t" "$(command -v $t || echo missing)"; done
      apk info -L binutils 2>/dev/null | grep -c . | sed "s/^/binutils_files=/"
      if command -v readelf >/dev/null; then TOOL=readelf
      elif command -v objdump >/dev/null; then TOOL=objdump
      elif command -v scanelf >/dev/null; then TOOL=scanelf
      else echo "NO_ELF_TOOL"; exit 3; fi
      echo "TOOL_USED=$TOOL"
      for f in /usr/sbin/nginx /usr/lib/nginx/modules/*.so; do
        echo "== $f"
        case "$TOOL" in
          readelf) readelf -d "$f" | grep NEEDED ;;
          objdump) objdump -p "$f" | grep NEEDED ;;
          scanelf) scanelf -qn "$f" ;;
        esac
      done' > "$D/linkage_dt_needed.txt" || fail NO_ELF_TOOL_IN_IMAGE
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'for f in /usr/sbin/nginx /usr/lib/nginx/modules/*.so; do echo "== $f"; ldd "$f" 2>&1; done' > "$D/linkage_ldd.txt" || true
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'nginx -T 2>&1' > "$D/activation_nginx_T.txt" || fail ACTIVATION
  kubectl -n "$NAMESPACE" exec "$POD" -- sh -c 'for p in $(pgrep nginx); do echo "== pid $p"; cat /proc/$p/maps; done' > "$D/runtime_maps.txt" || fail RUNTIME_MAPS
  # Machine-readable summary (patch 0015).
  #  - mapping is counted as the number of distinct nginx PIDs whose memory map contains the
  #    library, not the number of map lines (one library occupies several regions);
  #  - configuration counters ignore comment lines, otherwise a comment mentioning the module
  #    is counted as if the directive were configured.
  CONF_NOCOMMENT="$D/activation_nginx_T.nocomment.txt"
  grep -v '^[[:space:]]*#' "$D/activation_nginx_T.txt" > "$CONF_NOCOMMENT" || true
  pids_with() { awk -v lib="$1" '/^== pid /{pid=$3} $0 ~ lib {seen[pid]=1} END{n=0; for (p in seen) n++; print n}' "$D/runtime_maps.txt"; }
  {
    echo "pod=$POD"
    echo "nginx_pids=$(grep -c '^== pid ' "$D/runtime_maps.txt" || true)"
    echo "libgd_mapped_pids=$(pids_with libgd)"
    echo "libexpat_mapped_pids=$(pids_with libexpat)"
    echo "module_loaded=$(grep -c '^[[:space:]]*load_module' "$CONF_NOCOMMENT" || true)"
    echo "image_filter_directive=$(grep -cE '^[[:space:]]*image_filter([[:space:]_]|;)' "$CONF_NOCOMMENT" || true)"
  } > "$D/summary.txt"
done

kubectl -n "$NAMESPACE" get svc,endpoints -l "app=$DEPLOY" -o yaml > "$OUTDIR/exposure.yaml" 2>/dev/null || true
kubectl -n "$NAMESPACE" get deploy "$DEPLOY" -o yaml > "$OUTDIR/deployment.yaml"

( cd "$OUTDIR" && find . -type f ! -name sha256.txt -print0 | sort -z | xargs -0 sha256sum > sha256.txt )
( cd "$OUTDIR" && sha256sum -c sha256.txt >/dev/null ) || fail CHECKSUM

echo "STATUS=PASS_REACHABILITY_EVIDENCE_${DEPLOY}" | tee -a "$OUTDIR/metadata.txt"
