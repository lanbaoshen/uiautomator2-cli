"""Device-level commands for u2cli.

Commands that operate on the device as a whole (not on individual elements):
screenshot, dump-hierarchy, press, swipe, info, shell, send-keys, etc.
"""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET

import click

from u2cli.device import connect_device, output_result


# ---------------------------------------------------------------------------
# UI hierarchy → compact text tree
# ---------------------------------------------------------------------------

_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def _bounds_area(bounds_str: str) -> int:
    m = _BOUNDS_RE.fullmatch(bounds_str)
    if not m:
        return 0
    x1, y1, x2, y2 = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return max(0, x2 - x1) * max(0, y2 - y1)


def _short_class(cls: str) -> str:
    """'android.widget.TextView' → 'TextView'"""
    return cls.rpartition(".")[2] if cls else cls


def _is_invisible(node: ET.Element) -> bool:
    if node.get("displayed") == "false":
        return True
    bounds = node.get("bounds", "")
    return bool(bounds) and _bounds_area(bounds) == 0


def _has_content(node: ET.Element) -> bool:
    return bool(
        node.get("text", "").strip()
        or node.get("content-desc", "").strip()
        or node.get("resource-id", "").strip()
    )


def _is_interactive(node: ET.Element) -> bool:
    return node.get("clickable") == "true" or node.get("scrollable") == "true"


def _render_node(node: ET.Element, lines: list[str], depth: int) -> None:
    """Recursively render *node* into *lines* as an indented text tree."""
    if _is_invisible(node):
        return

    children = list(node)

    # Collapse pure-container nodes with exactly one child
    if (
        node.tag != "hierarchy"
        and not _has_content(node)
        and not _is_interactive(node)
        and len(children) == 1
    ):
        _render_node(children[0], lines, depth)
        return

    # Build the line for this node
    parts: list[str] = []

    cls = node.get("class", node.tag)
    if cls and cls != "hierarchy":
        parts.append(_short_class(cls))

    text = node.get("text", "").strip()
    if text:
        parts.append(f'"{text}"')

    desc = node.get("content-desc", "").strip()
    if desc and desc != text:
        parts.append(f'desc="{desc}"')

    rid = node.get("resource-id", "").strip()
    if rid:
        parts.append(f"#{rid}")

    bounds = node.get("bounds", "")
    if bounds:
        m = _BOUNDS_RE.fullmatch(bounds)
        if m:
            parts.append(f"[{m.group(1)},{m.group(2)},{m.group(3)},{m.group(4)}]")

    flags = []
    if node.get("clickable") == "true":
        flags.append("click")
    if node.get("scrollable") == "true":
        flags.append("scroll")
    if node.get("checked") == "true":
        flags.append("checked")
    if node.get("focused") == "true":
        flags.append("focused")
    if node.get("selected") == "true":
        flags.append("selected")
    if node.get("enabled") == "false":
        flags.append("disabled")
    if flags:
        parts.append(" ".join(flags))

    # Only emit a line if there's something to say (skip bare hierarchy root)
    if parts:
        lines.append("  " * depth + " ".join(parts))
        child_depth = depth + 1
    else:
        child_depth = depth

    for child in children:
        _render_node(child, lines, child_depth)


def _hierarchy_to_text(xml_str: str) -> str:
    """Convert a uiautomator2 XML hierarchy to a compact indented text tree."""
    root = ET.fromstring(xml_str)
    lines: list[str] = []
    _render_node(root, lines, 0)
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Device info & screen
# ---------------------------------------------------------------------------


@click.command("device-info")
def cmd_device_info():
    """Show device information (model, SDK version, screen size, etc.)."""
    u2_code = "d.device_info"
    d = connect_device()
    info = d.device_info
    output_result(info, u2_code)


@click.command("ui-info")
def cmd_ui_info():
    """Show UiAutomator device info (screen size, orientation, current package)."""
    u2_code = "d.info"
    d = connect_device()
    info = d.info
    output_result(info, u2_code)


