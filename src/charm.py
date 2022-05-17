#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Grafana Mimir Charm.
"""

import logging
import socket
import yaml

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus

from charms.grafana_k8s.v0.grafana_source import GrafanaSourceProvider
from charms.prometheus_k8s.v0.prometheus_remote_write import PrometheusRemoteWriteProvider

MIMIR_PORT = 9009
MIMIR_PUSH_PATH = "/api/v1/push"
MIMIR_CONFIG_FILE = "/etc/mimir/config.yaml"
MIMIR_DIRS = {
    "bucket_store": "/tmp/mimir/tsdb-sync",
    "data": "/tmp/mimir/data/tsdb",
    "tsdb": "/tmp/mimir/tsdb",
    "compactor": "/tmp/mimir/compactor",
    "rules": "/tmp/mimir/rules",
    "data-alertmanager": "/tmp/mimir/data-alertmanager"
}
logger = logging.getLogger(__name__)


class MimirCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self._name = "mimir"

        self.remote_write_provider = PrometheusRemoteWriteProvider(
            self, endpoint_port=MIMIR_PORT, endpoint_path=MIMIR_PUSH_PATH
        )
        self.grafana_source_provider = GrafanaSourceProvider(
            self, source_type="prometheus", source_url=self._grafana_source_url()
        )

        self.framework.observe(self.on.mimir_pebble_ready, self._on_mimir_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_mimir_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
        """
        self._create_mimir_dirs()
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
                    "command": f"mimir -target=all,alertmanager --config.file {MIMIR_CONFIG_FILE}",
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

    def _create_mimir_dirs(self):
        container = self.unit.get_container(self._name)

        if not container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble ready")
            return

        for _, path in MIMIR_DIRS.items():
            if not container.exists(path):
                container.make_dir(path, make_parents=True)

    def _mimir_config(self) -> str:
        config = {
            "multitenancy_enabled": False,
            "blocks_storage": {
                "backend": "filesystem",
                "bucket_store": {
                        "sync_dir": MIMIR_DIRS["bucket_store"]
                },
                "filesystem": {
                        "dir": MIMIR_DIRS["data"]
                },
                "tsdb": {
                    "dir": MIMIR_DIRS["tsdb"]
                }
            },
            "compactor": {
                "data_dir": MIMIR_DIRS["compactor"],
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
            "ruler": {
                "alertmanager_url": f"http://localhost:{MIMIR_PORT}/alertmanager"
            },
            "ruler_storage": {
                "backend": "filesystem",
                "filesystem": {
                    "dir": MIMIR_DIRS["rules"]
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
            },
            "alertmanager_storage": {
                "backend": "filesystem",
                "filesystem": {
                    "dir": MIMIR_DIRS["data-alertmanager"]
                }
            }
        }

        return yaml.dump(config)

    def _grafana_source_url(self):
        return f"http://{socket.getfqdn()}:{MIMIR_PORT}/prometheus"


if __name__ == "__main__":
    main(MimirCharm)
