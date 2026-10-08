#!/usr/bin/env bash
# testbed_preflight.sh -- pemeriksaan BACA-SAJA testbed HANFIS (WSL, Docker Desktop, Kubernetes, Prometheus, image, repo).
# Tidak mengubah apa pun di klaster, Docker, atau repo (hanya menulis satu berkas log). Hasil: PASS atau HOLD per butir; keluar 0 bila semua PASS, 2 bila ada HOLD.
# Jalankan dari WSL:   bash scripts/testbed_preflight.sh [idle|run]
#   idle (bawaan): testbed menganggur; ketiadaan beban kerja, NodePort, dan Prometheus hanya INFO.
#   run          : persiapan run telemetri; semuanya wajib (HOLD bila tidak ada).
set -u
set -o pipefail
NS="${HANFIS_NS:-hanfis-research}"; CTX="${HANFIS_KUBE_CONTEXT:-docker-desktop}"; NODEPORT="${HANFIS_NODEPORT:-30080}"
PROM="${HANFIS_PROM_URL:-http://127.0.0.1:29090}"; P0IF_IMAGE="${HANFIS_P0IF_IMAGE:-hanfis/p0if:1.2}"
P0IF_ID="${HANFIS_P0IF_ID:-sha256:4b3e7080b453f4549a3a8e31dea91d3d009c0de9fa61cb5efbfdaeb44f0dc3d5}"
MIN_FREE_GB="${HANFIS_MIN_FREE_GB:-20}"; REPO="${HANFIS_REPO:-/mnt/c/Research/ANFIS}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; LOGDIR="$REPO/results_python/testbed_preflight"; LOG="$LOGDIR/preflight_$STAMP.txt"
HOLDS=0
MODE="${1:-idle}"
if [ "$MODE" != "idle" ] && [ "$MODE" != "run" ]; then echo "mode tidak dikenal: $MODE (pakai idle atau run)"; exit 64; fi
pass(){ echo "PASS  $1"; }
hold(){ echo "HOLD  $1"; HOLDS=$((HOLDS+1)); }
info(){ echo "INFO  $1"; }
have(){ command -v "$1" >/dev/null 2>&1; }
need_run(){ if [ "$MODE" = "run" ]; then hold "$1"; else info "(idle) $1"; fi; }

