# Validação do pipeline — Mini PC

Status em 2026-08-12. Device: `minipc-rtx3050-01`.

---

## O que essa rodada prova

Que a esteira de medição funciona de ponta a ponta num device real:
detecção de hardware, orquestração do teste, telemetria em paralelo,
gravação de resultado versionado.

**Não é benchmark de desempenho real.** A carga usada é sintética —
não roda modelo nenhum. Isso vem depois.

---

## Hardware testado

| Item | Valor |
|---|---|
| CPU | Intel i5-8500T, 6 cores |
| RAM | 32 GB |
| GPU | NVIDIA RTX 3050, 6 GB |
| SO | Ubuntu 24.04.4, kernel 6.17 |
| Acesso | SSH remoto (túnel Cloudflare) |

GPU real diverge da especificação original (constava RTX PRO 2000 16GB) —
sinalizado, aguardando confirmação de qual spec é a correta.

---

## O que foi validado

- Catalogação automática de hardware (`collect_hw_info.py`)
- Gate térmico (aguarda esfriar antes de medir)
- Aquecimento descartado + 5 repetições medidas
- Telemetria por amostra: CPU%, RAM, temperatura, uso e potência de GPU
- Dois backends: `cpu` e `gpu`, cenário `baseline` — **5/5 repetições OK** nos dois

---

## Resultados completos

Os números de `cpu` e `gpu` saem praticamente idênticos **de propósito** —
é a carga sintética, tem um teto de tempo fixo, não mede computação real.
Não interpretar isso como "CPU e GPU empatam": ainda não houve inferência
de verdade nenhuma. Os dados abaixo são o `summary.json` completo de cada
execução, sem corte.

### Desempenho — backend `cpu`

| Métrica | mean | p50 | p95 | min | max | n |
|---|---|---|---|---|---|---|
| wall_time_s | 2.1809 | 2.18 | 2.18 | — | — | — |
| ttft_ms | 150.292 | 150.32 | 150.32 | 150.19 | 150.32 | 5 |
| latency_ms | 2150.572 | 2150.62 | 2150.65 | 2150.43 | 2150.65 | 5 |
| throughput_tok_s | 59.52 | 59.52 | 59.52 | 59.52 | 59.52 | 5 |

### Desempenho — backend `gpu`

| Métrica | mean | p50 | p95 | min | max | n |
|---|---|---|---|---|---|---|
| wall_time_s | 2.1808 | 2.18 | 2.18 | — | — | — |
| ttft_ms | 150.318 | 150.32 | 150.32 | 150.31 | 150.32 | 5 |
| latency_ms | 2150.604 | 2150.65 | 2150.65 | 2150.43 | 2150.65 | 5 |
| throughput_tok_s | 59.52 | 59.52 | 59.52 | 59.52 | 59.52 | 5 |

### Recursos — backend `cpu`

| Campo | Valor |
|---|---|
| n_samples / interval_s | 11 / 1.0 s |
| avg_cpu_pct / peak_cpu_pct | 0.71% / 2.3% |
| avg_ram_used_mb / peak_ram_used_mb | 1947.88 MB / 1952.8 MB |
| peak_proc_rss_mb | null (não capturado nessa rodada) |
| avg_gpu_pct / peak_gpu_pct | 0.0% / 0.0% |
| temp_start_c / avg_temp_c / max_temp_c | 45.0 °C / 44.82 °C / 45.0 °C |
| avg_power_w / peak_power_w / energy_j | null / null / null |
| power_source | unavailable (sem sensor de board no x86) |
| avg_gpu_power_w / peak_gpu_power_w | 6.58 W / 6.77 W |
| energy_gpu_j | 68.06 J |
| gpu_power_source | nvidia-smi |

### Recursos — backend `gpu`

| Campo | Valor |
|---|---|
| n_samples / interval_s | 11 / 1.0 s |
| avg_cpu_pct / peak_cpu_pct | 0.71% / 2.4% |
| avg_ram_used_mb / peak_ram_used_mb | 1954.45 MB / 1959.5 MB |
| peak_proc_rss_mb | null (não capturado nessa rodada) |
| avg_gpu_pct / peak_gpu_pct | 0.0% / 0.0% |
| temp_start_c / avg_temp_c / max_temp_c | 46.0 °C / 44.82 °C / 46.0 °C |
| avg_power_w / peak_power_w / energy_j | null / null / null |
| power_source | unavailable (sem sensor de board no x86) |
| avg_gpu_power_w / peak_gpu_power_w | 6.54 W / 6.74 W |
| energy_gpu_j | 67.65 J |
| gpu_power_source | nvidia-smi |

### Métricas derivadas

| Métrica | cpu | gpu |
|---|---|---|
| energy_per_tok_mj | null (depende de energy_j, que é null) | null |
| tok_s_per_w | null (depende de avg_power_w, que é null) | null |
| tok_s_per_gb | 31.211 | 31.104 |

### Iterações individuais — backend `cpu`

| # | wall_time_s | ttft_ms | latency_ms | throughput_tok_s | tokens_out |
|---|---|---|---|---|---|
| 1 | 2.1814 | 150.32 | 2150.62 | 59.52 | 128 |
| 2 | 2.1807 | 150.32 | 2150.65 | 59.52 | 128 |
| 3 | 2.1806 | 150.19 | 2150.52 | 59.52 | 128 |
| 4 | 2.1805 | 150.32 | 2150.43 | 59.52 | 128 |
| 5 | 2.1812 | 150.31 | 2150.64 | 59.52 | 128 |

### Iterações individuais — backend `gpu`

| # | wall_time_s | ttft_ms | latency_ms | throughput_tok_s | tokens_out |
|---|---|---|---|---|---|
| 1 | 2.1810 | 150.32 | 2150.43 | 59.52 | 128 |
| 2 | 2.1816 | 150.31 | 2150.65 | 59.52 | 128 |
| 3 | 2.1807 | 150.32 | 2150.65 | 59.52 | 128 |
| 4 | 2.1803 | 150.32 | 2150.65 | 59.52 | 128 |
| 5 | 2.1804 | 150.32 | 2150.64 | 59.52 | 128 |

Todas as 10 iterações (5+5) retornaram código 0 — nenhuma falha.

### Catálogo de hardware completo

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

---

## Encontrado no caminho

Bug real: variável `$MODEL_PATH` não definida quebrava o comando no shell
do Linux (funcionava por acidente no ambiente de teste no Windows).
Corrigido e validado nessa mesma rodada.

---

## Falta pra fechar

- Raspberry Pi 5 (Hailo e Coral) — pipeline ainda não testado neles
- Inferência real: `llama.cpp` + modelo LFM2-350M na máquina — fase seguinte
- Confirmar spec correta da GPU do mini PC

---

## Próximo passo

Abrir acesso SSH aos dois Raspberry Pi e repetir essa mesma validação.
