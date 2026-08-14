#!/usr/bin/env python3
"""
llama_docker_workload.py -- carga real: llama.cpp rodando em container Docker.

Sobe (ou reaproveita, se ja estiver rodando) um llama-server em container,
manda um /completion, le os tempos exatos que o proprio servidor devolve
(mais confiavel que ler texto solto do terminal), e imprime METRICS: no
formato que run_benchmark.py espera.

O servidor NAO e derrubado no final -- fica de pe entre repeticoes pra nao
recarregar o modelo do zero a cada chamada. Derrubar manualmente depois:
    docker stop llama-bench-run

Metricas de recurso (RAM, CPU, GPU, temperatura, potencia) continuam sendo
coletadas em paralelo pelo monitor.py, fora deste script.
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

CONTAINER_NAME = "llama-bench-run"
PORT = 8080
HEALTH_URL = f"http://localhost:{PORT}/health"
COMPLETION_URL = f"http://localhost:{PORT}/completion"


def sh(cmd, timeout=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def server_running():
    out = sh(["docker", "ps", "--filter", f"name=^{CONTAINER_NAME}$", "--format", "{{.Names}}"])
    return CONTAINER_NAME in out.stdout


def start_server(hf_repo, gpu):
    image = "ghcr.io/ggml-org/llama.cpp:server-cuda" if gpu else "ghcr.io/ggml-org/llama.cpp:server"
    cmd = ["docker", "run", "-d", "--rm", "--name", CONTAINER_NAME, "-p", f"{PORT}:8080"]
    if gpu:
        cmd += ["--gpus", "all"]
    cmd += [image, "-hf", hf_repo, "--port", "8080", "--host", "0.0.0.0"]
    r = sh(cmd)
    if r.returncode != 0:
        raise RuntimeError(f"falha ao subir container: {r.stderr.strip()}")


def wait_ready(timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(HEALTH_URL, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def complete(prompt, n_predict):
    body = json.dumps({"prompt": prompt, "n_predict": n_predict}).encode()
    req = urllib.request.Request(
        COMPLETION_URL, data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--model", default="LiquidAI/LFM2-350M-GGUF:Q4_K_M")
    ap.add_argument("--prompt", default="Ola, tudo bem?")
    ap.add_argument("--n-predict", type=int, default=128)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--duration", type=float, default=None)
    a = ap.parse_args()

    gpu = a.device in ("cuda", "gpu")

    if not server_running():
        print(f"[llama] subindo servidor ({'gpu' if gpu else 'cpu'})...", file=sys.stderr)
        start_server(a.model, gpu)
        if not wait_ready():
            print("[erro] servidor nao ficou pronto a tempo", file=sys.stderr)
            sys.exit(1)
    else:
        print("[llama] reaproveitando servidor ja no ar", file=sys.stderr)

    try:
        result = complete(a.prompt, a.n_predict)
    except urllib.error.URLError as e:
        print(f"[erro] falha na chamada ao servidor: {e}", file=sys.stderr)
        sys.exit(1)

    t = result.get("timings", {})
    prompt_ms = t.get("prompt_ms")
    predicted_ms = t.get("predicted_ms")
    predicted_n = t.get("predicted_n")
    predicted_per_second = t.get("predicted_per_second")

    metrics = {
        "ttft_ms": round(prompt_ms, 2) if prompt_ms is not None else None,
        "latency_ms": round((prompt_ms or 0) + (predicted_ms or 0), 2)
        if predicted_ms is not None else None,
        "throughput_tok_s": round(predicted_per_second, 2)
        if predicted_per_second is not None else None,
        "tokens_out": predicted_n,
    }
    print(f"[llama] device={a.device} model={a.model} tokens_out={predicted_n}")
    print("METRICS:" + json.dumps(metrics))


if __name__ == "__main__":
    main()
