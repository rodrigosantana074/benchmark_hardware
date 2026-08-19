# Validação do pipeline — Mini PC

Device: `minipc-rtx3050-01`. Última atualização: 2026-08-14.

---

## Resumo executivo

- Pipeline validado de ponta a ponta em hardware real: detecção de
  hardware, gate térmico, telemetria em paralelo, gravação versionada.
- Dois backends (`cpu`, `gpu`) testados em duas etapas: carga sintética
  (valida o mecanismo) e inferência real do LFM2-350M via `llama.cpp` em
  contêiner Docker.
- Com o modelo real, `cpu` entrega throughput médio mais alto (99.1 tok/s)
  que `gpu` (88.3 tok/s), mas com ~3x mais variação entre repetições. GPU
  é mais lenta na média e muito mais previsível.
- GPU real do device diverge da especificação recebida (RTX 3050 6GB, não
  RTX PRO 2000 16GB) — pendente confirmação.
- Um bug de portabilidade Linux/Windows e um comportamento inesperado do
  `llama.cpp` foram encontrados e corrigidos durante a validação.

---

## Catálogo de hardware completo

| Campo | Valor |
|---|---|
| CPU | Intel Core i5-8500T @ 2.10GHz, 6 cores físicos/lógicos, até 3500 MHz |
| Governor de CPU | powersave |
| RAM total / swap | 31931 MB / 8192 MB |
| GPU | NVIDIA GeForce RTX 3050, 6144 MiB |
| Zonas térmicas | acpitz (thermal_zone0), x86_pkg_temp (thermal_zone1) |
| Refrigeração | ativa |
| Sensor de potência interno | não — `power_source: external_required` |
| Armazenamento | 915 GB total, 787 GB livre (nvme0n1p2) |
| SO | Ubuntu 24.04.4 LTS |
| Kernel | 6.17.0-35-generic |
| Python | 3.12.3 |
| Temperatura ambiente | null (não informada na coleta) |
| Acesso | SSH remoto via Cloudflare Tunnel |

Fonte: `hardware/devices/minipc-rtx3050-01.json`. GPU real diverge da
especificação recebida originalmente (constava RTX PRO 2000 16GB) —
pendente confirmação com o dono do equipamento.

---

## Metodologia

- `collect_hw_info.py` cataloga o hardware automaticamente.
- `run_benchmark.py` aplica gate térmico (aguarda ≤45°C), descarta 2
  repetições de aquecimento, mede 5 repetições por backend/cenário.
- `monitor.py` roda em paralelo à carga, amostrando CPU/RAM/temperatura/GPU
  a cada segundo — independente do que a carga reporta.
- Duas cargas: `reference_workload.py` (sintética, sem computação real) e
  `llama_docker_workload.py` (real — `llama.cpp` servindo o LFM2-350M via
  HTTP dentro de um contêiner, métricas lidas do JSON de resposta).

---

## Etapa 1 — Validação com carga sintética

Cenário `baseline`, 5/5 repetições OK nos dois backends. Objetivo: provar
que a esteira de medição (detecção de hardware, gate térmico, telemetria
paralela, gravação) funciona antes de confiar nela pra medir algo real. A
carga sintética tem teto de tempo fixo e não computa nada — não é
resultado de desempenho, é validação de instrumento.

### Desempenho

| Métrica | mean | p50 | p95 | min | max | n |
|---|---|---|---|---|---|---|
| **cpu** — wall_time_s | 2.1809 | 2.18 | 2.18 | — | — | — |
| **cpu** — ttft_ms | 150.292 | 150.32 | 150.32 | 150.19 | 150.32 | 5 |
| **cpu** — latency_ms | 2150.572 | 2150.62 | 2150.65 | 2150.43 | 2150.65 | 5 |
| **cpu** — throughput_tok_s | 59.52 | 59.52 | 59.52 | 59.52 | 59.52 | 5 |
| **gpu** — wall_time_s | 2.1808 | 2.18 | 2.18 | — | — | — |
| **gpu** — ttft_ms | 150.318 | 150.32 | 150.32 | 150.31 | 150.32 | 5 |
| **gpu** — latency_ms | 2150.604 | 2150.65 | 2150.65 | 2150.43 | 2150.65 | 5 |
| **gpu** — throughput_tok_s | 59.52 | 59.52 | 59.52 | 59.52 | 59.52 | 5 |

### Recursos

| Campo | cpu | gpu |
|---|---|---|
| n_samples / interval_s | 11 / 1.0 s | 11 / 1.0 s |
| avg_cpu_pct / peak_cpu_pct | 0.71% / 2.3% | 0.71% / 2.4% |
| avg_ram_used_mb / peak_ram_used_mb | 1947.88 / 1952.8 MB | 1954.45 / 1959.5 MB |
| peak_proc_rss_mb | null (não capturado) | null (não capturado) |
| avg_gpu_pct / peak_gpu_pct | 0.0% / 0.0% | 0.0% / 0.0% |
| temp_start_c / avg_temp_c / max_temp_c | 45.0 / 44.82 / 45.0 °C | 46.0 / 44.82 / 46.0 °C |
| avg_power_w / peak_power_w / energy_j | null / null / null | null / null / null |
| power_source | unavailable | unavailable |
| avg_gpu_power_w / peak_gpu_power_w | 6.58 / 6.77 W | 6.54 / 6.74 W |
| energy_gpu_j | 68.06 J | 67.65 J |
| gpu_power_source | nvidia-smi | nvidia-smi |

