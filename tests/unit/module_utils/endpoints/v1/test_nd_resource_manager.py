# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Unit tests for ep_api_v1_resource_manager.py
"""

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

from ansible_collections.cisco.nd.plugins.module_utils.enums import HttpVerbEnum
from ansible_collections.cisco.nd.plugins.module_utils.ep.ep_api_v1_manage_resource_manager import (
    EpApiV1ManageDeleteFabricResourceById,
    EpApiV1ManageGetFabricResourceById,
    EpApiV1ManageGetFabricResources,
    EpApiV1ManageGetFabricUnusedVlans,
    EpApiV1ManageGetFabricsPools,
    EpApiV1ManageGetFabricsProposeVlan,
    EpApiV1ManagePostFabricResources,
    EpApiV1ManagePostFabricResourcesActionsRemove,
    EpApiV1ManagePostFabricResourcesActionsRemoveResource,
)
from ansible_collections.cisco.nd.tests.unit.module_utils.common_utils import does_not_raise


def test_ep_resource_manager_00010():
    with does_not_raise():
        ep = EpApiV1ManageGetFabricsPools(fabric_name="fab1")
    assert ep.verb == HttpVerbEnum.GET
    assert ep.path == "/api/v1/manage/fabrics/fab1/pools"


def test_ep_resource_manager_00020():
    with does_not_raise():
        ep = EpApiV1ManageGetFabricsPools(fabric_name="fab1")
        ep.endpoint_params.pool_id = 10
        ep.lucene_params.filter = "poolType:idPool"
    assert ep.path == "/api/v1/manage/fabrics/fab1/pools?poolId=10&filter=poolType%3AidPool"


def test_ep_resource_manager_00030():
    with does_not_raise():
        ep = EpApiV1ManageGetFabricsProposeVlan(fabric_name="fab1")
        ep.endpoint_params.vlan_type = "networkVlan"
        ep.endpoint_params.tenant_name = "common"
    assert ep.verb == HttpVerbEnum.GET
    assert ep.path == "/api/v1/manage/fabrics/fab1/proposeVlan?vlanType=networkVlan&tenantName=common"


def test_ep_resource_manager_00040():
    with does_not_raise():
        ep = EpApiV1ManageGetFabricResources(fabric_name="fab1")
        ep.endpoint_params.switch_id = "SAL1234"
        ep.endpoint_params.pool_name = "L3_VNI"
    assert ep.verb == HttpVerbEnum.GET
    assert ep.path == "/api/v1/manage/fabrics/fab1/resources?switchId=SAL1234&poolName=L3_VNI"


def test_ep_resource_manager_00050():
    with does_not_raise():
        ep = EpApiV1ManagePostFabricResources(fabric_name="fab1")
        ep.endpoint_params.tenant_name = "common"
    assert ep.verb == HttpVerbEnum.POST
    assert ep.path == "/api/v1/manage/fabrics/fab1/resources?tenantName=common"


def test_ep_resource_manager_00060():
    with does_not_raise():
        ep = EpApiV1ManagePostFabricResourcesActionsRemove(fabric_name="fab1")
    assert ep.verb == HttpVerbEnum.POST
    assert ep.path == "/api/v1/manage/fabrics/fab1/resources/actions/remove"


def test_ep_resource_manager_00070():
    with does_not_raise():
        ep = EpApiV1ManagePostFabricResourcesActionsRemoveResource(fabric_name="fab1")
    assert ep.verb == HttpVerbEnum.POST
    assert ep.path == "/api/v1/manage/fabrics/fab1/resources/actions/removeResource"


def test_ep_resource_manager_00080():
    with does_not_raise():
        ep = EpApiV1ManageGetFabricResourceById(fabric_name="fab1", resource_id=123)
    assert ep.verb == HttpVerbEnum.GET
    assert ep.path == "/api/v1/manage/fabrics/fab1/resources/123"


def test_ep_resource_manager_00090():
    with does_not_raise():
        ep = EpApiV1ManageDeleteFabricResourceById(fabric_name="fab1", resource_id=456)
    assert ep.verb == HttpVerbEnum.DELETE
    assert ep.path == "/api/v1/manage/fabrics/fab1/resources/456"


def test_ep_resource_manager_00100():
    with does_not_raise():
        ep = EpApiV1ManageGetFabricUnusedVlans(fabric_name="fab1")
        ep.endpoint_params.vlan_type = "networkVlan"
        ep.endpoint_params.switch_id = "SAL1234"
    assert ep.verb == HttpVerbEnum.GET
    assert ep.path == "/api/v1/manage/fabrics/fab1/unusedVlans?vlanType=networkVlan&switchId=SAL1234"
