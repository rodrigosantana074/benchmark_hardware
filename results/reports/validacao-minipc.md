# Validação do pipeline — Mini PC

Status em 2026-08-14. Device: `minipc-rtx3050-01`.

---

## O que essa rodada prova

Que a esteira de medição funciona de ponta a ponta num device real:
detecção de hardware, orquestração do teste, telemetria em paralelo,
gravação de resultado versionado.

A carga usada é sintética — não roda modelo nenhum.

---

## Hardware testado

| Item | Valor |
|---|---|
| CPU | Intel i5-8500T, 6 cores |
| RAM | 32 GB |
| GPU | NVIDIA RTX 3050, 6 GB |
| SO | Ubuntu 24.04.4, kernel 6.17 |
| Acesso | SSH remoto (Cloudflare Tunnel) |

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

## Inferência real — LFM2-350M, backend `gpu`

Primeiro benchmark de IA de verdade do projeto, não mais carga sintética.
`llama.cpp` (servidor, imagem `ghcr.io/ggml-org/llama.cpp:server-cuda`)
rodando em container Docker isolado, modelo `LiquidAI/LFM2-350M-GGUF:Q4_K_M`
baixado direto do Hugging Face. Cenário `baseline`, 5/5 repetições OK.
`run_id: 20260814T191545Z__minipc-rtx3050-01__slm-latency__gpu__baseline`.

### Desempenho

| Métrica | mean | p50 | p95 | min | max | n |
|---|---|---|---|---|---|---|
| wall_time_s | 1.5908 | 1.59 | 1.59 | — | — | — |
| ttft_ms | 21.46 | 21.46 | 21.48 | 21.44 | 21.48 | 5 |
| latency_ms | 1471.67 | 1471.64 | 1472.04 | 1471.41 | 1472.12 | 5 |
| throughput_tok_s | 88.266 | 88.27 | 88.28 | 88.24 | 88.28 | 5 |

### Recursos

| Campo | Valor |
|---|---|
| n_samples / interval_s | 8 / 1.0 s |
| avg_cpu_pct / peak_cpu_pct | 14.96% / 17.3% |
| avg_ram_used_mb / peak_ram_used_mb | 2591.07 MB / 2619.2 MB |
| avg_gpu_pct / peak_gpu_pct | **93.38% / 98.0%** |
| temp_start_c / avg_temp_c / max_temp_c | 53.0 °C / 56.25 °C / 57.0 °C |
| avg_power_w / peak_power_w / energy_j | null / null / null (sem sensor de board no x86) |
| avg_gpu_power_w / peak_gpu_power_w | 25.61 W / 26.23 W |
| energy_gpu_j | 183.65 J |
| gpu_power_source | nvidia-smi |

### Métricas derivadas

| Métrica | Valor |
|---|---|
| energy_per_tok_mj | null (depende de energy_j, que é null) |
| tok_s_per_w | null (depende de avg_power_w, que é null) |
| tok_s_per_gb | 34.508 |

### Iterações individuais

| # | wall_time_s | ttft_ms | latency_ms | throughput_tok_s | tokens_out |
|---|---|---|---|---|---|
| 1 | 1.5919 | 21.45 | 1472.12 | 88.24 | 128 |
| 2 | 1.5902 | 21.48 | 1471.74 | 88.26 | 128 |
| 3 | 1.5905 | 21.47 | 1471.64 | 88.27 | 128 |
| 4 | 1.5904 | 21.46 | 1471.41 | 88.28 | 128 |
| 5 | 1.5909 | 21.44 | 1471.44 | 88.28 | 128 |

### Comparado com a carga sintética (mesmo device, mesmo backend)

| Sinal | Sintética (dia anterior) | Inferência real |
|---|---|---|
| avg_gpu_pct | 0.0% | 93.38% |
| avg_gpu_power_w | 6.54 W | 25.61 W |
| avg_temp_c | 44.82 °C | 56.25 °C |
| throughput_tok_s | 59.52 (número de mentira) | 88.266 (real) |

A diferença de uso de GPU, potência e temperatura entre as duas rodadas é o
sinal de que dessa vez o hardware foi exigido de verdade — é o que faltava
pra dizer que a esteira de medição também captura carga real, não só a
simulação.

---

## Inferência real — LFM2-350M, backend `cpu`

Mesmo modelo, mesmo cenário, agora sem GPU — `llama.cpp` (imagem
`ghcr.io/ggml-org/llama.cpp:server`, sem CUDA) em container. 5/5 repetições
OK. `run_id: 20260814T194605Z__minipc-rtx3050-01__slm-latency__cpu__baseline`.

### Desempenho

| Métrica | mean | p50 | p95 | min | max | n |
|---|---|---|---|---|---|---|
| wall_time_s | 1.4359 | 1.34 | 1.72 | — | — | — |
| ttft_ms | 15.294 | 12.94 | 20.27 | 12.78 | 21.16 | 5 |
| latency_ms | 1318.62 | 1219.23 | 1605.2 | 1213.11 | 1693.62 | 5 |
| throughput_tok_s | 99.096 | 105.27 | 105.9 | 75.94 | 105.93 | 5 |

