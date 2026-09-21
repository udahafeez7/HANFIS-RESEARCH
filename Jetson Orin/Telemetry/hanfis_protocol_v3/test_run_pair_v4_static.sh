#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RUNNER="$DIR/run_pair_v4.sh"; CLIENT="$DIR/jetson_capture_v4.sh"; COLLECTOR="$DIR/server_collector_v4.sh"; HELPER="$DIR/server_collector_v4.py"; LIVE_DRY="$DIR/run_stage3c_v4_2_live_dry.sh"; EXECUTOR="$DIR/execute_run17_attempt2_v4_2_2.sh"; FAIL=0
pass(){ echo "PASS $1"; }; fail(){ echo "FAIL $1"; FAIL=1; }
bash -n "$RUNNER" && pass runner_syntax || fail runner_syntax
bash -n "$CLIENT" && pass client_syntax || fail client_syntax
bash -n "$COLLECTOR" && pass collector_syntax || fail collector_syntax
bash -n "$LIVE_DRY" && pass live_dry_syntax || fail live_dry_syntax
bash -n "$EXECUTOR" && pass executor_syntax || fail executor_syntax
python3 -m py_compile "$HELPER" && pass collector_python_syntax || fail collector_python_syntax
python3 "$HELPER" --self-test && pass collector_self_test || fail collector_self_test
python3 "$DIR/test_server_collector_v4_mock.py" && pass collector_mock_e2e || fail collector_mock_e2e
for p in 'jetson@10.176.68.96' 'http://10.176.68.126:30080/' 'http://127.0.0.1:29090' 'server_collector_v4.sh' 'p0-baseline-nodeport-v4' 'hanfis-nodeport-gateway-v4' 'EXPECTED_TARGET_PORT' 'EXPECTED_NODE_PORT' 'HOLD_RUN17_NOT_AUTHORIZED' 'CONFIRM_RUN17=YES_RUN17' 'HOLD_EXTERNAL_OBSERVER_PREFLIGHT' 'EXTERNAL_ACTIVE_TARGETS' 'WORKLOAD_SPAN_SECONDS' 'ACCESS_PATH=JETSON_TO_WINDOWS_DOCKER_GATEWAY_TO_NODEPORT'; do grep -Fq "$p" "$RUNNER" && pass "gate_${p//[^A-Za-z0-9]/_}" || fail "gate_${p//[^A-Za-z0-9]/_}"; done
for p in 'REQUESTS:-1500' 'REQUEST_INTERVAL_SECONDS:-0.21' 'MIN_WORKLOAD_SECONDS:-300' 'REQUEST_PACING=ABSOLUTE_DEADLINE' 'scheduled_epoch' 'time_starttransfer' 'CLIENT_STATUS=HOLD_WORKLOAD'; do grep -Fq "$p" "$CLIENT" && pass "client_${p//[^A-Za-z0-9]/_}" || fail "client_${p//[^A-Za-z0-9]/_}"; done
if grep -Eq '10\.176\.68\.(28|250)|127\.0\.0\.1:18080|TARGET_URL:-http://[^:]+:18080' "$RUNNER" "$CLIENT"; then fail stale_path_absent; else pass stale_path_absent; fi
if grep -Fq 'timeout 65s' "$CLIENT"; then fail fixed_65s_absent; else pass fixed_65s_absent; fi
if grep -Fq -- '-v index=' "$CLIENT" "$LIVE_DRY"; then fail reserved_awk_index_absent; else pass reserved_awk_index_absent; fi
[ "$(awk -v start=100 -v idx=2 -v interval=0.21 'BEGIN {printf "%.6f", start + idx*interval}')" = "100.420000" ] && pass absolute_deadline_awk_runtime || fail absolute_deadline_awk_runtime
for p in 'container_cpu_usage_seconds_total' 'container_memory_working_set_bytes' 'machine_cpu_cores' 'machine_memory_bytes' 'NODE_CPU_EXPLICIT_UTILIZATION_FACTOR' 'UTILIZATION_REGIME' 'STRICT_LOW_0_TO_1_PERCENT' 'COUNTER_RESET_CHECK' 'SERIES_CONTINUITY' 'PROM_QUERY_SETTLE_SECONDS' 'BOUNDARY_SETTLEMENT' 'SNAPSHOT_EXACT_CROSSCHECK' 'RATE_INCREASE_COHERENCE' 'WINDOW_ESTIMATOR_DIFFERENCE' 'RECORDED_NOT_GATED' 'PASS_STRICT' 'RUN17_EXECUTED'; do grep -Fq "$p" "$HELPER" && pass "collector_${p//[^A-Za-z0-9]/_}" || fail "collector_${p//[^A-Za-z0-9]/_}"; done
for p in 'RUN_ATTEMPT' 'RUN_ATTEMPT must be a positive integer' 'SERVER_BOUNDARY_SETTLEMENT' 'SERVER_SNAPSHOT_EXACT_CROSSCHECK' 'SERVER_RATE_INCREASE_COHERENCE' 'SERVER_WINDOW_ESTIMATOR_DIFFERENCE' 'SERVER_NODE_UTILIZATION_STATUS' 'SERVER_UTILIZATION_SAMPLES' 'HOLD_NODE_UTILIZATION_GATE' 'HOLD_WRONG_PYTHON_ENVIRONMENT' 'POST_MONITORING_READY' 'HOLD_POST_CONDITION_TREATMENT_GATE' 'external-prometheus-v4.2.2-retained-series-aware'; do grep -Fq "$p" "$RUNNER" && pass "runner_${p//[^A-Za-z0-9]/_}" || fail "runner_${p//[^A-Za-z0-9]/_}"; done
for p in 'OFF_ACTIVITY_WINDOW_SECONDS' 'OFF_ACTIVITY_ABS_TOL_CPU_SECONDS' 'OFF_RETAINED_MONITORING_CPU_SERIES_START' 'OFF_MONITORING_ACTIVITY_GATE' 'ZERO_ACTIVITY_ACCEPTED_AFTER_KUBERNETES_ZERO_POD_GATE'; do grep -Fq "$p" "$HELPER" && pass "collector_${p//[^A-Za-z0-9]/_}" || fail "collector_${p//[^A-Za-z0-9]/_}"; done
grep -Fq 'off-retained-zero-activity' "$DIR/test_server_collector_v4_mock.py" && pass retained_series_positive_test || fail retained_series_positive_test
grep -Fq 'off-active-monitoring' "$DIR/test_server_collector_v4_mock.py" && pass active_monitoring_negative_test || fail active_monitoring_negative_test
grep -Fq 'Exact snapshot crosscheck' "$DIR/test_server_collector_v4_mock.py" && pass negative_exact_snapshot_test || fail negative_exact_snapshot_test
grep -Fq 'rate/increase coherence' "$DIR/test_server_collector_v4_mock.py" && pass negative_rate_increase_test || fail negative_rate_increase_test
grep -Fq 'Node root CPU counter reset detected' "$DIR/test_server_collector_v4_mock.py" && pass negative_node_reset_test || fail negative_node_reset_test
for p in 'RUN=0' 'RUN17_EXECUTED=NO' 'PROM_QUERY_SETTLE_SECONDS=5' 'REQUESTS:-1500' 'REQUEST_INTERVAL_SECONDS:-0.21' 'COLLECTOR_SAMPLES:-64' 'SERVER_INSTANCE_REGEX' 'NODE_RATE_WINDOW_SECONDS' 'STATUS=PASS_STAGE3C_V4_2_2_LIVE_DRY_VALIDATION'; do grep -Fq "$p" "$LIVE_DRY" && pass "live_dry_${p//[^A-Za-z0-9]/_}" || fail "live_dry_${p//[^A-Za-z0-9]/_}"; done
for p in 'RUN_ATTEMPT=2' 'CONFIRM_RUN17=YES_RUN17' 'RUN17_ATTEMPT2_REPEAT_AUTHORIZED=NO' 'STATUS=PASS_RUN17_ATTEMPT2_PAIR_ARCHIVED' 'MONITORING_RESTORED=YES'; do grep -Fq "$p" "$EXECUTOR" && pass "executor_${p//[^A-Za-z0-9]/_}" || fail "executor_${p//[^A-Za-z0-9]/_}"; done
if [ "$FAIL" -eq 0 ]; then echo 'STATUS=PASS_STAGE3C_COLLECTOR_V4_2_2_STATIC_TESTS'; else echo 'STATUS=FAIL_STAGE3C_COLLECTOR_V4_2_2_STATIC_TESTS'; exit 1; fi
