# Catálogo de hardware

Um arquivo JSON por dispositivo em `devices/<device-id>.json`, gerado por
script — não escrito à mão, para não divergir do que está na placa.

```bash
python scripts/collect_hw_info.py --device-id rpi5-01 \
    --label "Raspberry Pi 5 8GB" --cooling ativa --ambient-temp-c 24.5
```

O script detecta a plataforma e coleta CPU, governor, RAM, acelerador presente,
zonas térmicas legíveis, sensores de potência disponíveis, SO e kernel.

## Convenção de identificador

`<plataforma>-<modelo>-<numero>`, por exemplo `jetson-orin-nano-01`, `rpi5-01`.
O identificador entra no nome de toda execução, então precisa ser estável.

## Campos que dependem de informação externa

O script não tem como descobrir sozinho:

- `thermal.cooling` — passiva, ativa ou dissipador
- `ambient_temp_c` — temperatura ambiente do local da medição
- `power.note` — quando a potência depende de instrumento externo

Passe esses valores por argumento na coleta, ou edite o JSON antes de commitar.

## Aceleradores

O campo `accelerator` é preenchido pelo que foi detectado no momento da coleta:
GPU integrada em plataformas Tegra, GPU discreta via `nvidia-smi`, ou
acelerador externo identificado em USB/PCIe. Se nenhum for encontrado, o tipo
fica como `none_or_external` — o que significa que o backend `npu` não está
disponível naquele dispositivo até que um acelerador seja conectado e a coleta
refeita.