Repare na variação: p95/max bem acima da mediana, e a iteração 5 destoa das
outras (ver tabela de iterações). Diferente da GPU, que saiu com desvio
mínimo entre repetições.

### Recursos

| Campo | Valor |
|---|---|
| n_samples / interval_s | 7 / 1.0 s |
| avg_cpu_pct / peak_cpu_pct | **94.59% / 100.0%** |
| avg_ram_used_mb / peak_ram_used_mb | 3899.89 MB / 3920.4 MB |
| avg_gpu_pct / peak_gpu_pct | 0.0% / 0.0% |
| temp_start_c / avg_temp_c / max_temp_c | 60.0 °C / 61.71 °C / 65.0 °C |
| avg_power_w / peak_power_w / energy_j | null / null / null (sem sensor de board no x86) |
| avg_gpu_power_w / peak_gpu_power_w | 6.5 W / 6.77 W (GPU ociosa, não usada) |
| energy_gpu_j | 40.7 J |
| gpu_power_source | nvidia-smi |

### Métricas derivadas

| Métrica | Valor |
|---|---|
| energy_per_tok_mj | null |
| tok_s_per_w | null |
| tok_s_per_gb | 25.884 |

### Iterações individuais

| # | wall_time_s | ttft_ms | latency_ms | throughput_tok_s | tokens_out |
|---|---|---|---|---|---|
| 1 | 1.3348 | 16.73 | 1215.61 | 105.93 | 128 |
| 2 | 1.3300 | 12.78 | 1213.11 | 105.80 | 128 |
| 3 | 1.3371 | 12.86 | 1219.23 | 105.27 | 128 |
| 4 | 1.3686 | 12.94 | 1251.53 | 102.54 | 128 |
| 5 | 1.8091 | 21.16 | 1693.62 | 75.94 | 128 |

A iteração 5 tem latência ~40% maior e throughput ~28% menor que as outras
quatro — a temperatura já tinha subido pro pico (65°C) nesse ponto, e a
máquina tem uma sessão gráfica remota ativa competindo por CPU. Não dá pra
afirmar qual das duas causas pesou mais sem repetir com mais amostras.

---

## Comparação direta — cpu vs. gpu, inferência real

| Métrica | cpu | gpu |
|---|---|---|
| throughput_tok_s (mean) | **99.10** | 88.27 |
| throughput_tok_s (variação min–max) | 75.94 – 105.93 (instável) | 88.24 – 88.28 (estável) |
| ttft_ms (mean) | 15.29 | 21.46 |
| latency_ms (mean) | 1318.62 | 1471.67 |
| avg_cpu_pct | 94.59% | 14.96% |
| avg_gpu_pct | 0.0% | 93.38% |
| avg_ram_used_mb | 3899.89 MB | 2591.07 MB |
| avg_temp_c / max_temp_c | 61.71 °C / 65.0 °C | 56.25 °C / 57.0 °C |
| avg_gpu_power_w | 6.5 W (ociosa) | 25.61 W (em uso) |

Achado real, não esperado de antemão: pra esse modelo pequeno (350M
parâmetros), o `cpu` saiu com throughput médio **mais alto** que o `gpu`
nessa máquina — mas com quase o triplo de variação entre repetições, mais
uso de RAM, e mais aquecimento. A GPU entregou número mais baixo só na
média, só que extremamente consistente entre as 5 repetições. Qual
"vence" depende do que importa mais pro caso de uso: throughput de pico ou
previsibilidade — exatamente o tipo de resposta que esse projeto existe
pra dar, em vez de eleger um vencedor absoluto.

Isso é só uma repetição de 5 amostras; não é conclusivo, é sinal. Cenários
com contexto maior, modelo maior, ou carga sustentada tendem a inverter
isso — GPU historicamente escala melhor conforme o tamanho do modelo cresce.

---

## Encontrado no caminho

- Bug real: variável `$MODEL_PATH` não definida quebrava o comando no shell
  do Linux (funcionava por acidente no ambiente de teste no Windows).
  Corrigido e validado antes da primeira rodada.
- O `llama.cpp` em modo interativo/chat entra num loop esperando entrada que
  nunca chega quando rodado sem terminal de verdade — resolvido usando o
  servidor HTTP (`llama-server`) em vez do modo linha de comando, com um
  script tradutor (`workloads/llama_docker_workload.py`) que lê os tempos
  exatos do JSON de resposta do servidor.

---

## Falta pra fechar

- Raspberry Pi 5 (Hailo e Coral) — pipeline ainda não testado neles
- Métrica de energia do sistema inteiro — só a GPU é medida; falta sensor
  externo ou wattímetro pra fechar `energy_per_tok_mj`/`tok_s_per_w`
- Cenários além de `baseline` (mem_constrained, thermal_sustained,
  concurrent) — ainda não exercitados com inferência real
- A variação alta no `cpu` (iteração 5) merece mais amostras antes de
  virar conclusão

---

## Próximo passo

Abrir acesso SSH aos dois Raspberry Pi e repetir essa mesma validação —
primeiro com a carga sintética (provar o pipeline), depois com inferência
real.
