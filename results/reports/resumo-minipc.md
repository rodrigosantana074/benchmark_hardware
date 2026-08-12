# Resumo — validação do pipeline no mini PC

Versão em linguagem simples do que foi feito e encontrado. Os dados técnicos
completos (com todos os campos originais) estão em `validacao-minipc.md`,
nessa mesma pasta.

---

## O que foi feito

Testamos, num mini PC real (não numa simulação), se o sistema que criamos
pra medir desempenho de inteligência artificial em hardwares diferentes
realmente funciona. A ideia do projeto é rodar o mesmo teste em máquinas
diferentes — mini PC, Raspberry Pi, e no futuro a Jetson — e comparar quem
se sai melhor em cada situação, sem gastar recurso demais nem esquentar
demais.

Nessa etapa específica, ainda não testamos um modelo de IA de verdade
gerando texto. Testamos a "esteira" que vai medir isso: se o sistema
consegue identificar o hardware sozinho, se consegue medir o que acontece
com a máquina (processador, memória, temperatura, placa de vídeo) enquanto
alguma coisa roda, e se consegue guardar esses dados de forma organizada.

## A máquina usada

Conseguimos acesso remoto (por SSH, como se fosse controlar outro
computador pelo terminal) a um mini PC de um colega. As especificações
reais, conferidas na hora:

- Processador Intel i5-8500T, 6 núcleos
- 32 GB de memória RAM
- Placa de vídeo NVIDIA RTX 3050, com 6 GB de memória própria
- Sistema operacional Ubuntu (Linux)

Um ponto de atenção: a especificação que recebemos originalmente apontava
uma placa de vídeo diferente e mais forte (RTX PRO 2000, 16 GB). A que
apareceu de verdade na máquina foi a RTX 3050, de 6 GB. Pode ser que a
especificação original estivesse errada, ou que seja outro equipamento —
vale confirmar qual é a informação certa.

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
- Testamos rodando tanto pelo processador quanto pela placa de vídeo, e os
  dois caminhos funcionaram sem falha nas 5 repetições

## Sobre os números desta rodada

Os números de tempo de resposta e velocidade saíram praticamente iguais
entre processador e placa de vídeo. Isso **não quer dizer que os dois têm o
mesmo desempenho** — é porque o teste usado ainda é artificial (uma
simulação que só espera um tempo fixo e finge que gerou uma resposta), feito
pra provar que a medição funciona, não pra medir desempenho real de IA
ainda. Quando rodarmos um modelo de verdade, esses números vão refletir a
diferença real entre processador e placa de vídeo.

O que os números já mostram de real: o uso de processador e memória ficou
bem baixo (a máquina mal foi exigida, como esperado pra um teste que não
processa nada pesado ainda), e a temperatura se manteve estável, sem
esquentar. A placa de vídeo consumiu uma quantidade pequena de energia,
compatível com estar praticamente ociosa.

Uma limitação encontrada: esse mini PC não tem um sensor interno de
consumo de energia total da máquina (só a Jetson tem esse sensor
embutido). Pra medir quanto a máquina inteira consome de energia, seria
necessário um medidor externo, ligado na tomada. Isso não é um problema do
sistema — é uma informação que, sem esse aparelho, o sistema corretamente
deixa em branco em vez de inventar um número.

## O que encontramos no caminho

Durante o teste, apareceu um erro real: um dos comandos usados internamente
dependia de uma informação (o caminho do arquivo do modelo) que não estava
definida. Isso passou despercebido nos testes anteriores porque, por uma
coincidência de como o Windows trata esse tipo de comando, o erro não
aparecia lá — só apareceu ao rodar no Linux de verdade. Foi corrigido na
hora e validado na mesma rodada.

Isso reforça por que testar em hardware real (e não só simular) é
importante: alguns problemas só aparecem no ambiente de verdade.

## Status atual

- Mini PC: pipeline validado, funcionando nos dois modos (processador e
  placa de vídeo)
- Raspberry Pi (os dois, um com acelerador Hailo e outro com Coral): ainda
  não testados
- Teste com modelo de IA real: ainda não rodou — é a próxima fase, já com
  autorização pra prosseguir, rodando de forma isolada (em contêiner) por
  segurança, já que a máquina é de outra pessoa

## Próximo passo

Repetir essa mesma validação nos dois Raspberry Pi, e então avançar pra
rodar um modelo de IA de verdade (Liquid AI) dentro de um contêiner no
mini PC.