main() {
  echo "== preflight testbed HANFIS  $STAMP  mode=$MODE  ns=$NS ctx=$CTX =="
  if grep -qi microsoft /proc/version 2>/dev/null; then info "berjalan di WSL: $(uname -r)"; else info "tidak terdeteksi WSL (uname: $(uname -r))"; fi

  # 1. Docker
  if have docker; then
    ver="$(docker version --format '{{.Server.Version}}' 2>/dev/null || true)"
    if [ -n "$ver" ]; then pass "docker daemon aktif (server $ver)"; else hold "docker daemon tidak merespons (jalankan Docker Desktop, tunggu 'Engine running')"; fi
  else hold "perintah docker tidak ada (aktifkan WSL integration di Docker Desktop > Settings > Resources)"; fi

  # 2. Kubernetes
  if have kubectl; then
    cur="$(kubectl config current-context 2>/dev/null || true)"
    if [ "$cur" = "$CTX" ]; then pass "konteks kubectl = $cur"; else hold "konteks kubectl '$cur' bukan '$CTX'"; fi
    nodes="$(kubectl get nodes --no-headers 2>/dev/null || true)"
    nn="$(printf '%s\n' "$nodes" | awk 'NF{c++} END{print c+0}')"; nr="$(printf '%s\n' "$nodes" | awk 'NF && $2 !~ /^Ready/{c++} END{print c+0}')"
    if [ "$nn" -gt 0 ] && [ "$nr" -eq 0 ]; then pass "node: $nn, semua Ready"; else hold "node: $nn, tidak Ready: $nr (aktifkan Kubernetes di Docker Desktop)"; fi
    if [ -n "$(kubectl get ns "$NS" -o name 2>/dev/null || true)" ]; then pass "namespace $NS ada"; else hold "namespace $NS tidak ada"; fi
    deps="$(kubectl -n "$NS" get deploy -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.replicas}{" "}{.status.readyReplicas}{"\n"}{end}' 2>/dev/null || true)"
    if [ -z "$deps" ]; then need_run "tidak ada deployment di namespace $NS"; else
      while read -r name want ready; do
        [ -n "${name:-}" ] || continue; ready="${ready:-0}"
        if [ "${want:-0}" -gt 0 ] && [ "$ready" = "$want" ]; then pass "deployment $name: $ready/$want siap"; else hold "deployment $name: ${ready}/${want:-?} siap"; fi
      done <<< "$deps"
    fi
    bad="$(kubectl -n "$NS" get pods --no-headers 2>/dev/null | awk 'NF && $3 != "Running" && $3 != "Completed"{c++} END{print c+0}')"
    if [ "$bad" -eq 0 ]; then pass "tidak ada pod bermasalah di $NS"; else hold "$bad pod tidak Running di $NS"; fi
  else hold "perintah kubectl tidak ada"; fi

  # 3. Layanan
  code="$(curl -s -o /dev/null -m 5 -w '%{http_code}' "http://127.0.0.1:$NODEPORT/" 2>/dev/null || true)"
  if [ "$code" = "200" ]; then pass "HTTP NodePort $NODEPORT = 200"; else need_run "HTTP NodePort $NODEPORT = '${code:-tanpa jawaban}' (harus 200 saat run)"; fi
  pr="$(curl -s -m 5 "$PROM/-/ready" 2>/dev/null || true)"
  if printf '%s' "$pr" | grep -qi ready; then pass "Prometheus siap ($PROM)"; else need_run "Prometheus tidak siap di $PROM"; fi

  if have docker; then
    while IFS= read -r line; do [ -n "$line" ] && info "kontainer: $line"; done <<< "$(docker ps -a --filter name=hanfis --format '{{.Names}} | {{.Status}}' 2>/dev/null || true)"
  fi

  # 4. Identitas image kontrol positif (pagar P13: tag unik, identitas dicatat)
  if have docker; then
    id="$(docker image inspect "$P0IF_IMAGE" --format '{{.Id}}' 2>/dev/null || true)"
    if [ -z "$id" ]; then hold "image $P0IF_IMAGE tidak ada di store Docker"
    elif [ "$id" = "$P0IF_ID" ]; then pass "image $P0IF_IMAGE identik dengan A-15 ($id)"
    else hold "image $P0IF_IMAGE berbeda dari A-15: $id (harapan $P0IF_ID)"; fi
  fi

  # 4b. Jetson (klien telemetri): hanya memeriksa port TCP terbuka, tanpa autentikasi
  jh="${HANFIS_JETSON_HOST:-10.176.68.96}"; jp="${HANFIS_JETSON_PORT:-22}"
  if timeout 4 bash -c "exec 3<>/dev/tcp/$jh/$jp" 2>/dev/null; then pass "Jetson $jh:$jp terjangkau"; else need_run "Jetson $jh:$jp tidak terjangkau (nyalakan Jetson, cek jaringan)"; fi

  # 5. Sumber daya dan repo
  free="$(df -BG --output=avail "$REPO" 2>/dev/null | tail -1 | tr -dc '0-9' || true)"
  if [ -n "$free" ] && [ "$free" -ge "$MIN_FREE_GB" ]; then pass "ruang bebas ${free} GB (>= $MIN_FREE_GB)"; else hold "ruang bebas '${free:-?}' GB (< $MIN_FREE_GB)"; fi
  if [ -d "$REPO/.git" ] || git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
    info "git: $(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null) @ $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null); berkas berubah/tak terlacak: $(git -C "$REPO" status --short 2>/dev/null | wc -l)"
  else hold "$REPO bukan repositori git"; fi
  if have trivy; then info "trivy: $(trivy --version 2>/dev/null | tr '\n' ' ' | cut -c1-160)"; else info "trivy tidak ada di PATH"; fi
  info "waktu UTC: $(date -u +%FT%TZ)"
  if [ "$HOLDS" -eq 0 ]; then echo "STATUS=PASS_TESTBED_PREFLIGHT"; return 0; else echo "STATUS=HOLD_TESTBED_PREFLIGHT ($HOLDS butir)"; return 2; fi
}

mkdir -p "$LOGDIR" 2>/dev/null || true
main 2>&1 | tee "$LOG"
exit "${PIPESTATUS[0]}"
