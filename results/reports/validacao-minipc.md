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

## Hardware

| Item | Valor |
|---|---|
| CPU | Intel i5-8500T, 6 cores, governor `powersave` |
| RAM | 32 GB (31931 MB) |
| GPU | NVIDIA RTX 3050, 6 GB (6144 MiB) |
| SO / kernel | Ubuntu 24.04.4 LTS / 6.17.0-35-generic |
| Armazenamento | 915 GB total, 787 GB livre |
| Acesso | SSH remoto via Cloudflare Tunnel |

Catálogo completo em `hardware/devices/minipc-rtx3050-01.json`.

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

## Validação com carga sintética

Cenário `baseline`, 5/5 repetições OK nos dois backends. Serve só pra
provar o mecanismo — a carga tem teto de tempo fixo, não computa nada.

| Métrica | cpu | gpu |
|---|---|---|
| ttft_ms (mean) | 150.29 | 150.32 |
| latency_ms (mean) | 2150.57 | 2150.60 |
| throughput_tok_s (mean) | 59.52 | 59.52 |
| avg_cpu_pct | 0.71% | 0.71% |
| avg_ram_used_mb | 1947.88 | 1954.45 |
| avg_gpu_pct | 0.0% | 0.0% |
| avg_temp_c / max_temp_c | 44.82 °C / 45.0 °C | 44.82 °C / 46.0 °C |
| avg_gpu_power_w | 6.58 W | 6.54 W |
| tok_s_per_gb | 31.211 | 31.104 |

Variação entre as 5 repetições de cada backend: sub-0.01% em toda métrica
de desempenho — assinatura de simulação com teto fixo, não de computação
real. `avg_power_w`/`energy_j` (potência do sistema inteiro, não só da
GPU) ficaram `null`: esse mini PC não tem sensor de board como a Jetson;
sem wattímetro externo, esse campo continua vazio em qualquer rodada
futura nesse device.

`run_id`s: `20260812T000804Z__minipc-rtx3050-01__slm-latency__cpu__baseline`,
`20260811T194531Z__minipc-rtx3050-01__slm-latency__gpu__baseline`.

---

## Inferência real — LFM2-350M

`llama.cpp` (servidor HTTP, `ghcr.io/ggml-org/llama.cpp:server[-cuda]`) em
contêiner, modelo `LiquidAI/LFM2-350M-GGUF:Q4_K_M` baixado do Hugging
Face. Cenário `baseline`, 5/5 repetições OK nos dois backends.

| Métrica | cpu | gpu |
|---|---|---|
| throughput_tok_s (mean) | **99.10** | 88.27 |
| throughput_tok_s (min–max) | 75.94 – 105.93 | 88.24 – 88.28 |
| ttft_ms (mean) | 15.29 | 21.46 |
| latency_ms (mean) | 1318.62 | 1471.67 |
| avg_cpu_pct | 94.59% | 14.96% |
| avg_gpu_pct | 0.0% | 93.38% |
| avg_ram_used_mb | 3899.89 | 2591.07 |
| avg_temp_c / max_temp_c | 61.71 °C / 65.0 °C | 56.25 °C / 57.0 °C |
| avg_gpu_power_w | 6.5 (ociosa) | 25.61 |
| energy_gpu_j | 40.7 | 183.65 |
| tok_s_per_gb | 25.884 | 34.508 |

`run_id`s: `20260814T194605Z__minipc-rtx3050-01__slm-latency__cpu__baseline`,
`20260814T191545Z__minipc-rtx3050-01__slm-latency__gpu__baseline`.

**Leitura.** `cpu` entrega throughput médio mais alto, mas com quase 3x
mais variação entre repetições — a iteração 5 (75.94 tok/s, 1693 ms de
latência) destoa das outras quatro (todas acima de 100 tok/s), coincidindo
com o pico de temperatura (65°C) e com uma sessão gráfica remota ativa
disputando CPU na máquina:

| # | latency_ms | throughput_tok_s |
|---|---|---|
| 1 | 1215.61 | 105.93 |
| 2 | 1213.11 | 105.80 |
| 3 | 1219.23 | 105.27 |
| 4 | 1251.53 | 102.54 |
| 5 | 1693.62 | 75.94 |

`gpu` é mais lento na média, mas com variação abaixo de 0.05% entre as 5
repetições. Cinco amostras não bastam pra generalizar — é sinal, não
conclusão. O contraste antes/depois confirma que a telemetria captura
carga real, não só simulação: uso de GPU foi de 0% (carga sintética) pra
93% aqui, potência de 6.5W pra 25.6W quando processando.

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

- Raspberry Pi 5 (Hailo e Coral) — pipeline ainda não testado neles.
- Energia do sistema inteiro — só a GPU é medida hoje; falta sensor
  externo ou wattímetro.
- Cenários além de `baseline` (`mem_constrained`, `thermal_sustained`,
  `concurrent`) — ainda não exercitados com inferência real.
- Confirmar com o dono do equipamento se a divergência de GPU (RTX PRO
  2000 vs RTX 3050) é outra unidade ou erro de especificação.
- Variação alta do `cpu` na inferência real precisa de mais amostras antes
  de virar conclusão.

**Próximo passo:** repetir essa validação (sintética, depois real) nos
dois Raspberry Pi.
