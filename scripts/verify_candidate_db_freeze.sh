#!/usr/bin/env bash
# Re-verifies the DB-freeze check against ALREADY-PRODUCED candidate scan
# bundles (data/evidence/<slug>_trivy_scan_*/), without re-running trivy.
#
# The first run of run_candidate_scans_20261001.sh (2026-10-01) reported
# all 10 successful scans as DRIFTED. That was a false positive in the
# ORIGINAL script: trivy_version_and_db.txt has two "UpdatedAt:" lines
# (Vulnerability DB and Java DB); the original auto-detection and
# per-scan check both used a plain `grep UpdatedAt | head -1`, mixing the
# two kinds together, so the "expected" value it compared against ended
# up being the Java DB's majority timestamp while each scan's "seen"
# value was the Vulnerability DB's timestamp -- apples to oranges. Both
# run_candidate_scans_20261001.sh and this script now extract ONLY the
# Vulnerability DB's UpdatedAt.
#
# Usage: scripts/verify_candidate_db_freeze.sh [bundle_glob]
#   Default bundle_glob: data/evidence/*/trivy_version_and_db.txt, restricted
#   to the 11 candidate asset_id prefixes below so unrelated evidence
#   bundles are not pulled in by accident.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

vuln_db_updated_at() {
  awk '/^Vulnerability DB:/{f=1; next} f && /UpdatedAt:/{sub(/^ *UpdatedAt: */, ""); print; exit}' "$1"
}

CANDIDATE_SLUGS=(etcd-3-5 opa-0-70 gatekeeper-3-17 cilium-1-16 istio-proxy-1-23 kafka-3-8 \
                 velero-1-15 metrics-server-0-7 cosign-2-4 external-secrets-0-10 kube-state-metrics-2-13)

EXPECTED="$(
  for f in data/evidence/*/trivy_version_and_db.txt; do
    base="$(basename "$(dirname "$f")")"
    is_candidate=0
    for s in "${CANDIDATE_SLUGS[@]}"; do [[ "$base" == "${s}_trivy_scan_"* ]] && is_candidate=1; done
    [ "$is_candidate" -eq 1 ] && continue   # exclude the candidates themselves from "what's expected"
    vuln_db_updated_at "$f"
  done | sort | uniq -c | sort -rn | head -1 | sed -E 's/^ *[0-9]+ *//'
)"
echo "Expected (Vulnerability DB UpdatedAt, from the 109 existing assets): $EXPECTED"
echo

FOUND=0
for slug in "${CANDIDATE_SLUGS[@]}"; do
  bundle="$(ls -dt data/evidence/${slug}_trivy_scan_* 2>/dev/null | head -1 || true)"  # -t: newest first, not alphabetical
  if [ -z "$bundle" ]; then
    echo "$slug: no bundle found (not yet scanned, or scan failed before writing evidence)"
    continue
  fi
  FOUND=$((FOUND + 1))
  seen="$(vuln_db_updated_at "$bundle/trivy_version_and_db.txt" 2>/dev/null || echo "UNREADABLE")"
  if [ "$seen" = "$EXPECTED" ]; then
    echo "$slug: OK ($seen)"
  else
    echo "$slug: DRIFTED (saw '$seen', expected '$EXPECTED')"
  fi
done
echo
echo "checked $FOUND of ${#CANDIDATE_SLUGS[@]} candidate bundles"
