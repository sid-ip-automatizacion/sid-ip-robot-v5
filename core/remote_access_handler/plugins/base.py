"""Abstract base class for device connection plugins."""

from abc import ABC, abstractmethod


class BaseConnectionPlugin(ABC):
    """Interface that every connection plugin must implement.

    A connection plugin encapsulates the transport layer (SSH, API, etc.)
    and exposes a uniform command-execution API to the upper layers.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish the connection to the device."""

    @abstractmethod
    def disconnect(self) -> None:
        """Tear down the connection gracefully."""

    @abstractmethod
    def send_command(self, command: str) -> str:
        """Execute a single show-level command and return its raw output."""

    def send_setup_commands(self, commands: list[str]) -> None:
        """Send context-changing commands (e.g. vdom entry).

        The default implementation simply sends each command via
        :meth:`send_command` and discards the output.  Subclasses may
        override this to use timing-based methods when prompt detection
        is unreliable after context changes.
        """
        for cmd in commands:
            self.send_command(cmd)
