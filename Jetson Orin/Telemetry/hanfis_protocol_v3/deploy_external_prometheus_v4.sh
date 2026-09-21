#!/usr/bin/env bash
# Deploy an out-of-treatment Prometheus observer in Docker, not Kubernetes.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OBSERVER_NAMESPACE="${OBSERVER_NAMESPACE:-hanfis-observer}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-hanfis-external-prometheus}"
CONTAINER_NAME="${CONTAINER_NAME:-hanfis-external-prometheus-v4}"
DATA_VOLUME="${DATA_VOLUME:-hanfis-external-prometheus-v4-data}"
DOCKER_NETWORK="${DOCKER_NETWORK:-kind}"
LISTEN_PORT="${LISTEN_PORT:-29090}"
TOKEN_DURATION="${TOKEN_DURATION:-24h}"
RUNTIME_DIR="${RUNTIME_DIR:-$HOME/.local/share/hanfis-external-prometheus-v4}"
PROM_URL="http://127.0.0.1:${LISTEN_PORT}"

for required in kubectl docker curl python3 install mktemp ss grep awk wc mv seq sleep; do
  command -v "$required" >/dev/null 2>&1 || { echo "Missing command: $required" >&2; exit 1; }
done

[ -f "$SCRIPT_DIR/prometheus_external_v4.yml" ] || { echo "Missing prometheus_external_v4.yml" >&2; exit 1; }
[ "$(kubectl auth can-i get nodes --subresource=proxy --as="system:serviceaccount:${OBSERVER_NAMESPACE}:${SERVICE_ACCOUNT}")" = yes ] || {
  echo "STATUS=HOLD_OBSERVER_RBAC"
  exit 1
}
docker network inspect "$DOCKER_NETWORK" >/dev/null

PROM_IMAGE="${PROM_IMAGE:-$(kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].spec.containers[?(@.name=="prometheus")].image}')}"
[ -n "$PROM_IMAGE" ] || { echo "STATUS=HOLD_PROMETHEUS_IMAGE_UNRESOLVED"; exit 1; }

if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "STATUS=HOLD_CONTAINER_ALREADY_EXISTS"
  echo "CONTAINER=$CONTAINER_NAME"
  exit 1
fi
if ss -ltn | awk '{print $4}' | grep -Eq "(^|:)$LISTEN_PORT$"; then
  echo "STATUS=HOLD_LISTEN_PORT_IN_USE"
  exit 1
fi

install -d -m 700 "$RUNTIME_DIR"
install -m 600 "$SCRIPT_DIR/prometheus_external_v4.yml" "$RUNTIME_DIR/prometheus.yml"
TOKEN_TMP=$(mktemp "$RUNTIME_DIR/token.XXXXXX")
chmod 600 "$TOKEN_TMP"
kubectl create token "$SERVICE_ACCOUNT" -n "$OBSERVER_NAMESPACE" --duration="$TOKEN_DURATION" > "$TOKEN_TMP"
[ "$(wc -c < "$TOKEN_TMP")" -gt 100 ] || { rm -f "$TOKEN_TMP"; echo "STATUS=HOLD_TOKEN_EMPTY"; exit 1; }
mv "$TOKEN_TMP" "$RUNTIME_DIR/token"

docker pull "$PROM_IMAGE"
docker volume create "$DATA_VOLUME" >/dev/null
docker run -d --name "$CONTAINER_NAME" --restart unless-stopped \
  --network "$DOCKER_NETWORK" --user 0:0 \
  -p "127.0.0.1:${LISTEN_PORT}:9090" \
  -v "$RUNTIME_DIR/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  -v "$RUNTIME_DIR/token:/etc/prometheus/token:ro" \
  -v "$DATA_VOLUME:/prometheus" \
  "$PROM_IMAGE" \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=30d \
  --web.listen-address=0.0.0.0:9090 >/dev/null

READY=0
for _ in $(seq 1 30); do
  if curl -fsS --max-time 2 "$PROM_URL/-/ready" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  docker logs --tail 50 "$CONTAINER_NAME"
  echo "STATUS=HOLD_EXTERNAL_PROMETHEUS_NOT_READY"
  exit 1
fi

sleep 12
query_scalar() {
  local expression="$1"
  curl -fsS --get --max-time 10 "$PROM_URL/api/v1/query" --data-urlencode "query=$expression" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("data",{}).get("result",[]); print(r[0]["value"][1] if r else "0")'
}
UP_TARGETS=$(query_scalar 'count(up{job=~"external-cadvisor-.*"} == 1)')
CPU_SERIES=$(query_scalar 'count(container_cpu_usage_seconds_total)')

cat > "$RUNTIME_DIR/deployment-metadata.txt" <<EOF
PROTOCOL=external-prometheus-v4
OBSERVER_LOCATION=DOCKER_OUTSIDE_KUBERNETES_TREATMENT
CONTAINER_NAME=$CONTAINER_NAME
PROMETHEUS_IMAGE=$PROM_IMAGE
PROMETHEUS_URL=$PROM_URL
DOCKER_NETWORK=$DOCKER_NETWORK
SCRAPE_INTERVAL=5s
SCRAPE_TIMEOUT=4s
TARGETS=desktop-worker:10250,desktop-control-plane:10250
DATA_VOLUME=$DATA_VOLUME
TOKEN_DURATION=$TOKEN_DURATION
UP_TARGETS=$UP_TARGETS
CPU_COUNTER_SERIES=$CPU_SERIES
RUN17_EXECUTED=NO
EOF

echo "PROMETHEUS_IMAGE=$PROM_IMAGE"
echo "PROMETHEUS_URL=$PROM_URL"
echo "EXTERNAL_UP_TARGETS=$UP_TARGETS/2"
echo "EXTERNAL_CPU_COUNTER_SERIES=$CPU_SERIES"
if [ "$UP_TARGETS" = 2 ] && awk -v n="$CPU_SERIES" 'BEGIN{exit !(n>0)}'; then
  echo "STATUS=PASS_EXTERNAL_PROMETHEUS_V4"
else
  docker logs --tail 50 "$CONTAINER_NAME"
  echo "STATUS=HOLD_EXTERNAL_PROMETHEUS_TARGETS"
  exit 1
fi
