# P0-IF: positive control for runtime reachability (patch 0014)

## Why

On the P0 baseline, 19 of 21 runtime adjudications were NOT_APPLICABLE_OBSERVED_DEPLOYMENT:
nginx never loads libexpat, so almost every label is the same. A model cannot learn to
discriminate risk from an almost constant target. P0-IF creates the contrast case: the same
image in two configurations, one with the `image_filter` module loaded (libgd -> libexpat
actually mapped into the process) and one without.

The original `p0-baseline` deployment is **not modified**: telemetry continuity with Runs 7-17
and the frozen evidence for the existing 22 adjudications are preserved.

## Full procedure (run from /mnt/c/Research/ANFIS)

```bash
cd /mnt/c/Research/ANFIS
source /home/hafiz/.venvs/anfis/bin/activate

# 0. Verify the Alpine module package exists before building (fail-closed)
docker run --rm alpine:3.21 sh -c \
  'apk update >/dev/null && apk search -x nginx-mod-http-image-filter && apk info -d nginx-mod-http-image-filter | head -3'
#    Expected: the package name is printed. If it is not, stop and report the output.

# 1. Build the image (Docker Desktop shares its daemon with the cluster, so no registry is needed)
docker build -t hanfis/p0if:1.0 /mnt/c/Research/ANFIS/kubernetes/p0if

# 2. Confirm the module and its libraries are really inside the image
docker run --rm hanfis/p0if:1.0 sh -c \
  'ls -l /usr/lib/nginx/modules/ngx_http_image_filter_module.so && ldd /usr/lib/nginx/modules/ngx_http_image_filter_module.so | grep -E "libgd|libexpat"'

# 2b. Confirm the ELF tooling is inside the image (evidence dimension 2)
docker run --rm hanfis/p0if:1.0 sh -c 'command -v readelf; command -v objdump; command -v scanelf'

# 3. Deploy both conditions
kubectl apply -f /mnt/c/Research/ANFIS/kubernetes/p0if/p0if.yaml
kubectl -n hanfis-research rollout status deploy/p0if-off --timeout=120s
kubectl -n hanfis-research rollout status deploy/p0if-on  --timeout=120s
kubectl -n hanfis-research get pods -l hanfis.role=positive-control -o wide

# 4. Capture evidence for both conditions (read-only, no exploit traffic)
./scripts/capture_reachability_evidence.sh p0if-off /mnt/c/Research/ANFIS/results_python/evidence/p0if-off
./scripts/capture_reachability_evidence.sh p0if-on  /mnt/c/Research/ANFIS/results_python/evidence/p0if-on /resize/sample.jpg

# 5. Read the two summaries
cat /mnt/c/Research/ANFIS/results_python/evidence/p0if-off/*/summary.txt
cat /mnt/c/Research/ANFIS/results_python/evidence/p0if-on/*/summary.txt
```

## Acceptance criteria

| Dimension | p0if-off | p0if-on |
|---|---|---|
| Package identity (libexpat, libgd, module) | present 2/2 | present 2/2 |
| `load_module` in `nginx -T` | 0 | 2/2 |
| `image_filter` directive | 0 | 2/2 |
| `libgd_mapped_pids` (distinct nginx PIDs) | 0 | all PIDs |
| `libexpat_mapped_pids` | 0 | all PIDs |
| Trigger path HTTP code | not exercised | 200 |
| Resulting reachability_level (A-01) | 0.25 | 1.0 |

If `libexpat_mapped` is 0 on p0if-on, the chain libgd -> libexpat does not hold in this Alpine
build; report the `linkage_ldd.txt` of the module and stop. Do not adjust the expected value.


## Re-running after an image rebuild

`rollout restart` leaves terminating pods behind for a few seconds. The capture script now waits
until at least two pods are Running **and** Ready **and** not being deleted before it execs into
them, and records the image and imageID it actually measured in `metadata.txt`. If a capture still
reports `HOLD_FEWER_THAN_TWO_READY_REPLICAS`, inspect:

```bash
kubectl -n hanfis-research get pods -l app=p0if-on -o wide
kubectl -n hanfis-research describe deploy/p0if-on | tail -20
```
