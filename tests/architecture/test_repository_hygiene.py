import io
import re
import tokenize
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMMENT_SCAN_ROOTS = (
    REPOSITORY_ROOT / "src",
    REPOSITORY_ROOT / "tests",
    REPOSITORY_ROOT / "tools",
    REPOSITORY_ROOT / "infra",
)
CODE_COMMENT_SUFFIXES = {".py", ".sh"}
GERMAN_COMMENT_MARKERS = re.compile(
    r"\b("
    r"alle|auf|ausfuehrung|ausführung|bevor|bis|datei|definieren|ende|"
    r"fehlerhandling|fertig|für|fuer|hauptprogramm|jede|kurzen|nicht|"
    r"separaten|simuliere|starte|threads|warte|zeitaufwand"
    r")\b",
    re.IGNORECASE,
)


class TestRepositoryHygiene(unittest.TestCase):
    def test_legacy_non_production_leftovers_are_removed(self):
        forbidden_paths = (
            REPOSITORY_ROOT / "docker" / "swarm" / "prepere.py",
            REPOSITORY_ROOT / "docker" / "setup.py_old",
            REPOSITORY_ROOT
            / "src"
            / "tiny_swarm_world"
            / "infrastructure"
            / "adapters"
            / "ui"
            / "demo.py",
        )
        present_paths = [
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in forbidden_paths
            if path.exists()
        ]

        self.assertEqual([], present_paths)

    def test_code_comments_are_english_only(self):
        violations = [
            f"{path.relative_to(REPOSITORY_ROOT).as_posix()}:{line_number}: {comment}"
            for path in _code_files()
            for line_number, comment in _comments(path)
            if GERMAN_COMMENT_MARKERS.search(comment)
        ]

        self.assertEqual([], violations)


def _code_files() -> list[Path]:
    return sorted(
        path
        for root in COMMENT_SCAN_ROOTS
        if root.exists()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in CODE_COMMENT_SUFFIXES
    )


def _comments(path: Path) -> list[tuple[int, str]]:
    if path.suffix == ".py":
        return _python_comments(path)
    if path.suffix == ".sh":
        return _shell_comments(path)
    return []


def _python_comments(path: Path) -> list[tuple[int, str]]:
    source = path.read_text(encoding="utf-8")
    comments = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            comments.append((token.start[0], token.string))
    return comments


def _shell_comments(path: Path) -> list[tuple[int, str]]:
    return [
        (line_number, line.strip())
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            1,
        )
        if line.lstrip().startswith("#") and not line.startswith("#!")
    ]
