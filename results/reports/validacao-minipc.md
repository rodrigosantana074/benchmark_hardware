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

## Números desta rodada

| Métrica | Backend cpu | Backend gpu |
|---|---|---|
| TTFT médio | 150.3 ms | 150.3 ms |
| Latência média | 2150.6 ms | 2150.6 ms |
| Throughput | 59.52 tok/s | 59.52 tok/s |
| Potência GPU (média) | 6.58 W | 6.54 W |
| Temperatura máxima | 45.0 °C | 46.0 °C |

Os números de `cpu` e `gpu` saem praticamente idênticos **de propósito** —
é a carga sintética, tem um teto de tempo fixo, não mede computação real.
Não interpretar isso como "CPU e GPU empatam": ainda não houve inferência
de verdade nenhuma.

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
