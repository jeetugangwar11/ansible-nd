# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Pydantic Models for Resource Management Operations.

Generated from OpenAPI schema (manage.json) for Nexus Dashboard Manage APIs v1.1.332.
These models provide type-safe representations of the API request/response payloads
for resource management, including pools, VLANs, and resource allocation operations.

Usage:
    from ansible_collections.cisco.nd.plugins.module_utils.models.resource__manager_models import (
        PoolType,
        ScopeType,
        VlanType,
        PoolDataModel,
        ProposeVlanResponseModel,
        ResourceDetailsGetModel,
        ResourceDetailsPostModel,
        UnusedVlanResponseModel,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
from enum import Enum
from ipaddress import ip_address, ip_network
from typing import List, Dict, Any, Optional, ClassVar, Literal, Union
from typing_extensions import Self
from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import Field, field_validator, model_validator

from ansible_collections.cisco.nd.plugins.module_utils.models.base import (
    NDBaseModel,
    NDNestedModel,
)

# from models.base import NDBaseModel, NDNestedModel


# =============================================================================
# ENUMS - Extracted from OpenAPI Schema components/schemas
# =============================================================================


class PoolType(str, Enum):
    """
    Pool type enumeration.

    Based on: components/schemas/poolData.poolType
    Description: Indicates the type of resource being allocated and managed under the pool
    """

    IP_POOL = "ipPool"
    SUBNET_POOL = "subnetPool"
    ID_POOL = "idPool"

    @classmethod
    def choices(cls) -> List[str]:
        """Return list of valid choices."""
        return [e.value for e in cls]


class ScopeType(str, Enum):
    """
    Scope type enumeration.

    Based on: components/schemas discriminator scopeType
    Description: Indicates the scope level for the resource under which the uniqueness is maintained
    """

    FABRIC = "fabric"
    DEVICE = "device"
    DEVICE_INTERFACE = "deviceInterface"
    LINK = "link"
    DEVICE_PAIR = "devicePair"

    @classmethod
    def choices(cls) -> List[str]:
        """Return list of valid choices."""
        return [e.value for e in cls]


class VlanType(str, Enum):
    """
    VLAN type enumeration.

    Based on: API parameter vlanType
    Description: The type of VLAN to query
    """

    NETWORK_VLAN = "networkVlan"
    VRF_VLAN = "vrfVlan"
    SERVICE_NETWORK_VLAN = "serviceNetworkVlan"
    VPC_PEER_LINK_VLAN = "vpcPeerLinkVlan"

    @classmethod
    def choices(cls) -> List[str]:
        """Return list of valid choices."""
        return [e.value for e in cls]


# =============================================================================
# VALIDATOR MIXIN
# =============================================================================


class ResourceValidators:
    """
    Common validators for resource-related fields.
    """

    @staticmethod
    def validate_ip_address(v: Optional[str]) -> Optional[str]:
        """Validate IPv4 or IPv6 address."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        try:
            ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")

    @staticmethod
    def validate_cidr(v: Optional[str]) -> Optional[str]:
        """Validate CIDR notation (IP/mask)."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        if "/" not in v:
            raise ValueError(f"CIDR notation required (IP/mask format): {v}")
        try:
            ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError(f"Invalid CIDR format: {v}")

    @staticmethod
    def validate_pool_range(v: Optional[str]) -> Optional[str]:
        """Validate pool range format (e.g., '2300-2600' or '10.1.1.0/24')."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        # Check if it's a CIDR notation
        if "/" in v:
            return ResourceValidators.validate_cidr(v)
        # Check if it's a range (e.g., '2300-2600')
        if "-" in v:
            parts = v.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    if start >= end:
                        raise ValueError(f"Invalid range: start ({start}) must be less than end ({end})")
                    return v
                except ValueError as e:
                    raise ValueError(f"Invalid range format: {v}. Error: {str(e)}")
        return v


# =============================================================================
# NESTED MODELS - Scope Details
# =============================================================================


class FabricScope(NDNestedModel):
    """
    Scope details for resources that are under fabric scope.

    Based on: components/schemas/fabricScope
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.FABRIC] = Field(
        ScopeType.FABRIC,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    fabric_name: Optional[str] = Field(default=None, alias="fabricName", description="Indicates the fabric name")


class DeviceScope(NDNestedModel):
    """
    Scope details for resources that are under device scope.

    Based on: components/schemas/deviceScope
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.DEVICE] = Field(
        ScopeType.DEVICE,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    switch_name: Optional[str] = Field(default=None, alias="switchName", description="Indicates the name of the switch")
    switch_id: Optional[str] = Field(default=None, alias="switchId", description="Indicates the serial Number of the switch")
    switch_ip: Optional[str] = Field(default=None, alias="switchIp", description="IP Address of the switch")

    @field_validator("switch_ip", mode="before")
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        return ResourceValidators.validate_ip_address(v)


class DeviceInterfaceScope(NDNestedModel):
    """
    Scope details for resources that are under deviceInterface scope.

    Based on: components/schemas/deviceInterfaceScope
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.DEVICE_INTERFACE] = Field(
        ScopeType.DEVICE_INTERFACE,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    switch_name: Optional[str] = Field(default=None, alias="switchName", description="Indicates the name of the switch")
    switch_id: Optional[str] = Field(default=None, alias="switchId", description="Indicates the serial Number of the switch")
    switch_ip: Optional[str] = Field(default=None, alias="switchIp", description="IP Address of the switch")
    interface_name: Optional[str] = Field(default=None, alias="interfaceName", description="Interface name")

    @field_validator("switch_ip", mode="before")
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        return ResourceValidators.validate_ip_address(v)


class LinkScope(NDNestedModel):
    """
    Scope details for resources that are under link scope.

    Based on: components/schemas/linkScope
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.LINK] = Field(
        ScopeType.LINK,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    src_switch_name: Optional[str] = Field(default=None, alias="srcSwitchName", description="Indicates the name of the Source switch in the link")
    src_switch_id: Optional[str] = Field(default=None, alias="srcSwitchId", description="Indicates the serial Number of the source switch")
    src_switch_ip: Optional[str] = Field(default=None, alias="srcSwitchIp", description="IP Address of the source switch")
    src_interface_name: Optional[str] = Field(default=None, alias="srcInterfaceName", description="Source switch's interface name")
    dst_switch_name: Optional[str] = Field(default=None, alias="dstSwitchName", description="Indicates the name of the Destination switch on the link")
    dst_switch_id: Optional[str] = Field(default=None, alias="dstSwitchId", description="Indicates the serial Number of the Destination switch")
    dst_switch_ip: Optional[str] = Field(default=None, alias="dstSwitchIp", description="IP Address of the Destination switch")
    dst_interface_name: Optional[str] = Field(default=None, alias="dstInterfaceName", description="Destination switch's interface name")
    src_resource_id: Optional[int] = Field(default=None, alias="srcResourceId", description="Unique identifier of the allocated resource on the source switch")
    dst_resource_id: Optional[int] = Field(
        default=None, alias="dstResourceId", description="Unique identifier of the allocated resource on the destination switch"
    )

    @field_validator("src_switch_ip", "dst_switch_ip", mode="before")
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        return ResourceValidators.validate_ip_address(v)


class DevicePairScope(NDNestedModel):
    """
    Scope details for resources that are under devicePair scope.

    Based on: components/schemas/devicePairScope
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.DEVICE_PAIR] = Field(
        ScopeType.DEVICE_PAIR,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    src_switch_name: Optional[str] = Field(default=None, alias="srcSwitchName", description="Indicates the name of the Source switch in the devicePair")
    src_switch_id: Optional[str] = Field(default=None, alias="srcSwitchId", description="Indicates the serial Number of the source switch")
    src_switch_ip: Optional[str] = Field(default=None, alias="srcSwitchIp", description="IP Address of the source switch")
    dst_switch_name: Optional[str] = Field(default=None, alias="dstSwitchName", description="Indicates the name of the Destination switch on the link")
    dst_switch_id: Optional[str] = Field(default=None, alias="dstSwitchId", description="Indicates the serial Number of the Destination switch")
    dst_switch_ip: Optional[str] = Field(default=None, alias="dstSwitchIp", description="IP Address of the Destination switch")
    src_resource_id: Optional[int] = Field(default=None, alias="srcResourceId", description="Unique identifier of the allocated resource on the source switch")
    dst_resource_id: Optional[int] = Field(
        default=None, alias="dstResourceId", description="Unique identifier of the allocated resource on the destination switch"
    )
    peer_resource_id: Optional[int] = Field(
        default=None, alias="peerResourceId", description="Unique identifier of the allocated resource on the destination switch"
    )

    @field_validator("src_switch_ip", "dst_switch_ip", mode="before")
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        return ResourceValidators.validate_ip_address(v)


# Scope POST models (for POST requests, some have different required fields)


class FabricScopePost(NDNestedModel):
    """
    Scope details for resources that are under fabric scope (POST).

    Based on: components/schemas/fabricScopePost
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.FABRIC] = Field(
        ...,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    fabric_name: str = Field(..., alias="fabricName", description="Indicates the fabric name")


class DeviceScopePost(NDNestedModel):
    """
    Scope details for resources that are under device scope (POST).

    Based on: components/schemas/deviceScopePost
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.DEVICE] = Field(
        ...,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    switch_id: str = Field(..., alias="switchId", description="Indicates the serial Number of the switch")


class DeviceInterfaceScopePost(NDNestedModel):
    """
    Scope details for resources that are under deviceInterface scope (POST).

    Based on: components/schemas/deviceInterfaceScopePost
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.DEVICE_INTERFACE] = Field(
        ...,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    switch_id: str = Field(..., alias="switchId", description="Indicates the serial Number of the switch")
    interface_name: str = Field(..., alias="interfaceName", description="Interface name")


class LinkScopePost(NDNestedModel):
    """
    Scope details for resources that are under link scope (POST).

    Based on: components/schemas/linkScopePost
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.LINK] = Field(
        ...,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    src_switch_id: str = Field(..., alias="srcSwitchId", description="Indicates the serial Number of the source switch")
    src_interface_name: str = Field(..., alias="srcInterfaceName", description="Source switch's interface name")
    dst_switch_id: str = Field(..., alias="dstSwitchId", description="Indicates the serial Number of the Destination switch")
    dst_interface_name: str = Field(..., alias="dstInterfaceName", description="Destination switch's interface name")


class DevicePairScopePost(NDNestedModel):
    """
    Scope details for resources that are under devicePair scope (POST).

    Based on: components/schemas/devicePairScopePost
    """

    identifiers: ClassVar[List[str]] = []

    scope_type: Literal[ScopeType.DEVICE_PAIR] = Field(
        ...,
        alias="scopeType",
        description="Indicates the scope level for the resource under which the uniqueness is maintained",
    )
    src_switch_id: str = Field(..., alias="srcSwitchId", description="Indicates the serial Number of the source switch")
    dst_switch_id: str = Field(..., alias="dstSwitchId", description="Indicates the serial Number of the Destination switch")


# =============================================================================
# POOL MODELS
# =============================================================================


class PoolDataModel(NDBaseModel):
    """
    Pool Schema for IP and SUBNET Pools that are created in Resource Manager.

    Based on: components/schemas/poolData
    Path: GET /fabrics/{fabricName}/pools
    """

    identifiers: ClassVar[List[str]] = ["pool_id", "pool_name"]
    exclude_from_diff: ClassVar[List[str]] = []

    pool_id: Optional[int] = Field(default=None, alias="poolId", description="Unique identifier of the pool")
    pool_name: Optional[str] = Field(default=None, alias="poolName", description="Name of the pool")
    fabric_name: Optional[str] = Field(default=None, alias="fabricName", description="Fabric name under which the pool's scope is valid")
    vrf_name: Optional[str] = Field(
        default=None,
        alias="vrfName",
        description="default for the pools that are managed across all VRFs. And contains the name of VRF under which the pool's scope is managed",
    )
    pool_type: Optional[PoolType] = Field(
        default=None, alias="poolType", description="Indicates the type of resource being allocated and managed under the pool"
    )
    pool_range: Optional[str] = Field(default=None, alias="poolRange", description="Range of values which are generated from the pool")
    overlap_allowed: Optional[bool] = Field(
        default=False,
        alias="overlapAllowed",
        description="true duplicate values for resources on the pool is permitted and false indicates duplicate of resource allocation is thrown error during allocation",
    )

    @field_validator("pool_range", mode="before")
    @classmethod
    def validate_range(cls, v: Optional[str]) -> Optional[str]:
        return ResourceValidators.validate_pool_range(v)

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


class PoolsResponseModel(NDNestedModel):
    """
    Response body for get all pools API call.

    Based on: Response schema for GET /fabrics/{fabricName}/pools
    """

    identifiers: ClassVar[List[str]] = []

    pools: List[PoolDataModel] = Field(default_factory=list, description="List of pool data")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")


# =============================================================================
# PROPOSE VLAN MODELS
# =============================================================================


class ProposeVlanResponseModel(NDNestedModel):
    """
    The next available VLAN ID for the given VLAN type across all switches in the fabric.

    Based on: components/schemas/proposeVlanResponse
    Path: GET /fabrics/{fabricName}/proposeVlan
    """

    identifiers: ClassVar[List[str]] = []

    propose_vlan: Optional[int] = Field(default=None, alias="proposeVlan", description="Next available VLAN across all switches")

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


# =============================================================================
# RESOURCE MODELS
# =============================================================================


class ResourceDataBase(NDNestedModel):
    """
    Base allocation details of the resource.

    Based on: components/schemas/resourceDataBase
    """

    identifiers: ClassVar[List[str]] = []

    pool_name: Optional[str] = Field(default=None, alias="poolName", description="Pool under which the resource is allocated")
    scope_details: Optional[Union[FabricScope, DeviceScope, DeviceInterfaceScope, LinkScope, DevicePairScope]] = Field(
        default=None, alias="scopeDetails", description="Based on Scope type the scope details are taken"
    )
    is_pre_allocated: Optional[bool] = Field(
        default=False,
        alias="isPreAllocated",
        description="Set it to true if the resource is pre-allocated to an entity i.e resource is reserved",
    )
    entity_name: Optional[str] = Field(default=None, alias="entityName", description="Indicates the Name by which the resource is allocated")
    resource_value: Optional[str] = Field(default=None, alias="resourceValue", description="Resource can be an ID, IP or Subnet resource being managed in RM")
    resource_id: Optional[int] = Field(default=None, alias="resourceId", description="Unique identifier of the allocated resource")
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="shows the VRf name if the pool is a VRF level pool and the resource allocation is done on VRF level",
    )


