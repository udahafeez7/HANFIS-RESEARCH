#!/usr/bin/env bash
# Scans the 11 candidate images proposed toward the 120-image target
# (configs/assets_candidates_toward120.csv) using the existing
# scripts/scan_image_evidence.sh, with the Trivy DB explicitly frozen so
# these new assets share the same CVE-knowledge cutoff as the 109 existing
# assets (A-15: "pindai ulang semua image dengan DB beku pada tanggal
# pembekuan dataset" -- a scan only knows the CVEs known at scan time).
#
# scan_image_evidence.sh itself has no --skip-db-update flag and the
# cached DB's NextUpdate (2026-09-30) has already passed as of today
# (2026-10-01), so trivy would otherwise silently refresh the DB on first
# use. This script does NOT modify scan_image_evidence.sh (shared,
# already proven across 109 assets); instead it freezes the DB from
# outside via TRIVY_SKIP_DB_UPDATE=true, then VERIFIES after each scan
# that the DB actually stayed frozen rather than trusting the env var
# silently -- if Trivy ignores it for any reason, this script aborts
# rather than producing 11 assets on a different DB cutoff than the rest.
#
# Usage: scripts/run_candidate_scans_20261001.sh [--expected-db-updated-at TIMESTAMP]
#   Default --expected-db-updated-at is read from the most common UpdatedAt
#   across existing data/evidence/*/trivy_version_and_db.txt files.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# IMPORTANT: trivy_version_and_db.txt has TWO "UpdatedAt:" lines -- one under
# "Vulnerability DB:" and one under "Java DB:". A plain `grep UpdatedAt` mixes
# both kinds together; the fix (caught after the first real run produced 10
# false "DRIFTED" results) is to extract ONLY the Vulnerability DB's
# UpdatedAt, both here and in the per-scan check below, via the same awk.
vuln_db_updated_at() {
  awk '/^Vulnerability DB:/{f=1; next} f && /UpdatedAt:/{sub(/^ *UpdatedAt: */, ""); print; exit}' "$1"
}

EXPECTED_DB_UPDATED_AT="${1:-}"
if [ -z "$EXPECTED_DB_UPDATED_AT" ]; then
  EXPECTED_DB_UPDATED_AT="$(
    for f in data/evidence/*/trivy_version_and_db.txt; do [ -f "$f" ] && vuln_db_updated_at "$f"; done \
      | sort | uniq -c | sort -rn | head -1 | sed -E 's/^ *[0-9]+ *//'
  )"
fi
if [ -z "$EXPECTED_DB_UPDATED_AT" ]; then
  echo "ABORT: could not determine an expected DB UpdatedAt from existing evidence, and none was passed explicitly."
  exit 1
fi
echo "Freezing Trivy DB -- expecting UpdatedAt: $EXPECTED_DB_UPDATED_AT"
export TRIVY_SKIP_DB_UPDATE=true

# asset_id, digest-pinned image_ref -- transcribed from this session's docker
# inspect output; validated below before any scan runs, so a transcription
# typo fails loudly here rather than scanning the wrong (or no) image.
CANDIDATES=(
  "etcd-3-5|quay.io/coreos/etcd@sha256:a055da833a7c013b836ed0822e8ec1f99b059658be255ad8d0fcd31b635ae3d6"
  "opa-0-70|docker.io/openpolicyagent/opa@sha256:2b1c4b231f6dfa6a2baea4af4109203b10cd4b65e836d72f03bfe5d8dfce7095"
  "gatekeeper-3-17|docker.io/openpolicyagent/gatekeeper@sha256:b7b4d7cfdd52c877267dac0824977eaf289fd4640b9bd530e7fc742c6d6e5cc0"
  "cilium-1-16|quay.io/cilium/cilium@sha256:d55ec38938854133e06739b1af237932b9c4dd4e75e9b7b2ca3acc72540a44bf"
  "istio-proxy-1-23|docker.io/istio/proxyv2@sha256:2876cfc2fdf47e4b9665390ccc9ccf2bf913b71379325b8438135c9f35578e1a"
  "kafka-3-8|docker.io/apache/kafka@sha256:22c4bea38875408e8f9fe52aca8e3a6ee67f9aa0090db59af99a2f6647558db5"
  "velero-1-15|docker.io/velero/velero@sha256:8a82ab0b14a8fc479cf494172c0f7d168d018a3bb1d19c9a0d8889d3039288fc"
  "metrics-server-0-7|registry.k8s.io/metrics-server/metrics-server@sha256:ffcb2bf004d6aa0a17d90e0247cf94f2865c8901dcab4427034c341951c239f9"
  "cosign-2-4|gcr.io/projectsigstore/cosign@sha256:dc905e434d9d7f0a5cff8e76abdfae02be313cfa5f3eac6e89209d9bd52e3b92"
  "external-secrets-0-10|ghcr.io/external-secrets/external-secrets@sha256:b97ebc9975ccc378a5f29e9fc77e52e1d76cdbf48acad078428392eb6114c33f"
  "kube-state-metrics-2-13|registry.k8s.io/kube-state-metrics/kube-state-metrics@sha256:639a1e2da549210adddc0391ff91e270e83f7873014aec53258462812f741e6f"
)

