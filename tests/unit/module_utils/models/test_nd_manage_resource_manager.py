# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Unit tests for nd_manage_resource_manager.py Pydantic models.

Tests cover:
- Enum values and ``choices()`` helpers
- ``ResourceValidators`` static validators
- Scope GET models (FabricScope, DeviceScope, DeviceInterfaceScope, LinkScope, DevicePairScope)
- Scope POST models (FabricScopePost, DeviceScopePost, DeviceInterfaceScopePost, LinkScopePost, DevicePairScopePost)
- Pool models (PoolDataModel, PoolsResponseModel)
- Propose-VLAN model (ProposeVlanResponseModel)
- Resource models (ResourceDetailsGetModel, ResourceDetailsPostModel)
- Allocate/remove action models
- UnusedVlanResponseModel
"""

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

from contextlib import contextmanager

import pytest

from ansible_collections.cisco.nd.plugins.models.nd_manage_resource_manager.nd_manage_resource_manager import (
    AllocateResourcesRequestModel,
    AllocateResourcesResponseModel,
    DeviceInterfaceScope,
    DeviceInterfaceScopePost,
    DevicePairScope,
    DevicePairScopePost,
    DeviceScope,
    DeviceScopePost,
    FabricScope,
    FabricScopePost,
    LinkScope,
    LinkScopePost,
    PoolDataModel,
    PoolsResponseModel,
    PoolType,
    ProposeVlanResponseModel,
    RemoveResourceByDetailsResponseModel,
    RemoveResourcesByIdRequestModel,
    RemoveResourcesResponseItem,
    RemoveResourcesResponseModel,
    ResourceDataBase,
    ResourceDataBasePost,
    ResourceDataBasePostResponse,
    ResourceDetailsGetModel,
    ResourceDetailsPostModel,
    ResourcesResponseModel,
    ResourceValidators,
    ScopeType,
    UnusedVlanResponseModel,
    VlanType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@contextmanager
def does_not_raise():
    """Context manager that asserts no exception is raised."""
    yield


# =============================================================================
# Enum: PoolType
# =============================================================================


def test_pool_type_00100():
    """
    # Summary
    PoolType has the three expected string values.

    ## Test
    - IP_POOL == "ipPool"
    - SUBNET_POOL == "subnetPool"
    - ID_POOL == "idPool"
    """
    assert PoolType.IP_POOL == "ipPool"
    assert PoolType.SUBNET_POOL == "subnetPool"
    assert PoolType.ID_POOL == "idPool"


def test_pool_type_00110():
    """
    # Summary
    PoolType.choices() returns all three values.

    ## Test
    - choices() list has exactly three elements
    - Each expected value is present
    """
    choices = PoolType.choices()
    assert len(choices) == 3
    assert "ipPool" in choices
    assert "subnetPool" in choices
    assert "idPool" in choices


# =============================================================================
# Enum: ScopeType
# =============================================================================


def test_scope_type_00100():
    """
    # Summary
    ScopeType has the five expected string values.
    """
    assert ScopeType.FABRIC == "fabric"
    assert ScopeType.DEVICE == "device"
    assert ScopeType.DEVICE_INTERFACE == "deviceInterface"
    assert ScopeType.LINK == "link"
    assert ScopeType.DEVICE_PAIR == "devicePair"


def test_scope_type_00110():
    """
    # Summary
    ScopeType.choices() returns all five values.
    """
    choices = ScopeType.choices()
    assert len(choices) == 5
    for expected in ("fabric", "device", "deviceInterface", "link", "devicePair"):
        assert expected in choices


# =============================================================================
# Enum: VlanType
# =============================================================================


def test_vlan_type_00100():
    """
    # Summary
    VlanType has the four expected string values.
    """
    assert VlanType.NETWORK_VLAN == "networkVlan"
    assert VlanType.VRF_VLAN == "vrfVlan"
    assert VlanType.SERVICE_NETWORK_VLAN == "serviceNetworkVlan"
    assert VlanType.VPC_PEER_LINK_VLAN == "vpcPeerLinkVlan"


def test_vlan_type_00110():
    """
    # Summary
    VlanType.choices() returns all four values.
    """
    choices = VlanType.choices()
    assert len(choices) == 4


# =============================================================================
# ResourceValidators
# =============================================================================


def test_resource_validators_ip_00100():
    """
    # Summary
    validate_ip_address accepts a valid IPv4 address.
    """
    result = ResourceValidators.validate_ip_address("192.168.1.1")
    assert result == "192.168.1.1"


def test_resource_validators_ip_00110():
    """
    # Summary
    validate_ip_address accepts a valid IPv6 address.
    """
    result = ResourceValidators.validate_ip_address("::1")
    assert result == "::1"


def test_resource_validators_ip_00120():
    """
    # Summary
    validate_ip_address returns None for None input.
    """
    result = ResourceValidators.validate_ip_address(None)
    assert result is None


def test_resource_validators_ip_00130():
    """
    # Summary
    validate_ip_address raises ValueError for an invalid address.
    """
    with pytest.raises(ValueError, match="Invalid IP address"):
        ResourceValidators.validate_ip_address("not-an-ip")


def test_resource_validators_cidr_00100():
    """
    # Summary
    validate_cidr accepts a valid CIDR string.
    """
    result = ResourceValidators.validate_cidr("10.0.0.0/24")
    assert result == "10.0.0.0/24"


def test_resource_validators_cidr_00110():
    """
    # Summary
    validate_cidr raises ValueError when no slash is present.
    """
    with pytest.raises(ValueError, match="CIDR notation required"):
        ResourceValidators.validate_cidr("10.0.0.0")


def test_resource_validators_cidr_00120():
    """
    # Summary
    validate_cidr raises ValueError for a malformed CIDR string.
    """
    with pytest.raises(ValueError, match="Invalid CIDR format"):
        ResourceValidators.validate_cidr("999.999.999.0/24")


def test_resource_validators_cidr_00130():
    """
    # Summary
    validate_cidr returns None for None input.
    """
    assert ResourceValidators.validate_cidr(None) is None


def test_resource_validators_pool_range_00100():
    """
    # Summary
    validate_pool_range accepts a valid numeric range string.
    """
    result = ResourceValidators.validate_pool_range("2300-2600")
    assert result == "2300-2600"


def test_resource_validators_pool_range_00110():
    """
    # Summary
    validate_pool_range accepts a valid CIDR notation range.
    """
    result = ResourceValidators.validate_pool_range("10.1.1.0/24")
    assert result == "10.1.1.0/24"


def test_resource_validators_pool_range_00120():
    """
    # Summary
    validate_pool_range returns None for None input.
    """
    assert ResourceValidators.validate_pool_range(None) is None


def test_resource_validators_pool_range_00130():
    """
    # Summary
    validate_pool_range raises ValueError when start >= end in a range.
    """
    with pytest.raises(ValueError, match="Invalid range"):
        ResourceValidators.validate_pool_range("2600-2300")


# =============================================================================
# FabricScope (GET)
# =============================================================================


def test_fabric_scope_00100():
    """
    # Summary
    FabricScope can be created with only defaults.

    ## Test
    - scope_type defaults to ScopeType.FABRIC
    - fabric_name defaults to None
    """
    with does_not_raise():
        instance = FabricScope()
    assert instance.scope_type == ScopeType.FABRIC
    assert instance.fabric_name is None


def test_fabric_scope_00110():
    """
    # Summary
    FabricScope accepts fabric_name via alias.
    """
    instance = FabricScope(**{"fabricName": "MyFabric"})
    assert instance.fabric_name == "MyFabric"


def test_fabric_scope_00120():
    """
    # Summary
    FabricScope identifiers ClassVar is an empty list.
    """
    assert FabricScope.identifiers == []


# =============================================================================
# DeviceScope (GET)
# =============================================================================


def test_device_scope_00100():
    """
    # Summary
    DeviceScope can be created with all optional fields absent.
    """
    with does_not_raise():
        instance = DeviceScope()
    assert instance.scope_type == ScopeType.DEVICE


def test_device_scope_00110():
    """
    # Summary
    DeviceScope validates switch_ip via alias and validator.
    """
    instance = DeviceScope(**{"switchIp": "10.0.0.1"})
    assert instance.switch_ip == "10.0.0.1"


def test_device_scope_00120():
    """
    # Summary
    DeviceScope raises ValidationError for an invalid switchIp.
    """
    from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import (
        ValidationError,
    )

    with pytest.raises((ValidationError, ValueError)):
        DeviceScope(**{"switchIp": "bad-ip"})


# =============================================================================
# DeviceInterfaceScope (GET)
# =============================================================================


def test_device_interface_scope_00100():
    """
    # Summary
    DeviceInterfaceScope defaults scope_type to deviceInterface.
    """
    instance = DeviceInterfaceScope()
    assert instance.scope_type == ScopeType.DEVICE_INTERFACE


def test_device_interface_scope_00110():
    """
    # Summary
    DeviceInterfaceScope accepts interfaceName via alias.
    """
    instance = DeviceInterfaceScope(**{"interfaceName": "Ethernet1/1"})
    assert instance.interface_name == "Ethernet1/1"


# =============================================================================
# LinkScope (GET)
# =============================================================================


def test_link_scope_00100():
    """
    # Summary
    LinkScope defaults scope_type to link.
    """
    instance = LinkScope()
    assert instance.scope_type == ScopeType.LINK


def test_link_scope_00110():
    """
    # Summary
    LinkScope validates srcSwitchIp and dstSwitchIp via alias.
    """
    instance = LinkScope(**{"srcSwitchIp": "10.0.0.1", "dstSwitchIp": "10.0.0.2"})
    assert instance.src_switch_ip == "10.0.0.1"
    assert instance.dst_switch_ip == "10.0.0.2"


def test_link_scope_00120():
    """
    # Summary
    LinkScope raises ValidationError for invalid srcSwitchIp.
    """
    from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import (
        ValidationError,
    )

    with pytest.raises((ValidationError, ValueError)):
        LinkScope(**{"srcSwitchIp": "not_valid_ip"})


def test_link_scope_00130():
    """
    # Summary
    LinkScope accepts integer resource IDs.
    """
    instance = LinkScope(**{"srcResourceId": 10, "dstResourceId": 20})
    assert instance.src_resource_id == 10
    assert instance.dst_resource_id == 20


# =============================================================================
# DevicePairScope (GET)
# =============================================================================


def test_device_pair_scope_00100():
    """
    # Summary
    DevicePairScope defaults scope_type to devicePair.
    """
    instance = DevicePairScope()
    assert instance.scope_type == ScopeType.DEVICE_PAIR


def test_device_pair_scope_00110():
    """
    # Summary
    DevicePairScope accepts peerResourceId.
    """
    instance = DevicePairScope(**{"peerResourceId": 99})
    assert instance.peer_resource_id == 99


# =============================================================================
# FabricScopePost (POST)
# =============================================================================


def test_fabric_scope_post_00100():
    """
    # Summary
    FabricScopePost requires scopeType and fabricName.
    """
    with does_not_raise():
        instance = FabricScopePost(
            **{"scopeType": "fabric", "fabricName": "TestFabric"}
        )
    assert instance.fabric_name == "TestFabric"


def test_fabric_scope_post_00110():
    """
    # Summary
    FabricScopePost raises ValidationError when fabricName is missing.
    """
    from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import (
        ValidationError,
    )

    with pytest.raises((ValidationError, TypeError)):
        FabricScopePost(**{"scopeType": "fabric"})


# =============================================================================
# DeviceScopePost (POST)
# =============================================================================


def test_device_scope_post_00100():
    """
    # Summary
    DeviceScopePost requires switchId.
    """
    instance = DeviceScopePost(**{"scopeType": "device", "switchId": "FDO123"})
    assert instance.switch_id == "FDO123"


def test_device_scope_post_00110():
    """
    # Summary
    DeviceScopePost raises ValidationError when switchId is missing.
    """
    from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import (
        ValidationError,
    )

    with pytest.raises((ValidationError, TypeError)):
        DeviceScopePost(**{"scopeType": "device"})


# =============================================================================
# DeviceInterfaceScopePost (POST)
# =============================================================================


def test_device_interface_scope_post_00100():
    """
    # Summary
    DeviceInterfaceScopePost requires switchId and interfaceName.
    """
    instance = DeviceInterfaceScopePost(
        **{
            "scopeType": "deviceInterface",
            "switchId": "FDO123",
            "interfaceName": "Eth1/1",
        }
    )
    assert instance.switch_id == "FDO123"
    assert instance.interface_name == "Eth1/1"


# =============================================================================
# LinkScopePost (POST)
# =============================================================================


def test_link_scope_post_00100():
    """
    # Summary
    LinkScopePost requires srcSwitchId, srcInterfaceName, dstSwitchId, dstInterfaceName.
    """
    payload = {
        "scopeType": "link",
        "srcSwitchId": "SRC123",
        "srcInterfaceName": "Eth1/1",
        "dstSwitchId": "DST456",
        "dstInterfaceName": "Eth2/1",
    }
    instance = LinkScopePost(**payload)
    assert instance.src_switch_id == "SRC123"
    assert instance.dst_switch_id == "DST456"


# =============================================================================
# DevicePairScopePost (POST)
# =============================================================================


def test_device_pair_scope_post_00100():
    """
    # Summary
    DevicePairScopePost requires srcSwitchId and dstSwitchId.
    """
    instance = DevicePairScopePost(
        **{"scopeType": "devicePair", "srcSwitchId": "SRC1", "dstSwitchId": "DST1"}
    )
    assert instance.src_switch_id == "SRC1"
    assert instance.dst_switch_id == "DST1"


# =============================================================================
# PoolDataModel
# =============================================================================


def test_pool_data_model_00100():
    """
    # Summary
    PoolDataModel can be instantiated with all fields optional.

    ## Test
    - overlap_allowed defaults to False
    - pool_type is None when absent
    """
    with does_not_raise():
        instance = PoolDataModel()
    assert instance.overlap_allowed is False
    assert instance.pool_type is None


def test_pool_data_model_00110():
    """
    # Summary
    PoolDataModel accepts full payload via aliases and validates pool_range.
    """
    payload = {
        "poolId": 1,
        "poolName": "LOOPBACK_POOL",
        "fabricName": "FabricA",
        "vrfName": "default",
        "poolType": "ipPool",
        "poolRange": "10.2.0.0/24",
        "overlapAllowed": True,
    }
    instance = PoolDataModel(**payload)
    assert instance.pool_id == 1
    assert instance.pool_name == "LOOPBACK_POOL"
    assert instance.pool_type == PoolType.IP_POOL
    assert instance.pool_range == "10.2.0.0/24"
    assert instance.overlap_allowed is True


def test_pool_data_model_00120():
    """
    # Summary
    PoolDataModel.to_payload() returns a dict with camelCase aliases.
    """
    instance = PoolDataModel(**{"poolName": "MY_POOL", "poolType": "idPool"})
    payload = instance.to_payload()
    assert "poolName" in payload
    assert payload["poolName"] == "MY_POOL"
    assert "poolType" in payload


def test_pool_data_model_00130():
    """
    # Summary
    PoolDataModel.from_response() creates an instance from a response dict.
    """
    response = {
        "poolId": 5,
        "poolName": "VLAN_POOL",
        "poolType": "idPool",
        "poolRange": "100-200",
    }
    instance = PoolDataModel.from_response(response)
    assert instance.pool_id == 5
    assert instance.pool_name == "VLAN_POOL"


def test_pool_data_model_00140():
    """
    # Summary
    PoolDataModel raises ValidationError for an invalid pool_range.
    """
    from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import (
        ValidationError,
    )

    with pytest.raises((ValidationError, ValueError)):
        PoolDataModel(**{"poolRange": "500-100"})  # start >= end


def test_pool_data_model_00150():
    """
    # Summary
    PoolDataModel identifiers ClassVar contains pool_id and pool_name.
    """
    assert "pool_id" in PoolDataModel.identifiers
    assert "pool_name" in PoolDataModel.identifiers


# =============================================================================
# PoolsResponseModel
# =============================================================================


def test_pools_response_model_00100():
    """
    # Summary
    PoolsResponseModel defaults to an empty pools list.
    """
    instance = PoolsResponseModel()
    assert instance.pools == []
    assert instance.meta is None


def test_pools_response_model_00110():
    """
    # Summary
    PoolsResponseModel nests a list of PoolDataModel instances.
    """
    payload = {
        "pools": [{"poolId": 1, "poolName": "P1"}, {"poolId": 2, "poolName": "P2"}],
        "meta": {"total": 2},
    }
    instance = PoolsResponseModel(**payload)
    assert len(instance.pools) == 2
    assert instance.pools[0].pool_name == "P1"
    assert instance.meta == {"total": 2}


# =============================================================================
# ProposeVlanResponseModel
# =============================================================================


def test_propose_vlan_response_model_00100():
    """
    # Summary
    ProposeVlanResponseModel defaults propose_vlan to None.
    """
    instance = ProposeVlanResponseModel()
    assert instance.propose_vlan is None


def test_propose_vlan_response_model_00110():
    """
    # Summary
    ProposeVlanResponseModel accepts proposeVlan via alias.
    """
    instance = ProposeVlanResponseModel(**{"proposeVlan": 200})
    assert instance.propose_vlan == 200


def test_propose_vlan_response_model_00120():
    """
    # Summary
    ProposeVlanResponseModel.from_response() creates an instance from a dict.
    """
    response = {"proposeVlan": 310}
    instance = ProposeVlanResponseModel.from_response(response)
    assert instance.propose_vlan == 310


def test_propose_vlan_response_model_00130():
    """
    # Summary
    ProposeVlanResponseModel.to_payload() serialises non-None fields.
    """
    instance = ProposeVlanResponseModel(**{"proposeVlan": 400})
    payload = instance.to_payload()
    assert payload.get("proposeVlan") == 400


# =============================================================================
# ResourceDetailsGetModel
# =============================================================================


def test_resource_details_get_model_00100():
    """
    # Summary
    ResourceDetailsGetModel can be instantiated with all optional fields absent.
    """
    with does_not_raise():
        instance = ResourceDetailsGetModel()
    assert instance.resource_id is None
    assert instance.vrf_name == "default"


def test_resource_details_get_model_00110():
    """
    # Summary
    ResourceDetailsGetModel accepts full payload via aliases.
    """
    payload = {
        "resourceId": 42,
        "poolName": "LOOPBACK",
        "entityName": "Leaf1",
        "resourceValue": "10.1.1.1",
        "isPreAllocated": True,
        "createTimestamp": "2026-01-01T00:00:00Z",
        "scopeDetails": {"scopeType": "fabric", "fabricName": "FabricA"},
    }
    instance = ResourceDetailsGetModel(**payload)
    assert instance.resource_id == 42
    assert instance.entity_name == "Leaf1"
    assert instance.is_pre_allocated is True
    assert instance.create_timestamp == "2026-01-01T00:00:00Z"
    assert isinstance(instance.scope_details, FabricScope)


def test_resource_details_get_model_00120():
    """
    # Summary
    ResourceDetailsGetModel.to_payload() round-trips the model.
    """
    payload = {"resourceId": 7, "poolName": "P1", "resourceValue": "10.0.0.10"}
    instance = ResourceDetailsGetModel.from_response(payload)
    result = instance.to_payload()
    assert result["resourceId"] == 7
    assert result["poolName"] == "P1"


def test_resource_details_get_model_00130():
    """
    # Summary
    ResourceDetailsGetModel scope_details discriminates on DeviceScope.
    """
    payload = {
        "scopeDetails": {
            "scopeType": "device",
            "switchName": "Leaf-1",
            "switchId": "FDO123",
            "switchIp": "192.0.2.1",
        }
    }
    instance = ResourceDetailsGetModel(**payload)
    assert isinstance(instance.scope_details, DeviceScope)
    assert instance.scope_details.switch_ip == "192.0.2.1"


def test_resource_details_get_model_00140():
    """
    # Summary
    ResourceDetailsGetModel scope_details discriminates on LinkScope.
    """
    payload = {
        "scopeDetails": {
            "scopeType": "link",
            "srcSwitchIp": "10.0.0.1",
            "dstSwitchIp": "10.0.0.2",
        }
    }
    instance = ResourceDetailsGetModel(**payload)
    assert isinstance(instance.scope_details, LinkScope)


def test_resource_details_get_model_00150():
    """
    # Summary
    ResourceDetailsGetModel identifiers ClassVar contains resource_id.
    """
    assert "resource_id" in ResourceDetailsGetModel.identifiers


# =============================================================================
# ResourceDetailsPostModel
# =============================================================================


def test_resource_details_post_model_00100():
    """
    # Summary
    ResourceDetailsPostModel requires pool_name and scope_details.
    """
    payload = {
        "poolName": "LOOPBACK_POOL",
        "scopeDetails": {"scopeType": "fabric", "fabricName": "FabricA"},
    }
    with does_not_raise():
        instance = ResourceDetailsPostModel(**payload)
    assert instance.pool_name == "LOOPBACK_POOL"
    assert isinstance(instance.scope_details, FabricScopePost)


def test_resource_details_post_model_00110():
    """
    # Summary
    ResourceDetailsPostModel raises ValidationError when pool_name is missing.
    """
    from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import (
        ValidationError,
    )

    with pytest.raises((ValidationError, TypeError)):
        ResourceDetailsPostModel(
            **{"scopeDetails": {"scopeType": "fabric", "fabricName": "F1"}}
        )


def test_resource_details_post_model_00120():
    """
    # Summary
    ResourceDetailsPostModel.to_payload() includes all set fields.
    """
    payload = {
        "poolName": "MY_POOL",
        "scopeDetails": {"scopeType": "device", "switchId": "SN123"},
        "entityName": "Router1",
        "resourceValue": "192.168.0.1",
    }
    instance = ResourceDetailsPostModel(**payload)
    result = instance.to_payload()
    assert result["poolName"] == "MY_POOL"
    assert result["entityName"] == "Router1"


def test_resource_details_post_model_00130():
    """
    # Summary
    ResourceDetailsPostModel.from_response() creates an instance from a dict.
    """
    response = {
        "poolName": "VLAN_POOL",
        "scopeDetails": {
            "scopeType": "devicePair",
            "srcSwitchId": "A",
            "dstSwitchId": "B",
        },
    }
    instance = ResourceDetailsPostModel.from_response(response)
    assert instance.pool_name == "VLAN_POOL"
    assert isinstance(instance.scope_details, DevicePairScopePost)


def test_resource_details_post_model_00140():
    """
    # Summary
    ResourceDetailsPostModel vrf_name defaults to "default".
    """
    payload = {
        "poolName": "P",
        "scopeDetails": {"scopeType": "fabric", "fabricName": "F"},
    }
    instance = ResourceDetailsPostModel(**payload)
    assert instance.vrf_name == "default"


# =============================================================================
# AllocateResourcesRequestModel
# =============================================================================


def test_allocate_resources_request_model_00100():
    """
    # Summary
    AllocateResourcesRequestModel wraps a list of ResourceDetailsPostModel.
    """
    payload = {
        "resources": [
            {
                "poolName": "POOL_A",
                "scopeDetails": {"scopeType": "fabric", "fabricName": "F1"},
            }
        ]
    }
    instance = AllocateResourcesRequestModel(**payload)
    assert len(instance.resources) == 1
    assert instance.resources[0].pool_name == "POOL_A"


def test_allocate_resources_request_model_00110():
    """
    # Summary
    AllocateResourcesRequestModel.to_payload() serialises the full structure.
    """
    payload = {
        "resources": [
            {
                "poolName": "POOL_B",
                "scopeDetails": {"scopeType": "device", "switchId": "SN1"},
                "entityName": "switch1",
            }
        ]
    }
    instance = AllocateResourcesRequestModel(**payload)
    result = instance.to_payload()
    assert "resources" in result
    assert result["resources"][0]["poolName"] == "POOL_B"


# =============================================================================
# AllocateResourcesResponseModel
# =============================================================================


def test_allocate_resources_response_model_00100():
    """
    # Summary
    AllocateResourcesResponseModel defaults to an empty resources list.
    """
    instance = AllocateResourcesResponseModel()
    assert instance.resources == []


def test_allocate_resources_response_model_00110():
    """
    # Summary
    AllocateResourcesResponseModel.from_response() parses a 207 response.
    """
    response = {
        "resources": [
            {
                "poolName": "P1",
                "resourceId": 100,
                "status": "SUCCESS",
                "scopeDetails": {"scopeType": "fabric", "fabricName": "F1"},
            }
        ]
    }
    instance = AllocateResourcesResponseModel.from_response(response)
    assert len(instance.resources) == 1
    assert instance.resources[0].status == "SUCCESS"
    assert instance.resources[0].resource_id == 100


# =============================================================================
# RemoveResourcesByIdRequestModel
# =============================================================================


def test_remove_resources_by_id_request_model_00100():
    """
    # Summary
    RemoveResourcesByIdRequestModel wraps a list of integer IDs.
    """
    instance = RemoveResourcesByIdRequestModel(**{"resourceIds": [1, 2, 3]})
    assert instance.resource_ids == [1, 2, 3]


def test_remove_resources_by_id_request_model_00110():
    """
    # Summary
    RemoveResourcesByIdRequestModel.to_payload() serialises with alias.
    """
    instance = RemoveResourcesByIdRequestModel(**{"resourceIds": [10]})
    result = instance.to_payload()
    assert result.get("resourceIds") == [10]


# =============================================================================
# RemoveResourcesResponseItem
# =============================================================================


def test_remove_resources_response_item_00100():
    """
    # Summary
    RemoveResourcesResponseItem stores status and message.
    """
    instance = RemoveResourcesResponseItem(
        **{"resourceValue": "10.0.0.1", "status": "SUCCESS", "message": None}
    )
    assert instance.resource_value == "10.0.0.1"
    assert instance.status == "SUCCESS"


# =============================================================================
# RemoveResourcesResponseModel
# =============================================================================


def test_remove_resources_response_model_00100():
    """
    # Summary
    RemoveResourcesResponseModel defaults to an empty resources list.
    """
    instance = RemoveResourcesResponseModel()
    assert instance.resources == []


def test_remove_resources_response_model_00110():
    """
    # Summary
    RemoveResourcesResponseModel.from_response() parses a 207 response.
    """
    response = {
        "resources": [
            {"resourceValue": "10.0.0.1", "status": "SUCCESS"},
            {"resourceValue": "10.0.0.2", "status": "ERROR", "message": "Not found"},
        ]
    }
    instance = RemoveResourcesResponseModel.from_response(response)
    assert len(instance.resources) == 2
    assert instance.resources[1].message == "Not found"


# =============================================================================
# RemoveResourceByDetailsResponseModel
# =============================================================================


def test_remove_resource_by_details_response_model_00100():
    """
    # Summary
    RemoveResourceByDetailsResponseModel stores the status field.
    """
    instance = RemoveResourceByDetailsResponseModel(**{"status": "SUCCESS"})
    assert instance.status == "SUCCESS"


def test_remove_resource_by_details_response_model_00110():
    """
    # Summary
    RemoveResourceByDetailsResponseModel.from_response() creates an instance.
    """
    response = {"status": "DELETED"}
    instance = RemoveResourceByDetailsResponseModel.from_response(response)
    assert instance.status == "DELETED"


# =============================================================================
# ResourcesResponseModel
# =============================================================================


def test_resources_response_model_00100():
    """
    # Summary
    ResourcesResponseModel defaults to an empty list.
    """
    instance = ResourcesResponseModel()
    assert instance.resources == []


def test_resources_response_model_00110():
    """
    # Summary
    ResourcesResponseModel nests multiple ResourceDetailsGetModel instances.
    """
    payload = {
        "resources": [
            {"resourceId": 1, "poolName": "P1"},
            {"resourceId": 2, "poolName": "P2"},
        ]
    }
    instance = ResourcesResponseModel(**payload)
    assert len(instance.resources) == 2
    assert instance.resources[0].resource_id == 1


# =============================================================================
# ResourceDataBase (nested base)
# =============================================================================


def test_resource_data_base_00100():
    """
    # Summary
    ResourceDataBase can be instantiated with defaults.
    """
    with does_not_raise():
        instance = ResourceDataBase()
    assert instance.pool_name is None
    assert instance.vrf_name == "default"
    assert instance.is_pre_allocated is False


def test_resource_data_base_00110():
    """
    # Summary
    ResourceDataBase accepts DeviceInterfaceScope as scope_details.
    """
    payload = {
        "scopeDetails": {
            "scopeType": "deviceInterface",
            "switchName": "Sw1",
            "switchId": "SN123",
            "switchIp": "10.1.1.1",
            "interfaceName": "Eth1/1",
        }
    }
    instance = ResourceDataBase(**payload)
    assert isinstance(instance.scope_details, DeviceInterfaceScope)


# =============================================================================
# ResourceDataBasePost (nested base for POST)
# =============================================================================


def test_resource_data_base_post_00100():
    """
    # Summary
    ResourceDataBasePost defaults vrf_name to "default".
    """
    with does_not_raise():
        instance = ResourceDataBasePost()
    assert instance.vrf_name == "default"


def test_resource_data_base_post_00110():
    """
    # Summary
    ResourceDataBasePost accepts DevicePairScopePost as scope_details.
    """
    payload = {
        "poolName": "P",
        "scopeDetails": {
            "scopeType": "devicePair",
            "srcSwitchId": "S1",
            "dstSwitchId": "S2",
        },
    }
    instance = ResourceDataBasePost(**payload)
    assert isinstance(instance.scope_details, DevicePairScopePost)


# =============================================================================
# ResourceDataBasePostResponse
# =============================================================================


def test_resource_data_base_post_response_00100():
    """
    # Summary
    ResourceDataBasePostResponse captures create_timestamp, status, and message.
    """
    payload = {
        "poolName": "POOL",
        "resourceId": 5,
        "createTimestamp": "2026-03-11T00:00:00Z",
        "status": "SUCCESS",
        "message": None,
    }
    instance = ResourceDataBasePostResponse(**payload)
    assert instance.create_timestamp == "2026-03-11T00:00:00Z"
    assert instance.status == "SUCCESS"
    assert instance.resource_id == 5


# =============================================================================
# UnusedVlanResponseModel
# =============================================================================


def test_unused_vlan_response_model_00100():
    """
    # Summary
    UnusedVlanResponseModel defaults both lists to None.
    """
    instance = UnusedVlanResponseModel()
    assert instance.unused_vlans is None
    assert instance.unused_global_vlans is None


def test_unused_vlan_response_model_00110():
    """
    # Summary
    UnusedVlanResponseModel accepts lists of integers via aliases.
    """
    payload = {"unusedVlans": [100, 101, 102], "unusedGlobalVlans": [200, 201]}
    instance = UnusedVlanResponseModel(**payload)
    assert instance.unused_vlans == [100, 101, 102]
    assert instance.unused_global_vlans == [200, 201]


def test_unused_vlan_response_model_00120():
    """
    # Summary
    UnusedVlanResponseModel.from_response() creates an instance from a dict.
    """
    response = {"unusedVlans": [10, 20], "unusedGlobalVlans": []}
    instance = UnusedVlanResponseModel.from_response(response)
    assert 10 in instance.unused_vlans


def test_unused_vlan_response_model_00130():
    """
    # Summary
    UnusedVlanResponseModel.to_payload() omits None fields.
    """
    instance = UnusedVlanResponseModel(**{"unusedVlans": [300, 301]})
    payload = instance.to_payload()
    assert "unusedVlans" in payload
    assert "unusedGlobalVlans" not in payload
