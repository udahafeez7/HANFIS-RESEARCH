#!/usr/bin/env bash
# Expand the asset inventory from configs/image_candidates.csv: pull each tag ONCE on the freeze date,
# resolve its registry digest, scan it as a frozen evidence bundle, and append a posture-factorial row.
# Usage: scripts/scan_inventory.sh [candidates.csv] [max_images]
# Fail-closed per image (a failure is logged and the loop continues); Trivy DB is downloaded once and then
# frozen for the whole campaign (TRIVY_SKIP_DB_UPDATE=true), so every bundle carries the same DB date.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
CAND="${1:-configs/image_candidates.csv}"; MAX="${2:-999}"
LOG="results_python/evidence/scan_inventory_$(date -u +%Y%m%dT%H%M%SZ).log"; mkdir -p "$(dirname "$LOG")"
command -v trivy >/dev/null || { echo "ABORT: trivy not on PATH"; exit 1; }
command -v docker >/dev/null || { echo "ABORT: docker not on PATH"; exit 1; }
echo "freeze_date_utc=$(date -u +%Y-%m-%d)" | tee "$LOG"
n=0; ok=0; fail=0
tail -n +2 "$CAND" | while IFS=, read -r ASSET REF CATEGORY NOTE; do
  [ -z "$ASSET" ] && continue
  n=$((n+1)); [ "$n" -gt "$MAX" ] && break
  if grep -q "^$ASSET," configs/assets.csv; then echo "SKIP $ASSET (already in inventory)" | tee -a "$LOG"; continue; fi
  echo "=== [$n] $ASSET  $REF" | tee -a "$LOG"
  if ! docker pull -q "$REF" >/dev/null 2>&1; then echo "FAIL $ASSET: pull" | tee -a "$LOG"; fail=$((fail+1)); continue; fi
  DIGEST_REF="$(docker image inspect "$REF" --format '{{index .RepoDigests 0}}' 2>/dev/null || true)"
  [[ "$DIGEST_REF" == *@sha256:* ]] || { echo "FAIL $ASSET: no RepoDigest for $REF" | tee -a "$LOG"; fail=$((fail+1)); continue; }
  NAME="${DIGEST_REF%%@*}"; DIGEST="${DIGEST_REF##*@}"
  IMAGE_ID="docker.io/${NAME#docker.io/}@${DIGEST}"
  OUT="$(TRIVY_SKIP_DB_UPDATE="${TRIVY_SKIP_DB_UPDATE:-false}" scripts/scan_image_evidence.sh "$ASSET" "$IMAGE_ID" 2>&1 | tee -a "$LOG")" || true
  export TRIVY_SKIP_DB_UPDATE=true            # DB frozen after the first successful download
  SCAN_JSON="$(printf '%s\n' "$OUT" | grep '^SCAN_JSON=' | tail -1 | cut -d= -f2-)"
  [ -n "$SCAN_JSON" ] && [ -f "$SCAN_JSON" ] || { echo "FAIL $ASSET: scan" | tee -a "$LOG"; fail=$((fail+1)); continue; }
  if python scripts/assign_posture.py append --asset-id "$ASSET" --image-id "$IMAGE_ID" --scan-json "$SCAN_JSON" | tee -a "$LOG"; then
    ok=$((ok+1))
  else
    echo "FAIL $ASSET: inventory append" | tee -a "$LOG"; fail=$((fail+1))
  fi
done
echo "LOG=$LOG"
echo "inventory rows now: $(($(wc -l < configs/assets.csv) - 1))"
echo "STATUS=SCAN_INVENTORY_DONE (see $LOG for FAIL lines)"
