"""Strict JSON and a bounded schema subset shared by local tools, without I/O."""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any


TOOL_SCHEMA_VERSION = "1.0"


def json_value(value: Any, *, depth: int = 0) -> Any:
    """Copy strict JSON values without non-finite numbers, non-string keys or coercion."""
    if depth > 64:
        raise ValueError("JSON nesting exceeds 64 levels.")
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValueError("JSON object keys must be strings.")
        return {key: json_value(item, depth=depth + 1) for key, item in value.items()}
    if type(value) is list:
        return [json_value(item, depth=depth + 1) for item in value]
    raise ValueError("Expected strict JSON; non-finite numbers and non-JSON objects are forbidden.")


def json_dumps(value: Any) -> str:
    return json.dumps(json_value(value), ensure_ascii=True, sort_keys=True, allow_nan=False, separators=(",", ":"))


def json_loads(text: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON number: {value}")

    return json_value(json.loads(text, object_pairs_hook=pairs, parse_constant=constant))


def nonnegative_number(value: Any, field: str) -> float:
    try:
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError
        return float(value)
    except (ValueError, OverflowError):
        raise ValueError(f"{field} must be a finite non-negative number, not bool.") from None


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(f"{field} must be an array of nonempty strings.")
    return list(value)


def object_fields(value: Any, required: set[str], optional: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    if required - value.keys():
        raise ValueError(f"{field} missing fields: {sorted(required - value.keys())}")
    if value.keys() - required - optional:
        raise ValueError(f"{field} unknown fields: {sorted(value.keys() - required - optional)}")
    return value


def nonempty_string(value: Any, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field} must be a nonempty string.")
    return value


_TYPES = {"object", "array", "string", "number", "integer", "boolean", "null"}
_KEYWORDS = {"type", "properties", "required", "additionalProperties", "items", "enum", "minimum", "maximum",
             "minItems", "maxItems", "minLength", "maxLength", "description", "default"}


def check_schema(schema: Any) -> None:
    """Validate the supported schema subset, rejecting unknown keywords and references."""
    schema = json_value(schema)
    if not isinstance(schema, dict) or set(schema) - _KEYWORDS:
        raise ValueError("Unknown schema keyword or invalid schema object.")
    types = schema.get("type")
    types = [types] if isinstance(types, str) else types
    if not isinstance(types, list) or not types or any(type(item) is not str or item not in _TYPES for item in types):
        raise ValueError("Unknown schema type.")
    if len(types) != len(set(types)):
        raise ValueError("Duplicate schema type.")
    if "description" in schema:
        nonempty_string(schema["description"], "schema.description")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise ValueError("Schema enum must be a nonempty array.")
    if set(schema) & {"properties", "required", "additionalProperties"}:
        if "object" not in types or schema.get("additionalProperties", False) is not False:
            raise ValueError("Object schemas must reject additional properties.")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("Schema properties must be an object.")
        required = string_list(schema.get("required", []), "schema.required")
        if len(required) != len(set(required)) or set(required) - properties.keys():
            raise ValueError("Invalid schema required fields.")
        for child in properties.values():
            check_schema(child)
    if "array" in types:
        if "items" not in schema:
            raise ValueError("Array schema requires items.")
        check_schema(schema["items"])
    elif "items" in schema:
        raise ValueError("items requires array type.")
    for low, high, applicable in (("minimum", "maximum", {"number", "integer"}),
                                  ("minItems", "maxItems", {"array"}),
                                  ("minLength", "maxLength", {"string"})):
        for key in (low, high):
            if key not in schema:
                continue
            value = schema[key]
            if not set(types) & applicable or type(value) not in (int, float):
                raise ValueError(f"Invalid schema bound: {key}")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(f"Non-finite schema bound: {key}")
            if low != "minimum" and (type(value) is not int or value < 0):
                raise ValueError(f"Invalid schema length: {key}")
        if low in schema and high in schema and schema[low] > schema[high]:
            raise ValueError("Schema lower bound exceeds upper bound.")
    if "default" in schema:
        validate_schema(schema["default"], schema, "schema.default")


def validate_schema(value: Any, schema: Mapping[str, Any], field: str = "arguments") -> None:
    """Validate strict JSON against a checked schema; booleans are not numeric values."""
    value = json_value(value)
    types = schema["type"]
    types = [types] if isinstance(types, str) else types
    matches = {"object": isinstance(value, dict), "array": type(value) is list, "string": type(value) is str,
               "number": type(value) in (int, float), "integer": type(value) is int,
               "boolean": type(value) is bool, "null": value is None}
    if not any(matches[kind] for kind in types):
        raise ValueError(f"{field} does not match schema type {types}.")
    if "enum" in schema and json_dumps(value) not in {json_dumps(item) for item in schema["enum"]}:
        raise ValueError(f"{field} does not match schema enum.")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        object_fields(value, set(schema.get("required", [])), set(properties), field)
        for key, item in value.items():
            validate_schema(item, properties[key], f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_schema(item, schema["items"], f"{field}[{index}]")
    for key, actual, is_lower in (("minimum", value, True), ("maximum", value, False),
                                  ("minItems", len(value) if isinstance(value, list) else None, True),
                                  ("maxItems", len(value) if isinstance(value, list) else None, False),
                                  ("minLength", len(value) if isinstance(value, str) else None, True),
                                  ("maxLength", len(value) if isinstance(value, str) else None, False)):
        if key not in schema or actual is None:
            continue
        if key in ("minimum", "maximum") and type(value) not in (int, float):
            continue
        if (is_lower and actual < schema[key]) or (not is_lower and actual > schema[key]):
            raise ValueError(f"{field} violates schema {key}.")
