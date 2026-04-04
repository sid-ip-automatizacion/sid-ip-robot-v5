"""Netmiko-based connection plugin for Fortinet and Juniper devices."""

from netmiko import ConnectHandler

from .base import BaseConnectionPlugin
from ..exceptions import DeviceConnectionError, CommandExecutionError


class NetmikoPlugin(BaseConnectionPlugin):
    """SSH connection via Netmiko.

    Parameters
    ----------
    hostname : str
        IP address or FQDN of the target device.
    username, password : str
        Login credentials.
    device_type : str
        Netmiko device type, e.g. ``"fortinet"`` or ``"juniper_junos"``.
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        device_type: str,
    ) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password
        self.device_type = device_type
        self._connection = None

    def connect(self) -> None:
        try:
            self._connection = ConnectHandler(
                device_type=self.device_type,
                host=self.hostname,
                username=self.username,
                password=self.password,
            )
        except Exception as exc:
            raise DeviceConnectionError(
                f"Netmiko connection to {self.hostname} failed: {exc}"
            ) from exc

    def disconnect(self) -> None:
        if self._connection:
            self._connection.disconnect()

    def send_command(self, command: str) -> str:
        try:
            return self._connection.send_command(command)
        except Exception as exc:
            raise CommandExecutionError(
                f"Command '{command}' failed on {self.hostname}: {exc}"
            ) from exc

    def send_setup_commands(self, commands: list[str]) -> None:
        """Use timing-based sending for context-changing commands.

        Fortinet vdom entry (``config vdom`` / ``edit root``) changes
        the prompt in a way that pattern-based ``send_command`` cannot
        reliably detect, so ``send_command_timing`` is used instead.
        """
        for cmd in commands:
            try:
                self._connection.send_command_timing(cmd)
            except Exception as exc:
                raise CommandExecutionError(
                    f"Setup command '{cmd}' failed on {self.hostname}: {exc}"
                ) from exc
