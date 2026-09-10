"""Build the shared Python desktop source on Windows or macOS with Nuitka."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


APP_DIR = Path(__file__).resolve().parent
PROTOCOL_PACKAGE = APP_DIR.parent / "protocol" / "shared_protocol" / "python"
VERSIONS = json.loads((APP_DIR / "version.json").read_text(encoding="utf-8"))


def numeric_version() -> str:
    """Return a Windows-compatible four-part version while retaining beta in UI."""
    base = VERSIONS["app_version"].split("-", 1)[0]
    return f"{base}.{int(VERSIONS['app_build'])}"


def build_command(platform: str, sign_identity: str | None = None) -> list[str]:
    if platform not in ("win32", "darwin"):
        raise ValueError(f"Unsupported desktop platform: {platform}")
    platform_name = "windows" if platform == "win32" else "macos"
    dist_dir = APP_DIR / "dist" / platform_name
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--mode=app-dist",
        "--enable-plugin=pyside6",
        "--include-package=bleak",
        "--include-package=winrt",
        "--include-package=galeon_protocol",
        "--include-module=PySide6.QtOpenGL",
        "--include-module=PySide6.QtOpenGLWidgets",
        f"--include-data-files={APP_DIR / 'version.json'}=version.json",
        "--include-qt-plugins=platforms,styles,imageformats,iconengines,platforminputcontexts",
        "--noinclude-qt-translations",
        "--assume-yes-for-downloads",
        "--remove-output",
        f"--output-dir={dist_dir}",
        str(APP_DIR / "AeroMeter.py"),
    ]
    if platform == "win32":
        command.insert(3, "--mingw64")
        command.extend(
            [
                "--windows-console-mode=disable",
                "--company-name=Galeon",
                "--product-name=Galeon AeroMeter",
                "--file-description=Galeon AeroMeter Desktop",
                f"--file-version={numeric_version()}",
                f"--product-version={numeric_version()}",
                "--copyright=Copyright Galeon",
            ]
        )
    else:
        command.extend(
            [
                "--macos-app-name=AeroMeter",
                "--macos-app-mode=gui",
                "--macos-signed-app-name=com.andyxu.AeroMeterDesktop",
                f"--macos-app-version={VERSIONS['app_version'].split('-', 1)[0]}",
                "--macos-app-protected-resource=NSBluetoothAlwaysUsageDescription:AeroMeter uses Bluetooth to receive pressure and flow measurements.",
                "--macos-app-protected-resource=NSBluetoothPeripheralUsageDescription:AeroMeter uses Bluetooth to receive pressure and flow measurements.",
                "--copyright=Copyright Galeon",
            ]
        )
        if sign_identity:
            command.extend(
                [
                    f"--macos-sign-identity={sign_identity}",
                    "--macos-sign-notarization",
                ]
            )
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sign-identity", help="macOS Developer ID Application identity")
    args = parser.parse_args()
    if sys.platform not in ("win32", "darwin"):
        raise SystemExit("Desktop packages are supported on Windows and macOS only")
    if not (PROTOCOL_PACKAGE / "pyproject.toml").is_file():
        raise SystemExit("Protocol submodule is missing; initialize Git submodules first")
    environment = os.environ.copy()
    # Sandboxed/packaged hosts can assign a very long user-cache path. MinGW's
    # nested Windows SDK headers may then exceed the legacy path limit.
    environment.setdefault("NUITKA_CACHE_DIR", str(APP_DIR / ".cache" / "nuitka"))
    subprocess.run(
        build_command(sys.platform, args.sign_identity),
        cwd=APP_DIR,
        env=environment,
        check=True,
    )
    if sys.platform == "win32":
        print(f"Windows application: {APP_DIR / 'dist' / 'windows' / 'AeroMeter.dist'}")
    else:
        print(f"macOS application: {APP_DIR / 'dist' / 'macos' / 'AeroMeter.app'}")


if __name__ == "__main__":
    main()
