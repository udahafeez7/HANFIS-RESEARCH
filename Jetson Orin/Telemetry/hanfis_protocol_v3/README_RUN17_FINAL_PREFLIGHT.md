# HANFIS Run 17 Final Preflight v4.2.1

This package validates the frozen Stage 3C v4.2 code, NodePort path, internal and external Prometheus, two external cAdvisor targets, clocks, free storage, and the absence of an existing Run 17 output. It creates a checksummed preflight evidence archive.

Version 4.2.1 counts ready backends through both EndpointSlice and the classic Endpoints object. This prevents a false HOLD when one Kubernetes discovery representation is empty while the service path remains healthy.

It does not run or authorize Run 17.

Expected final markers:

```text
AUTHORIZATION_STATUS=NOT_GRANTED
RUN17_EXECUTED=NO
STATUS=PASS_RUN17_FINAL_PREFLIGHT
```
