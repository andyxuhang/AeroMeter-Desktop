"""One cross-platform entry point for the AeroMeter desktop application."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
VENV = APP_DIR / ".venv"
PROTOCOL_PACKAGE = ROOT / "protocol" / "shared_protocol" / "python"


def venv_python() -> Path:
    relative = Path("Scripts/python.exe") if sys.platform == "win32" else Path("bin/python")
    return VENV / relative


def require_protocol() -> None:
    if not (PROTOCOL_PACKAGE / "pyproject.toml").is_file():
        raise SystemExit(
            "Protocol submodule is missing. Run: git submodule update --init --recursive"
        )


def require_environment() -> Path:
    python = venv_python()
    if not python.is_file():
        raise SystemExit("Desktop environment is missing. Run: python desktop_app/manage.py setup")
    return python


def setup(development: bool) -> None:
    require_protocol()
    if not venv_python().is_file():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    python = venv_python()
    requirements = APP_DIR / ("requirements-dev.txt" if development else "requirements.txt")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-e", str(PROTOCOL_PACKAGE)], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)
    print(f"Desktop environment ready: {VENV}")


def invoke(arguments: list[str]) -> None:
    subprocess.run([str(require_environment()), *arguments], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the shared AeroMeter desktop app")
    commands = parser.add_subparsers(dest="command", required=True)
    setup_parser = commands.add_parser("setup", help="create the local Python environment")
    setup_parser.add_argument(
        "--development", action="store_true", help="also install release build tools"
    )
    commands.add_parser("run", help="start the desktop application")
    commands.add_parser("test", help="run desktop unit and off-screen UI tests")
    build_parser = commands.add_parser("build", help="build a Windows exe or macOS app")
    build_parser.add_argument("--sign-identity", help="macOS Developer ID Application identity")
    args = parser.parse_args()

    if args.command == "setup":
        setup(args.development)
    elif args.command == "run":
        invoke([str(APP_DIR / "main.py")])
    elif args.command == "test":
        invoke(["-m", "unittest", "discover", "-s", str(APP_DIR / "tests"), "-q"])
    elif args.command == "build":
        command = [str(APP_DIR / "build_desktop.py")]
        if args.sign_identity:
            command.extend(["--sign-identity", args.sign_identity])
        invoke(command)


if __name__ == "__main__":
    main()
