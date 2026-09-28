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
