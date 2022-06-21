# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import yaml

from mimir.alertmanager import DEFAULT_ALERTMANAGER_CONFIG, AlertManager


class TestAlertManager(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_setting_config_returns_http_status(self, mocked_urlopen):
        msg = "HTTP 200 OK"
        mocked_urlopen.return_value = msg
        alertmanager = AlertManager()
        status = alertmanager.set_config(DEFAULT_ALERTMANAGER_CONFIG)
        mocked_urlopen.assert_called()
        self.assertEqual(status, msg)

    @patch("urllib.request.urlopen")
    def test_setting_config_logs_on_http_error(self, mocked_urlopen):
        msg = "Internal Error"
        mocked_urlopen.side_effect = HTTPError(
            url="http://error.com", code=500, msg=msg, hdrs={}, fp=None
        )
        alertmanager = AlertManager()
        with self.assertLogs(level="DEBUG") as logger:
            alertmanager.set_config(DEFAULT_ALERTMANAGER_CONFIG)
            mocked_urlopen.assert_called()
            message = logger.output
            self.assertEqual(len(message), 1)
            self.assertIn(msg, message[0])

    @patch("urllib.request.urlopen")
    def test_setting_config_logs_on_url_error(self, mocked_urlopen):
        msg = "Invalid URL"
        mocked_urlopen.side_effect = URLError(msg)
        alertmanager = AlertManager()
        with self.assertLogs(level="DEBUG") as logger:
            alertmanager.set_config(DEFAULT_ALERTMANAGER_CONFIG)
            mocked_urlopen.assert_called()
            message = logger.output
            self.assertEqual(len(message), 1)
            self.assertIn(msg, message[0])

    @patch("urllib.request.urlopen")
    def test_setting_config_logs_on_timout_error(self, mocked_urlopen):
        msg = "Request timeout"
        mocked_urlopen.side_effect = TimeoutError()
        alertmanager = AlertManager()
        with self.assertLogs(level="DEBUG") as logger:
            alertmanager.set_config(DEFAULT_ALERTMANAGER_CONFIG)
            mocked_urlopen.assert_called()
            message = logger.output
            self.assertEqual(len(message), 1)
            self.assertIn(msg, message[0])

    @patch("urllib.request.urlopen")
    def test_geting_alert_rules(self, mocked_urlopen):
        mock_rules = {"rule": "somerule"}
        http_response = yaml.dump(mock_rules).encode("utf-8")
        mocked_urlopen.return_value.read.return_value = http_response
        mocked_urlopen.return_value.headers.get_content_charset.return_value = "utf-8"
        alertmanager = AlertManager()
        rules = alertmanager.get_alert_rules()
        mocked_urlopen.assert_called()
        self.assertDictEqual(rules, mock_rules)

    @patch("urllib.request.urlopen")
    def test_getting_alert_rules_logs_on_http_error(self, mocked_urlopen):
        msg = "Internal Error"
        mocked_urlopen.side_effect = HTTPError(
            url="http://error.com", code=500, msg=msg, hdrs={}, fp=None
        )
        alertmanager = AlertManager()
        with self.assertLogs(level="DEBUG") as logger:
            rules = alertmanager.get_alert_rules()
            mocked_urlopen.assert_called()
            message = logger.output
            self.assertEqual(len(message), 1)
            self.assertIn(msg, message[0])
            self.assertDictEqual(rules, {})

    @patch("urllib.request.urlopen")
    def test_getting_alert_rules_logs_on_url_error(self, mocked_urlopen):
        msg = "Invalid URL"
        mocked_urlopen.side_effect = URLError(msg)
        alertmanager = AlertManager()
        with self.assertLogs(level="DEBUG") as logger:
            rules = alertmanager.get_alert_rules()
            mocked_urlopen.assert_called()
            message = logger.output
            self.assertEqual(len(message), 1)
            self.assertIn(msg, message[0])
            self.assertDictEqual(rules, {})

    @patch("urllib.request.urlopen")
    def test_getting_alert_rules_logs_on_timout_error(self, mocked_urlopen):
        msg = "Request timeout"
        mocked_urlopen.side_effect = TimeoutError()
        alertmanager = AlertManager()
        with self.assertLogs(level="DEBUG") as logger:
            rules = alertmanager.get_alert_rules()
            mocked_urlopen.assert_called()
            message = logger.output
            self.assertEqual(len(message), 1)
            self.assertIn(msg, message[0])
            self.assertDictEqual(rules, {})

    @patch("urllib.request.urlopen")
    def test_geting_alerts(self, mocked_urlopen):
        mock_alerts = {"alert": "somealert"}
        http_response = json.dumps(mock_alerts).encode("utf-8")
        mocked_urlopen.return_value.read.return_value = http_response
        mocked_urlopen.return_value.headers.get_content_charset.return_value = "utf-8"
        alertmanager = AlertManager()
        rules = alertmanager.get_alerts()
        mocked_urlopen.assert_called()
        self.assertDictEqual(rules, mock_alerts)

    @patch("urllib.request.urlopen")
    def test_setting_alert_rule_group_returns_http_status(self, mocked_urlopen):
        msg = "HTTP 200 OK"
        mocked_urlopen.return_value = msg
        alertmanager = AlertManager()
        status = alertmanager.set_alert_rule_group({"somegroup": "agroup"})
        mocked_urlopen.assert_called()
        self.assertEqual(status, msg)

    @patch("urllib.request.urlopen")
    def test_deleting_alert_rule_group_returns_http_status(self, mocked_urlopen):
        msg = "HTTP 200 OK"
        mocked_urlopen.return_value = msg
        alertmanager = AlertManager()
        status = alertmanager.delete_alert_rule_group("somegroup")
        mocked_urlopen.assert_called()
        self.assertEqual(status, msg)
