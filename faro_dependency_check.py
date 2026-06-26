from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "faro_data"
LOG_PATH = DATA_DIR / "dependency_check.log"
REQ_PATH = ROOT / "requirements.txt"

REQUIRED_STDLIB = [
    "tkinter",
    "sqlite3",
    "webbrowser",
    "urllib.parse",
    "pathlib",
    "json",
    "csv",
    "html",
    "uuid",
]

PACKAGE_IMPORT_MAP = {
    "pyttsx3": "pyttsx3",
    "pillow": "PIL",
    "requests": "requests",
    "pyperclip": "pyperclip",
}


def log(text: str) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {text}\n")


def import_ok(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception as exc:
        log(f"FAIL import {module_name}: {exc}")
        return False


def parse_requirements() -> list[str]:
    if not REQ_PATH.exists():
        return []
    packages = []
    for line in REQ_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line
        for sep in ["==", ">=", "<=", "~=", ">", "<"]:
            if sep in pkg:
                pkg = pkg.split(sep, 1)[0].strip()
                break
        if pkg:
            packages.append(line)
    return packages


def package_import_name(requirement: str) -> str:
    name = requirement
    for sep in ["==", ">=", "<=", "~=", ">", "<"]:
        if sep in name:
            name = name.split(sep, 1)[0].strip()
            break
    return PACKAGE_IMPORT_MAP.get(name.lower(), name.replace("-", "_"))


def install_missing(requirements: list[str]) -> bool:
    if not requirements:
        log("No external requirements declared.")
        return True

    missing = []
    for req in requirements:
        mod = package_import_name(req)
        if not import_ok(mod):
            missing.append(req)

    if not missing:
        log("External requirements already installed. Nothing to install.")
        print("[OK] Dependencias externas ya instaladas. No se instala nada.")
        return True

    print("[INFO] Faltan dependencias externas:")
    for m in missing:
        print(" -", m)

    print("[INFO] Instalando solo dependencias faltantes...")
    log("Installing missing packages: " + ", ".join(missing))

    cmd = [sys.executable, "-m", "pip", "install", *missing]
    proc = subprocess.run(cmd, text=True)
    if proc.returncode != 0:
        log(f"pip install failed with code {proc.returncode}")
        return False

    for req in missing:
        mod = package_import_name(req)
        if not import_ok(mod):
            print(f"[ERROR] No se pudo importar {mod} después de instalar.")
            return False

    print("[OK] Dependencias faltantes instaladas.")
    return True


def main() -> int:
    DATA_DIR.mkdir(exist_ok=True)
    log("Dependency check started.")

    if sys.version_info < (3, 10):
        print("[ERROR] FARO necesita Python 3.10 o superior.")
        print("Instalá una versión actual de Python desde python.org.")
        log("Python version too old.")
        return 2

    print(f"[OK] Python detectado: {sys.version.split()[0]}")

    stdlib_missing = []
    for module in REQUIRED_STDLIB:
        if import_ok(module):
            print(f"[OK] {module}")
        else:
            stdlib_missing.append(module)
            print(f"[ERROR] Falta o falla: {module}")

    if stdlib_missing:
        print()
        print("[ERROR] Faltan módulos base de Python.")
        if "tkinter" in stdlib_missing:
            print("Tkinter no está disponible. En Windows, reinstalá Python desde python.org y marcá Tcl/Tk.")
        print(f"Detalle en: {LOG_PATH}")
        return 3

    requirements = parse_requirements()
    if not install_missing(requirements):
        print(f"[ERROR] No se pudieron instalar todas las dependencias. Ver log: {LOG_PATH}")
        return 4

    log("Dependency check completed successfully.")
    print("[OK] FARO listo para abrir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
