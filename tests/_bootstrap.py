"""Runs inside Blender (started by tests/run.py).

    blender -b --factory-startup --python tests/_bootstrap.py -- <test_file.py> <result.json>

Enables the extension unless the test module sets ``AUTO_ENABLE = False``,
runs each top-level ``test_*`` function in definition order and writes
``[{"name", "ok", "error"}]`` to the result file; a test that raises
``kit.Skip`` (something this machine or clone lacks) is ``{"name", "ok": True,
"skipped": reason}``.
"""

import importlib.util
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    test_path, out_path = Path(argv[0]), Path(argv[1])
    results = []

    try:
        spec = importlib.util.spec_from_file_location(test_path.stem, test_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if getattr(mod, "AUTO_ENABLE", True):
            kit.enable()
        tests = [(n, f) for n, f in vars(mod).items() if n.startswith("test_") and callable(f)]
        for name, func in tests:
            print(f"TEST {name}", flush=True)      # the last name in a crashed run's log = the crashing test
            try:
                func()
                results.append({"name": name, "ok": True})
            except kit.Skip as ex:
                results.append({"name": name, "ok": True, "skipped": str(ex)})
            except Exception:
                results.append({"name": name, "ok": False, "error": traceback.format_exc()})
    except kit.Skip as ex:          # the test file needs data that isn't here (kit.Skip at import)
        results.append({"name": "<file>", "ok": True, "skipped": str(ex)})
    except Exception:
        results.append({"name": "<setup>", "ok": False, "error": traceback.format_exc()})

    out_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
    if not all(r["ok"] for r in results):
        sys.exit(1)


main()
