# Catálogo de hardware — dicionário de campos

Gerado por `scripts/collect_hw_info.py`. Um JSON por dispositivo.

| Campo | Significado | Origem |
|---|---|---|
| `device_id` | Identificador estável, usado no nome de toda execução | argumento |
| `platform` | Família da placa detectada | `/proc/device-tree/model`, arquivos do fornecedor |
| `board_model` | Modelo da placa | device tree |
| `cpu.model`, `cores_*`, `max_freq_mhz` | Descrição da CPU | `/proc/cpuinfo` e psutil |
| `cpu.governor` | Governor de frequência — afeta o resultado | sysfs |
| `memory.total_mb` | RAM total | psutil |
| `memory.bandwidth_gbps` | Banda de RAM aproximada (leitura+escrita) | `memmove` de um buffer de 256MB, menor tempo entre 5 repetições |
| `accelerator.type` | `gpu_integrated`, `gpu_discrete`, `npu_external` ou `none_or_external` | detectado |
| `accelerator.model` | Descrição do acelerador encontrado | detectado |
| `accelerator.details` | Versões de runtime, presença de acelerador dedicado, identificação em USB/PCIe | sysfs, utilitários do fornecedor |
| `thermal.zones` | Zonas térmicas legíveis e seus caminhos | sysfs |
| `thermal.cooling` | Passiva, ativa ou dissipador | argumento `--cooling` |
| `power.internal_sensor` | Se há sensor de potência acessível por software | sysfs |
| `power.power_source` | `internal` ou `external_required` | derivado |
| `ambient_temp_c` | Temperatura ambiente da medição | argumento `--ambient-temp-c` |
| `software.os`, `kernel`, `python` | Ambiente de execução | sistema |

## Por que o catálogo existe

Dois números iguais podem vir de configurações completamente diferentes:
governor distinto, refrigeração distinta, versão de runtime distinta. O catálogo
é o que separa uma medição reproduzível de um número isolado.

## Banda de memória

`memory.bandwidth_gbps` não é pico teórico nem substitui uma ferramenta
dedicada (STREAM, `sysbench memory`) — é uma medida relativa, feita do
mesmo jeito (via `ctypes.memmove`, sem depender de pacote externo nem
`sudo`) em qualquer device, pra permitir comparar CPU/GPU/dispositivos
entre si. Não compare esse número com benchmark publicado de fabricante;
compare só entre devices catalogados por este mesmo script.

Motivação: inferência de LLM tende a ser limitada por banda de memória,
não por poder de cálculo bruto — a cada token gerado, o hardware relê os
pesos do modelo inteiro. Esse campo existe pra dar uma pista de *por que*
um backend rende mais tokens/s que outro, além do resultado em si.

## Aceleradores

`accelerator` reflete o que estava presente no momento da coleta. A detecção
cobre GPU integrada em plataformas embarcadas, GPU discreta e aceleradores
externos identificáveis em USB ou PCIe. Se o acelerador do dispositivo mudar,
refaça a coleta: o backend `npu` de qualquer spec depende dessa informação.
