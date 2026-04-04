"""Custom exceptions for the network_inventory package."""


class NetworkInventoryError(Exception):
    """Base exception for all network_inventory errors."""


class DeviceConnectionError(NetworkInventoryError):
    """Raised when an SSH connection to a device fails."""


class CommandExecutionError(NetworkInventoryError):
    """Raised when a command fails to execute on a device."""


class ParseError(NetworkInventoryError):
    """Raised when raw command output cannot be parsed."""


class TaskNotFoundError(NetworkInventoryError):
    """Raised when a requested task name is not registered."""


class UnsupportedVendorError(NetworkInventoryError):
    """Raised when the vendor has no registered parser or plugin."""
