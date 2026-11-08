"""Operator entry point for dependency-light installation bootstrap."""

from collections.abc import Sequence
from tiny_swarm_world.infrastructure.composition_installation import (
    simple_install_main,
    prepare_bootstrap_environment as _prepare_bootstrap_environment,
)

__all__ = ["main", "_prepare_bootstrap_environment"]


def main(argv: Sequence[str] | None = None) -> int:
    return simple_install_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
