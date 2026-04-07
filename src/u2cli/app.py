"""App management commands for u2cli.

Commands for installing, launching, stopping, and managing Android apps.
"""

from __future__ import annotations

import click

from u2cli.device import connect_device, output_result


@click.command("app-start")
@click.option("--activity", default=None, help="Specific activity to launch")
@click.option("--wait", is_flag=True, default=False, help="Wait for app to launch")
@click.option("--stop", is_flag=True, default=False, help="Stop app before launching")
@click.argument("package")
def cmd_app_start(activity, wait, stop, package):
    """Start (launch) an Android app by package name."""
    parts = [repr(package)]
    if activity:
        parts.append(f"activity={activity!r}")
    if wait:
        parts.append("wait=True")
    if stop:
        parts.append("stop=True")
    u2_code = f"d.app_start({', '.join(parts)})"

    d = connect_device()
    kw: dict = {}
    if activity:
        kw["activity"] = activity
    if wait:
        kw["wait"] = True
    if stop:
        kw["stop"] = True
    d.app_start(package, **kw)
    output_result(None, u2_code)


@click.command("app-stop")
@click.option("--all", "stop_all", is_flag=True, default=False, help="Stop all third-party apps")
@click.argument("package", required=False)
def cmd_app_stop(stop_all, package):
    """Force-stop an app (or all third-party apps with --all)."""
    d = connect_device()
    if stop_all:
        u2_code = "d.app_stop_all()"
        d.app_stop_all()
        output_result(None, u2_code)
    elif package:
        u2_code = f"d.app_stop({package!r})"
        d.app_stop(package)
        output_result(None, u2_code)
    else:
        raise click.UsageError("Provide PACKAGE or use --all.")


@click.command("app-clear")
@click.argument("package")
def cmd_app_clear(package):
    """Clear app data (pm clear <package>)."""
    u2_code = f"d.app_clear({package!r})"
    d = connect_device()
    d.app_clear(package)
    output_result(None, u2_code)


@click.command("app-install")
@click.argument("apk")
def cmd_app_install(apk):
    """Install an APK from a local path or URL."""
    u2_code = f"d.app_install({apk!r})"
    d = connect_device()
    d.app_install(apk)
    output_result(None, u2_code)


@click.command("app-uninstall")
@click.argument("package")
def cmd_app_uninstall(package):
    """Uninstall an app by package name."""
    u2_code = f"d.app_uninstall({package!r})"
    d = connect_device()
    result = d.app_uninstall(package)
    output_result(result, u2_code)


@click.command("app-info")
@click.argument("package")
def cmd_app_info(package):
    """Get app version info (versionName, versionCode)."""
    u2_code = f"d.app_info({package!r})"
    d = connect_device()
    info = d.app_info(package)
    output_result(info, u2_code)


@click.command("app-list")
@click.option(
    "--filter",
    "pkg_filter",
    default="",
    help="Filter string (passed to pm list packages)",
)
def cmd_app_list(pkg_filter):
    """List installed packages."""
    if pkg_filter:
        u2_code = f"d.app_list({pkg_filter!r})"
    else:
        u2_code = "d.app_list()"
    d = connect_device()
    packages = d.app_list(pkg_filter)
    output_result(packages, u2_code)


@click.command("app-list-running")
def cmd_app_list_running():
    """List currently running packages."""
    u2_code = "d.app_list_running()"
    d = connect_device()
    packages = d.app_list_running()
    output_result(packages, u2_code)


@click.command("app-wait")
@click.option("--timeout", default=20.0, type=float, help="Timeout in seconds")
@click.option("--front", is_flag=True, default=False, help="Wait until app is in foreground")
@click.argument("package")
def cmd_app_wait(timeout, front, package):
    """Wait until an app is running (or in the foreground with --front)."""
    parts = [repr(package), f"timeout={timeout}"]
    if front:
        parts.append("front=True")
    u2_code = f"d.app_wait({', '.join(parts)})"

    d = connect_device()
    pid = d.app_wait(package, timeout=timeout, front=front)
    output_result(pid, u2_code)
