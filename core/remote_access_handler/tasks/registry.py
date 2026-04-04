"""Task registry with decorator-based registration."""

from ..exceptions import TaskNotFoundError

_TASK_REGISTRY: dict[str, type] = {}


def register_task(name: str):
    """Class decorator that registers a task under *name*.

    Usage::

        @register_task("basic_info")
        class BasicInfoTask(BaseTask):
            ...
    """

    def decorator(cls):
        _TASK_REGISTRY[name] = cls
        return cls

    return decorator


class TaskRegistry:
    """Read-only façade for looking up registered tasks."""

    @staticmethod
    def get(name: str):
        """Return the task class for *name*, or raise :exc:`TaskNotFoundError`."""
        cls = _TASK_REGISTRY.get(name)
        if cls is None:
            raise TaskNotFoundError(f"Task '{name}' is not registered.")
        return cls

    @staticmethod
    def exists(name: str) -> bool:
        return name in _TASK_REGISTRY

    @staticmethod
    def available() -> list[str]:
        """Return a sorted list of registered task names."""
        return sorted(_TASK_REGISTRY)