class ResourceDetailsGetModel(NDBaseModel):
    """
    Schema for GET APIs that contains the resource allocation details.

    Based on: components/schemas/resourceDetailsGet
    Path: GET /fabrics/{fabricName}/resources
    Path: GET /fabrics/{fabricName}/resources/{resourceId}
    """

    identifiers: ClassVar[List[str]] = ["resource_id"]
    exclude_from_diff: ClassVar[List[str]] = []

    # From resourceDataBase
    pool_name: Optional[str] = Field(default=None, alias="poolName", description="Pool under which the resource is allocated")
    scope_details: Optional[Union[FabricScope, DeviceScope, DeviceInterfaceScope, LinkScope, DevicePairScope]] = Field(
        default=None, alias="scopeDetails", description="Based on Scope type the scope details are taken"
    )
    is_pre_allocated: Optional[bool] = Field(
        default=False,
        alias="isPreAllocated",
        description="Set it to true if the resource is pre-allocated to an entity i.e resource is reserved",
    )
    entity_name: Optional[str] = Field(default=None, alias="entityName", description="Indicates the Name by which the resource is allocated")
    resource_value: Optional[str] = Field(default=None, alias="resourceValue", description="Resource can be an ID, IP or Subnet resource being managed in RM")
    resource_id: Optional[int] = Field(default=None, alias="resourceId", description="Unique identifier of the allocated resource")
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="shows the VRf name if the pool is a VRF level pool and the resource allocation is done on VRF level",
    )

    # Additional fields from resourceDetailsGet
    create_timestamp: Optional[str] = Field(default=None, alias="createTimestamp", description="Time when the resource was allocated or reserved")

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


