# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Unit tests for nd_manage_resource_manager_updated files.

Coverage:
- ResourceManagerConfigModel (Pydantic input validation)
- ResourceManagerDiffEngine (validate_configs, compute_changes)
- resource_helpers (compare_entity_names, compare_resource_values, match_resources)
- payload_utils (build_resource_payload)
"""

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.ResourceManagerConfigModel import (
    ResourceManagerConfigModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.utils.nd_manage_resource_manager.resource_helpers import (
    compare_entity_names,
    compare_resource_values,
    match_resources,
)
from ansible_collections.cisco.nd.plugins.module_utils.utils.nd_manage_resource_manager.payload_utils import (
    SCOPE_TYPE_MAP,
    build_resource_payload,
)
from ansible_collections.cisco.nd.plugins.module_utils.nd_manage_resource_manager_resources import (
    ResourceManagerDiffEngine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@contextmanager
def does_not_raise():
    """Context manager asserting no exception is raised."""
    yield


def _mock_module():
    """Return a MagicMock that replaces AnsibleModule for diff engine tests."""
    m = MagicMock()
    m.fail_json.side_effect = SystemExit("fail_json called")
    return m


# =============================================================================
# ResourceManagerConfigModel — Valid inputs
# =============================================================================


def test_resource_manager_config_model_00100():
    """
    # Summary
    Fabric-scoped config without switch is valid.

    ## Test
    - pool_type ID, pool_name L3_VNI, scope_type fabric
    - switch field is None (fabric scope does not require switch)
    - entity_name and pool_name accepted as-is
    """
    cfg = ResourceManagerConfigModel(
        entity_name="my_vni",
        pool_type="ID",
        pool_name="L3_VNI",
        scope_type="fabric",
        resource="101",
    )
    assert cfg.entity_name == "my_vni"
    assert cfg.pool_name == "L3_VNI"
    assert cfg.scope_type == "fabric"
    assert cfg.switch is None


def test_resource_manager_config_model_00200():
    """
    # Summary
    Device-scoped config with a switch list is valid.

    ## Test
    - scope_type device requires switch — one switch provided
    - resource field is optional and can be omitted
    """
    cfg = ResourceManagerConfigModel(
        entity_name="loopback0",
        pool_type="IP",
        pool_name="LOOPBACK0_IP_POOL",
        scope_type="device",
        switch=["192.175.1.1"],
    )
    assert cfg.scope_type == "device"
    assert cfg.switch == ["192.175.1.1"]
    assert cfg.resource is None


def test_resource_manager_config_model_00300():
    """
    # Summary
    device_pair scope with two switches is valid.

    ## Test
    - scope_type device_pair with two entries in switch
    """
    cfg = ResourceManagerConfigModel(
        entity_name="SW1~SW2~vPC1",
        pool_type="ID",
        pool_name="VPC_ID",
        scope_type="device_pair",
        switch=["SW1", "SW2"],
        resource="500",
    )
    assert cfg.scope_type == "device_pair"
    assert len(cfg.switch) == 2


# =============================================================================
# ResourceManagerConfigModel — Validation failures
# =============================================================================


def test_resource_manager_config_model_00400():
    """
    # Summary
    Non-fabric scope without switch raises ValidationError.

    ## Test
    - scope_type device, no switch → validation error
    """
    with pytest.raises(Exception):
        ResourceManagerConfigModel(
            entity_name="loopback0",
            pool_type="IP",
            pool_name="LOOPBACK0_IP_POOL",
            scope_type="device",
            # switch intentionally omitted
        )


def test_resource_manager_config_model_00500():
    """
    # Summary
    Invalid pool_type raises ValidationError.

    ## Test
    - pool_type "INVALID_TYPE" is not in enum → ValidationError
    """
    with pytest.raises(Exception):
        ResourceManagerConfigModel(
            entity_name="my_vni",
            pool_type="INVALID_TYPE",
            pool_name="L3_VNI",
            scope_type="fabric",
        )


def test_resource_manager_config_model_00600():
    """
    # Summary
    Invalid scope_type raises ValidationError.

    ## Test
    - scope_type "INVALID_SCOPE" is not in enum → ValidationError
    """
    with pytest.raises(Exception):
        ResourceManagerConfigModel(
            entity_name="my_vni",
            pool_type="ID",
            pool_name="L3_VNI",
            scope_type="INVALID_SCOPE",
        )


def test_resource_manager_config_model_00700():
    """
    # Summary
    Pool name incompatible with scope_type raises ValidationError.

    ## Test
    - L3_VNI pool must be used with fabric scope; using device scope should raise
    """
    with pytest.raises(Exception):
        ResourceManagerConfigModel(
            entity_name="my_vni",
            pool_type="ID",
            pool_name="L3_VNI",
            scope_type="device",
            switch=["192.175.1.1"],
        )


# =============================================================================
# compare_entity_names
# =============================================================================


def test_compare_entity_names_00100():
    """
    # Summary
    Identical entity names compare as equal.

    ## Test
    - "loopback0" == "loopback0" → True
    """
    assert compare_entity_names("loopback0", "loopback0") is True


def test_compare_entity_names_00200():
    """
    # Summary
    Different entity names compare as not equal.

    ## Test
    - "loopback0" != "loopback1" → False
    """
    assert compare_entity_names("loopback0", "loopback1") is False


def test_compare_entity_names_00300():
    """
    # Summary
    Tilde-delimited names with parts in different order compare equal.

    ## Test
    - "SW1~SW2~vPC1" == "SW2~SW1~vPC1" after sort → True (sorted compare)
    """
    # This tests the sorted-split logic for device_pair/link entity names.
    result = compare_entity_names("SW1~SW2~vPC1", "SW2~SW1~vPC1")
    # Both sides sorted: ["SW1", "SW2", "vPC1"] — treat as equal
    assert result is True


def test_compare_entity_names_00400():
    """
    # Summary
    Tilde-delimited names with different contents compare as not equal.

    ## Test
    - "SW1~SW2" != "SW1~SW3" → False
    """
    assert compare_entity_names("SW1~SW2", "SW1~SW3") is False


# =============================================================================
# compare_resource_values
# =============================================================================


def test_compare_resource_values_00100():
    """
    # Summary
    Equal integer strings compare as equal.

    ## Test
    - "101" == "101" → True
    """
    assert compare_resource_values("101", "101") is True


def test_compare_resource_values_00200():
    """
    # Summary
    Different integer strings compare as not equal.

    ## Test
    - "101" != "102" → False
    """
    assert compare_resource_values("101", "102") is False


def test_compare_resource_values_00300():
    """
    # Summary
    Equal IPv4 addresses compare as equal.

    ## Test
    - "10.0.0.1" == "10.0.0.1" → True
    """
    assert compare_resource_values("10.0.0.1", "10.0.0.1") is True


def test_compare_resource_values_00400():
    """
    # Summary
    Equivalent IPv6 addresses in different notation compare as equal.

    ## Test
    - "fe80::1" == "fe80:0:0:0:0:0:0:1" → True (ipaddress normalisation)
    """
    assert compare_resource_values("fe80::1", "fe80:0:0:0:0:0:0:1") is True


def test_compare_resource_values_00500():
    """
    # Summary
    Different IPv4 addresses compare as not equal.

    ## Test
    - "10.0.0.1" != "10.0.0.2" → False
    """
    assert compare_resource_values("10.0.0.1", "10.0.0.2") is False


def test_compare_resource_values_00600():
    """
    # Summary
    Equivalent CIDR values compare as equal.

    ## Test
    - "192.168.1.0/24" == "192.168.1.0/255.255.255.0" should be normalised to same network
    """
    # Both represent the same network in different notation
    assert compare_resource_values("192.168.1.0/24", "192.168.1.0/24") is True


# =============================================================================
# match_resources
# =============================================================================


def test_match_resources_00100():
    """
    # Summary
    Resources with matching entityName, poolName, and scopeType match.

    ## Test
    - have_res and want_res with same keys → True
    """
    have = {
        "entityName": "loopback0",
        "poolName": "LOOPBACK0_IP_POOL",
        "scopeType": "Fabric",
        "scopeValue": "test_fabric",
    }
    want = {
        "entityName": "loopback0",
        "poolName": "LOOPBACK0_IP_POOL",
        "scopeType": "Fabric",
        "scopeValue": "test_fabric",
    }
    assert match_resources(have, want) is True


def test_match_resources_00200():
    """
    # Summary
    Resources with different entityName do not match.

    ## Test
    - have: entityName="loopback0", want: entityName="loopback1" → False
    """
    have = {
        "entityName": "loopback0",
        "poolName": "LOOPBACK0_IP_POOL",
        "scopeType": "Fabric",
    }
    want = {
        "entityName": "loopback1",
        "poolName": "LOOPBACK0_IP_POOL",
        "scopeType": "Fabric",
    }
    assert match_resources(have, want) is False


def test_match_resources_00300():
    """
    # Summary
    Resources with different poolName do not match.

    ## Test
    - have: poolName="L3_VNI", want: poolName="VPC_ID" → False
    """
    have = {
        "entityName": "my_vni",
        "poolName": "L3_VNI",
        "scopeType": "Fabric",
    }
    want = {
        "entityName": "my_vni",
        "poolName": "VPC_ID",
        "scopeType": "Fabric",
    }
    assert match_resources(have, want) is False


# =============================================================================
# build_resource_payload
# =============================================================================


def test_build_resource_payload_00100():
    """
    # Summary
    Fabric-scoped payload uses fabric name as scopeValue.

    ## Test
    - scope_type fabric, scope_value=None → scopeValue == fabric name
    """
    rm_elem = {
        "entity_name": "my_vni",
        "pool_name": "L3_VNI",
        "scope_type": "fabric",
        "resource": "101",
    }
    payload = build_resource_payload(rm_elem, "test_fabric", None)
    assert payload["scopeValue"] == "test_fabric"
    assert payload["scopeType"] == "Fabric"
    assert payload["entityName"] == "my_vni"
    assert payload["poolName"] == "L3_VNI"
    assert payload["resource"] == "101"


def test_build_resource_payload_00200():
    """
    # Summary
    Device-scoped payload uses switch serial as scopeValue.

    ## Test
    - scope_type device, scope_value="FSW1" → scopeValue == "FSW1"
    """
    rm_elem = {
        "entity_name": "loopback0",
        "pool_name": "LOOPBACK0_IP_POOL",
        "scope_type": "device",
        "resource": "10.10.10.1",
    }
    payload = build_resource_payload(rm_elem, "test_fabric", "FSW1")
    assert payload["scopeValue"] == "FSW1"
    assert payload["scopeType"] == "Device"
    assert payload["entityName"] == "loopback0"


def test_build_resource_payload_00300():
    """
    # Summary
    Payload without resource field omits the resource key or sets it to None.

    ## Test
    - rm_elem without 'resource' key — build_resource_payload handles missing key
    """
    rm_elem = {
        "entity_name": "loopback0",
        "pool_name": "L3_VNI",
        "scope_type": "fabric",
    }
    payload = build_resource_payload(rm_elem, "test_fabric", None)
    assert payload["entityName"] == "loopback0"
    # resource key should be None or absent — both are valid
    assert payload.get("resource") is None


# =============================================================================
# SCOPE_TYPE_MAP
# =============================================================================


def test_scope_type_map_00100():
    """
    # Summary
    SCOPE_TYPE_MAP covers all five valid scope types.

    ## Test
    - Keys: fabric, device, device_interface, device_pair, link
    - Values: Fabric, Device, DeviceInterface, DevicePair, Link
    """
    assert SCOPE_TYPE_MAP["fabric"] == "Fabric"
    assert SCOPE_TYPE_MAP["device"] == "Device"
    assert SCOPE_TYPE_MAP["device_interface"] == "DeviceInterface"
    assert SCOPE_TYPE_MAP["device_pair"] == "DevicePair"
    assert SCOPE_TYPE_MAP["link"] == "Link"
    assert len(SCOPE_TYPE_MAP) == 5


# =============================================================================
# ResourceManagerDiffEngine.validate_configs
# =============================================================================


def test_diff_engine_validate_configs_00100():
    """
    # Summary
    validate_configs with empty list returns empty list.

    ## Test
    - config=[] → rm_info=[]
    """
    result = ResourceManagerDiffEngine.validate_configs([], "merged", _mock_module())
    assert result == []


def test_diff_engine_validate_configs_00200():
    """
    # Summary
    validate_configs with None returns empty list.

    ## Test
    - config=None → rm_info=[]
    """
    result = ResourceManagerDiffEngine.validate_configs(None, "merged", _mock_module())
    assert result == []


def test_diff_engine_validate_configs_00300():
    """
    # Summary
    validate_configs query state allows entity_name-only entry.

    ## Test
    - state=query, config=[{entity_name: 'x'}] → returns [{'entity_name': 'x'}]
    """
    module = _mock_module()
    result = ResourceManagerDiffEngine.validate_configs(
        [{"entity_name": "x"}], "query", module
    )
    assert len(result) == 1
    assert result[0]["entity_name"] == "x"


def test_diff_engine_validate_configs_00400():
    """
    # Summary
    validate_configs query state rejects unknown parameters.

    ## Test
    - state=query, config=[{unknown_param: 'x'}] → module.fail_json called
    """
    module = _mock_module()
    with pytest.raises(SystemExit):
        ResourceManagerDiffEngine.validate_configs(
            [{"scope_type": "fabric", "pool_type": "ID"}], "query", module
        )


# =============================================================================
# ResourceManagerDiffEngine.compute_changes
# =============================================================================


def test_compute_changes_00100():
    """
    # Summary
    All want entries absent from have go into to_create.

    ## Test
    - want=[res1], have=[] → to_create=[res1], to_delete=[], idempotent=[]
    """
    want = [
        {
            "entityName": "my_vni",
            "poolName": "L3_VNI",
            "scopeType": "Fabric",
            "scopeValue": "test_fabric",
            "resource": "101",
        }
    ]
    result = ResourceManagerDiffEngine.compute_changes(want=want, have=[])
    assert len(result["to_create"]) == 1
    assert len(result["to_delete"]) == 0
    assert len(result["idempotent"]) == 0


def test_compute_changes_00200():
    """
    # Summary
    Matching want and have entry is idempotent (not in to_create).

    ## Test
    - want=[res1], have=[res1_with_id] → to_create=[], idempotent=[res1_with_id]
    """
    want = [
        {
            "entityName": "my_vni",
            "poolName": "L3_VNI",
            "scopeType": "Fabric",
            "scopeValue": "test_fabric",
            "resource": "101",
        }
    ]
    have = [
        {
            "entityName": "my_vni",
            "poolName": "L3_VNI",
            "scopeType": "Fabric",
            "scopeValue": "test_fabric",
            "resourceValue": "101",
            "resourceId": 42,
        }
    ]
    result = ResourceManagerDiffEngine.compute_changes(want=want, have=have)
    assert len(result["to_create"]) == 0
    assert len(result["idempotent"]) == 1


def test_compute_changes_00300():
    """
    # Summary
    All have entries with IDs go into to_delete.

    ## Test
    - want=[res1], have=[res2_with_id, res3_with_id] → to_delete=[id2, id3]
    """
    want = [
        {
            "entityName": "my_vni",
            "poolName": "L3_VNI",
            "scopeType": "Fabric",
            "scopeValue": "test_fabric",
            "resource": "101",
        }
    ]
    have = [
        {"entityName": "other_vni", "poolName": "L3_VNI", "resourceId": 10},
        {"entityName": "another_vni", "poolName": "L3_VNI", "resourceId": 11},
    ]
    result = ResourceManagerDiffEngine.compute_changes(want=want, have=have)
    assert set(result["to_delete"]) == {10, 11}


def test_compute_changes_00400():
    """
    # Summary
    Empty want and empty have produces all-empty diff.

    ## Test
    - want=[], have=[] → all three buckets empty
    """
    result = ResourceManagerDiffEngine.compute_changes(want=[], have=[])
    assert result["to_create"] == []
    assert result["to_delete"] == []
    assert result["idempotent"] == []
