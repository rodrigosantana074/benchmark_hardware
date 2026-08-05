# Benchmarks

Um arquivo YAML por benchmark em `specs/`. A spec é a fonte de verdade do que
foi executado: `run_benchmark.py` copia os campos dela para o contexto de cada
resultado, então a configuração nunca se perde do número.

## Contrato da carga

Qualquer comando referenciado por um backend deve imprimir, como última linha da
saída padrão:

```
METRICS:{"ttft_ms": 143.2, "latency_ms": 5920.5, "throughput_tok_s": 21.6, "tokens_out": 128}
```

O orquestrador lê essa linha e agrega mean/p50/p95 entre as repetições. Métricas
de recurso (RAM, CPU, GPU, temperatura, potência) são coletadas em paralelo pelo
monitor — a carga não precisa medir nada disso.

Ver `workloads/reference_workload.py` para uma implementação mínima do contrato.

## Backends

`cpu`, `gpu` e `npu` são rótulos de destino de execução, não de fabricante. O
que cada um significa em determinado dispositivo fica registrado no campo
`runtime` da spec e no `accelerator` do catálogo de hardware.

O backend `npu` depende de qual acelerador está presente no dispositivo. Rode
`collect_hw_info.py` antes de preencher o comando: o script identifica o que
está conectado.

## Lista de benchmarks

| Benchmark | Escopo | Status |
|---|---|---|
| `slm-latency` | TTFT, latência e tokens/s em geração | rascunho |
| `slm-prefill` | Custo de prefill por tamanho de contexto | a definir |
| `sustained-load` | Degradação sob carga contínua | a definir |
| `cold-start` | Tempo de carregamento do modelo | a definir |
| `vision-classify` | Classificação de imagem, para exercitar a NPU | a definir |
