"""Bounded JSON parser for isolated versioned drafts."""
from __future__ import annotations

import json
import math

LIMIT = 1024 * 1024
_MAX_DEPTH = 32
_MAX_ITEMS = 50000


def _string_end(text: str, index: int) -> int:
    index += 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text[index] == '"':
            return index + 1
        else:
            index += 1
    return index


def _scan_limits(text: str) -> None:
    stack: list[list[object]] = []
    items = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in " \t\r\n":
            index += 1
            continue
        if char in "]}":
            if stack:
                stack.pop()
            index += 1
            continue
        if char == ",":
            if stack and stack[-1][0] == "array":
                stack[-1][1] = True
            index += 1
            continue
        if char == ":":
            items += 1
            index += 1
        else:
            if stack and stack[-1][0] == "array" and stack[-1][1] is True:
                items += 1
                stack[-1][1] = False
            if char in "[{":
                stack.append(["array" if char == "[" else "object", char == "["])
                if len(stack) > _MAX_DEPTH:
                    raise ValueError("Invalid draft.")
                index += 1
            elif char == '"':
                index = _string_end(text, index)
            else:
                while index < len(text) and text[index] not in " \t\r\n,]}:":
                    index += 1
        if items > _MAX_ITEMS:
            raise ValueError("Invalid draft.")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Invalid draft.")
        result[key] = value
    return result


def _nonfinite(_value: str) -> object:
    raise ValueError("Invalid draft.")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Invalid draft.")
    return result


def bounded_json(raw: bytes) -> object:
    if len(raw) > LIMIT:
        raise ValueError("Invalid draft.")
    text = raw.decode("utf-8", "strict")
    _scan_limits(text)
    return json.loads(text, object_pairs_hook=_unique, parse_constant=_nonfinite, parse_float=_finite_float)
