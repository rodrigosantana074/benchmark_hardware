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
python scripts/collect_hw_info.py --device-id minipc-rtx2000-01

# 2. Por experimento
python scripts/run_benchmark.py \
    --spec benchmarks/specs/slm-latency.yaml \
    --device-id minipc-rtx2000-01 \
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

## Rodando remoto (SSH)

Sem serviço fixo, sem daemon — cada device roda os scripts localmente, você
só entra por SSH pra disparar. Uma vez por device:

```bash
git clone <remote> && cd benchmark-edge-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/collect_hw_info.py --device-id minipc-rtx2000-01 \
    --cooling ativa --ambient-temp-c 24
```

Rode dentro de `tmux`/`screen`, nunca direto na sessão SSH: `thermal_sustained`
sozinho passa de 10min por repetição, e a sessão caindo no meio perde a corrida.

```bash
tmux new -s bench
python scripts/run_benchmark.py --spec benchmarks/specs/slm-latency.yaml \
    --device-id minipc-rtx2000-01 --backend gpu --scenario baseline
# Ctrl+B D pra sair sem matar o processo
```

O resultado volta pro repo central por `git push` — cada run grava em
`results/runs/<run_id>/`; commita e sobe depois de cada bateria. O campo
`repo_commit` em `meta.json` amarra cada resultado ao commit em que foi gerado.

## Definições pendentes

- Lista final de benchmarks (ver `benchmarks/README.md`)
- Versão e quantização exatas dos modelos
- Runtime do backend `npu` pra Hailo/Coral — hoje fora de escopo pro
  `slm-latency` (ver `docs/PLANO_EXPERIMENTOS.md`), entra quando o
  `vision-classify` for definido
- Método de medição de energia em dispositivos sem sensor interno de board —
  GPU discreta agora tem `avg_gpu_power_w`/`energy_gpu_j` via `nvidia-smi`,
  mas isso é potência só da GPU, não do sistema inteiro
- Onde fica o remote git pros devices darem push (a definir)
