#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); FAIL=0
pass(){ echo "PASS $1"; }; fail(){ echo "FAIL $1"; FAIL=1; }
bash -n "$DIR/deploy_external_prometheus_v4.sh" && pass deploy_syntax || fail deploy_syntax
python3 - <<'PY' "$DIR/prometheus_external_v4.yml" && pass yaml_parse || fail yaml_parse
import sys,yaml
with open(sys.argv[1], encoding="utf-8") as f: yaml.safe_load(f)
PY
for p in 'scrape_interval: 5s' 'scrape_timeout: 4s' 'desktop-worker:10250' 'desktop-control-plane:10250' 'credentials_file: /etc/prometheus/token'; do grep -Fq "$p" "$DIR/prometheus_external_v4.yml" && pass "config_${p//[^A-Za-z0-9]/_}" || fail "config_${p//[^A-Za-z0-9]/_}"; done
for p in '127.0.0.1:${LISTEN_PORT}:9090' 'hanfis-external-prometheus-v4' 'HOLD_OBSERVER_RBAC' 'HOLD_CONTAINER_ALREADY_EXISTS' 'RUN17_EXECUTED=NO' 'PASS_EXTERNAL_PROMETHEUS_V4'; do grep -Fq "$p" "$DIR/deploy_external_prometheus_v4.sh" && pass "deploy_${p//[^A-Za-z0-9]/_}" || fail "deploy_${p//[^A-Za-z0-9]/_}"; done
if grep -Eq 'port-forward|10\.176\.68\.(28|250)' "$DIR/deploy_external_prometheus_v4.sh" "$DIR/prometheus_external_v4.yml"; then fail stale_dependency_absent; else pass stale_dependency_absent; fi
if [ "$FAIL" -eq 0 ]; then echo 'STATUS=PASS_STAGE3B_EXTERNAL_PROMETHEUS_STATIC_TESTS'; else echo 'STATUS=FAIL_STAGE3B_EXTERNAL_PROMETHEUS_STATIC_TESTS'; exit 1; fi
