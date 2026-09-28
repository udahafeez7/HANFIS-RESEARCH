#!/usr/bin/env bash
# Apply the newest patch archive from the project patch folder.
#
#   cd /mnt/c/Research/ANFIS && ./scripts/apply_latest_patch.sh            # newest zip
#   cd /mnt/c/Research/ANFIS && ./scripts/apply_latest_patch.sh 0017       # a specific number
#
# Patch archives live in /mnt/c/Research/ANFIS/Patch (Windows: C:\Research\ANFIS\Patch).
# The script verifies the checksum against HANFIS_patches_SHA256SUMS.txt when the entry exists,
# unpacks to /tmp/p<number>, applies with `git am -3`, and runs the test suite.

set -uo pipefail

ROOT="/mnt/c/Research/ANFIS"
PATCH_DIR="$ROOT/Patch"
SUMS="$ROOT/HANFIS_patches_SHA256SUMS.txt"
WANT="${1:-}"

cd "$ROOT" || exit 1
[ -d "$PATCH_DIR" ] || { echo "STATUS=HOLD_NO_PATCH_DIR: $PATCH_DIR"; exit 1; }

if [ -n "$WANT" ]; then
  ZIP=$(ls -1t "$PATCH_DIR"/*"$WANT"*.zip 2>/dev/null | head -1)
else
  ZIP=$(ls -1t "$PATCH_DIR"/*.zip 2>/dev/null | head -1)
fi
[ -n "${ZIP:-}" ] || { echo "STATUS=HOLD_NO_ZIP_FOUND in $PATCH_DIR"; ls -la "$PATCH_DIR"; exit 1; }
echo "ARCHIVE=$ZIP"

ACTUAL=$(sha256sum "$ZIP" | awk '{print $1}')
echo "SHA256=$ACTUAL"
if [ -f "$SUMS" ] && grep -q "$(basename "$ZIP")" "$SUMS"; then
  EXPECTED=$(grep "$(basename "$ZIP")" "$SUMS" | awk '{print $1}' | head -1)
  if [ "$ACTUAL" = "$EXPECTED" ]; then
    echo "CHECKSUM=OK"
  else
    echo "CHECKSUM=MISMATCH expected=$EXPECTED"; echo "STATUS=HOLD_CHECKSUM"; exit 1
  fi
else
  echo "CHECKSUM=NOT_LISTED (continuing; add the entry to $SUMS)"
fi

NUM=$(basename "$ZIP" | grep -oE '[0-9]{4}' | head -1)
DEST="/tmp/p${NUM:-tmp}"
rm -rf "$DEST" && mkdir -p "$DEST"
unzip -o "$ZIP" -d "$DEST" >/dev/null || { echo "STATUS=HOLD_UNZIP"; exit 1; }
ls -la "$DEST"

git am -3 "$DEST"/*.patch
RC=$?
if [ "$RC" -ne 0 ]; then
  echo "STATUS=HOLD_GIT_AM (run 'git am --abort' to return to the previous state)"
  exit "$RC"
fi

git log --oneline -1
python -m pytest -q test tests
echo "STATUS=PASS_APPLY_${NUM:-tmp}"