@click.command("screenshot")
@click.argument("filename", default="screenshot.png")
def cmd_screenshot(filename):
    """Take a screenshot and save to FILENAME (default: screenshot.png)."""
    u2_code = f"d.screenshot({filename!r})"
    d = connect_device()
    d.screenshot(filename)
    abs_path = os.path.abspath(filename)
    output_result(None, u2_code, extra={"saved_to": abs_path})


@click.command("dump-hierarchy")
@click.option("--compressed", is_flag=True, default=False, help="Use compressed hierarchy")
@click.option("--max-depth", default=None, type=int, help="Maximum hierarchy depth")
@click.option("--output", "-o", default=None, help="Save output to file instead of stdout")
@click.option("--raw", is_flag=True, default=False, help="Output raw XML without simplification")
def cmd_dump_hierarchy(compressed, max_depth, output, raw):
    """Dump the UI hierarchy as a compact indented text tree.

    Invisible nodes, pure-container nodes, and noise attributes are removed.
    Pass --raw to get the original XML from uiautomator2.
    """
    kwargs_parts = []
    if compressed:
        kwargs_parts.append("compressed=True")
    if max_depth is not None:
        kwargs_parts.append(f"max_depth={max_depth}")
    u2_code = f"d.dump_hierarchy({', '.join(kwargs_parts)})"

    d = connect_device()
    kw: dict = {}
    if compressed:
        kw["compressed"] = True
    if max_depth is not None:
        kw["max_depth"] = max_depth
    xml = d.dump_hierarchy(**kw)

    result = xml if raw else _hierarchy_to_text(xml)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        output_result(None, u2_code, extra={"saved_to": os.path.abspath(output)})
    else:
        output_result(result, u2_code)


@click.command("window-size")
def cmd_window_size():
    """Get the screen window size (width, height)."""
    u2_code = "d.window_size()"
    d = connect_device()
    w, h = d.window_size()
    output_result({"width": w, "height": h}, u2_code)


# ---------------------------------------------------------------------------
# Screen on/off & orientation
# ---------------------------------------------------------------------------


@click.command("screen-on")
def cmd_screen_on():
    """Turn the screen on (wake device)."""
    u2_code = "d.screen_on()"
    d = connect_device()
    d.screen_on()
    output_result(None, u2_code)


@click.command("screen-off")
def cmd_screen_off():
    """Turn the screen off (sleep device)."""
    u2_code = "d.screen_off()"
    d = connect_device()
    d.screen_off()
    output_result(None, u2_code)


@click.command("orientation")
@click.option(
    "--set",
    "set_orientation",
    default=None,
    type=click.Choice(["natural", "left", "right", "upsidedown"]),
    help="Set screen orientation",
)
def cmd_orientation(set_orientation):
    """Get or set screen orientation."""
    d = connect_device()
    if set_orientation:
        u2_code = f"d.orientation = {set_orientation!r}"
        d.orientation = set_orientation
        output_result(None, u2_code)
    else:
        u2_code = "d.orientation"
        orientation = d.orientation
        output_result(orientation, u2_code)


# ---------------------------------------------------------------------------
# Input: press key, swipe, click, send-keys
# ---------------------------------------------------------------------------


@click.command("press")
@click.argument("key", metavar="KEY")
def cmd_press(key):
    """Press a hardware/soft key by name or keycode integer.

    Named keys: home, back, menu, enter, delete, recent, volume_up,
    volume_down, power, camera, search, space
    """
    key_val: int | str
    try:
        key_val = int(key)
        u2_code = f"d.press({key_val})"
    except ValueError:
        key_val = key
        u2_code = f"d.press({key_val!r})"

    d = connect_device()
    d.press(key_val)
    output_result(None, u2_code)


@click.command("swipe")
@click.option("--duration", default=0.5, type=float, help="Swipe duration in seconds")
@click.option("--steps", default=None, type=int, help="Number of steps (overrides duration)")
@click.argument("fx", type=float)
@click.argument("fy", type=float)
@click.argument("tx", type=float)
@click.argument("ty", type=float)
def cmd_swipe(duration, steps, fx, fy, tx, ty):
    """Swipe from (FX, FY) to (TX, TY). Coords can be 0-1 (relative) or pixels."""
    if steps is not None:
        u2_code = f"d.swipe({fx}, {fy}, {tx}, {ty}, steps={steps})"
    else:
        u2_code = f"d.swipe({fx}, {fy}, {tx}, {ty}, duration={duration})"

    d = connect_device()
    if steps is not None:
        d.swipe(fx, fy, tx, ty, steps=steps)
    else:
        d.swipe(fx, fy, tx, ty, duration=duration)
    output_result(None, u2_code)


