# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import patch

import yaml
from helpers import patch_network_get
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.testing import Harness

from charm import MimirCharm
from mimir.config import MIMIR_CONFIG_FILE

S3_CONFIG = {
    "endpoint": "s3.eu-west-1.amazonaws.com",
    "insecure": True,
    "bucket_name": "mimir_bucket",
    "secret_access_key": "mimir_s3_access_key",
    "access_key_id": "mimir_s3_access_id",
}
CPU_OVER_USE_RULE_FILE = "tests/unit/alert_rules/cpu_overuse.json"


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(MimirCharm)
        self.harness.set_model_name("charm_test")
        self.name = "mimir"
        self.peername = "mimir-peers"
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_peer_units_set_hostname_on_peer_relation_joined(self):
        # create a peer relation and unit after pebble is ready
        self.harness.container_pebble_ready(self.name)
        peer_rel_id = self.harness.add_relation(self.peername, self.name)
        unit_name = "mimir-k8s/0"
        self.harness.add_relation_unit(peer_rel_id, unit_name)

        # check peer unit has set its hostname
        data = self.harness.get_relation_data(peer_rel_id, unit_name)
        self.assertIn("peer_hostname", data)
        self.assertTrue(data["peer_hostname"])

    def test_mimir_config_is_set_on_pebble_ready(self):
        self.harness.container_pebble_ready(self.name)
        plan = self.harness.get_container_pebble_plan(self.name)
        self.assertIn(self.name, plan.services)

    def test_charm_reconfigures_mimir_on_peer_relation_chagned(self):
        # create a peer relation and unit after pebble is ready
        self.harness.container_pebble_ready(self.name)
        peer_rel_id = self.harness.add_relation(self.peername, self.name)
        first_unit_name = "mimir-k8s/0"
        self.harness.add_relation_unit(peer_rel_id, first_unit_name)

        # check initial Mimir memberlist contains a single node
        container = self.harness.charm.unit.get_container(self.name)
        config = yaml.safe_load(container.pull(MIMIR_CONFIG_FILE))
        members = config["memberlist"]["join_members"]
        self.assertEqual(len(members), 1)

        # add a second Mimir node
        second_unit_name = "mimir-k8s/1"
        self.harness.add_relation_unit(peer_rel_id, second_unit_name)
        self.harness.update_relation_data(
            peer_rel_id, second_unit_name, {"peer_hostname": second_unit_name}
        )

        # check Mimir memberlist now contains two nodes
        container = self.harness.charm.unit.get_container(self.name)
        config = yaml.safe_load(container.pull(MIMIR_CONFIG_FILE))
        members = config["memberlist"]["join_members"]
        self.assertEqual(len(members), 2)
        self.assertIn(second_unit_name, members)

    def test_charm_reconfigures_mimir_on_peer_relation_departed(self):
        # create a peer relation and a unit
        self.harness.container_pebble_ready(self.name)
        peer_rel_id = self.harness.add_relation(self.peername, self.name)
        first_unit_name = "mimir-k8s/0"
        self.harness.add_relation_unit(peer_rel_id, first_unit_name)

        # add a second Mimir node
        second_unit_name = "mimir-k8s/1"
        self.harness.add_relation_unit(peer_rel_id, second_unit_name)
        self.harness.update_relation_data(
            peer_rel_id, second_unit_name, {"peer_hostname": second_unit_name}
        )

        # check Mimir memberlist now contains two nodes
        container = self.harness.charm.unit.get_container(self.name)
        config = yaml.safe_load(container.pull(MIMIR_CONFIG_FILE))
        members = config["memberlist"]["join_members"]
        self.assertEqual(len(members), 2)
        self.assertIn(second_unit_name, members)

        # remove the second unit
        self.harness.remove_relation_unit(peer_rel_id, second_unit_name)

        # check Mimir memberlist has been updated to contain a single unit
        container = self.harness.charm.unit.get_container(self.name)
        config = yaml.safe_load(container.pull(MIMIR_CONFIG_FILE))
        members = config["memberlist"]["join_members"]
        self.assertEqual(len(members), 1)
        self.assertNotIn(second_unit_name, members)

    def test_charm_blocks_on_replication_without_object_storage(self):
        # a single peer unit is active regardless of object storage availability
        self.harness.container_pebble_ready(self.name)
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

        # adding additional peer units blocks if object storage is not available
        peer_rel_id = self.harness.add_relation(self.peername, self.name)
        self.harness.add_relation_unit(peer_rel_id, "mimir-k8s/1")
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

        # providing s3 configuration unblocks the replicated charm
        self.harness.update_config({"s3": yaml.dump(S3_CONFIG)})
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

    def test_replication_prior_to_pebble_ready_eventually_works(self):
        # check charm is not active yet
        self.assertIsInstance(self.harness.charm.unit.status, MaintenanceStatus)

        # provide an s3 config and add a peer
        self.harness.update_config({"s3": yaml.dump(S3_CONFIG)})
        peer_rel_id = self.harness.add_relation(self.peername, self.name)
        self.harness.add_relation_unit(peer_rel_id, "mimir-k8s/1")
        self.assertIsInstance(self.harness.charm.unit.status, WaitingStatus)

        # check charm is active when pebble becomes ready
        self.harness.container_pebble_ready(self.name)
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

    @patch_network_get(private_address="10.1.1.2")
    def test_charm_sets_alert_rules_if_pebble_is_ready(self):
        # ensure pebble is ready
        self.harness.container_pebble_ready(self.name)
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

        # add remote write relation and set alert rules
        remote_write_rel_id = self.harness.add_relation(
            "receive-remote-write", "grafana-agent"
        )
        self.harness.add_relation_unit(remote_write_rel_id, "grafana-agent/0")
        with open(CPU_OVER_USE_RULE_FILE) as rule_file:
            with patch.object(
                self.harness.charm._alertmanager, "set_alert_rule_group"
            ) as mock_set_rules:

                # check Mimir charm does not set alert rules when there is no relation data
                self.assertFalse(mock_set_rules.called)
                self.harness.update_relation_data(
                    remote_write_rel_id,
                    "grafana-agent",
                    {
                        "alert_rules": rule_file.read(),
                    },
                )
                # check Mimir charm sets alert rules after relation data is set
                self.assertTrue(mock_set_rules.called)

    @patch_network_get(private_address="10.1.1.2")
    def test_remote_write_relation_is_eventually_handled(self):
        # check charm is not active yet
        self.assertIsInstance(self.harness.charm.unit.status, MaintenanceStatus)

        # add remote write relation and set alert rules
        remote_write_rel_id = self.harness.add_relation(
            "receive-remote-write", "grafana-agent"
        )
        self.harness.add_relation_unit(remote_write_rel_id, "grafana-agent/0")
        with open(CPU_OVER_USE_RULE_FILE) as rule_file:
            self.harness.update_relation_data(
                remote_write_rel_id, "grafana-agent", {"alert_rules": rule_file.read()}
            )
            with patch.object(
                self.harness.charm._alertmanager, "set_alert_rule_group"
            ) as mock_set_rules:

                self.harness.update_relation_data(
                    remote_write_rel_id,
                    "grafana-agent",
                    {
                        "alert_rules": rule_file.read(),
                    },
                )
                # check Mimir charm has not sets alert rules even after relation data is set
                self.assertFalse(mock_set_rules.called)

                # check charm is still waiting for pebble ready
                self.assertIsInstance(self.harness.charm.unit.status, WaitingStatus)

                # check charm is active when pebble becomes ready
                self.harness.container_pebble_ready(self.name)
                self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

                # check alert rules have now been set
                self.assertFalse(mock_set_rules.called)
