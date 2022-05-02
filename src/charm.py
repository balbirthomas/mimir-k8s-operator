#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Grafana Mimir Charm.
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class MimirCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.mimir_pebble_ready, self._on_mimir_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_mimir_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
        """
        # Get the mimir config
        config_file = self._mimir_config()

        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "mimir layer",
            "description": "pebble config layer for mimir",
            "services": {
                "mimir": {
                    "override": "replace",
                    "summary": "mimir",
                    "command": f"mimir -target=all --config.file {config_file}",
                    "startup": "enabled",
                }
            },
        }
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("mimir", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        """Handle Mimir configuration chagne.
        """

    def _mimir_config(self):
        return "/etc/mimir/config.yaml"


if __name__ == "__main__":
    main(MimirCharm)
