#!/usr/bin/env bash
# Frozen Trivy evidence bundle for ONE digest-pinned image, same layout as data/evidence/p0_trivy_scan_r9NceXFV.
# Usage: scripts/scan_image_evidence.sh <asset_slug> <image@sha256:...> [trivy_cache_dir]
# Output: data/evidence/<asset_slug>_trivy_scan_<rand>/{target_image.txt,trivy_image_id.txt,scan_started_utc.txt,
#         scan_finished_utc.txt,scan.log,<slug>_vulnerabilities.json,trivy_version_and_db.txt,SCAN_SHA256.txt}
set -euo pipefail
SLUG="${1:?asset_slug}"; IMAGE="${2:?image@sha256:...}"; CACHE="${3:-$HOME/.cache/trivy}"
[[ "$IMAGE" == *@sha256:* ]] || { echo "ABORT: image must be digest-pinned (name@sha256:...)"; exit 1; }
command -v trivy >/dev/null || { echo "ABORT: trivy not on PATH"; exit 1; }
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/data/evidence/${SLUG}_trivy_scan_$(head -c 6 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 8)"
mkdir -p "$OUT"
echo "$IMAGE" > "$OUT/target_image.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/scan_started_utc.txt"
trivy --version > "$OUT/trivy_version_and_db.txt"
trivy image --cache-dir "$CACHE" --scanners vuln --format json --output "$OUT/${SLUG}_vulnerabilities.json" \
      --timeout 15m "$IMAGE" 2>&1 | tee "$OUT/scan.log"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/scan_finished_utc.txt"
python3 - "$OUT/${SLUG}_vulnerabilities.json" > "$OUT/trivy_image_id.txt" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); print(d.get("Metadata", {}).get("ImageID", d.get("ArtifactID", "")))
PY
( cd "$OUT" && sha256sum target_image.txt trivy_image_id.txt scan_started_utc.txt scan_finished_utc.txt scan.log \
  "${SLUG}_vulnerabilities.json" trivy_version_and_db.txt > SCAN_SHA256.txt )
echo "BUNDLE=$OUT"
echo "SCAN_JSON=data/evidence/$(basename "$OUT")/${SLUG}_vulnerabilities.json"
