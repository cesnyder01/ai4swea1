"""Report local environment details for the assignment project.

This script is intentionally lightweight so it can run before the machine-learning
dependencies are installed.
"""

from __future__ import annotations

import importlib.metadata as metadata
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def format_bytes(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "unavailable"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def get_package_version(package_name: str) -> str:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "not installed"


def get_system_memory_gb() -> str:
    try:
        import ctypes

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return f"{status.ullTotalPhys / (1024 ** 3):.2f} GiB total, {status.ullAvailPhys / (1024 ** 3):.2f} GiB available"
    except Exception:
        pass
    return "unavailable"


def inspect_torch() -> dict[str, Any]:
    details: dict[str, Any] = {"installed": False}
    try:
        import torch

        details["installed"] = True
        details["version"] = torch.__version__
        details["cuda_available"] = torch.cuda.is_available()
        details["cuda_version"] = torch.version.cuda
        details["device_count"] = torch.cuda.device_count()
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            details["device_name"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        details["error"] = str(exc)
    return details


def main() -> int:
    print("Project root:", PROJECT_ROOT)
    print("Python executable:", sys.executable)
    print("Python version:", sys.version.replace("\n", " "))
    print("Platform:", platform.platform())
    print("Machine:", platform.machine())
    print("Processor:", platform.processor() or "unavailable")
    print("Current working directory:", Path.cwd())
    print("Project root exists:", PROJECT_ROOT.exists())
    print("Disk free on project drive:", format_bytes(shutil.disk_usage(PROJECT_ROOT).free))
    print("System RAM:", get_system_memory_gb())
    print("Installed package versions:")
    for package_name in ["tree-sitter", "tree-sitter-java", "PyYAML", "pytest", "ruff", "pandas", "torch"]:
        print(f"  {package_name}: {get_package_version(package_name)}")
    print("PyTorch details:")
    torch_details = inspect_torch()
    for key, value in torch_details.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
