#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def mimir_charm(ops_test):
    """Mimir charm used for integration testing."""
    charm = await ops_test.build_charm(".")
    return charm
