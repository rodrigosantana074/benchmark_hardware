#!/usr/bin/env python3
"""
collect_hw_info.py — coleta as especificacoes do dispositivo e grava o catalogo
em hardware/devices/<device-id>.json.

Roda uma vez por dispositivo (e novamente se o SO/firmware mudar).
Funciona em Raspberry Pi, Jetson e maquinas x86 genericas.

Uso:
    python scripts/collect_hw_info.py --device-id jetson-orin-nano-01
    python scripts/collect_hw_info.py --device-id rasp-pi5-01 --notes "dissipador ativo"
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVICES_DIR = ROOT / "hardware" / "devices"


def sh(cmd, timeout=10):
    """Executa comando e devolve stdout limpo, ou None se falhar."""
    try:
        out = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        val = out.stdout.strip()
        return val or None
    except Exception:
        return None


def read_file(path):
    try:
        return Path(path).read_text(errors="ignore").strip().replace("\x00", "")
    except Exception:
        return None


def detect_platform():
    """Retorna 'jetson', 'raspberry_pi' ou 'generic'."""
    model = read_file("/proc/device-tree/model") or ""
    if "jetson" in model.lower() or Path("/etc/nv_tegra_release").exists():
        return "jetson"
    if "raspberry" in model.lower():
        return "raspberry_pi"
    return "generic"


def cpu_info():
    info = {
        "arch": platform.machine(),
        "model": None,
        "cores_physical": None,
        "cores_logical": os.cpu_count(),
        "max_freq_mhz": None,
        "governor": None,
    }
    cpuinfo = read_file("/proc/cpuinfo") or ""
    for key in ("model name", "Model", "Hardware"):
        m = re.search(rf"^{key}\s*:\s*(.+)$", cpuinfo, re.M)
        if m:
            info["model"] = m.group(1).strip()
            break

    try:
        import psutil

        info["cores_physical"] = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        if freq and freq.max:
            info["max_freq_mhz"] = round(freq.max, 1)
    except Exception:
        pass

    gov = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if gov:
        info["governor"] = gov
    return info


def memory_bandwidth_gbps(size_mb=256, iterations=5):
    """Banda de RAM aproximada (leitura+escrita), via memmove da libc.

    Nao e pico teorico nem substitui STREAM/sysbench -- e uma medida
    relativa, feita do mesmo jeito em qualquer device (sem apt/sudo),
    pensada pra comparar bandwidth entre CPU/GPU/devices, nao pra bater
    com numero de datasheet. Usa o menor tempo entre as repeticoes pra
    reduzir ruido de scheduling do SO.
    """
    try:
        import ctypes
        import time

        size = size_mb * 1024 * 1024
        src = ctypes.create_string_buffer(size)
        dst = ctypes.create_string_buffer(size)
        ctypes.memset(src, 1, size)

        best = None
        for _ in range(iterations):
            t0 = time.perf_counter()
            ctypes.memmove(dst, src, size)
            elapsed = time.perf_counter() - t0
            if best is None or elapsed < best:
                best = elapsed
        if not best:
            return None
        return round((size / best) / 1e9, 2)
    except Exception:
        return None


def memory_info():
    info = {
        "total_mb": None,
        "swap_total_mb": None,
        "unified_with_gpu": False,
        "bandwidth_gbps": None,
        "bandwidth_method": "memmove (ver docs/CATALOGO_HARDWARE.md)",
    }
    try:
        import psutil

        info["total_mb"] = round(psutil.virtual_memory().total / 1024**2)
        info["swap_total_mb"] = round(psutil.swap_memory().total / 1024**2)
    except Exception:
        meminfo = read_file("/proc/meminfo") or ""
        m = re.search(r"MemTotal:\s+(\d+) kB", meminfo)
        if m:
            info["total_mb"] = round(int(m.group(1)) / 1024)
    info["bandwidth_gbps"] = memory_bandwidth_gbps()
    return info


def accelerator_info(plat):
    """Descreve o acelerador disponivel: GPU integrada, NPU, ou nenhum."""
    acc = {"type": None, "model": None, "details": {}}

    if plat == "jetson":
        acc["type"] = "gpu_integrated"
        release = read_file("/etc/nv_tegra_release")
        acc["details"]["l4t_release"] = release
        acc["details"]["jetpack_model"] = read_file("/proc/device-tree/model")
        acc["details"]["cuda_version"] = sh("nvcc --version | tail -n 2 | head -n 1")
        acc["details"]["nvpmodel"] = sh("nvpmodel -q 2>/dev/null | tr '\\n' ' '")
        acc["details"]["memory_unified"] = True
        acc["model"] = "GPU integrada Tegra"
        # NPU: Jetson Orin possui DLA
        if Path("/sys/kernel/debug/nvdla0").exists() or "orin" in (
            acc["details"].get("jetpack_model") or ""
        ).lower():
            acc["details"]["dla_present"] = True

    elif plat == "raspberry_pi":
        acc["type"] = "none_or_external"
        acc["model"] = None  # nenhum acelerador de inferencia por padrao
        acc["details"]["firmware"] = sh("vcgencmd version | tr '\\n' ' '")
        # Detecta acelerador USB/PCIe (Coral, Hailo, etc.)
        usb = sh("lsusb") or ""
        pci = sh("lspci") or ""
        found = []
        for name, pat in (
            ("Google Coral Edge TPU", r"Global Unichip|Google Inc"),
            ("Hailo", r"Hailo"),
            ("Intel Movidius NCS", r"Movidius|Myriad"),
        ):
            if re.search(pat, usb + pci, re.I):
                found.append(name)
        if found:
            acc["type"] = "npu_external"
            acc["details"]["npu_detected"] = found

    else:
        nv = sh("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
        if nv:
            acc["type"] = "gpu_discrete"
            acc["model"] = nv
    return acc


def thermal_info(plat):
    zones = []
    base = Path("/sys/devices/virtual/thermal")
    if base.exists():
        for zone in sorted(base.glob("thermal_zone*")):
            zones.append(
                {
                    "zone": zone.name,
                    "type": read_file(zone / "type"),
                    "path": str(zone / "temp"),
                }
            )
    info = {"zones": zones, "cooling": None}
    if plat == "raspberry_pi":
        info["vcgencmd_available"] = shutil.which("vcgencmd") is not None
    if plat == "jetson":
        info["tegrastats_available"] = shutil.which("tegrastats") is not None
    return info


def power_info(plat):
    """Onde ler potencia, se houver sensor."""
    rails = []
    for pattern in (
        "/sys/bus/i2c/drivers/ina3221x/*/iio:device*/in_power*_input",
        "/sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*/in*_input",
    ):
        from glob import glob

        rails.extend(sorted(glob(pattern)))
    return {
        "internal_sensor": bool(rails),
        "rails": rails,
        "power_source": "internal" if rails else "external_required",
        "note": None
        if rails
        else "Sem sensor interno. Medir com wattimetro externo e registrar manualmente.",
    }


def storage_info():
    out = sh("df -h / | tail -n 1")
    return {"root_fs": out}


def software_info():
    return {
        "os": read_file("/etc/os-release"),
        "kernel": platform.release(),
        "python": sys.version.split()[0],
        "pip_freeze_hint": "gerar com: pip freeze > hardware/devices/<id>.requirements.txt",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device-id", required=True, help="ex.: jetson-orin-nano-01")
    ap.add_argument("--label", default=None, help="nome amigavel do dispositivo")
    ap.add_argument("--owner", default=None, help="quem esta com o dispositivo")
    ap.add_argument("--location", default=None, help="lab | casa-werick | ...")
    ap.add_argument("--cooling", default=None,
                    help="passiva | ativa | dissipador — nao e detectavel por software")
    ap.add_argument("--ambient-temp-c", type=float, default=None,
                    help="temperatura ambiente no local da medicao")
    ap.add_argument("--notes", default=None)
    args = ap.parse_args()

    plat = detect_platform()

    thermal = thermal_info(plat)
    thermal["cooling"] = args.cooling

    catalog = {
        "device_id": args.device_id,
        "label": args.label or args.device_id,
        "platform": plat,
        "board_model": read_file("/proc/device-tree/model"),
        "owner": args.owner,
        "location": args.location,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "cpu": cpu_info(),
        "memory": memory_info(),
        "accelerator": accelerator_info(plat),
        "thermal": thermal,
        "power": power_info(plat),
        "storage": storage_info(),
        "software": software_info(),
        "ambient_temp_c": args.ambient_temp_c,
        "notes": args.notes,
    }

    DEVICES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEVICES_DIR / f"{args.device_id}.json"
    out_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"[ok] catalogo gravado em {out_path}")
    faltando = [k for k, v in (("cooling", thermal["cooling"]),
                               ("ambient_temp_c", args.ambient_temp_c)) if v is None]
    if faltando:
        print("[!] campos nao detectaveis por software ainda vazios: "
              + ", ".join(faltando))
        print("    passe --cooling e --ambient-temp-c, ou edite o JSON antes de commitar.")
    acc = catalog["accelerator"]
    print(f"[i] acelerador detectado: {acc['type']} — {acc['model'] or 'nenhum'}")


if __name__ == "__main__":
    main()
