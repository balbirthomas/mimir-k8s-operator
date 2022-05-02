# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest

from charm import MimirCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(MimirCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        return True

