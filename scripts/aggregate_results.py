#!/usr/bin/env python3
"""
aggregate_results.py — varre results/runs/ e consolida tudo numa tabela unica,
com metrica e contexto lado a lado (uma linha = um par metrica+contexto).

Uso:
    python scripts/aggregate_results.py --out results/reports/comparativo.csv
    python scripts/aggregate_results.py --format md
"""

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "results" / "runs"

COLUMNS = [
    # contexto
    "run_id", "device_id", "board_model", "backend", "accelerator", "scenario", "runtime",
    "model", "quantization", "power_mode", "cooling", "ambient_temp_c",
    "temp_start_c", "repetitions", "status",
    # desempenho
    "wall_time_p50_s", "ttft_p50_ms", "throughput_mean_tok_s",
    "energy_per_tok_mj", "tok_s_per_w", "tok_s_per_gb",
    # recursos
    "peak_ram_used_mb", "avg_cpu_pct", "peak_cpu_pct", "avg_gpu_pct",
    "max_temp_c", "avg_power_w", "energy_j", "power_source",
    "avg_gpu_power_w", "energy_gpu_j", "gpu_power_source",
]


def dig(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d


def collect():
    rows = []
    for run_dir in sorted(RUNS_DIR.glob("*")):
        meta_p, sum_p = run_dir / "meta.json", run_dir / "summary.json"
        if not (meta_p.exists() and sum_p.exists()):
            continue
        meta = json.loads(meta_p.read_text())
        summ = json.loads(sum_p.read_text())
        c = meta.get("context", {})
        perf = summ.get("performance", {})
        res = summ.get("resources", {})
        der = summ.get("derived", {}) or {}
        rows.append({
            "run_id": summ.get("run_id"),
            "device_id": c.get("device_id"),
            "board_model": c.get("board_model"),
            "accelerator": c.get("accelerator"),
            "backend": c.get("backend"),
            "scenario": c.get("scenario"),
            "runtime": c.get("runtime"),
            "model": c.get("model"),
            "quantization": c.get("quantization"),
            "power_mode": c.get("power_mode"),
            "cooling": c.get("cooling"),
            "ambient_temp_c": c.get("ambient_temp_c"),
            "temp_start_c": c.get("temp_start_c"),
            "repetitions": c.get("repetitions"),
            "status": summ.get("status"),
            "wall_time_p50_s": dig(perf, "wall_time_s", "p50"),
            "ttft_p50_ms": dig(perf, "ttft_ms", "p50"),
            "throughput_mean_tok_s": dig(perf, "throughput_tok_s", "mean"),
            "energy_per_tok_mj": der.get("energy_per_tok_mj"),
            "tok_s_per_w": der.get("tok_s_per_w"),
            "tok_s_per_gb": der.get("tok_s_per_gb"),
            "peak_ram_used_mb": res.get("peak_ram_used_mb"),
            "avg_cpu_pct": res.get("avg_cpu_pct"),
            "peak_cpu_pct": res.get("peak_cpu_pct"),
            "avg_gpu_pct": res.get("avg_gpu_pct"),
            "max_temp_c": res.get("max_temp_c"),
            "avg_power_w": res.get("avg_power_w"),
            "energy_j": res.get("energy_j"),
            "power_source": res.get("power_source"),
            "avg_gpu_power_w": res.get("avg_gpu_power_w"),
            "energy_gpu_j": res.get("energy_gpu_j"),
            "gpu_power_source": res.get("gpu_power_source"),
        })
    return rows


def to_markdown(rows, cols):
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    body = [
        "| " + " | ".join("—" if r.get(c) is None else str(r.get(c)) for c in cols) + " |"
        for r in rows
    ]
    return "\n".join([head, sep, *body])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--format", choices=["csv", "md"], default="csv")
    ap.add_argument("--columns", default=None, help="lista separada por virgula")
    args = ap.parse_args()

    rows = collect()
    if not rows:
        print(f"[!] nenhum run encontrado em {RUNS_DIR}")
        return
    cols = args.columns.split(",") if args.columns else COLUMNS

    if args.format == "md":
        text = to_markdown(rows, cols)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(text)
            print(f"[ok] {len(rows)} runs -> {args.out}")
        else:
            print(text)
        return

    out = Path(args.out or ROOT / "results" / "reports" / "comparativo.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"[ok] {len(rows)} runs -> {out}")


if __name__ == "__main__":
    main()
