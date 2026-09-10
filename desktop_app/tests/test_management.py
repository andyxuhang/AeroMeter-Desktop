"""Pure tests for the shared Windows/macOS management and packaging helpers."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_desktop
import manage


class ManagementTests(unittest.TestCase):
    def test_windows_environment_uses_scripts_python(self):
        with patch.object(manage.sys, "platform", "win32"):
            self.assertEqual(
                manage.venv_python(), manage.VENV / "Scripts" / "python.exe"
            )

    def test_macos_environment_uses_bin_python(self):
        with patch.object(manage.sys, "platform", "darwin"):
            self.assertEqual(manage.venv_python(), manage.VENV / "bin" / "python")

    def test_windows_build_uses_common_source_and_numeric_version(self):
        command = build_desktop.build_command("win32")
        self.assertIn("--mode=app-dist", command)
        self.assertIn("--enable-plugin=pyside6", command)
        self.assertIn("--include-package=galeon_protocol", command)
        self.assertIn("--include-package=bleak", command)
        self.assertIn("--include-package=winrt", command)
        self.assertIn("--include-module=PySide6.QtOpenGL", command)
        self.assertIn("--windows-console-mode=disable", command)
        self.assertIn("--file-version=1.2.0.10", command)
        self.assertTrue(
            any(item.startswith("--windows-icon-from-ico=") for item in command)
        )
        self.assertTrue(any(item.endswith("AeroMeter.py") for item in command))

    def test_macos_build_uses_same_source_and_permissions(self):
        command = build_desktop.build_command("darwin", "Developer ID")
        self.assertIn("--mode=app-dist", command)
        self.assertIn("--macos-app-mode=gui", command)
        self.assertIn("--macos-sign-identity=Developer ID", command)
        self.assertTrue(
            any("NSBluetoothAlwaysUsageDescription" in item for item in command)
        )
        self.assertIn("--macos-app-version=1.2.0", command)
        self.assertTrue(any(item.endswith("AeroMeter.py") for item in command))


if __name__ == "__main__":
    unittest.main()