class ResourceDataBasePost(NDNestedModel):
    """
    Allocation details of the resource for POST requests.

    Based on: components/schemas/resourceDataBasePost
    """

    identifiers: ClassVar[List[str]] = []

    pool_name: Optional[str] = Field(default=None, alias="poolName", description="Pool under which the resource is allocated")
    scope_details: Optional[Union[FabricScopePost, DeviceScopePost, DeviceInterfaceScopePost, LinkScopePost, DevicePairScopePost]] = Field(
        default=None, alias="scopeDetails", description="Based on Scope type the scope details are taken"
    )
    is_pre_allocated: Optional[bool] = Field(
        default=False,
        alias="isPreAllocated",
        description="Set it to true if the resource is pre-allocated to an entity i.e resource is reserved",
    )
    entity_name: Optional[str] = Field(default=None, alias="entityName", description="Indicates the Name by which the resource is allocated")
    resource_value: Optional[str] = Field(default=None, alias="resourceValue", description="Resource can be an ID, IP or Subnet resource being managed in RM")
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="shows the VRf name if the pool is a VRF level pool and the resource allocation is done on VRF level",
    )


class ResourceDetailsPostModel(NDBaseModel):
    """
    Schema for POST APIs to allocate resource.

    Based on: components/schemas/resourceDetailsPost
    Path: POST /fabrics/{fabricName}/resources
    Path: POST /fabrics/{fabricName}/resources/actions/removeResource
    """

    identifiers: ClassVar[List[str]] = []
    exclude_from_diff: ClassVar[List[str]] = []

    # From resourceDataBasePost
    pool_name: str = Field(..., alias="poolName", description="Pool under which the resource is allocated")
    scope_details: Union[FabricScopePost, DeviceScopePost, DeviceInterfaceScopePost, LinkScopePost, DevicePairScopePost] = Field(
        ..., alias="scopeDetails", description="Based on Scope type the scope details are taken"
    )
    is_pre_allocated: Optional[bool] = Field(
        default=False,
        alias="isPreAllocated",
        description="Set it to true if the resource is pre-allocated to an entity i.e resource is reserved",
    )
    entity_name: Optional[str] = Field(default=None, alias="entityName", description="Indicates the Name by which the resource is allocated")
    resource_value: Optional[str] = Field(default=None, alias="resourceValue", description="Resource can be an ID, IP or Subnet resource being managed in RM")
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="shows the VRf name if the pool is a VRF level pool and the resource allocation is done on VRF level",
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


