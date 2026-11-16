"""Install the figure environment and optionally render the main or SI figures."""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parent
PYTHON_VERSION = (3, 12)
PACKAGES = {
    "matplotlib": ("3.10.8", "matplotlib"),
    "numpy": ("2.2.6", "numpy"),
    "pandas": ("2.2.3", "pandas"),
    "scipy": ("1.15.3", "scipy"),
    "pwlf": ("2.5.2", "pwlf"),
    "networkx": ("3.4.2", "networkx"),
    "openpyxl": ("3.1.5", "openpyxl"),
    "Pillow": ("11.3.0", "PIL"),
    "fonttools": ("4.68.0", "fontTools"),
}
GROUPS = {"main": ("main figs 1-6", 6), "si": ("SI figs", 26)}


def figure_scripts(group):
    name, count = GROUPS[group]
    folder = ROOT / name
    scripts = sorted(folder.glob("*/plot*.py"))
    if len(scripts) != count or len({script.parent for script in scripts}) != count:
        raise RuntimeError(
            f"Expected {count} figure subfolders with one script each in {folder}. "
            f"Use the complete repository figure collection and keep each script with its data."
        )
    return scripts


def run_python(python, *args, **options):
    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [str(python), "-X", "utf8", *map(str, args)], cwd=ROOT, env=env, **options
    )


def setup(directory):
    binary = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
    python = directory.joinpath(*binary)
    if not python.is_file():
        print(f"Creating Python 3.12 environment at {directory}", flush=True)
        venv.EnvBuilder(with_pip=True).create(directory)

    result = run_python(
        python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
        check=True, capture_output=True, text=True
    )
    if result.stdout.strip() != ".".join(map(str, PYTHON_VERSION)):
        raise RuntimeError(f"{directory} uses Python {result.stdout.strip()}. Choose a new path with --venv.")

    requirements = {name: version for name, (version, _) in PACKAGES.items()}
    get_versions = (
        "import json; from importlib.metadata import distributions; "
        "print(json.dumps({d.metadata['Name'].lower(): d.version for d in distributions()}))"
    )
    versions = run_python(python, "-c", get_versions, check=True, capture_output=True, text=True)
    installed = json.loads(versions.stdout)
    if any(installed.get(name.lower()) != version for name, version in requirements.items()):
        print("Installing the figure packages", flush=True)
        run_python(
            python, "-m", "pip", "install", "--disable-pip-version-check", "--only-binary=:all:",
            *(f"{name}=={version}" for name, version in requirements.items()), check=True
        )
    run_python(python, "-m", "pip", "check", check=True)
    imports = ", ".join(module for _, module in PACKAGES.values())
    run_python(python, "-c", f"import {imports}", check=True)
    return python


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--venv", type=Path, default=ROOT / ".venv-figures",
                     help="Location of the figure environment (default: .venv-figures beside this file).")
    cli.add_argument("--plot", choices=("main", "si", "all"),
                     help="Render the selected figures after setting up the environment.")
    args = cli.parse_args()
    if (sys.implementation.name != "cpython" or sys.version_info[:2] != PYTHON_VERSION
            or struct.calcsize("P") != 8):
        cli.error("Run this pipeline with 64-bit CPython 3.12 (py -3.12 on Windows or python3.12 on macOS/Linux).")
    try:
        groups = tuple(GROUPS) if args.plot == "all" else (args.plot,) if args.plot else ()
        scripts = [script for group in groups for script in figure_scripts(group)]
        python = setup(args.venv.expanduser().resolve())
        print(f"Figure environment ready. Python: {python}", flush=True)
        for index, script in enumerate(scripts, 1):
            print(f"[{index}/{len(scripts)}] {script.relative_to(ROOT)}", flush=True)
            run_python(python, script, check=True)
        if scripts:
            print(f"Rendered {len(scripts)} figures beside their plotting scripts.")
    except subprocess.CalledProcessError as exc:
        command = " ".join(map(str, exc.cmd[1:]))
        cli.exit(1, f"Figure pipeline stopped (exit {exc.returncode}) while running {command}. See the output above.\n")
    except (OSError, RuntimeError) as exc:
        cli.exit(1, f"Figure pipeline stopped: {exc}\n")


if __name__ == "__main__":
    main()
