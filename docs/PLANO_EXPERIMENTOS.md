# Plano de experimentos

Cada célula preenchida corresponde a uma pasta em `results/runs/`.

## Dimensões

- **Dispositivo:** conforme catálogo em `hardware/devices/`
- **Backend:** `cpu`, `gpu`, `npu`
- **Modelo:** ao menos um SLM alvo e um baseline para contraste
- **Cenário:** `baseline`, `low_power`, `mem_constrained`, `thermal_sustained`, `concurrent`

## Hardware disponível

| device_id | Placa | Acelerador | Backends aplicáveis |
|---|---|---|---|
| `minipc-rtx2000-01` | Mini PC, i5-8500T, 32GB | RTX PRO 2000 16GB | `cpu`, `gpu` |
| `rpi5-hailo-01` | Raspberry Pi 5, 16GB | Hailo | `cpu`, `npu`* |
| `rpi5-coral-01` | Raspberry Pi 5, 16GB | Coral Edge TPU | `cpu`, `npu`* |
| Jetson | — | — | sem hardware ainda |

\* Ver seção **Escopo do backend `npu`** — Hailo e Coral não rodam decode
autoregressivo de SLM nas condições atuais. `npu` fica restrito ao benchmark
`vision-classify` até essa lacuna fechar.

## Grade

| Dispositivo | Backend | Cenário | Status |
|---|---|---|---|
| `minipc-rtx2000-01` | cpu | baseline | pendente |
| `minipc-rtx2000-01` | gpu | baseline | pendente |
| `minipc-rtx2000-01` | gpu | low_power | pendente |
| `minipc-rtx2000-01` | gpu | thermal_sustained | pendente |
| `minipc-rtx2000-01` | cpu | mem_constrained | pendente |
| `rpi5-hailo-01` | cpu | baseline | pendente |
| `rpi5-hailo-01` | cpu | low_power | pendente |
| `rpi5-hailo-01` | cpu | mem_constrained | pendente |
| `rpi5-hailo-01` | cpu | thermal_sustained | pendente |
| `rpi5-coral-01` | cpu | baseline | pendente |
| `rpi5-coral-01` | cpu | low_power | pendente |
| `rpi5-coral-01` | cpu | mem_constrained | pendente |
| `rpi5-coral-01` | cpu | thermal_sustained | pendente |
| Jetson | * | * | sem hardware ainda |

Manter o mesmo modelo e a mesma quantização em toda a grade. Variar o modelo é
um segundo eixo, rodado depois que o primeiro fecha.

## Escopo do backend `npu`

Hailo-8 e Coral Edge TPU são aceleradores de CNN. O compilador de cada um
(Hailo Dataflow Compiler, Edge TPU Compiler) não sustenta atenção nem shape
dinâmico do jeito que decode token-a-token de um SLM precisa — não é driver
faltando, é a arquitetura do acelerador não encaixar no workload.

Por isso `npu` não entra em `slm-latency` nesses dois dispositivos por
enquanto. Quando `vision-classify` (ver `benchmarks/README.md`) for definido,
`npu` passa a ser medido ali, que é o benchmark que existe pra isso.

## Hipóteses

A comparação só sustenta conclusão se a hipótese for declarada antes da medição.

| # | Hipótese | Como se verifica |
|---|---|---|
| H1 | A GPU vence em throughput bruto, mas perde em energia por token em cargas curtas | comparar `throughput_tok_s` e `energy_per_tok_mj` no cenário `baseline` |
| H2 | Sob carga contínua, a vantagem da GPU diminui por throttling | comparar `baseline` e `thermal_sustained`; confirmar na série temporal |
| H3 | Sob restrição de memória, o backend com menor pico de RAM continua operando onde o outro falha | taxa de execuções com status `failed` por backend em `mem_constrained` |
| H4 | O acelerador dedicado entrega mais throughput por watt que CPU e GPU | comparar `tok_s_per_w`, quando houver medição de potência |

Hipótese refutada é resultado. O que não pode acontecer é medir primeiro e
escolher a conclusão depois.