class AllocateResourcesRequestModel(NDNestedModel):
    """
    Request body for allocating resources.

    Based on: Request schema for POST /fabrics/{fabricName}/resources
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[ResourceDetailsPostModel] = Field(..., description="Array of resources that are needed for resource allocation")

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)


class ResourceDataBasePostResponse(NDNestedModel):
    """
    Allocated resources with status details.

    Based on: components/schemas/resourceDataBasePostResponse
    """

    identifiers: ClassVar[List[str]] = []

    # From resourceDataBase
    pool_name: Optional[str] = Field(default=None, alias="poolName", description="Pool under which the resource is allocated")
    scope_details: Optional[Union[FabricScope, DeviceScope, DeviceInterfaceScope, LinkScope, DevicePairScope]] = Field(
        default=None, alias="scopeDetails", description="Based on Scope type the scope details are taken"
    )
    is_pre_allocated: Optional[bool] = Field(
        default=False,
        alias="isPreAllocated",
        description="Set it to true if the resource is pre-allocated to an entity i.e resource is reserved",
    )
    entity_name: Optional[str] = Field(default=None, alias="entityName", description="Indicates the Name by which the resource is allocated")
    resource_value: Optional[str] = Field(default=None, alias="resourceValue", description="Resource can be an ID, IP or Subnet resource being managed in RM")
    resource_id: Optional[int] = Field(default=None, alias="resourceId", description="Unique identifier of the allocated resource")
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="shows the VRf name if the pool is a VRF level pool and the resource allocation is done on VRF level",
    )

    # Additional response fields
    create_timestamp: Optional[str] = Field(default=None, alias="createTimestamp", description="Time when the resource was allocated or reserved")
    status: Optional[str] = Field(default=None, description="status of the resource create request")
    message: Optional[str] = Field(default=None, description="Optional message details describing the resource create error")


class AllocateResourcesResponseModel(NDNestedModel):
    """
    Response body for allocate resources API call (multi-status response).

    Based on: Response schema for POST /fabrics/{fabricName}/resources (207 response)
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[ResourceDataBasePostResponse] = Field(default_factory=list, description="Response for Bulk Create resources request")

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


