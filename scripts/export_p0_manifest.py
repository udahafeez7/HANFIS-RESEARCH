#!/usr/bin/env python3
"""Buat manifest P0 BERSIH dari ekspor klaster 7 Agustus (O5-B4-P0-deployment-before-off.yaml): buang medan yang diisi server
(uid, resourceVersion, generation, creationTimestamp, managedFields, status, anotasi revisi/last-applied) dan simpan sebagai berkas repo
yang dapat dilacak. TIDAK menyentuh klaster. Gagal-tertutup: tepat satu Deployment p0-baseline di ns hanfis-research; tidak menimpa berkas yang ada.
  python scripts/export_p0_manifest.py [--src <yaml>] [--out kubernetes/p0/p0-baseline-deployment.yaml] [--force]"""
import argparse, copy, hashlib, sys
from pathlib import Path
import yaml
SRC = "Kubernetes/Observability/Results/O5-B4-preflight-20260807-095253/O5-B4-P0-deployment-before-off.yaml"
EXPECTED_DIGEST = "sha256:65e3e85dbaed8ba248841d9d58a899b6197106c23cb0ff1a132b7bfe0547e4c0"   # basis P0 yang dipatok di A-15
DROP_META = {"uid", "resourceVersion", "generation", "creationTimestamp", "managedFields", "selfLink", "ownerReferences", "finalizers"}
DROP_ANN = {"deployment.kubernetes.io/revision", "kubectl.kubernetes.io/last-applied-configuration"}
def find(docs):
    out = []
    for d in docs:
        if not d: continue
        for it in (d.get("items", []) if d.get("kind") == "List" else [d]):
            if it.get("kind") == "Deployment" and it["metadata"].get("name") == "p0-baseline" and it["metadata"].get("namespace", "hanfis-research") == "hanfis-research": out.append(it)
    return out
def clean(dep):
    d = copy.deepcopy(dep); d.pop("status", None); m = d["metadata"]
    for k in list(m):
        if k in DROP_META: m.pop(k)
    ann = {k: v for k, v in (m.get("annotations") or {}).items() if k not in DROP_ANN}
    m.pop("annotations", None)
    if ann: m["annotations"] = ann
    t = d["spec"]["template"]["metadata"]; t.pop("creationTimestamp", None)
    return d
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--src", default=SRC); ap.add_argument("--out", default="kubernetes/p0/p0-baseline-deployment.yaml"); ap.add_argument("--force", action="store_true"); a = ap.parse_args(argv)
    src = Path(a.src); out = Path(a.out)
    if not src.exists(): sys.exit(f"ABORT: sumber tidak ada: {src}")
    if out.exists() and not a.force: sys.exit(f"ABORT: {out} sudah ada (pakai --force bila sengaja)")
    found = find(list(yaml.safe_load_all(src.read_text(encoding="utf-8"))))
    if len(found) != 1: sys.exit(f"ABORT: Deployment p0-baseline ditemukan {len(found)}x (harus 1)")
    d = clean(found[0]); sha = hashlib.sha256(src.read_bytes()).hexdigest()
    hdr = (f"# P0 baseline (Deployment), dibersihkan dari ekspor klaster 2026-08-07.\n# Sumber: {src}\n# sha256 sumber: {sha}\n"
           f"# Dihasilkan oleh scripts/export_p0_manifest.py; medan yang diisi server dibuang, spesifikasi tidak diubah.\n"
           f"# SYARAT SEBELUM apply: image berupa TAG ({d['spec']['template']['spec']['containers'][0]['image']}); digest lokalnya harus {EXPECTED_DIGEST}\n"
           f"# (pagar P13). Bila beda, jangan di-apply tanpa amendemen.\n")
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(hdr + yaml.safe_dump(d, sort_keys=False), encoding="utf-8")
    c = d["spec"]["template"]["spec"]["containers"][0]
    print(f"ditulis: {out}\nnama={d['metadata']['name']} ns={d['metadata'].get('namespace')} replika={d['spec']['replicas']} image={c['image']}\nresources={c.get('resources')}\nlabel pod={d['spec']['template']['metadata'].get('labels')} selector={d['spec']['selector'].get('matchLabels')}")
    return 0
if __name__ == "__main__": sys.exit(main())
