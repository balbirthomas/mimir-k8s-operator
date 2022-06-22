#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import logging
import time

import pytest
from helpers import oci_image, unit_address
from pytest_operator.plugin import OpsTest

from mimir.alertmanager import AlertManager

logger = logging.getLogger(__name__)

mimir_app_name = "mimir-k8s"
grafana_agent_app_name = "grafana-agent-k8s"

alert_rule_name = "cpuoveruse"
alert_rule = {
    "name": alert_rule_name,
    "rules": [
        {
            "alert": alert_rule_name,
            "expr": "process_cpu_seconds_total > 0",
        }
    ],
}


@pytest.mark.abort_on_fail
async def test_mimir_charm_ingests_metrics_alert_rules_and_raises_alerts(
    ops_test: OpsTest, mimir_charm
):
    """Test basic functionality of Mimir charm."""
    await asyncio.gather(
        ops_test.model.deploy(
            mimir_charm,
            resources={"mimir-image": oci_image("./metadata.yaml", "mimir-image")},
            application_name=mimir_app_name,
        ),
        ops_test.model.deploy(
            "grafana-agent-k8s",
            channel="edge",
            application_name=grafana_agent_app_name,
        ),
    )

    app_names = [mimir_app_name, grafana_agent_app_name]
    await ops_test.model.wait_for_idle(apps=app_names, status="active", wait_for_units=1)

    await ops_test.model.add_relation(mimir_app_name, grafana_agent_app_name)
    await ops_test.model.wait_for_idle(apps=app_names, status="active")

    mimir_address = await unit_address(ops_test, mimir_app_name, 0)
    alertmanager = AlertManager(mimir_address)

    # extract juju topology labels set by relation with grafana-agent
    alert_rule_groups = alertmanager.get_alert_rules()
    labels = alert_rule_groups["anonymous"][0]["rules"][0]["labels"]

    # wait for metrics from grafana-agent
    time.sleep(2 * 60)

    # set an alert rule that is sure to fire
    # (with grafana-agent juju topology labels)
    rule = alert_rule.copy()
    rule["rules"][0]["labels"] = labels
    alertmanager.set_alert_rule_group(rule)

    # give mimir some time to ingest the rule
    time.sleep(10)

    # get current list of rules and check new rule has been set
    alert_rule_groups = alertmanager.get_alert_rules()
    group_names = [group["name"] for group in alert_rule_groups["anonymous"]]
    assert alert_rule_name in group_names

    # give mimir ruler some time to trigger an alert
    time.sleep(2 * 60)

    # get all current alerts
    alerts_firing = alertmanager.get_alerts()
    alerts_data = alerts_firing.get("data", {})
    alerts = alerts_data.get("alerts", [])

    # check an alert has been raised
    assert len(alerts) > 0
    alert = alerts[0]
    assert "state" in alert
    assert alert["state"] == "firing"

    # check raised alert is the expected one
    alert_labels = alert.get("labels", {})
    assert alert_labels
    assert "alertname" in alert_labels
    assert alert_labels["alertname"] == alert_rule_name
    assert "juju_application" in labels
    assert labels["juju_application"] == "grafana-agent-k8s"


async def test_alert_rules_are_removed_on_relation_broken(
    ops_test: OpsTest, mimir_charm
):
    # remove grafana agent and wait for Mimir to become stable
    await ops_test.model.applications[grafana_agent_app_name].remove()
    await ops_test.model.wait_for_idle(apps=[mimir_app_name], status="active")

    # fetch interface to Mimir alertmanager
    mimir_address = await unit_address(ops_test, mimir_app_name, 0)
    alertmanager = AlertManager(mimir_address)

    # get current list of rules and check there are no alert rule groups
    alert_rule_groups = alertmanager.get_alert_rules()
    assert len(alert_rule_groups) == 0