class ResourcesResponseModel(NDNestedModel):
    """
    Response body for get resources API call.

    Based on: Response schema for GET /fabrics/{fabricName}/resources
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[ResourceDetailsGetModel] = Field(default_factory=list, description="List of resource data")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")


# =============================================================================
# RESOURCE ACTIONS MODELS
# =============================================================================


class RemoveResourcesByIdRequestModel(NDNestedModel):
    """
    Request body for removing resources by ID.

    Based on: Request schema for POST /fabrics/{fabricName}/resources/actions/remove
    """

    identifiers: ClassVar[List[str]] = []

    resource_ids: List[int] = Field(..., alias="resourceIds", description="Array of resource Ids")

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)


class RemoveResourcesResponseItem(NDNestedModel):
    """
    Individual resource removal response item.

    Based on: Response item schema for POST /fabrics/{fabricName}/resources/actions/remove
    """

    identifiers: ClassVar[List[str]] = []

    resource_value: Optional[str] = Field(default=None, alias="resourceValue", description="unique identifier of the resource")
    status: Optional[str] = Field(default=None, description="status of the resource Delete request")
    message: Optional[str] = Field(default=None, description="Optional message details describing the resource delete error")


class RemoveResourcesResponseModel(NDNestedModel):
    """
    Response body for remove resources API call (multi-status response).

    Based on: Response schema for POST /fabrics/{fabricName}/resources/actions/remove (207 response)
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[RemoveResourcesResponseItem] = Field(default_factory=list, description="Response for Bulk Delete resources request")

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


