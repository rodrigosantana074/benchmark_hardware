#!/usr/bin/env python3
"""
run_benchmark.py — orquestra uma execucao de benchmark.

Faz, nesta ordem:
  1. carrega a spec do benchmark e o catalogo do dispositivo;
  2. confere o gate termico (nao mede em cima de hardware quente);
  3. roda warm-up (descartado);
  4. roda N repeticoes com o monitor amostrando em paralelo;
  5. grava meta.json (contexto) + samples.ndjson (serie) + summary.json (metricas).

Nenhuma metrica e gravada sem o contexto correspondente.

Uso:
    python scripts/run_benchmark.py \
        --spec benchmarks/specs/slm-latency.yaml \
        --device-id jetson-orin-nano-01 \
        --backend gpu \
        --scenario baseline
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monitor import Monitor, detect_platform  # noqa: E402

try:
    import yaml
except ImportError:
    print("[erro] falta PyYAML. Rode: pip install -r requirements.txt")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "results" / "runs"
DEVICES_DIR = ROOT / "hardware" / "devices"


def git_commit():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        ).stdout.strip() or None
    except Exception:
        return None


def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 2)


def thermal_gate(threshold_c, timeout_s=600):
    """Espera o dispositivo esfriar antes de medir."""
    m = Monitor(interval=1.0)
    start = time.time()
    while time.time() - start < timeout_s:
        temp, _ = m.temp.read()
        if temp is None:
            print("[!] sem leitura de temperatura — gate termico ignorado")
            return None
        if temp <= threshold_c:
            print(f"[ok] temperatura inicial: {temp} °C")
            return temp
        print(f"[..] aguardando cooldown: {temp} °C > {threshold_c} °C")
        time.sleep(10)
    print(f"[!] timeout do cooldown — seguindo com {temp} °C (registrado)")
    return temp


def run_once(command, env_extra, timeout):
    """Executa a carga uma vez e devolve (wall_time_s, returncode, stdout)."""
    env = dict(os.environ, **{k: str(v) for k, v in (env_extra or {}).items()})
    t0 = time.perf_counter()
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True, env=env, timeout=timeout
    )
    wall = time.perf_counter() - t0
    return wall, proc.returncode, proc.stdout, proc.stderr


def parse_metrics_from_stdout(stdout):
    """
    Convencao: a carga pode imprimir uma linha JSON prefixada com METRICS:
    ex.:  METRICS:{"ttft_ms": 143.2, "throughput_tok_s": 21.4, "tokens_out": 128}
    """
    for line in reversed(stdout.splitlines()):
        if line.strip().startswith("METRICS:"):
            try:
                return json.loads(line.split("METRICS:", 1)[1])
            except json.JSONDecodeError:
                pass
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--device-id", required=True)
    ap.add_argument("--backend", required=True, choices=["cpu", "gpu", "npu"])
    ap.add_argument("--scenario", default="baseline")
    ap.add_argument("--repetitions", type=int, default=None)
    ap.add_argument("--warmup", type=int, default=None)
    ap.add_argument("--ambient-temp-c", type=float, default=None)
    ap.add_argument("--notes", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text())
    device_path = DEVICES_DIR / f"{args.device_id}.json"
    if not device_path.exists():
        print(f"[erro] catalogo ausente: {device_path}")
        print("       rode antes: python scripts/collect_hw_info.py --device-id "
              f"{args.device_id}")
        sys.exit(1)
    device = json.loads(device_path.read_text())

    backend_cfg = (spec.get("backends") or {}).get(args.backend)
    if backend_cfg is None:
        print(f"[erro] backend '{args.backend}' nao definido em {args.spec}")
        sys.exit(1)

    scenario_cfg = (spec.get("scenarios") or {}).get(args.scenario, {})
    reps = args.repetitions or spec.get("repetitions", 5)
    warm = args.warmup if args.warmup is not None else spec.get("warmup", 2)
    interval = spec.get("sample_interval_s", 1.0)
    timeout = spec.get("timeout_s", 1800)
    gate_c = spec.get("thermal_gate_c", 45)

    command = backend_cfg["command"]
    env_extra = {**(backend_cfg.get("env") or {}), **(scenario_cfg.get("env") or {})}
    if scenario_cfg.get("command_suffix"):
        command = f"{command} {scenario_cfg['command_suffix']}"

    run_id = (
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        f"__{args.device_id}__{spec['id']}__{args.backend}__{args.scenario}"
    )
    run_dir = RUNS_DIR / run_id
    print(f"[i] run_id: {run_id}")
    print(f"[i] comando: {command}")
    if args.dry_run:
        print("[dry-run] nada foi executado.")
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    temp_start = thermal_gate(gate_c)

    # ---- warm-up (descartado) -------------------------------------------
    for i in range(warm):
        print(f"[warmup {i+1}/{warm}]")
        run_once(command, env_extra, timeout)

    # ---- medicao ---------------------------------------------------------
    iterations = []
    monitor = Monitor(
        interval=interval, out_path=run_dir / "samples.ndjson"
    ).start()
    try:
        for i in range(reps):
            print(f"[run {i+1}/{reps}]")
            wall, rc, out, err = run_once(command, env_extra, timeout)
            it = {
                "iteration": i + 1,
                "wall_time_s": round(wall, 4),
                "returncode": rc,
                "metrics": parse_metrics_from_stdout(out),
            }
            if rc != 0:
                it["stderr_tail"] = err.strip().splitlines()[-5:]
                print(f"[!] iteracao {i+1} retornou codigo {rc}")
            iterations.append(it)
    finally:
        monitor.stop()

    # ---- agregacao -------------------------------------------------------
    ok = [it for it in iterations if it["returncode"] == 0]
    walls = [it["wall_time_s"] for it in ok]

    def agg_metric(name):
        vals = [
            it["metrics"][name]
            for it in ok
            if isinstance(it["metrics"].get(name), (int, float))
        ]
        if not vals:
            return None
        return {
            "mean": round(sum(vals) / len(vals), 3),
            "p50": percentile(vals, 50),
            "p95": percentile(vals, 95),
            "min": round(min(vals), 3),
            "max": round(max(vals), 3),
            "n": len(vals),
        }

    resource = monitor.summary()
    summary = {
        "run_id": run_id,
        "status": "ok" if len(ok) == reps else "partial" if ok else "failed",
        "iterations_ok": len(ok),
        "iterations_total": reps,
        "performance": {
            "wall_time_s": {
                "mean": round(sum(walls) / len(walls), 4) if walls else None,
                "p50": percentile(walls, 50),
                "p95": percentile(walls, 95),
            },
            "ttft_ms": agg_metric("ttft_ms"),
            "latency_ms": agg_metric("latency_ms"),
            "throughput_tok_s": agg_metric("throughput_tok_s"),
        },
        "resources": resource,
        "iterations": iterations,
    }

    meta = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_commit": git_commit(),
        "context": {
            "device_id": args.device_id,
            "device_platform": device.get("platform"),
            "board_model": device.get("board_model"),
            "location": device.get("location"),
            "backend": args.backend,
            "accelerator": (device.get("accelerator") or {}).get("model"),
            "accelerator_type": (device.get("accelerator") or {}).get("type"),
            "scenario": args.scenario,
            "scenario_description": scenario_cfg.get("description"),
            "runtime": backend_cfg.get("runtime"),
            "model": spec.get("model"),
            "quantization": spec.get("quantization"),
            "workload": spec.get("workload"),
            "power_mode": scenario_cfg.get("power_mode")
            or backend_cfg.get("power_mode"),
            "cooling": device.get("thermal", {}).get("cooling"),
            "ambient_temp_c": args.ambient_temp_c,
            "temp_start_c": temp_start,
            "repetitions": reps,
            "warmup_discarded": warm,
            "seed": spec.get("seed"),
            "command": command,
            "env_overrides": env_extra,
        },
        "methodology_ref": "docs/METODOLOGIA.md",
        "host": {"python": sys.version.split()[0], "kernel": platform.release()},
        "notes": args.notes,
    }

    # ---- metricas derivadas (so existem quando os insumos existem) --------
    tokens_out = (spec.get("workload") or {}).get("output_tokens")
    thr = summary["performance"]["throughput_tok_s"]
    derived = {
        "energy_per_tok_mj": round(resource["energy_j"] / tokens_out * 1000, 3)
        if resource.get("energy_j") and tokens_out
        else None,
        "tok_s_per_w": round(thr["mean"] / resource["avg_power_w"], 3)
        if thr and resource.get("avg_power_w")
        else None,
        "tok_s_per_gb": round(thr["mean"] / (resource["peak_ram_used_mb"] / 1024), 3)
        if thr and resource.get("peak_ram_used_mb")
        else None,
    }
    summary["derived"] = derived

    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )

    # ---- run.json: arquivo unico e autocontido, consumido pelo viewer -----
    run_doc = {
        "schema_version": "1.0",
        "run_id": run_id,
        "timestamp_utc": meta["timestamp_utc"],
        "status": summary["status"],
        "context": meta["context"],
        "performance": summary["performance"],
        "resources": summary["resources"],
        "derived": derived,
        "iterations": summary["iterations"],
        "samples": monitor.samples,
        "methodology_ref": meta["methodology_ref"],
        "repo_commit": meta["repo_commit"],
    }
    (run_dir / "run.json").write_text(json.dumps(run_doc, ensure_ascii=False))

    print(f"\n[ok] resultados em {run_dir}")
    print("     run.json pronto para abrir em viewer/index.html")
    print(json.dumps(summary["resources"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
