#!/usr/bin/env python3
"""
monitor.py — telemetria normalizada de RAM, CPU, temperatura, GPU e potencia.

O ponto central: Jetson e Raspberry Pi expoem esses dados por mecanismos
diferentes. Este modulo esconde essa diferenca e emite SEMPRE o mesmo formato
de amostra, para que os numeros sejam comparaveis.

Campo ausente vira null. Nunca zero.

Uso standalone:
    python scripts/monitor.py --duration 30 --out samples.ndjson

Uso como biblioteca:
    from monitor import Monitor
    with Monitor(interval=1.0, out_path="samples.ndjson", pid=proc.pid) as m:
        ...carga...
    summary = m.summary()
"""

import argparse
import json
import re
import shutil
import subprocess
import threading
import time
from glob import glob
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


# --------------------------------------------------------------------------
# Deteccao de plataforma
# --------------------------------------------------------------------------
def _read(path):
    try:
        return Path(path).read_text(errors="ignore").strip().replace("\x00", "")
    except Exception:
        return None


def detect_platform():
    model = (_read("/proc/device-tree/model") or "").lower()
    if "jetson" in model or Path("/etc/nv_tegra_release").exists():
        return "jetson"
    if "raspberry" in model:
        return "raspberry_pi"
    return "generic"


# --------------------------------------------------------------------------
# Leitores especificos por plataforma
# --------------------------------------------------------------------------
class TemperatureReader:
    """Le a zona termica mais quente. Cobre Jetson, Rasp e generico."""

    def __init__(self, platform_name):
        self.platform = platform_name
        self.zones = []
        for zone in sorted(glob("/sys/devices/virtual/thermal/thermal_zone*")):
            ztype = _read(f"{zone}/type") or ""
            # ignora zonas irrelevantes (ex.: PMIC costuma reportar valor fixo)
            if "pmic" in ztype.lower():
                continue
            self.zones.append((ztype, f"{zone}/temp"))
        self.has_vcgencmd = shutil.which("vcgencmd") is not None

    def read(self):
        temps = {}
        for ztype, path in self.zones:
            raw = _read(path)
            if raw and raw.lstrip("-").isdigit():
                val = int(raw)
                # sysfs reporta em miligraus (ou graus em alguns kernels)
                temps[ztype] = val / 1000.0 if abs(val) > 200 else float(val)

        if not temps and self.platform == "raspberry_pi" and self.has_vcgencmd:
            out = subprocess.run(
                ["vcgencmd", "measure_temp"], capture_output=True, text=True
            ).stdout
            m = re.search(r"([\d.]+)", out)
            if m:
                temps["vcgencmd"] = float(m.group(1))

        if not temps:
            return None, None
        hottest = max(temps.values())
        return round(hottest, 2), {k: round(v, 2) for k, v in temps.items()}


class PowerReader:
    """Potencia instantanea em watts. Jetson: rails INA3221. Rasp: indisponivel."""

    def __init__(self, platform_name):
        self.rails = []
        for pattern in (
            "/sys/bus/i2c/drivers/ina3221x/*/iio:device*/in_power*_input",
            "/sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*/power*_input",
        ):
            self.rails.extend(sorted(glob(pattern)))
        self.available = bool(self.rails)

    def read(self):
        if not self.available:
            return None  # ausencia explicita, nao zero
        total_mw = 0
        for rail in self.rails:
            raw = _read(rail)
            if raw and raw.isdigit():
                total_mw += int(raw)
        return round(total_mw / 1000.0, 3)


class GPUReader:
    """Utilizacao de GPU. Jetson: sysfs de carga do GR3D. Rasp: None."""

    def __init__(self, platform_name):
        self.path = None
        for candidate in (
            "/sys/devices/gpu.0/load",
            "/sys/devices/platform/gpu.0/load",
            "/sys/devices/17000000.gv11b/load",
        ):
            if Path(candidate).exists():
                self.path = candidate
                break
        self.available = self.path is not None

    def read(self):
        if not self.available:
            return None
        raw = _read(self.path)
        if raw and raw.isdigit():
            return round(int(raw) / 10.0, 1)  # sysfs reporta em permilagem
        return None


