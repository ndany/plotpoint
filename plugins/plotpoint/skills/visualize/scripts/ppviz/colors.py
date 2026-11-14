"""Resolve entity colors from the intent's highlight and the caller's color map.

Rules (references/spec.md):
- color_map wins: accent | context | slot1..slot8 | #rrggbb.
- With a highlight: highlighted entities get the accent, all others context gray.
- Without a highlight: entities get palette slots in order of appearance,
  skipping slots the color map already uses. Never cycled: a 9th unmapped
  entity is an error the caller resolves (fold into Other, or facet).
"""

from __future__ import annotations

from typing import Any

from . import config


class ColorError(ValueError):
    pass


def _named(value: str, theme: dict[str, Any]) -> str:
    if value == "accent":
        return theme["accent"]
    if value == "context":
        return theme["context"]
    if value.startswith("slot"):
        return theme["palette"][int(value[4:]) - 1]
    return value


def resolve(
    entities: list[str], highlight: list[Any] | None, color_map: dict[str, str] | None
) -> dict[str, str]:
    theme = config.theme()
    color_map = color_map or {}
    highlight_set = {str(h) for h in (highlight or [])}
    out: dict[str, str] = {}
    used = {_named(v, theme) for v in color_map.values()}
    free = [c for c in theme["palette"] if c not in used]
    for ent in entities:
        key = str(ent)
        if key in color_map:
            out[key] = _named(color_map[key], theme)
        elif highlight_set:
            out[key] = theme["accent"] if key in highlight_set else theme["context"]
        else:
            if not free:
                raise ColorError(
                    f"more than {len(theme['palette'])} colored entities; fold the "
                    "tail into 'Other', facet, or highlight the ones that matter"
                )
            out[key] = free.pop(0)
    return out
