"""Device connection management for u2cli."""

from __future__ import annotations

import json
import sys
from typing import Optional

import click
import uiautomator2 as u2


def connect_device(serial: Optional[str] = None) -> u2.Device:
    """Connect to a device.

    *serial* takes priority. If not given, falls back to the serial stored in
    the current Click context object (set by the top-level ``cli`` group).
    """
    if serial is None:
        ctx = click.get_current_context(silent=True)
        if ctx is not None and isinstance(ctx.obj, dict):
            serial = ctx.obj.get("serial")
    try:
        if serial:
            d = u2.connect(serial)
        else:
            d = u2.connect()
        return d
    except Exception as e:
        click.echo(json.dumps({"error": str(e), "type": type(e).__name__}, ensure_ascii=False), err=True)
        sys.exit(1)


def build_selector_repr(kwargs: dict) -> str:
    """Build a Python-style selector expression from kwargs."""
    parts = []
    for k, v in kwargs.items():
        if isinstance(v, str):
            parts.append(f"{k}={v!r}")
        else:
            parts.append(f"{k}={v!r}")
    return ", ".join(parts)


def output_result(
    result: object,
    u2_code: str,
    output_json: Optional[bool] = None,
    extra: Optional[dict] = None,
) -> None:
    """Output result in human-readable or JSON format, always including u2 code."""
    if output_json is None:
        ctx = click.get_current_context(silent=True)
        if ctx is not None and isinstance(ctx.obj, dict):
            output_json = ctx.obj.get("output_json", False)
        else:
            output_json = False

    data: dict = {"u2_code": u2_code}
    if extra:
        data.update(extra)
    if result is not None:
        data["result"] = result

    if output_json:
        click.echo(json.dumps(data, default=str, ensure_ascii=False))
    else:
        click.echo(f"u2_code: {u2_code}")
        if extra:
            for k, v in extra.items():
                click.echo(f"{k}: {v}")
        if result is not None:
            if isinstance(result, (dict, list)):
                click.echo(json.dumps(result, default=str, indent=2, ensure_ascii=False))
            else:
                click.echo(f"result: {result}")
