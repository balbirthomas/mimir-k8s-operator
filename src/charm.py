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

from mimir.config import (
    MIMIR_DIRS,
    MIMIR_PORT,
    MIMIR_PUSH_PATH,
    MIMIR_CONFIG_FILE,
    block_storage_config,
    compactor_config,
    distributor_config,
    ingester_config,
    ruler_config,
    ruler_storage_config,
    server_config,
    store_gateway_config,
    alertmanager_storage_config
)
from mimir.alertmanager import (
    AlertManager,
    DEFAULT_ALERT_TEMPLATE,
    DEFAULT_ALERTMANAGER_CONFIG
)

logger = logging.getLogger(__name__)


class MimirCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self._name = "mimir"
        self._alertmanager = AlertManager()

        self.remote_write_provider = PrometheusRemoteWriteProvider(
            self, endpoint_port=MIMIR_PORT, endpoint_path=MIMIR_PUSH_PATH
        )
        self.grafana_source_provider = GrafanaSourceProvider(
            self, source_type="prometheus", source_url=self._grafana_source_url()
        )

        self.framework.observe(self.on.mimir_pebble_ready, self._on_mimir_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.receive_remote_write_relation_changed, self._on_remote_write_relation_changed)

    def _on_mimir_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
        """
        self._create_mimir_dirs()
        # Set the mimir configuration
        self._set_mimir_config()
        self._set_alertmanager_config()

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
        self._set_alertmanager_config()

    def _on_remote_write_relation_changed(self, _):
        container = self.unit.get_container(self._name)

        if not container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble ready")
            return

        alerts_for_all_relations = self.remote_write_provider.alerts()
        for _, alerts in alerts_for_all_relations.items():
            self._set_alert_rules(alerts["groups"])

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
            "blocks_storage": block_storage_config(),
            "compactor": compactor_config(),
            "distributor": distributor_config(),
            "ingester": ingester_config(),
            "ruler": ruler_config(),
            "ruler_storage": ruler_storage_config(),
            "server": server_config(),
            "store_gateway": store_gateway_config(),
            "alertmanager_storage": alertmanager_storage_config()
        }

        return yaml.dump(config)

    def _grafana_source_url(self):
        return f"http://{socket.getfqdn()}:{MIMIR_PORT}/prometheus"

    def _set_alertmanager_config(self):
        container = self.unit.get_container(self._name)

        if not container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble ready")
            return

        aconfig = {
            "template_files": {
                "default_template": self.config["alertmanager_template"] or DEFAULT_ALERT_TEMPLATE,
            },
            "alertmanager_config": self.config["alertmanager_config"] or yaml.dump(DEFAULT_ALERTMANAGER_CONFIG)
        }
        self._alertmanager.set_config(aconfig)

    def _set_alert_rules(self, groups):
        for group in groups:
            alert_uploaded = self._alertmanager.set_alert_rule_group(group)
            if not alert_uploaded:
                logger.error("Failed to set alert group %s", group)


if __name__ == "__main__":
    main(MimirCharm)
