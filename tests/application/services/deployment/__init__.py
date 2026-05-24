from pathlib import Path
import unittest


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    test_pattern = pattern or "test*.py"
    for test_file in sorted(Path(__file__).parent.glob(test_pattern)):
        suite.addTests(loader.loadTestsFromName(f"{__name__}.{test_file.stem}"))
    return suite
