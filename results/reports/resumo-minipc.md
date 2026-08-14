# Resumo — validação do pipeline no mini PC

Versão em português simples, com os números reais mas sem o detalhamento
técnico completo. Dados brutos em `validacao-minipc.md`, nessa mesma pasta.

---

## O que fiz

Testei, num mini PC real (não simulação), se o sistema que criei pra medir
desempenho de IA em hardwares diferentes funciona de ponta a ponta:
detecção automática de hardware, telemetria (processador, memória,
temperatura, placa de vídeo) coletada em paralelo, e gravação organizada
do resultado.

Rodei em duas etapas: primeiro uma carga de teste que não processa nada de
verdade (só valida o mecanismo de medição), depois um modelo de IA real —
LFM2-350M, da Liquid AI — rodando isolado num contêiner.

## A máquina

- Processador Intel i5-8500T, 6 núcleos
- 32 GB de RAM
- Placa de vídeo NVIDIA RTX 3050, 6 GB
- Ubuntu (Linux), acesso remoto por SSH

A especificação que recebi originalmente apontava uma placa mais forte
(RTX PRO 2000, 16 GB). A que apareceu de verdade na máquina foi a RTX
3050 — ainda preciso confirmar qual informação é a correta.

## O que confirmei que funciona

- Identificação automática do hardware, sem digitar nada manualmente
- Espera a máquina esfriar antes de medir, pra não distorcer o resultado
- 5 repetições medidas, 2 de aquecimento descartadas antes de cada uma
- Telemetria coletada em paralelo, a cada segundo, sem depender da carga
  que tá rodando
- Processador e placa de vídeo testados nas duas etapas (teste e IA real)
  — 5 de 5 repetições certas em todos os casos

## IA real: processador vs. placa de vídeo

| Medição | Processador (cpu) | Placa de vídeo (gpu) |
|---|---|---|
| Throughput — velocidade de geração (média) | **99.1 tok/s** | 88.3 tok/s |
| Throughput — variação entre as 5 repetições | 76 a 106 (instável) | 88.24 a 88.28 (estável) |
| TTFT — tempo até começar a responder | 15.3 ms | 21.5 ms |
| Uso do processador | 94.6% | 15% |
| Uso da placa de vídeo | 0% | 93.4% |
| RAM usada | ~3.9 GB | ~2.6 GB |
| Temperatura média / máxima | 61.7 °C / 65 °C | 56.3 °C / 57 °C |
| Potência da placa de vídeo | 6.5 W (ociosa) | 25.6 W (processando) |

**Achado que não esperava:** pra esse modelo pequeno, o processador saiu
mais rápido na média — mas bem menos consistente. Uma das 5 repetições foi
bem mais lenta que as outras, coincidindo com o pico de temperatura da
máquina. A placa de vídeo foi mais devagar na média, só que extremamente
previsível entre as repetições.

Isso não quer dizer "processador é melhor que placa de vídeo" — quer dizer
que cada um leva vantagem em critério diferente (pico de velocidade vs.
previsibilidade), que é exatamente o tipo de resposta que esse projeto
existe pra dar, em vez de eleger um vencedor absoluto. Modelo maior ou
teste mais longo tende a inverter isso a favor da placa de vídeo.

Pra referência, a etapa anterior (carga de teste, sem IA real) tinha dado
os dois backends empatados em 59.5 tokens por segundo — número de mentira,
só provando que o mecanismo de medição funciona. O salto de uso da placa
de vídeo (de 0% pra 93%) e de potência (de 6.5W pra 25.6W) entre aquele
teste e esse é a confirmação visual de que dessa vez o hardware trabalhou
de verdade.

## Problema resolvido pelo caminho

O `llama.cpp`, rodado direto pela linha de comando, entrava num modo de
conversa e ficava esperando uma pergunta que nunca chegava — travava sem
nenhum erro aparecer. Resolvi rodando ele como um servidor: mando a
pergunta por HTTP e recebo a resposta com os tempos exatos, sem depender
de ler texto solto da tela.

## Status

- Mini PC: pipeline validado nos dois backends, com carga de teste e com
  IA real
- Raspberry Pi (um com acelerador Hailo, outro com Coral): ainda não
  testados
- Falta: medir a energia da máquina inteira (só a placa de vídeo é medida
  hoje) e testar outros cenários (carga sustentada, restrição de memória)
