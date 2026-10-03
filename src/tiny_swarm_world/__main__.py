"""Executable bootstrap for the command-line adapter."""

import asyncio
from collections.abc import Sequence

from tiny_swarm_world.infrastructure.adapters.cli import dispatcher


async def main(argv: Sequence[str] | None = None) -> None:
    await dispatcher.main(argv)


def cli(argv: Sequence[str] | None = None) -> None:
    asyncio.run(main(argv))


if __name__ == "__main__":
    cli()
