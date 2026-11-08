from pathlib import Path

from setuptools import find_packages, setup


def _runtime_requirements() -> list[str]:
    requirements_path = Path(__file__).with_name("requirements.txt")
    requirements = []
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            requirements.append(stripped)
    return requirements


setup(
    name="tiny-swarm-world",
    version="0.2.0",
    packages=["tiny_swarm_world", "tsw_core"] + [
        f"tiny_swarm_world.{package}"
        for package in find_packages(where="modules/tsw_core/src")
    ],
    package_dir={
        "tiny_swarm_world": "modules/tsw_core/src",
        "tsw_core": "modules/tsw_core",
    },
    include_package_data=True,
    package_data={"tsw_core": ["src/module.json"]},
    install_requires=_runtime_requirements(),
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "tiny-swarm-world=tiny_swarm_world.__main__:cli",
        ],
    },
)
