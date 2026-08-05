# Resultados

## Organização

Cada execução gera uma pasta em `runs/`, nomeada com data, dispositivo,
benchmark, backend e cenário:

```
runs/20260804T143012Z__jetson-orin-nano-01__slm-latency__gpu__baseline/
├── run.json         # arquivo autocontido: contexto + métricas + série (para o viewer)
├── meta.json        # só o contexto
├── summary.json     # só as métricas agregadas
└── samples.ndjson   # série temporal bruta, uma amostra por linha
```

`run.json` é o formato de intercâmbio: contém tudo o que a plataforma de
visualização precisa. Os outros três continuam existindo para inspeção manual
e para diff legível no controle de versão.

## Contexto que acompanha toda métrica

Dispositivo, placa, backend, acelerador, runtime, modelo, versão do modelo,
quantização, cenário, modo de energia, refrigeração, temperatura ambiente,
temperatura inicial, repetições, warm-up descartado, seed, carga
(entrada/saída/batch), comando executado e commit do repositório.

## Consolidação

```bash
python scripts/export_bundle.py                    # bundle.json -> viewer
python scripts/export_bundle.py --no-samples       # versão leve, sem série temporal
python scripts/aggregate_results.py --format md    # tabela markdown
python scripts/aggregate_results.py                # CSV
```

## Leitura dos números

- Comparar apenas linhas que diferem em **uma** dimensão. A plataforma sinaliza
  quando isso não acontece.
- `power_source: unavailable` significa ausência de sensor interno. A coluna de
  energia fica vazia, não zerada.
- Em plataformas com memória unificada entre CPU e GPU, o pico de RAM não é
  diretamente comparável ao de plataformas com memória separada.

## Execuções de exemplo

As pastas com `exemplo-generic-01` vêm da carga de referência e existem só para
demonstrar o formato. Apague ao registrar as primeiras medições reais.
