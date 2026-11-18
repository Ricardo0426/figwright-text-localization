#!/usr/bin/env python3
"""Compare explicitly mapped source copy with extracted design text.

Input:
{
  "items": [
    {
      "id": "headline",
      "source_cell": "Sheet1!G8",
      "expected": "Source copy",
      "actual": "Design copy",
      "ignore_case": true,
      "ignore_list_markers": false,
      "mode": "exact"
    }
  ]
}

"actual" may instead be a nonempty string array. Its supplied order is retained,
with one space between parts. Use this only for a deliberate multi-node mapping.

Normalization is Unicode NFC plus whitespace folding. Case folding defaults to
true; --strict forces case-sensitive comparison for every item. Digits, units,
punctuation, and word boundaries are retained. List-marker removal is opt-in and
only affects a marker at a line start followed by whitespace. Contains matching
must be explicitly selected per item and is identified as substring evidence.

Exit codes: 0 = all comparisons pass, 1 = comparison mismatch, 2 = input/IO error.
The input file is never modified.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """The supplied audit mapping is malformed or ambiguous."""


# This is deliberately line-local. It does not remove hyphens within words,
# numeric signs, punctuation at arbitrary positions, or markers without a gap.
LIST_PREFIX = re.compile(
    r"(?m)^[^\S\r\n]*(?:(?:[•●◦▪▫‣⁃*+\-])|(?:[0-9]+[.)]))[^\S\r\n]+"
)
ITEM_FIELDS = {
    "id", "source_cell", "expected", "actual",
    "ignore_case", "ignore_list_markers", "mode",
}


def normalize(
    value: str, *, ignore_case: bool, ignore_list_markers: bool
) -> str:
    """Preserve word boundaries while normalizing explicitly allowed variation."""
    result = unicodedata.normalize("NFC", value)
    # Normalize line endings before applying line-local list-prefix matching.
    result = result.replace("\r\n", "\n").replace("\r", "\n")
    if ignore_list_markers:
        result = LIST_PREFIX.sub("", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result.casefold() if ignore_case else result


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise InputError(f"Duplicate JSON key: {key!r}")
        obj[key] = value
    return obj


def require_boolean(item: dict[str, Any], name: str, default: bool) -> bool:
    value = item.get(name, default)
    if type(value) is not bool:
        raise InputError(f"{name} must be a JSON boolean")
    return value


def validate_items(document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or set(document) != {"items"}:
        raise InputError("Top-level JSON must contain exactly one 'items' field")
    items = document["items"]
    if not isinstance(items, list) or not items:
        raise InputError("'items' must be a nonempty array")
    seen: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            raise InputError(f"{prefix} must be an object")
        unknown = set(item) - ITEM_FIELDS
        if unknown:
            raise InputError(f"{prefix} has unknown fields: {sorted(unknown)}")
        if not isinstance(item.get("id"), str) or not item["id"].strip():
            raise InputError(f"{prefix}.id must be a nonempty string")
        if item["id"] in seen:
            raise InputError(f"{prefix}.id is duplicated: {item['id']!r}")
        seen.add(item["id"])
        if "source_cell" in item and not isinstance(item["source_cell"], str):
            raise InputError(f"{prefix}.source_cell must be a string when supplied")
        if not isinstance(item.get("expected"), str):
            raise InputError(f"{prefix}.expected must be a string")
        actual = item.get("actual")
        if not isinstance(actual, str):
            if not isinstance(actual, list) or not actual:
                raise InputError(
                    f"{prefix}.actual must be a string or nonempty string array"
                )
            if any(not isinstance(part, str) for part in actual):
                raise InputError(f"{prefix}.actual contains a non-string part")
        require_boolean(item, "ignore_case", True)
        require_boolean(item, "ignore_list_markers", False)
        mode = item.get("mode", "exact")
        if not isinstance(mode, str) or mode not in {"exact", "contains"}:
            raise InputError(f"{prefix}.mode must be 'exact' or 'contains'")
    return items


def compare_document(document: Any, *, strict: bool = False) -> dict[str, Any]:
    items = validate_items(document)
    results: list[dict[str, Any]] = []
    for item in items:
        actual = item["actual"]
        assembled = " ".join(actual) if isinstance(actual, list) else actual
        ignore_case = False if strict else item.get("ignore_case", True)
        ignore_list_markers = item.get("ignore_list_markers", False)
        expected_norm = normalize(
            item["expected"], ignore_case=ignore_case,
            ignore_list_markers=ignore_list_markers,
        )
        actual_norm = normalize(
            assembled, ignore_case=ignore_case,
            ignore_list_markers=ignore_list_markers,
        )
        mode = item.get("mode", "exact")
        if mode == "contains" and not expected_norm:
            raise InputError(
                f"Item {item['id']!r}: contains mode requires nonempty expected text"
            )
        if mode == "exact":
            passed = expected_norm == actual_norm
            evidence: dict[str, Any] = {"kind": "exact_equality", "equal": passed}
        else:
            offset = actual_norm.find(expected_norm)
            passed = offset >= 0
            evidence = {
                "kind": "substring",
                "explicitly_requested": True,
                "start_in_normalized_actual": offset if passed else None,
                "end_in_normalized_actual": offset + len(expected_norm) if passed else None,
                "note": "A substring match does not verify remaining design text.",
            }
        results.append({
            "id": item["id"],
            "source_cell": item.get("source_cell"),
            "expected": item["expected"],
            "actual": actual,
            "assembled_actual": assembled,
            "assembly": "supplied_order_joined_with_single_spaces"
                        if isinstance(actual, list) else "single_string",
            "mode": mode,
            "normalization": {
                "unicode": "NFC",
                "whitespace": "collapsed_to_single_space",
                "ignore_case": ignore_case,
                "ignore_list_markers": ignore_list_markers,
            },
            "normalized_expected": expected_norm,
            "normalized_actual": actual_norm,
            "status": "pass" if passed else "fail",
            "evidence": evidence,
        })
    passed_count = sum(result["status"] == "pass" for result in results)
    return {
        "status": "pass" if passed_count == len(results) else "fail",
        "total": len(results),
        "pass": passed_count,
        "fail": len(results) - passed_count,
        "strict_case": strict,
        "contains_mode_items": [
            result["id"] for result in results if result["mode"] == "contains"
        ],
        "items": results,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 audit mapping JSON")
    parser.add_argument("--output", required=True, type=Path, help="Report JSON to write")
    parser.add_argument(
        "--strict", action="store_true",
        help="Force case-sensitive comparison; overrides item ignore_case",
    )
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise InputError("--output must not replace --input")
        document = json.loads(
            args.input.read_text(encoding="utf-8-sig"),
            object_pairs_hook=reject_duplicate_keys,
        )
        report = compare_document(document, strict=args.strict)
        report["input_path"] = str(args.input.resolve())
        write_report(args.output, report)
    except (InputError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        error_report = {
            "status": "input_error",
            "error": str(exc),
            "input_path": str(args.input),
        }
        # Do not replace the input even when the mapping is malformed.
        if args.input.resolve() != args.output.resolve():
            try:
                write_report(args.output, error_report)
            except OSError as write_exc:
                error_report["report_write_error"] = str(write_exc)
        print(json.dumps(error_report, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(
        {key: report[key] for key in ("status", "total", "pass", "fail")},
        ensure_ascii=False,
    ))
    return 0 if report["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

