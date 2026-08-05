# Metodologia de medição

Plataformas de borda expõem telemetria por mecanismos diferentes. Se cada uma
for medida do seu próprio jeito, os números deixam de ser comparáveis. Este
documento fixa o que precisa ser igual para que dois resultados possam aparecer
na mesma tabela.

---

## 1. Condições de comparabilidade

Para dois resultados serem comparados diretamente, precisam compartilhar:

| Dimensão | Regra |
|---|---|
| Modelo | Mesmo checkpoint, mesma versão, mesma quantização |
| Carga | Mesmos prompts, mesmo número de tokens de entrada e de saída, mesmo batch |
| Repetições | Mínimo de 5 execuções medidas, com 2 de warm-up descartadas |
| Semente | Fixa e registrada |
| Estado térmico | Cooldown até o limiar configurado antes de cada execução |
| Modo de energia | Registrado explicitamente |
| Refrigeração | Registrada — altera o resultado sozinha |

Diferiu em alguma dessas dimensões? O resultado entra como cenário distinto,
nunca como comparação direta. A plataforma de visualização verifica isso e
sinaliza quando mais de uma variável muda ao mesmo tempo.

## 2. Métricas

**Desempenho:** `ttft_ms`, `latency_ms` (p50 e p95), `throughput_tok_s`,
`wall_time_s`.

**Recursos:** `peak_ram_mb`, `avg_ram_mb`, `avg_cpu_pct`, `peak_cpu_pct`,
`avg_gpu_pct`, `max_temp_c`, `avg_temp_c`, `avg_power_w`, `energy_j`.

**Derivadas:** energia por token, throughput por watt, throughput por GB de RAM.
São elas que respondem qual arquitetura compensa sob restrição, e não o
throughput bruto.

## 3. Normalização entre plataformas

| Grandeza | Origem possível | Estratégia |
|---|---|---|
| Temperatura | `thermal_zone*` no sysfs; utilitário do fornecedor quando o sysfs não expõe | O monitor lê todas as zonas disponíveis e reporta a mais quente, mantendo as demais no detalhe |
| Potência | Rails INA3221 no sysfs, quando existirem | Integração por amostra para obter energia; sem sensor, o campo fica nulo e a medição depende de instrumento externo |
| CPU e RAM | `psutil` | Idêntico em todas as plataformas |
| GPU | Carga exposta em sysfs, quando existir | Nulo quando ausente |

Campo ausente é `null`. Zero é medição. Confundir os dois inventa dado.

## 4. Protocolo de execução

1. Coletar ou atualizar o catálogo do dispositivo.
2. Fixar e registrar o modo de energia.
3. Aguardar a temperatura cair abaixo do limiar configurado.
4. Rodar as iterações de warm-up, descartadas.
5. Rodar as iterações medidas, com o monitor amostrando em paralelo.
6. Gravar contexto, série temporal e agregados.
7. Repetir para o próximo backend ou cenário.

## 5. Cenários

| ID | Descrição | Por que existe |
|---|---|---|
| `baseline` | Sem restrição, energia máxima | Teto de desempenho |
| `low_power` | Modo de energia reduzido | Operação com orçamento de energia limitado |
| `mem_constrained` | RAM limitada via cgroup | Restrição de recursos |
| `thermal_sustained` | Carga contínua prolongada | Expõe throttling, onde o ranking costuma se inverter |
| `concurrent` | Requisições simultâneas | Comportamento sob fila |

## 6. Ameaças à validade

Declarar no relatório o que se aplicar:

- Medições em ambiente sem temperatura controlada — registrar a temperatura
  ambiente de cada execução.
- Dispositivos sem sensor interno de potência — comparação energética parcial.
- Memória unificada entre CPU e GPU — pico de RAM não comparável entre
  arquiteturas de memória diferentes.
- Runtimes distintos por backend — parte da diferença medida é do runtime, não
  do silício. Registrar sempre qual foi usado.
