from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class HostProfile:
    provider: str
    memory_gb: float | None
    cpu_cores: float | None
    tier: str
    lavhost: bool


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _memory_bytes() -> int | None:
    try:
        import psutil

        total = int(psutil.virtual_memory().total)
    except (ImportError, OSError, ValueError):
        total = 0

    for path in (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        raw = _read_text(path)
        if not raw or raw == "max":
            continue
        try:
            limit = int(raw)
        except ValueError:
            continue
        if 0 < limit < 1 << 60:
            total = min(total, limit) if total else limit

    return total or None


def _cpu_cores() -> float | None:
    try:
        total = float(len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):
        try:
            total = float(os.cpu_count() or 0)
        except (OSError, ValueError):
            total = 0.0

    for path in (Path("/sys/fs/cgroup/cpu.max"),):
        values = _read_text(path).split()
        if len(values) != 2 or values[0] == "max":
            continue
        try:
            quota, period = int(values[0]), int(values[1])
        except ValueError:
            continue
        if quota > 0 and period > 0:
            available = quota / period
            total = min(total, available) if total else available

    legacy_quota = _read_text(Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us"))
    legacy_period = _read_text(Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us"))
    try:
        quota, period = int(legacy_quota), int(legacy_period)
        if quota > 0 and period > 0:
            available = quota / period
            total = min(total, available) if total else available
    except ValueError:
        pass

    return round(total, 2) if total > 0 else None


def get_host_profile(
    environ: Mapping[str, str] | None = None,
    *,
    sys_vendor: str | None = None,
    memory_bytes: int | None = None,
    cpu_cores: float | None = None,
) -> HostProfile:
    env = os.environ if environ is None else environ
    vendor = sys_vendor
    if vendor is None:
        vendor = _read_text(Path("/sys/class/dmi/id/sys_vendor"))
    vendor = vendor or _read_text(Path("/sys/devices/virtual/dmi/id/sys_vendor"))

    provider_override = env.get("EXOTICA_CLOUD_PROVIDER", "").strip()
    if provider_override:
        provider = "Oracle Cloud" if "oracle" in provider_override.lower() or "oci" == provider_override.lower() else provider_override
    elif "oracle" in vendor.lower():
        provider = "Oracle Cloud"
    elif env.get("LAVHOST"):
        provider = "lavHost"
    elif env.get("KUBERNETES_SERVICE_HOST"):
        provider = "Kubernetes"
    elif env.get("CODESPACES"):
        provider = "GitHub Codespaces"
    elif env.get("DOCKER"):
        provider = "Docker host"
    else:
        provider = "Self-hosted"

    if memory_bytes is None:
        override = env.get("EXOTICA_HOST_MEMORY_GB", "").strip()
        try:
            memory_bytes = int(float(override) * (1024**3)) if override else _memory_bytes()
        except ValueError:
            memory_bytes = _memory_bytes()
    memory_gb = round(memory_bytes / (1024**3), 1) if memory_bytes and memory_bytes > 0 else None
    if cpu_cores is None:
        cpu_override = env.get("EXOTICA_HOST_CPU_CORES", "").strip()
        try:
            cpu_cores = float(cpu_override) if cpu_override else _cpu_cores()
        except ValueError:
            cpu_cores = _cpu_cores()

    tier_override = env.get("EXOTICA_CLOUD_TIER", "").strip()
    tier = tier_override or "Not verified"
    return HostProfile(
        provider=provider,
        memory_gb=memory_gb,
        cpu_cores=cpu_cores,
        tier=tier,
        lavhost=bool(env.get("LAVHOST")),
    )
