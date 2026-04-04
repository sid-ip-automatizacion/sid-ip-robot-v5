"""Task sub-package.

Importing this module triggers registration of all built-in tasks so
that :class:`~network_inventory.tasks.registry.TaskRegistry` can find them.
"""

from . import basic_info  # noqa: F401 – registers the task

__all__ = ["basic_info"]