`avg_power_w`/`energy_j` (potência do sistema inteiro, não só da GPU)
ficam `null`: esse mini PC não tem sensor de board como a Jetson. Sem
wattímetro externo, esse campo continua vazio em qualquer rodada futura
nesse device.

### Métricas derivadas

| Métrica | cpu | gpu |
|---|---|---|
| energy_per_tok_mj | null (depende de energy_j) | null |
| tok_s_per_w | null (depende de avg_power_w) | null |
| tok_s_per_gb | 31.211 | 31.104 |

### Iterações individuais

| # | backend | wall_time_s | ttft_ms | latency_ms | throughput_tok_s | tokens_out |
|---|---|---|---|---|---|---|
| 1 | cpu | 2.1814 | 150.32 | 2150.62 | 59.52 | 128 |
| 2 | cpu | 2.1807 | 150.32 | 2150.65 | 59.52 | 128 |
| 3 | cpu | 2.1806 | 150.19 | 2150.52 | 59.52 | 128 |
| 4 | cpu | 2.1805 | 150.32 | 2150.43 | 59.52 | 128 |
| 5 | cpu | 2.1812 | 150.31 | 2150.64 | 59.52 | 128 |
| 1 | gpu | 2.1810 | 150.32 | 2150.43 | 59.52 | 128 |
| 2 | gpu | 2.1816 | 150.31 | 2150.65 | 59.52 | 128 |
| 3 | gpu | 2.1807 | 150.32 | 2150.65 | 59.52 | 128 |
| 4 | gpu | 2.1803 | 150.32 | 2150.65 | 59.52 | 128 |
| 5 | gpu | 2.1804 | 150.32 | 2150.64 | 59.52 | 128 |

Todas as 10 iterações (5+5) retornaram código 0. Variação entre repetições,
em qualquer métrica, sub-0.01% — assinatura de simulação com teto de tempo
fixo, não de computação real. Esse padrão de variância quase nula é, em si,
um dado: contrasta com a variação real observada na etapa 2 (ver iteração 5
do `cpu` real, abaixo), e serve de linha de base pra reconhecer quando uma
medição futura está ou não capturando carga de verdade.

`run_id`s: `20260812T000804Z__minipc-rtx3050-01__slm-latency__cpu__baseline`,
`20260811T194531Z__minipc-rtx3050-01__slm-latency__gpu__baseline`.

---

## Etapa 2 — Inferência real (LFM2-350M)

`llama.cpp` (servidor HTTP, imagens `ghcr.io/ggml-org/llama.cpp:server` e
`:server-cuda`) rodando em contêiner Docker isolado, modelo
`LiquidAI/LFM2-350M-GGUF:Q4_K_M` baixado direto do Hugging Face. Mesmo
cenário `baseline`, 5/5 repetições OK nos dois backends.

### Desempenho

| Métrica | mean | p50 | p95 | min | max | n |
|---|---|---|---|---|---|---|
| **cpu** — wall_time_s | 1.4359 | 1.34 | 1.72 | — | — | — |
| **cpu** — ttft_ms | 15.294 | 12.94 | 20.27 | 12.78 | 21.16 | 5 |
| **cpu** — latency_ms | 1318.62 | 1219.23 | 1605.2 | 1213.11 | 1693.62 | 5 |
| **cpu** — throughput_tok_s | 99.096 | 105.27 | 105.9 | 75.94 | 105.93 | 5 |
| **gpu** — wall_time_s | 1.5908 | 1.59 | 1.59 | — | — | — |
| **gpu** — ttft_ms | 21.46 | 21.46 | 21.48 | 21.44 | 21.48 | 5 |
| **gpu** — latency_ms | 1471.67 | 1471.64 | 1472.04 | 1471.41 | 1472.12 | 5 |
| **gpu** — throughput_tok_s | 88.266 | 88.27 | 88.28 | 88.24 | 88.28 | 5 |

### Recursos

| Campo | cpu | gpu |
|---|---|---|
| n_samples / interval_s | 7 / 1.0 s | 8 / 1.0 s |
| avg_cpu_pct / peak_cpu_pct | 94.59% / 100.0% | 14.96% / 17.3% |
| avg_ram_used_mb / peak_ram_used_mb | 3899.89 / 3920.4 MB | 2591.07 / 2619.2 MB |
| avg_gpu_pct / peak_gpu_pct | 0.0% / 0.0% | 93.38% / 98.0% |
| temp_start_c / avg_temp_c / max_temp_c | 60.0 / 61.71 / 65.0 °C | 53.0 / 56.25 / 57.0 °C |
| avg_power_w / peak_power_w / energy_j | null / null / null | null / null / null |
| power_source | unavailable | unavailable |
| avg_gpu_power_w / peak_gpu_power_w | 6.5 / 6.77 W (ociosa) | 25.61 / 26.23 W (em uso) |
| energy_gpu_j | 40.7 J | 183.65 J |
| gpu_power_source | nvidia-smi | nvidia-smi |

