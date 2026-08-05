# benchmark-edge-ai

Benchmark comparativo de inferência de SLMs em hardware de borda, medindo as
mesmas cargas em **CPU, GPU e NPU** sob restrição de recursos.

O objetivo não é eleger um vencedor absoluto, e sim demonstrar com medição
reproduzível **em quais cenários cada arquitetura leva vantagem** — e a que
custo de RAM, CPU, temperatura e energia.

## Conteúdo

| Diretório | O que é |
|---|---|
| `hardware/` | Catálogo dos dispositivos, gerado por script |
| `benchmarks/` | Especificação de cada benchmark (YAML) |
| `scripts/` | Coleta de hardware, telemetria, execução e exportação |
| `workloads/` | Cargas de inferência |
| `results/` | Uma pasta por execução: contexto, série temporal e métricas |
| `viewer/` | Plataforma para carregar os resultados e comparar visualmente |
| `docs/` | Metodologia, dicionário do catálogo, plano de experimentos |

## Uso

```bash
pip install -r requirements.txt

# 1. Uma vez por dispositivo — cataloga o hardware
python scripts/collect_hw_info.py --device-id jetson-orin-nano-01

# 2. Por experimento
python scripts/run_benchmark.py \
    --spec benchmarks/specs/slm-latency.yaml \
    --device-id jetson-orin-nano-01 \
    --backend gpu \
    --scenario baseline

# 3. Consolidação
python scripts/export_bundle.py                      # bundle.json para o viewer
python scripts/aggregate_results.py --format md      # tabela para o relatório
```

## Plataforma de visualização

`viewer/index.html` é uma página estática, sem servidor e sem dependências:
abra no navegador e arraste os arquivos de resultado. Nada sai da máquina.

Aceita três formatos de entrada:

- `run.json` — arquivo autocontido de uma execução (recomendado)
- `bundle.json` — vários resultados num arquivo só, via `export_bundle.py`
- `meta.json` + `summary.json` — o par bruto de uma execução

O que ela mostra:

- **Comparar** — barras agrupadas por qualquer dimensão (dispositivo, backend,
  cenário, quantização, runtime), com dez métricas incluindo derivadas como
  energia por token e throughput por watt.
- **Tabela** — todas as execuções com métrica e contexto lado a lado, ordenável,
  exportável em CSV.
- **Série temporal** — telemetria durante a execução. É aqui que o throttling
  aparece: queda de desempenho junto com subida de temperatura.

O elemento central é a **guarda de comparabilidade**: antes de mostrar o
gráfico, a plataforma verifica se os resultados exibidos diferem em mais de uma
dimensão. Se o modelo, a quantização, a carga ou o cenário variarem além do eixo
comparado, ela avisa que a diferença observada não pode ser atribuída ao eixo.
Comparação com duas variáveis soltas ao mesmo tempo não prova nada, e o gráfico
não deve deixar isso passar despercebido.

## Regra do repositório

Nenhuma métrica entra sem o contexto em que foi medida. Número solto não é
resultado.

## Definições pendentes

- Lista final de benchmarks (ver `benchmarks/README.md`)
- Versão e quantização exatas dos modelos
- Modelo do acelerador externo da Raspberry Pi — o script detecta o que estiver
  conectado; a spec do backend `npu` só pode ser fechada depois disso
- Método de medição de energia em dispositivos sem sensor interno
