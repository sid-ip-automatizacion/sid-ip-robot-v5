"""Abstract base class for all executable tasks."""

from abc import ABC, abstractmethod

from ..plugins.base import BaseConnectionPlugin


class BaseTask(ABC):
    """Every task receives an open connection and the vendor name.

    Subclasses implement :meth:`execute`, which must return the task's
    result (typically a ``dict``).
    """

    @abstractmethod
    def execute(self, connection: BaseConnectionPlugin, vendor: str) -> dict:
        """Run the task on a single device and return a result dict."""
