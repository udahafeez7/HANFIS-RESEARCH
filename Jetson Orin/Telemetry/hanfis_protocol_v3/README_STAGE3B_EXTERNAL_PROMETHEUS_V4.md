# HANFIS Stage 3B — External Prometheus v4

This package deploys a Prometheus container outside the Kubernetes treatment
boundary. It stays constant while the in-cluster `monitoring` namespace is
switched ON and OFF.

Properties:

- direct authenticated kubelet/cAdvisor scrape;
- 5-second scrape interval and 4-second timeout;
- worker and control-plane targets;
- API bound only to WSL localhost port 29090;
- persistent Docker volume with 30-day retention;
- fail-closed RBAC, port, readiness, target and series gates;
- no experiment runner and no Run 17 execution.

Run the static test before deployment:

```bash
chmod +x deploy_external_prometheus_v4.sh test_external_prometheus_v4_static.sh
sha256sum -c SHA256SUMS_STAGE3B_V4.txt
./test_external_prometheus_v4_static.sh
```

Deploy only after the static test passes:

```bash
./deploy_external_prometheus_v4.sh
```

Expected final status: `STATUS=PASS_EXTERNAL_PROMETHEUS_V4`.
