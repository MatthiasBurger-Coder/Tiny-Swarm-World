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
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=_runtime_requirements(),
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "tiny-swarm-world=tiny_swarm_world.__main__:cli",
        ],
    },
)