class NvidiaSMIReader:
    """GPU NVIDIA discreta (ex.: mini PC com RTX), via nvidia-smi.

    Uma chamada por amostra devolve temperatura, utilizacao e potencia da GPU
    juntas — evita tres subprocessos por segundo. Potencia aqui e so da GPU,
    nunca do sistema inteiro: nao e o mesmo campo que PowerReader (rails
    INA3221, potencia do board completo na Jetson). Ver docs/METODOLOGIA.md.
    """

    def __init__(self):
        self.binary = shutil.which("nvidia-smi")
        self.available = self.binary is not None

    def read(self):
        """-> (temp_c, gpu_pct, power_w), None quando indisponivel."""
        if not self.available:
            return None, None, None
        try:
            out = subprocess.run(
                [self.binary,
                 "--query-gpu=temperature.gpu,utilization.gpu,power.draw",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        except Exception:
            return None, None, None
        if not out:
            return None, None, None

        def f(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        parts = [p.strip() for p in out.splitlines()[0].split(",")]
        temp_c = f(parts[0]) if len(parts) > 0 else None
        gpu_pct = f(parts[1]) if len(parts) > 1 else None
        power_w = f(parts[2]) if len(parts) > 2 else None
        return temp_c, gpu_pct, power_w


# --------------------------------------------------------------------------
# Monitor
# --------------------------------------------------------------------------
class Monitor:
    def __init__(self, interval=1.0, out_path=None, pid=None):
        self.interval = interval
        self.out_path = Path(out_path) if out_path else None
        self.pid = pid
        self.platform = detect_platform()
        self.temp = TemperatureReader(self.platform)
        self.power = PowerReader(self.platform)
        self.gpu = GPUReader(self.platform)
        self.nvidia = NvidiaSMIReader()
        self.samples = []
        self._stop = threading.Event()
        self._thread = None
        self._fh = None
        self._proc = None
        if pid and psutil:
            try:
                self._proc = psutil.Process(pid)
            except Exception:
                self._proc = None

    # -- ciclo de vida ------------------------------------------------------
    def start(self):
        if self.out_path:
            self.out_path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = self.out_path.open("w")
        if psutil:
            psutil.cpu_percent(interval=None)  # zera o baseline
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 3)
        if self._fh:
            self._fh.close()
        return self

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    # -- coleta -------------------------------------------------------------
    def _merge_nvidia_temp(self, t_hottest, t_all, nv_temp):
        """Dobra a temperatura da GPU NVIDIA nas zonas ja lidas do sysfs."""
        if nv_temp is None:
            return t_hottest, t_all
        t_all = dict(t_all or {})
        t_all["nvidia_gpu"] = round(nv_temp, 2)
        t_hottest = max(t_hottest, nv_temp) if t_hottest is not None else nv_temp
        return t_hottest, t_all

    def read_temp(self):
        """Zona mais quente entre thermal_zone* e a GPU NVIDIA, quando houver.

        Usado pelo gate termico, fora do loop de amostragem — chamada isolada
        de nvidia-smi, sem custo extra pra sample().
        """
        t_hottest, t_all = self.temp.read()
        nv_temp, _, _ = self.nvidia.read()
        return self._merge_nvidia_temp(t_hottest, t_all, nv_temp)

    def sample(self):
        t_hottest, t_all = self.temp.read()
        nv_temp, nv_gpu_pct, nv_power_w = self.nvidia.read()
        t_hottest, t_all = self._merge_nvidia_temp(t_hottest, t_all, nv_temp)
        s = {
            "t": round(time.time(), 3),
            "cpu_pct": None,
            "ram_used_mb": None,
            "ram_pct": None,
            "proc_rss_mb": None,
            "gpu_pct": self.gpu.read() if self.gpu.available else nv_gpu_pct,
            "gpu_power_w": nv_power_w,
            "temp_c": t_hottest,
            "temp_zones_c": t_all,
            "power_w": self.power.read(),
        }
        if psutil:
            s["cpu_pct"] = psutil.cpu_percent(interval=None)
            vm = psutil.virtual_memory()
            s["ram_used_mb"] = round(vm.used / 1024**2, 1)
            s["ram_pct"] = vm.percent
            if self._proc:
                try:
                    s["proc_rss_mb"] = round(
                        self._proc.memory_info().rss / 1024**2, 1
                    )
                except Exception:
                    self._proc = None
        return s

    def _loop(self):
        while not self._stop.is_set():
            s = self.sample()
            self.samples.append(s)
            if self._fh:
                self._fh.write(json.dumps(s) + "\n")
                self._fh.flush()
            self._stop.wait(self.interval)

    # -- agregacao ----------------------------------------------------------
    def summary(self):
        def agg(key, fn):
            vals = [s[key] for s in self.samples if s.get(key) is not None]
            return round(fn(vals), 2) if vals else None

        def integrate(key):
            pts = [(s["t"], s[key]) for s in self.samples if s.get(key) is not None]
            if len(pts) < 2:
                return None
            return round(
                sum(
                    (pts[i][1] + pts[i - 1][1]) / 2 * (pts[i][0] - pts[i - 1][0])
                    for i in range(1, len(pts))
                ),
                2,
            )

        return {
            "platform": self.platform,
            "n_samples": len(self.samples),
            "interval_s": self.interval,
            "avg_cpu_pct": agg("cpu_pct", lambda v: sum(v) / len(v)),
            "peak_cpu_pct": agg("cpu_pct", max),
            "avg_ram_used_mb": agg("ram_used_mb", lambda v: sum(v) / len(v)),
            "peak_ram_used_mb": agg("ram_used_mb", max),
            "peak_proc_rss_mb": agg("proc_rss_mb", max),
            "avg_gpu_pct": agg("gpu_pct", lambda v: sum(v) / len(v)),
            "peak_gpu_pct": agg("gpu_pct", max),
            "temp_start_c": self.samples[0]["temp_c"] if self.samples else None,
            "avg_temp_c": agg("temp_c", lambda v: sum(v) / len(v)),
            "max_temp_c": agg("temp_c", max),
            # potencia do sistema inteiro (Jetson: rails INA3221). Ausente em
            # x86 sem wattimetro externo — nao confundir com avg_gpu_power_w.
            "avg_power_w": agg("power_w", lambda v: sum(v) / len(v)),
            "peak_power_w": agg("power_w", max),
            "energy_j": integrate("power_w"),
            "power_source": "internal" if self.power.available else "unavailable",
            # potencia so da GPU discreta (nvidia-smi). Escopo parcial: nao e
            # substituto de avg_power_w/energy_j em metricas derivadas.
            "avg_gpu_power_w": agg("gpu_power_w", lambda v: sum(v) / len(v)),
            "peak_gpu_power_w": agg("gpu_power_w", max),
            "energy_gpu_j": integrate("gpu_power_w"),
            "gpu_power_source": "nvidia-smi" if self.nvidia.available else "unavailable",
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=10.0)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--pid", type=int, default=None)
    args = ap.parse_args()

    m = Monitor(interval=args.interval, out_path=args.out, pid=args.pid)
    print(f"[i] plataforma detectada: {m.platform}")
    print(f"[i] potencia interna (board): {'sim' if m.power.available else 'nao'}")
    print(f"[i] nvidia-smi (gpu discreta): {'sim' if m.nvidia.available else 'nao'}")
    with m:
        time.sleep(args.duration)
    print(json.dumps(m.summary(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
