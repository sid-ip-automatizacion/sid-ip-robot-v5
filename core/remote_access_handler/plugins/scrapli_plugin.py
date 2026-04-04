"""Scrapli-based connection plugin for Cisco devices."""

from scrapli.driver.core import IOSXEDriver

from .base import BaseConnectionPlugin
from ..exceptions import DeviceConnectionError, CommandExecutionError


class ScrapliPlugin(BaseConnectionPlugin):
    """SSH connection via Scrapli IOSXEDriver (ssh2 transport).

    Parameters
    ----------
    hostname : str
        IP address or FQDN of the target device.
    username, password : str
        Login credentials.
    """

    def __init__(self, hostname: str, username: str, password: str) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password
        self._driver = None

    def connect(self) -> None:
        try:
            self._driver = IOSXEDriver(
                host=self.hostname,
                auth_username=self.username,
                auth_password=self.password,
                auth_strict_key=False,
                transport="ssh2",
            )
            self._driver.open()
        except Exception as exc:
            raise DeviceConnectionError(
                f"Scrapli connection to {self.hostname} failed: {exc}"
            ) from exc

    def disconnect(self) -> None:
        if self._driver:
            self._driver.close()

    def send_command(self, command: str) -> str:
        try:
            response = self._driver.send_command(command)
            return response.result
        except Exception as exc:
            raise CommandExecutionError(
                f"Command '{command}' failed on {self.hostname}: {exc}"
            ) from exc
