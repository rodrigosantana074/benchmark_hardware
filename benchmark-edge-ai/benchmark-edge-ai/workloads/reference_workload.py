#!/usr/bin/env python3
"""
Implementacao de referencia do contrato de carga.

Nao faz inferencia. Existe para validar o pipeline de medicao ponta a ponta e
para documentar o unico requisito que uma carga real precisa cumprir: imprimir
como ultima linha da saida padrao

    METRICS:{"ttft_ms": ..., "latency_ms": ..., "throughput_tok_s": ..., "tokens_out": ...}

Metricas de recurso (RAM, CPU, GPU, temperatura, potencia) sao coletadas em
paralelo pelo monitor. A carga nao mede nada disso.
"""

import argparse
import json
import random
import time

ap = argparse.ArgumentParser()
ap.add_argument("--device", default="cpu")
ap.add_argument("--model", default="reference")
ap.add_argument("--n-predict", type=int, default=128)
ap.add_argument("--concurrency", type=int, default=1)
ap.add_argument("--duration", type=float, default=None)
ap.add_argument("--seed", type=int, default=42)
a = ap.parse_args()

random.seed(a.seed)

t0 = time.perf_counter()
time.sleep(0.15)  # ocupa o lugar do prefill
ttft_ms = (time.perf_counter() - t0) * 1000

tok_s = {"cpu": 8.0, "cuda": 24.0, "npu": 15.0}.get(a.device, 8.0)
time.sleep(min(a.n_predict / tok_s, 2.0))  # ocupa o lugar da geracao
latency_ms = (time.perf_counter() - t0) * 1000

print(f"[ref] device={a.device} model={a.model} n_predict={a.n_predict}")
print(
    "METRICS:"
    + json.dumps(
        {
            "ttft_ms": round(ttft_ms, 2),
            "latency_ms": round(latency_ms, 2),
            "throughput_tok_s": round(a.n_predict / (latency_ms / 1000), 2),
            "tokens_out": a.n_predict,
        }
    )
)
