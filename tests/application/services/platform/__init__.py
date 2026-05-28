"""Platform application service tests."""

from pathlib import Path
import unittest


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del tests
    return loader.discover(
        str(Path(__file__).parent),
        pattern or "test*.py",
        top_level_dir=str(Path(__file__).parents[4]),
    )