class RemoveResourceByDetailsResponseModel(NDNestedModel):
    """
    Response body for remove resource by allocation details.

    Based on: Response schema for POST /fabrics/{fabricName}/resources/actions/removeResource (200 response)
    """

    identifiers: ClassVar[List[str]] = []

    status: Optional[str] = Field(default=None, description="Status of the release request")

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


# =============================================================================
# UNUSED VLAN MODELS
# =============================================================================


class UnusedVlanResponseModel(NDNestedModel):
    """
    Contains two lists of unused vlan IDs. 1. Dynamic range vlan IDs. 2. Global range vlan IDs.

    Based on: components/schemas/unusedVlanResponse
    Path: GET /fabrics/{fabricName}/unusedVlans
    """

    identifiers: ClassVar[List[str]] = []

    unused_vlans: Optional[List[int]] = Field(default=None, alias="unusedVlans", description="Array of unused vlan IDs from the dynamic vlan ID range")
    unused_global_vlans: Optional[List[int]] = Field(
        default=None, alias="unusedGlobalVlans", description="Array of unused vlan IDs from the global vlan ID range"
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PoolType",
    "ScopeType",
    "VlanType",
    # Validators
    "ResourceValidators",
    # Scope Models (GET)
    "FabricScope",
    "DeviceScope",
    "DeviceInterfaceScope",
    "LinkScope",
    "DevicePairScope",
    # Scope Models (POST)
    "FabricScopePost",
    "DeviceScopePost",
    "DeviceInterfaceScopePost",
    "LinkScopePost",
    "DevicePairScopePost",
    # Pool Models
    "PoolDataModel",
    "PoolsResponseModel",
    # Propose VLAN Models
    "ProposeVlanResponseModel",
    # Resource Base Models
    "ResourceDataBase",
    "ResourceDataBasePost",
    "ResourceDataBasePostResponse",
    # Resource Models (GET)
    "ResourceDetailsGetModel",
    "ResourcesResponseModel",
    # Resource Models (POST)
    "ResourceDetailsPostModel",
    "AllocateResourcesRequestModel",
    "AllocateResourcesResponseModel",
    # Resource Actions Models
    "RemoveResourcesByIdRequestModel",
    "RemoveResourcesResponseItem",
    "RemoveResourcesResponseModel",
    "RemoveResourceByDetailsResponseModel",
    # Unused VLAN Models
    "UnusedVlanResponseModel",
]