# Validate every digest BEFORE scanning anything (fail-closed: a single
# malformed entry aborts the whole batch rather than silently skipping it
# or scanning a truncated/wrong reference).
for entry in "${CANDIDATES[@]}"; do
  ref="${entry#*|}"
  digest="${ref##*@sha256:}"
  if [[ ! "$digest" =~ ^[0-9a-f]{64}$ ]]; then
    echo "ABORT: '$ref' does not have a well-formed 64-hex-char sha256 digest (got '$digest', length ${#digest}). Re-check against docker inspect output before re-running."
    exit 1
  fi
done
echo "All ${#CANDIDATES[@]} digests well-formed. Proceeding."
echo

RESULTS_CSV="configs/assets_candidates_toward120_scanresults.csv"
mkdir -p "$(dirname "$RESULTS_CSV")"
echo "asset_id,image_ref,bundle_dir,scan_json,db_frozen_ok,db_updated_at_seen" > "$RESULTS_CSV"

FAILS=0
for entry in "${CANDIDATES[@]}"; do
  slug="${entry%%|*}"
  ref="${entry#*|}"
  echo "=== $slug ($ref) ==="
  if ! BUNDLE_OUT="$(scripts/scan_image_evidence.sh "$slug" "$ref" 2>&1 | tee /dev/stderr | grep -E '^BUNDLE=')"; then
    echo "FAIL: scan_image_evidence.sh did not complete for $slug"
    echo "$slug,$ref,,,FAIL,ERROR" >> "$RESULTS_CSV"
    FAILS=$((FAILS + 1))
    continue
  fi
  BUNDLE="${BUNDLE_OUT#BUNDLE=}"
  DB_META="$BUNDLE/trivy_version_and_db.txt"
  SEEN_UPDATED_AT="$(vuln_db_updated_at "$DB_META")"
  if [ "$SEEN_UPDATED_AT" = "$EXPECTED_DB_UPDATED_AT" ]; then
    DB_OK="OK"
  else
    DB_OK="DRIFTED"
    echo "WARNING: $slug scanned with DB UpdatedAt '$SEEN_UPDATED_AT', expected '$EXPECTED_DB_UPDATED_AT' -- TRIVY_SKIP_DB_UPDATE did not hold. This asset's CVE cutoff differs from the rest of the inventory; do not merge into assets.csv until resolved."
  fi
  echo "$slug,$ref,$BUNDLE,$BUNDLE/${slug}_vulnerabilities.json,$DB_OK,$SEEN_UPDATED_AT" >> "$RESULTS_CSV"
  echo
done

echo "=== Summary ==="
column -t -s, "$RESULTS_CSV" 2>/dev/null || cat "$RESULTS_CSV"
if [ "$FAILS" -gt 0 ]; then
  echo
  echo "STATUS=CANDIDATE_SCANS_INCOMPLETE ($FAILS of ${#CANDIDATES[@]} failed)"
  exit 1
fi
if grep -q ",DRIFTED," "$RESULTS_CSV"; then
  echo
  echo "STATUS=CANDIDATE_SCANS_DB_DRIFT (all scans completed, but one or more used an unfrozen DB -- see warnings above)"
  exit 1
fi
echo
echo "wrote $RESULTS_CSV"
echo "STATUS=CANDIDATE_SCANS_DONE"
