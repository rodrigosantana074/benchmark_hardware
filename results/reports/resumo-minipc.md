# Resumo — validação do pipeline no mini PC

Os dados dos campos originais estão em `validacao-minipc.md`, nessa mesma pasta.

---

## O que foi feito

Testei, no mini PC, se o sistema que criei pra medir desempenho de inteligência artificial em hardwares diferentes realmente funciona. A ideia do projeto é rodar o mesmo teste em máquinas diferentes — mini PC, Raspberry Pi, e no futuro a Jetson — e comparar quem se sai melhor em cada situação, sem gastar recurso demais nem esquentar demais.

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

## Sobre os números desta rodada

Os números de tempo de resposta e velocidade saíram praticamente iguais
entre processador e placa de vídeo. Isso **não quer dizer que os dois têm o
mesmo desempenho** — é porque o teste usado ainda é artificial (uma
simulação que só espera um tempo fixo e finge que gerou uma resposta), feito
pra provar que a medição funciona, não pra medir desempenho real de IA
ainda. Quando rodarmos um modelo de verdade, esses números vão refletir a
diferença real entre processador e placa de vídeo.

### Tempo de resposta e velocidade

| O que foi medido | Processador (cpu) | Placa de vídeo (gpu) |
|---|---|---|
| Tempo até começar a responder | 150.3 ms | 150.3 ms |
| Tempo total até terminar a resposta | 2150.6 ms (2,15 s) | 2150.6 ms (2,15 s) |
| Velocidade de geração de texto | 59.52 "palavras" por segundo | 59.52 "palavras" por segundo |
| Repetições que deram certo | 5 de 5 | 5 de 5 |

### Consumo da máquina durante o teste

| O que foi medido | Processador (cpu) | Placa de vídeo (gpu) |
|---|---|---|
| Uso médio de processador | 0.71% | 0.71% |
| Uso máximo de processador (pico) | 2.3% | 2.4% |
| Memória RAM usada (média) | ~1948 MB | ~1954 MB |
| Uso da placa de vídeo (processamento) | 0% | 0% |
| Energia consumida pela placa de vídeo (média) | 6.58 W | 6.54 W |
| Energia consumida pela placa de vídeo (pico) | 6.77 W | 6.74 W |
| Energia total gasta pela placa de vídeo no teste | 68.06 joules | 67.65 joules |
| Temperatura no início do teste | 45.0 °C | 46.0 °C |
| Temperatura média durante o teste | 44.8 °C | 44.8 °C |
| Temperatura máxima atingida | 45.0 °C | 46.0 °C |

Uso de processador e memória ficou baixo porque o teste ainda não processa
nada pesado de verdade, número condizente com o esperado
pra essa etapa, não com o desempenho final. A GPU aparece com 0% de uso
processando porque a simulação não manda nenhum cálculo pra ela; a energia
registrada (6-7 W) é só o consumo da placa parada, "ligada mas ociosa".

### O que ficou sem medir, e por quê

O mini PC não tem um sensor interno de energia total (só a
Jetson tem esse sensor embutido de fábrica). Pra medir isso aqui, precisaria
de um medidor externo ligado na tomada. 

## O que encontramos no caminho

Durante o teste, apareceu um erro: um dos comandos usados internamente
dependia de uma informação (o caminho do arquivo do modelo) que não estava
definida. Isso passou despercebido nos testes anteriores porque, por uma
coincidência de como o Windows trata esse tipo de comando, o erro não
aparecia lá, só apareceu ao rodar no Linux de verdade. Foi corrigido na
hora e validado na mesma rodada.


## Status atual

- Mini PC: pipeline validado, funcionando nos dois modos (processador e
  placa de vídeo)
- Raspberry Pi (os dois, um com acelerador Hailo e outro com Coral): ainda
  não testados
- Teste com modelo de IA real: em progresso, rodando de forma isolada (em contêiner)

## Próximo passo

Repetir essa mesma validação nos dois Raspberry Pi, e então avançar pra
rodar um modelo de IA de verdade (Liquid AI) dentro de um contêiner no
mini PC.