@click.command("swipe-ext")
@click.option("--scale", default=0.8, type=float, help="Swipe distance as fraction of screen")
@click.argument(
    "direction",
    type=click.Choice(["left", "right", "up", "down"]),
)
def cmd_swipe_ext(scale, direction):
    """High-level directional swipe across the screen."""
    u2_code = f"d.swipe_ext({direction!r}, scale={scale})"
    d = connect_device()
    d.swipe_ext(direction, scale=scale)
    output_result(None, u2_code)


@click.command("click-coord")
@click.argument("x", type=float)
@click.argument("y", type=float)
def cmd_click_coord(x, y):
    """Click at absolute or relative (0-1) coordinates."""
    u2_code = f"d.click({x}, {y})"
    d = connect_device()
    d.click(x, y)
    output_result(None, u2_code)


@click.command("double-click")
@click.option("--duration", default=0.1, type=float, help="Delay between taps")
@click.argument("x", type=float)
@click.argument("y", type=float)
def cmd_double_click(duration, x, y):
    """Double-click at coordinates."""
    u2_code = f"d.double_click({x}, {y}, duration={duration})"
    d = connect_device()
    d.double_click(x, y, duration=duration)
    output_result(None, u2_code)


@click.command("long-click-coord")
@click.option("--duration", default=0.5, type=float, help="Long press duration in seconds")
@click.argument("x", type=float)
@click.argument("y", type=float)
def cmd_long_click_coord(duration, x, y):
    """Long-click at coordinates."""
    u2_code = f"d.long_click({x}, {y}, duration={duration})"
    d = connect_device()
    d.long_click(x, y, duration=duration)
    output_result(None, u2_code)


@click.command("send-keys")
@click.option("--no-clear", is_flag=True, default=False, help="Don't clear before typing")
@click.argument("text")
def cmd_send_keys(no_clear, text):
    """Type text into the currently focused input field."""
    clear = not no_clear
    u2_code = f"d.send_keys({text!r}, clear={clear})"
    d = connect_device()
    d.send_keys(text, clear=clear)
    output_result(None, u2_code)


# ---------------------------------------------------------------------------
# Notifications & system UI
# ---------------------------------------------------------------------------


@click.command("open-notification")
def cmd_open_notification():
    """Pull down the notification shade."""
    u2_code = "d.open_notification()"
    d = connect_device()
    d.open_notification()
    output_result(None, u2_code)


@click.command("open-quick-settings")
def cmd_open_quick_settings():
    """Pull down the quick settings panel."""
    u2_code = "d.open_quick_settings()"
    d = connect_device()
    d.open_quick_settings()
    output_result(None, u2_code)


@click.command("open-url")
@click.argument("url")
def cmd_open_url(url):
    """Open a URL in the default browser via intent."""
    u2_code = f"d.open_url({url!r})"
    d = connect_device()
    d.open_url(url)
    output_result(None, u2_code)


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------


@click.command("shell")
@click.option("--timeout", default=60, type=int, help="Command timeout in seconds")
@click.argument("cmd", nargs=-1, required=True)
def cmd_shell(timeout, cmd):
    """Run a shell command on the device.

    Example: u2cli shell ls /sdcard
    """
    cmd_str = " ".join(cmd)
    u2_code = f"d.shell({cmd_str!r}, timeout={timeout})"
    d = connect_device()
    resp = d.shell(cmd_str, timeout=timeout)
    output_result(
        {"output": resp.output, "exit_code": resp.exit_code},
        u2_code,
    )


# ---------------------------------------------------------------------------
# Current app
# ---------------------------------------------------------------------------


@click.command("current-app")
def cmd_current_app():
    """Show the currently running foreground app (package + activity)."""
    u2_code = "d.app_current()"
    d = connect_device()
    info = d.app_current()
    output_result(info, u2_code)
