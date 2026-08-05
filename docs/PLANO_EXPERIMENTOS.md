# Plano de experimentos

Cada célula preenchida corresponde a uma pasta em `results/runs/`.

## Dimensões

- **Dispositivo:** conforme catálogo em `hardware/devices/`
- **Backend:** `cpu`, `gpu`, `npu`
- **Modelo:** ao menos um SLM alvo e um baseline para contraste
- **Cenário:** `baseline`, `low_power`, `mem_constrained`, `thermal_sustained`, `concurrent`

## Grade

| Dispositivo | Backend | Cenário | Status |
|---|---|---|---|
| Jetson | cpu | baseline | pendente |
| Jetson | gpu | baseline | pendente |
| Jetson | gpu | low_power | pendente |
| Jetson | gpu | thermal_sustained | pendente |
| Jetson | cpu | mem_constrained | pendente |
| Jetson | npu | baseline | pendente |
| Raspberry Pi | cpu | baseline | pendente |
| Raspberry Pi | cpu | low_power | pendente |
| Raspberry Pi | cpu | mem_constrained | pendente |
| Raspberry Pi | cpu | thermal_sustained | pendente |
| Raspberry Pi | npu | baseline | depende do acelerador disponível |

Manter o mesmo modelo e a mesma quantização em toda a grade. Variar o modelo é
um segundo eixo, rodado depois que o primeiro fecha.

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
