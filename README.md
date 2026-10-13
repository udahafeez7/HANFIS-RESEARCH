# Patch inbox

Download every patch archive from the chat **into this folder**
(`C:\Research\ANFIS\Patch`, WSL `/mnt/c/Research/ANFIS/Patch`), then apply it with:

```bash
cd /mnt/c/Research/ANFIS && ./scripts/apply_latest_patch.sh          # newest archive
cd /mnt/c/Research/ANFIS && ./scripts/apply_latest_patch.sh 0017     # a specific one
```

The script verifies the SHA-256 against `../HANFIS_patches_SHA256SUMS.txt`, unpacks to
`/tmp/p<number>`, applies with `git am -3`, and runs the test suite. Archives are kept here as a
record; they are ignored by git.
