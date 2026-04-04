"""Nornir-based orchestration layer.

This module is the single entry point that the graphical (or any other)
layer calls.  It converts the user-facing input dictionary into a Nornir
inventory, runs the requested task in parallel across all devices, and
returns a plain list of result dictionaries.
"""

from __future__ import annotations

import logging
from typing import Any

from nornir import InitNornir
from nornir.core.inventory import (
    ConnectionOptions,
    Defaults,
    Groups,
    Host,
    Hosts,
    Inventory,
)
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task

from .exceptions import TaskNotFoundError
from .plugins import get_connection_plugin
from .tasks.registry import TaskRegistry

# Ensure built-in tasks are registered on first import.
from . import tasks as _tasks  # noqa: F401

logger = logging.getLogger(__name__)


# ── Custom Nornir inventory plugin ───────────────────────────────────────

class _DictInventoryPlugin:
    """Lightweight Nornir inventory plugin that builds hosts from a dict."""

    def __init__(self, hosts_data: dict[str, dict], **kwargs: Any) -> None:
        self.hosts_data = hosts_data

    def load(self) -> Inventory:
        hosts = Hosts()
        for name, data in self.hosts_data.items():
            hosts[name] = Host(
                name=name,
                hostname=data["hostname"],
                username=data["username"],
                password=data["password"],
                data=data.get("data", {}),
                connection_options=data.get("connection_options", {}),
            )
        return Inventory(hosts=hosts, groups=Groups(), defaults=Defaults())


# Register once at module level.
InventoryPluginRegister.register(
    "_DictInventoryPlugin", _DictInventoryPlugin
)


# ── Nornir task wrapper ─────────────────────────────────────────────────

def _nornir_task(task: Task, *, task_name: str) -> Result:
    """Nornir-compatible wrapper that bridges to our task/plugin layers."""
    vendor: str = task.host.data["vendor"]

    connection = get_connection_plugin(
        vendor=vendor,
        hostname=task.host.hostname,
        username=task.host.username,
        password=task.host.password,
    )

    try:
        connection.connect()
        task_instance = TaskRegistry.get(task_name)()
        result_data = task_instance.execute(connection, vendor)
        return Result(host=task.host, result=result_data)
    except Exception as exc:
        logger.exception("Task '%s' failed on %s", task_name, task.host.name)
        return Result(host=task.host, result=None, failed=True, exception=exc)
    finally:
        connection.disconnect()


# ── Public API ───────────────────────────────────────────────────────────

def execute(input_data: dict) -> list[dict]:
    """Run a task against one or more devices and return a list of results.

    Parameters
    ----------
    input_data : dict
        Expected keys:

        * ``username`` – SSH login user.
        * ``password`` – SSH login password.
        * ``task`` – registered task name (e.g. ``"basic_info"``).
        * ``devices`` – iterable of ``(ip, vendor)`` pairs.

    Returns
    -------
    list[dict]
        One result dictionary per device.  Failed devices include
        ``"failed": True`` and an ``"error"`` message.
    """
    username: str = input_data["username"]
    password: str = input_data["password"]
    task_name: str = input_data["task"]
    devices = input_data["devices"]

    if not TaskRegistry.exists(task_name):
        raise TaskNotFoundError(f"Task '{task_name}' is not registered.")

    # Build Nornir inventory from the flat device list.
    hosts_data: dict[str, dict] = {}
    for ip, vendor in devices:
        hosts_data[ip] = {
            "hostname": ip,
            "username": username,
            "password": password,
            "data": {"vendor": vendor.lower()},
        }

    nr = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {"num_workers": max(len(hosts_data), 1)},
        },
        inventory={
            "plugin": "_DictInventoryPlugin",
            "options": {"hosts_data": hosts_data},
        },
    )

    aggregated = nr.run(task=_nornir_task, task_name=task_name)

    results: list[dict] = []
    for host_name, multi_result in aggregated.items():
        host_result = multi_result[0]
        if host_result.failed:
            results.append(
                {
                    "host": host_name,
                    "failed": True,
                    "error": str(host_result.exception),
                }
            )
        else:
            results.append(host_result.result)

    return results
