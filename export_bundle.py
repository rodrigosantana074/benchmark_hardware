#!/usr/bin/env python3
"""
export_bundle.py — junta todos os run.json em um arquivo unico para abrir
na plataforma de visualizacao (viewer/index.html).

Uso:
    python scripts/export_bundle.py
    python scripts/export_bundle.py --no-samples --out results/reports/bundle-leve.json
    python scripts/export_bundle.py --filter device_id=rpi-01 --filter backend=cpu
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "results" / "runs"
DEFAULT_OUT = ROOT / "results" / "reports" / "bundle.json"


def matches(run, filters):
    ctx = run.get("context", {})
    return all(str(ctx.get(k)) == v for k, v in filters)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument(
        "--no-samples",
        action="store_true",
        help="remove a serie temporal (arquivo bem menor, sem grafico de throttling)",
    )
    ap.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="CAMPO=VALOR",
        help="filtra por campo de contexto, ex.: --filter backend=gpu",
    )
    ap.add_argument("--downsample", type=int, default=1,
                    help="mantem 1 a cada N amostras da serie temporal")
    args = ap.parse_args()

    filters = [f.split("=", 1) for f in args.filter]
    runs = []
    for path in sorted(RUNS_DIR.glob("*/run.json")):
        run = json.loads(path.read_text())
        if filters and not matches(run, filters):
            continue
        if args.no_samples:
            run["samples"] = []
        elif args.downsample > 1:
            run["samples"] = run.get("samples", [])[:: args.downsample]
        runs.append(run)

    if not runs:
        print(f"[!] nenhum run.json encontrado em {RUNS_DIR}")
        print("    execucoes antigas so tem meta.json/summary.json — rode de novo "
              "ou abra os dois arquivos direto no viewer.")
        return

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"schema_version": "1.0", "n_runs": len(runs), "runs": runs},
            ensure_ascii=False,
        )
    )
    size_kb = out.stat().st_size / 1024
    print(f"[ok] {len(runs)} resultado(s) -> {out} ({size_kb:.0f} KB)")
    print("     abra viewer/index.html e carregue esse arquivo")


if __name__ == "__main__":
    main()
