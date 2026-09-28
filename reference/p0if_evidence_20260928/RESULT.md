# P0-IF positive control: first capture, 2026-09-28

| Evidence dimension | p0if-off (2 replicas) | p0if-on (2 replicas) |
|---|---|---|
| Deployment status | 2/2 Running | 2/2 Running |
| `load_module` in configuration | 0 | 1 per pod |
| libgd in `/proc/<pid>/maps` | 0 lines | 10 lines per pod |
| libexpat in `/proc/<pid>/maps` | 0 lines | 10 lines per pod |
| Trigger `/resize/sample.jpg` | not exercised | HTTP 200 |
| Gate | PASS | PASS |

The contrast is unambiguous: the same image, the same two replicas, and the only difference is
whether the module is loaded. In the ON condition libgd and libexpat are actually mapped into the
nginx worker processes, so the 20 libexpat CVEs move from NOT_APPLICABLE_OBSERVED_DEPLOYMENT to
APPLICABLE_OBSERVED, giving reachability_level 1.0 against 0.25 for the OFF condition (A-01).

Two defects found in the first capture and fixed in patch 0015:

1. `image_filter_directive` was 1 for the OFF condition, which looks like a contradiction. The
   counter matched the explanatory **comment** inside the configuration, because `nginx -T` dumps
   comments as well. Counters now ignore comment lines (OFF: 0, ON: 2).
2. `command terminated with exit code 127` appeared twice per deployment: `readelf` is not part of
   the Alpine base image, so the DT_NEEDED dimension was silently empty. `binutils` is now in the
   image and the script fails closed if `readelf` is missing.

The mapping counter also changed from "number of map lines" to "number of distinct nginx PIDs
whose map contains the library", which is the quantity the acceptance criteria actually refer to.

## Second capture (v4, patches 0015-0017): all acceptance criteria met

| Counter | p0if-off (both pods) | p0if-on (both pods) | Criterion |
|---|---|---|---|
| `nginx_pids` | 2 | 2 | — |
| `libgd_mapped_pids` | 0 | 2 | 0 vs all |
| `libexpat_mapped_pids` | 0 | 2 | 0 vs all |
| `module_loaded` | 0 | 1 | 0 vs 1 |
| `image_filter_directive` | 0 | 2 | 0 vs 2 |
| Trigger | not exercised | HTTP 200 | — |
| Gate | PASS | PASS | PASS |

Both conditions ran the same image (`IMAGE_ID=docker.io/hanfis/p0if@sha256:e9c0780b...`), so the
contrast is attributable to the configuration alone. Amendment A-11 records the result:
reachability_level 0.25 for OFF and 1.0 for ON.

`linkage_dt_needed.txt` confirms the dependency chain and, incidentally, that it is *transitive*:
the module declares only `libgd.so.3` (plus musl), while `libexpat` is pulled in by libgd. This is
exactly the case the adjudication protocol distinguishes from a direct dependency, and it is the
reason the OFF condition is 0.25 rather than 0.1.

Note on tooling: `binutils_files=0` and `readelf=missing` in the container, so the capture fell
back to `scanelf` (pax-utils) as designed by patch 0016. The binutils entry in the Dockerfile does
not install on this Alpine build; scanelf output is sufficient for DT_NEEDED and no further change
is required, but the discrepancy is recorded here rather than silently ignored.
