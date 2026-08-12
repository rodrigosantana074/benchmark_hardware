# Resumo — validação do pipeline no mini PC

Os dados dos campos originais estão em `validacao-minipc.md`, nessa mesma pasta.

---

## O que foi feito

Testei no mini PC se o sistema que criei pra medir desempenho de inteligência artificial em hardwares diferentes realmente funciona. A ideia do projeto é rodar o mesmo teste em máquinas diferentes — mini PC, Raspberry Pi, e no futuro a Jetson — e comparar quem se sai melhor em cada situação, sem gastar recurso demais nem esquentar demais.

Nessa etapa específica, ainda não testamos um modelo de IA de verdade
gerando texto. Testei a "esteira" que vai medir isso: se o sistema
consegue identificar o hardware sozinho, se consegue medir o que acontece
com a máquina (processador, memória, temperatura, placa de vídeo) enquanto
alguma coisa roda, e se consegue guardar esses dados de forma organizada.

## A máquina usada

- Processador Intel i5-8500T, 6 núcleos
- 32 GB de memória RAM
- Placa de vídeo NVIDIA RTX 3050, com 6 GB de memória própria
- Sistema operacional Ubuntu (Linux)

## O que foi confirmado que funciona

- O sistema identifica sozinho o processador, a memória e a placa de vídeo
  da máquina, sem precisar digitar nada manualmente
- Antes de começar a medir, ele espera a máquina esfriar até uma
  temperatura segura — evita medir em cima de um hardware já quente, o
  que distorceria o resultado
- Ele roda o teste várias vezes seguidas (5 vezes, descartando 2 rodadas
  de "aquecimento" antes) e junta os números de forma organizada
- Enquanto o teste roda, outro processo fica de olho na máquina — uso de
  processador, memória, temperatura e o quanto a placa de vídeo está
  consumindo de energia — tudo isso é registrado a cada segundo,
  separadamente do teste em si
- Testei rodando tanto pelo processador quanto pela placa de vídeo, e os
  dois caminhos funcionaram sem falha nas 5 repetições

## Sobre os resultados

Os números de tempo de resposta e velocidade saíram praticamente iguais
entre processador e placa de vídeo. Isso **não quer dizer que os dois têm o
mesmo desempenho** — é porque o teste usado ainda é artificial (uma
simulação que só espera um tempo fixo e finge que gerou uma resposta), feito
pra provar que a medição funciona, não pra medir desempenho real de IA
ainda. Quando rodarmos um modelo de verdade, esses números vão refletir a
diferença real entre processador e placa de vídeo.

### Tempo de resposta e velocidade

| Medição | Processador (cpu) | Placa de vídeo (gpu) |
|---|---|---|
| TTFT-Time To First Token (tempo até começar a responder) | 150.3 ms | 150.3 ms |
| Latency (tempo total até terminar a resposta) | 2150.6 ms (2,15 s) | 2150.6 ms (2,15 s) |
| Throughput (velocidade de geração, em tokens por segundo) | 59.52 tok/s | 59.52 tok/s |
| Repetições OK | 5 de 5 | 5 de 5 |

### Consumo da máquina durante o teste

| Medição | Processador (cpu) | Placa de vídeo (gpu) |
|---|---|---|
| avg_cpu_pct (uso médio de processador) | 0.71% | 0.71% |
| peak_cpu_pct (uso máximo de processador, pico) | 2.3% | 2.4% |
| avg_ram_used_mb (memória RAM usada, média) | ~1948 MB | ~1954 MB |
| avg_gpu_pct (uso de processamento da GPU) | 0% | 0% |
| avg_gpu_power_w (potência média da GPU) | 6.58 W | 6.54 W |
| peak_gpu_power_w (potência máxima da GPU, pico) | 6.77 W | 6.74 W |
| energy_gpu_j (energia total consumida pela GPU) | 68.06 J | 67.65 J |
| temp_start_c (temperatura no início do teste) | 45.0 °C | 46.0 °C |
| avg_temp_c (temperatura média durante o teste) | 44.8 °C | 44.8 °C |
| max_temp_c (temperatura máxima atingida) | 45.0 °C | 46.0 °C |

Uso de processador e memória ficou baixo porque o teste ainda não processa
nada pesado de verdade, número condizente com o esperado
pra essa etapa, não com o desempenho final. A GPU aparece com 0% de uso
processando porque a simulação não manda nenhum cálculo pra ela; a energia
registrada (6-7 W) é só o consumo da placa parada, "ligada mas ociosa".

### O que ficou sem medir

O mini PC não tem um sensor interno de energia total (só a
Jetson tem esse sensor embutido de fábrica). Pra medir isso aqui, precisaria
de um medidor externo ligado na tomada. 


## Status 

- Mini PC: pipeline validado, funcionando nos dois modos (processador e
  placa de vídeo)
- Raspberry Pi (os dois, um com acelerador Hailo e outro com Coral): ainda
  não testados
- Teste com modelo de IA real: em progresso, rodando de forma isolada (em contêiner)


