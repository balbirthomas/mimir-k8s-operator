#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Grafana Mimir Charm.
"""

import logging
import yaml

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus

MIMIR_PORT = 9009
MIMIR_CONFIG_FILE = "/etc/mimir/config.yaml"
logger = logging.getLogger(__name__)


class MimirCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self._name = "mimir"
        self.framework.observe(self.on.mimir_pebble_ready, self._on_mimir_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_mimir_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
        """
        # Set the mimir configuration
        self._set_mimir_config()

        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "mimir layer",
            "description": "pebble config layer for mimir",
            "services": {
                self._name: {
                    "override": "replace",
                    "summary": self._name,
                    "command": f"mimir -target=all --config.file {MIMIR_CONFIG_FILE}",
                    "startup": "enabled",
                }
            },
        }
        # Add initial Pebble config layer using the Pebble API
        container.add_layer(self._name, pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        """Handle Mimir configuration chagne.
        """
        self._set_mimir_config()

    def _set_mimir_config(self):
        container = self.unit.get_container(self._name)

        if not container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble ready")
            return

        # push mimr config file to workload
        mimir_config = self._mimir_config()
        container.push(MIMIR_CONFIG_FILE, mimir_config, make_dirs=True)
        logger.info("Set new Mimir configuration")

    def _mimir_config(self) -> str:
        config = {
            "multitenancy_enabled": False,
            "blocks_storage": {
                "backend": "filesystem",
                "bucket_store": {
                        "sync_dir": "/tmp/mimir/tsdb-sync"
                },
                "filesystem": {
                        "dir": "/tmp/mimir/data/tsdb"
                },
                "tsdb": {
                    "dir": "/tmp/mimir/tsdb"
                }
            },
            "compactor": {
                "data_dir": "/tmp/mimir/compactor",
                "sharding_ring": {
                    "kvstore": {
                        "store": "memberlist"
                    }
                }
            },
            "distributor": {
                "ring": {
                    "instance_addr": "127.0.0.1",
                    "kvstore": {
                        "store": "memberlist"
                    }
                }
            },
            "ingester": {
                "ring": {
                    "instance_addr": "127.0.0.1",
                    "kvstore": {
                        "store": "memberlist",
                    },
                    "replication_factor": 1
                }
            },
            "ruler_storage": {
                "backend": "local",
                "local": {
                    "directory": "/tmp/mimir/rules"
                }
            },
            "server": {
                "http_listen_port": MIMIR_PORT,
                "log_level": "error"
            },
            "store_gateway": {
                "sharding_ring": {
                    "replication_factor": 1
                }
            }
        }

        return yaml.dump(config)


if __name__ == "__main__":
    main(MimirCharm)
