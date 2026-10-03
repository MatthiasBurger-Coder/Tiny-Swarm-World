"""Detect material orchestration complexity growth against a reviewed baseline."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "tiny_swarm_world"
BASELINE = ROOT / "documentation" / "arc42" / "05_analysis" / "arch-03-18-complexity-baseline.json"
EXCEPTIONS = ROOT / "documentation" / "arc42" / "05_analysis" / "arch-03-18-complexity-exceptions.json"
def covered_paths(source: Path = SOURCE) -> list[Path]:
    paths = set(source.glob("*.py"))
    paths.update((source / "infrastructure").glob("composition*.py"))
    paths.update((source / "application" / "services").rglob("*.py"))
    paths.update((source / "infrastructure" / "adapters").rglob("*.py"))
    return sorted(paths)


def _complexity(node: ast.AST) -> int:
    score = 1
    pending = [node]
    while pending:
        child = pending.pop()
        if child is not node and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        pending.extend(ast.iter_child_nodes(child))
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler, ast.Assert)):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            score += len(child.ifs) + 1
        elif isinstance(child, ast.Match):
            score += sum(not (isinstance(case.pattern, ast.MatchAs) and case.pattern.name is None)
                         for case in child.cases)
    return score


def _functions(tree: ast.AST, prefix: str = "") -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    result: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = f"{prefix}{node.name}"
            result.append((name, node))
            result.extend(_functions(node, f"{name}."))
        elif isinstance(node, ast.ClassDef):
            result.extend(_functions(node, f"{prefix}{node.name}."))
    return result


def _fingerprint(node: ast.AST) -> str:
    normalized = copy.deepcopy(node)
    if isinstance(normalized, (ast.FunctionDef, ast.AsyncFunctionDef)):
        normalized.name = "_"
    return hashlib.sha256(ast.dump(normalized, include_attributes=False).encode()).hexdigest()[:16]


def snapshot(paths: list[Path], root: Path = ROOT) -> dict[str, Any]:
    modules: dict[str, dict[str, object]] = {}
    duplicates: dict[str, list[str]] = {}
    for path in paths:
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        functions = _functions(tree)
        function_metrics: dict[str, dict[str, int]] = {}
        for name, node in functions:
            assert node.end_lineno is not None
            lines = node.end_lineno - node.lineno + 1
            complexity = _complexity(node)
            function_metrics[name] = {"lines": lines, "complexity": complexity}
            if complexity >= 8 and lines >= 12:
                duplicates.setdefault(_fingerprint(node), []).append(f"{relative}:{name}")
        classes = {
            node.name: {"lines": node.end_lineno - node.lineno + 1,
                        "complexity": sum(_complexity(method) for method in node.body
                                          if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)))}
            for node in tree.body if isinstance(node, ast.ClassDef) and node.end_lineno is not None
        }
        imports = {
            alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            ("." * node.level) + (node.module or "") for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        modules[relative] = {
            "lines": len(source.splitlines()),
            "complexity": sum(metric["complexity"] - 1 for metric in function_metrics.values()) + 1,
            "fanout": len(imports),
            "classes": classes,
            "functions": function_metrics,
        }
    repeated = {key: sorted(locations) for key, locations in duplicates.items()
                if len({item.split(":")[0] for item in locations}) > 1}
    return {"schema": 1, "modules": modules, "duplicates": repeated}


def findings(current: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    current_modules = current["modules"]
    baseline_modules = baseline["modules"]
    assert isinstance(current_modules, dict) and isinstance(baseline_modules, dict)
    result: list[str] = []
    for path in baseline_modules.keys() - current_modules.keys():
        result.append(f"missing-covered-module:{path}")
    for path, metrics in current_modules.items():
        previous = baseline_modules.get(path, {})
        assert isinstance(metrics, dict) and isinstance(previous, dict)
        current_functions = metrics["functions"]
        old_functions = previous.get("functions", {})
        assert isinstance(current_functions, dict) and isinstance(old_functions, dict)
        for name, value in current_functions.items():
            old = old_functions.get(name)
            assert isinstance(value, dict)
            if value["complexity"] >= 15 and value["lines"] >= 60:
                if old is None:
                    result.append(f"new-critical-function:{path}:{name}")
                elif old["complexity"] < 15 or old["lines"] < 60:
                    result.append(f"newly-critical-function:{path}:{name}")
                elif (value["complexity"] >= old["complexity"] + 4
                      or (value["complexity"] >= old["complexity"] + 2
                          and value["lines"] >= old["lines"] + 40)):
                    result.append(f"grown-critical-function:{path}:{name}")
        if not previous and (metrics["complexity"] >= 40
                             and metrics["fanout"] >= 12
                             and metrics["lines"] >= 300):
            result.append(f"new-critical-module:{path}")
        elif (previous and metrics["complexity"] >= 40 and metrics["fanout"] >= 12
              and metrics["lines"] >= 300
              and (previous["complexity"] < 40 or previous["fanout"] < 12
                   or previous["lines"] < 300)):
            result.append(f"newly-critical-module:{path}")
        elif previous and (metrics["complexity"] >= previous["complexity"] + 10
                           and metrics["fanout"] >= previous["fanout"] + 3):
            result.append(f"grown-module-coupling:{path}")
        if previous and metrics["complexity"] >= previous["complexity"] + 25:
            result.append(f"grown-module-complexity:{path}")
        if previous and metrics["fanout"] >= previous["fanout"] + 8:
            result.append(f"grown-module-fanout:{path}")
        current_classes = metrics["classes"]
        old_classes = previous.get("classes", {})
        assert isinstance(current_classes, dict) and isinstance(old_classes, dict)
        for name, value in current_classes.items():
            old = old_classes.get(name)
            assert isinstance(value, dict)
            if old is None and value["complexity"] >= 25 and value["lines"] >= 120:
                result.append(f"new-critical-class:{path}:{name}")
            elif (old and value["complexity"] >= 25 and value["lines"] >= 120
                  and (old["complexity"] < 25 or old["lines"] < 120)):
                result.append(f"newly-critical-class:{path}:{name}")
            elif old and value["complexity"] >= old["complexity"] + 8 and value["lines"] >= 120:
                result.append(f"grown-critical-class:{path}:{name}")
    current_duplicates = current["duplicates"]
    old_duplicates = baseline["duplicates"]
    assert isinstance(current_duplicates, dict) and isinstance(old_duplicates, dict)
    for digest, locations in current_duplicates.items():
        if set(locations) - set(old_duplicates.get(digest, [])):
            result.append(f"new-duplicate-orchestration:{digest}")
    return sorted(result)


def check(current: dict[str, Any], baseline: dict[str, Any], exceptions: dict[str, Any]) -> list[str]:
    if current["schema"] != 1 or baseline["schema"] != 1 or exceptions["schema"] != 1:
        raise ValueError("Unsupported complexity guardrail schema")
    allowed = exceptions["findings"]
    if not isinstance(allowed, dict):
        raise ValueError("Exception findings must be a mapping")
    for key, entry in allowed.items():
        if not isinstance(entry, dict) or not all(entry.get(field) for field in ("owner", "reason", "issue")):
            raise ValueError(f"Incomplete reviewed exception: {key}")
    detected = findings(current, baseline)
    stale = sorted(set(allowed) - set(detected))
    if stale:
        raise ValueError(f"Stale reviewed exceptions: {', '.join(stale)}")
    return sorted(set(detected) - set(allowed))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-current", action="store_true", help="Print current source snapshot for baseline review")
    args = parser.parse_args()
    current = snapshot(covered_paths())
    if args.show_current:
        print(json.dumps(current, indent=2, sort_keys=True))
        return
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    exceptions = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    failures = check(current, baseline, exceptions)
    if failures:
        print("Complexity guardrail review required:")
        for failure in failures:
            print(f"  {failure}")
        raise SystemExit(1)
    print(f"Complexity guardrail passed: {len(current['modules'])} orchestration modules checked")


if __name__ == "__main__":
    main()
