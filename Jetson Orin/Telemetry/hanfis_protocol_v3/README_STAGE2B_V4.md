# HANFIS Stage 2B — NodePort Pair Runner v4

This package migrates the paired experiment path from `kubectl port-forward`
to the validated NodePort/Docker-gateway path. It does **not** execute Run 17.

## Fixed defaults

- Jetson SSH: `jetson@10.176.68.96`
- External target: `http://10.176.68.126:30080/`
- Local gateway check: `http://127.0.0.1:30080/`
- Kubernetes Service: `p0-baseline-nodeport-v4`
- NodePort: `30080`; application targetPort: `8080`
- Docker gateway: `hanfis-nodeport-gateway-v4`
- Workload: 1500 requests at 0.21 s spacing (planned span 314.79 s)

The runner validates the Service, EndpointSlice, Docker gateway, local HTTP,
and Jetson full-chain HTTP before changing a treatment condition. Run 17 is
fail-closed unless `CONFIRM_RUN17=YES_RUN17` is explicitly supplied after all
later protocol and preregistration gates are complete.

## Installation (WSL / VS Code terminal)

Extract into the HANFIS project root. Keep `server_collector_v3_2.sh` in the
same directory; it remains an operational cross-check until Stage 3 installs
the external Prometheus collector.

Run static validation only:

```bash
chmod +x run_pair_v4.sh jetson_capture_v4.sh test_run_pair_v4_static.sh
sha256sum -c SHA256SUMS_STAGE2B_V4.txt
./test_run_pair_v4_static.sh
```

Expected: `STATUS=PASS_STAGE2B_V4_STATIC_TESTS`.

Do not run `./run_pair_v4.sh 17 ...` yet.
