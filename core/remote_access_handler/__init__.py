"""network_inventory – parallel network device information collector.

Usage::

    from network_inventory import execute

    results = execute({
        "username": "admin",
        "password": "secret",
        "task": "basic_info",
        "devices": (
            ("10.0.0.1", "cisco"),
            ("10.0.0.2", "fortinet"),
            ("10.0.0.3", "juniper"),
        ),
    })
"""

from .orchestrator import execute 

__all__ = ["execute"]