### Métricas derivadas

| Métrica | cpu | gpu |
|---|---|---|
| energy_per_tok_mj | null | null |
| tok_s_per_w | null | null |
| tok_s_per_gb | 25.884 | 34.508 |

### Iterações individuais

| # | backend | wall_time_s | ttft_ms | latency_ms | throughput_tok_s | tokens_out |
|---|---|---|---|---|---|---|
| 1 | cpu | 1.3348 | 16.73 | 1215.61 | 105.93 | 128 |
| 2 | cpu | 1.3300 | 12.78 | 1213.11 | 105.80 | 128 |
| 3 | cpu | 1.3371 | 12.86 | 1219.23 | 105.27 | 128 |
| 4 | cpu | 1.3686 | 12.94 | 1251.53 | 102.54 | 128 |
| 5 | cpu | 1.8091 | 21.16 | 1693.62 | 75.94 | 128 |
| 1 | gpu | 1.5919 | 21.45 | 1472.12 | 88.24 | 128 |
| 2 | gpu | 1.5902 | 21.48 | 1471.74 | 88.26 | 128 |
| 3 | gpu | 1.5905 | 21.47 | 1471.64 | 88.27 | 128 |
| 4 | gpu | 1.5904 | 21.46 | 1471.41 | 88.28 | 128 |
| 5 | gpu | 1.5909 | 21.44 | 1471.44 | 88.28 | 128 |

`run_id`s: `20260814T194605Z__minipc-rtx3050-01__slm-latency__cpu__baseline`,
`20260814T191545Z__minipc-rtx3050-01__slm-latency__gpu__baseline`.

**Leitura.** `cpu` entrega throughput médio mais alto (99.10 vs. 88.27
tok/s), mas com quase 3x mais variação entre repetições — a iteração 5 do
`cpu` (75.94 tok/s, 1693 ms de latência) destoa das outras quatro (todas
acima de 100 tok/s), coincidindo com o pico de temperatura da série (65°C)
e com uma sessão gráfica remota ativa disputando CPU na máquina. `gpu` é
mais lento na média, mas com variação abaixo de 0.05% entre as 5
repetições — o oposto do `cpu`. Cinco amostras por backend não bastam pra
generalizar; é sinal, não conclusão.

O contraste com a etapa 1 confirma que a telemetria capturou carga real,
não só simulação: uso de GPU foi de 0% (sintética) pra 93.38% aqui,
potência de 6.54W pra 25.61W quando processando, temperatura subiu de
forma real em ambos os backends (a sintética nunca saiu de ~45°C).

---

## Problemas encontrados e resolvidos

- **`$MODEL_PATH` indefinido quebrava o comando no Linux.** Funcionava por
  acidente no ambiente de teste no Windows (expansão de variável de
  ambiente diferente entre shells); corrigido em `run_benchmark.py` antes
  da primeira rodada real.
- **`llama.cpp` em modo linha de comando trava em ambiente não-interativo.**
  Auto-detecta modelo de chat e entra em modo conversa, esperando entrada
  que nunca chega sem terminal alocado. Resolvido rodando como servidor
  HTTP (`llama-server`) com um tradutor (`workloads/llama_docker_workload.py`)
  que lê os tempos exatos do JSON de resposta, em vez de depender de texto
  solto do terminal.

---

## Pendências

- Banda de RAM (`memory.bandwidth_gbps`, ver `docs/CATALOGO_HARDWARE.md`) —
  script já pronto e testado, mas ainda não rodado no mini PC nem nos RPi.
  Motivação: explicar *por que* `cpu` rendeu mais tokens/s que `gpu` no
  LFM2 (inferência de LLM tende a ser limitada por banda de memória, não
  cálculo bruto) — planejado pra amanhã, antes do Raspberry Pi.
- Raspberry Pi 5 (Hailo e Coral) — pipeline ainda não testado neles.
- Energia do sistema inteiro — só a GPU é medida hoje; falta sensor
  externo ou wattímetro.
- Cenários além de `baseline` (`mem_constrained`, `thermal_sustained`,
  `concurrent`) — ainda não exercitados com inferência real.
- Confirmar com o dono do equipamento se a divergência de GPU (RTX PRO
  2000 vs RTX 3050) é outra unidade ou erro de especificação.
- Variação alta do `cpu` na inferência real precisa de mais amostras antes
  de virar conclusão.

**Próximo passo:** repetir essa validação (etapa 1, depois etapa 2) nos
dois Raspberry Pi.
