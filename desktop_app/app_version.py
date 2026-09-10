"""Desktop app and contract versions are independent of installed firmware."""
import json
from pathlib import Path

VERSIONS = json.loads(Path(__file__).with_name("version.json").read_text(encoding="utf-8"))
APP_VERSION = VERSIONS["app_version"]
FRAMEWORK_VERSION = VERSIONS["framework_version"]
