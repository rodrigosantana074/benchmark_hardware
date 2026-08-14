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

---

## Agora com IA de verdade — modelo LFM2 rodando na GPU

Depois da validação com carga sintética, rodei o benchmark oficial com o
modelo real (LFM2-350M, da Liquid AI), isolado num contêiner Docker, na
placa de vídeo. 5 de 5 repetições certas.

| Medição | Sintético (dia anterior) | IA real |
|---|---|---|
| TTFT (tempo até começar a responder) | 150.3 ms | 21.5 ms |
| Latency (tempo total da resposta) | 2150.6 ms | 1471.7 ms |
| Throughput (tokens por segundo) | 59.52 tok/s (número de mentira) | 88.27 tok/s (real) |
| avg_gpu_pct (uso da placa de vídeo) | 0% | **93.4%** |
| avg_gpu_power_w (potência média da GPU) | 6.54 W | **25.6 W** |
| avg_temp_c (temperatura média) | 44.8 °C | 56.3 °C |
| avg_ram_used_mb (RAM usada) | ~1954 MB | ~2591 MB |

A diferença entre as duas colunas é o que prova que dessa vez a GPU
trabalhou de verdade: uso de processamento foi de 0% pra 93%, o consumo de
energia quase quadruplicou, e a temperatura subiu de forma real. Antes a
placa só ficava ligada e ociosa; agora ela processou o modelo.

Pelo caminho, tive que resolver um problema: rodando o `llama.cpp` direto
pela linha de comando, ele entrava num modo de conversa e ficava esperando
uma pergunta que nunca chegava (travava, sem erro nenhum aparecer). Troquei
pra rodar ele como um servidor — daí eu mando a pergunta por HTTP e recebo a
resposta com os tempos exatos, sem depender de ler texto solto da tela.

---

## E agora testei IA real no processador também

Mesmo modelo, mesmo teste, só que dessa vez sem usar a placa de vídeo —
tudo processado no processador comum. Também 5 de 5 repetições certas.

| Medição | Placa de vídeo (gpu) | Processador (cpu) |
|---|---|---|
| Throughput (tokens por segundo, média) | 88.27 tok/s | **99.10 tok/s** |
| Throughput (variação entre as 5 repetições) | 88.24 a 88.28 (bem estável) | 75.94 a 105.93 (bem instável) |
| TTFT (tempo até começar a responder) | 21.5 ms | 15.3 ms |
| avg_cpu_pct (uso do processador) | 15% | **94.6%** |
| avg_gpu_pct (uso da placa de vídeo) | 93.4% | 0% |
| avg_ram_used_mb (RAM usada) | ~2591 MB | ~3900 MB |
| Temperatura média / máxima | 56.3 °C / 57 °C | 61.7 °C / 65 °C |

**Achado que não esperava:** pra esse modelo pequeno, o processador saiu
com velocidade média até maior que a placa de vídeo — mas bem menos
consistente (uma das 5 repetições foi bem mais lenta que as outras,
provavelmente por causa do calor acumulado ou de outros programas rodando
na máquina ao mesmo tempo). A placa de vídeo foi mais lenta na média, só
que muito mais previsível — as 5 repetições saíram quase idênticas.

Isso não significa "processador é melhor que placa de vídeo" — significa
que, pra esse modelo pequeno e esse teste curto, cada um leva vantagem em
um critério diferente (velocidade de pico vs. previsibilidade), que é
exatamente o tipo de resposta que esse projeto existe pra dar. Com modelo
maior ou teste mais longo, isso tende a inverter a favor da GPU.

## Status

- Mini PC: pipeline validado nos dois modos (processador e placa de vídeo),
  com carga sintética e com IA real, nos dois backends
- Raspberry Pi (os dois, um com acelerador Hailo e outro com Coral): ainda
  não testados
- Falta: medir a energia da máquina inteira (só a placa de vídeo é medida
  hoje) e testar outros cenários (carga sustentada, restrição de memória)


