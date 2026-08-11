from __future__ import annotations

import json
from pathlib import Path

from tiny_swarm_world.application.ports.repositories.port_performance_evidence_repository import (
    PortPerformanceEvidenceRepository,
)
from tiny_swarm_world.domain.performance import PerformanceMeasurement


DEFAULT_PERFORMANCE_EVIDENCE_ROOT = Path(".tiny-swarm") / "evidence"


class PerformanceEvidenceLocalRepository(PortPerformanceEvidenceRepository):
    """Write one stable JSON/Markdown pair per validated measurement."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or DEFAULT_PERFORMANCE_EVIDENCE_ROOT).expanduser()

    def write(self, measurement: PerformanceMeasurement) -> tuple[Path, Path]:
        issue_root = self.root / measurement.issue_id
        stem = f"{measurement.workflow_id}--{measurement.segment_id}"
        json_path = issue_root / f"{stem}.json"
        markdown_path = issue_root / f"{stem}.md"
        issue_root.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(measurement.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(
            render_performance_evidence_markdown(measurement),
            encoding="utf-8",
        )
        return json_path, markdown_path


def render_performance_evidence_markdown(measurement: PerformanceMeasurement) -> str:
    """Render a stable human-readable projection of a measurement."""

    lines = [
        f"# Performance Evidence: {measurement.segment}",
        "",
        f"- Issue: `{measurement.issue_id}`",
        f"- Workflow: `{measurement.workflow_id}`",
        f"- Segment ID: `{measurement.segment_id}`",
        f"- Measurement scope: `{measurement.measurement_scope}`",
        f"- Target kind: `{measurement.target_kind}`",
        f"- Target IDs: {', '.join(f'`{target}`' for target in measurement.target_ids)}",
        f"- Environment summary: {_markdown_text(measurement.environment_summary)}",
        f"- Started at: {_optional_text(measurement.started_at)}",
        f"- Finished at: {_optional_text(measurement.finished_at)}",
        f"- Duration seconds: {_optional_text(measurement.duration_seconds)}",
        "",
        "## Counters",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    if measurement.counters:
        lines.extend(
            f"| `{key}` | {value} |"
            for key, value in measurement.counters.items()
        )
    else:
        lines.append("| *(none)* | — |")

    lines.extend(
        (
            "",
            "## Baseline and new values",
            "",
            "| Metric | Baseline | New |",
            "|---|---:|---:|",
        )
    )
    metric_names = sorted(set(measurement.baseline or {}) | set(measurement.new_values or {}))
    if metric_names:
        lines.extend(
            "| `{}` | {} | {} |".format(
                key,
                _optional_text((measurement.baseline or {}).get(key)),
                _optional_text((measurement.new_values or {}).get(key)),
            )
            for key in metric_names
        )
    else:
        lines.append("| *(none)* | — | — |")

    lines.extend(("", "## Limitations", ""))
    lines.extend(f"- {_markdown_text(limitation)}" for limitation in measurement.limitations)
    return "\n".join(lines) + "\n"


def _optional_text(value: object) -> str:
    return "—" if value is None else str(value)


def _markdown_text(value: str) -> str:
    return value.replace("|", "\\|")
