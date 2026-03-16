# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ResourceCreateResponse - Individual item returned in the batch-create response.

COMPOSITE model: contains Union[FabricScope, DeviceScope, DeviceInterfaceScope,
LinkScope, DevicePairScope] as the scope_details field.

Endpoint: POST /fabrics/{fabricName}/resources (207 multi-status response item)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import ClassVar, List, Optional, Union

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.DeviceInterfaceScopeModel import (
    DeviceInterfaceScope,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.DevicePairScopeModel import (
    DevicePairScope,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.DeviceScopeModel import (
    DeviceScope,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.FabricScopeModel import (
    FabricScope,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.LinkScopeModel import (
    LinkScope,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class ResourceCreateResponse(NDBaseModel):
    """
    Individual resource allocation response item for POST /fabrics/{fabricName}/resources.

    Composite: scope_details field is a Union of scope models discriminated
    by scopeType.
    """

    identifiers: ClassVar[List[str]] = []

    pool_name: Optional[str] = Field(
        default=None,
        alias="poolName",
        description="Pool under which the resource is allocated",
    )
    scope_details: Optional[
        Union[
            FabricScope, DeviceScope, DeviceInterfaceScope, LinkScope, DevicePairScope
        ]
    ] = Field(
        default=None,
        alias="scopeDetails",
        description="Scope details; discriminated by scopeType",
    )
    is_pre_allocated: Optional[bool] = Field(
        default=False,
        alias="isPreAllocated",
        description="true if the resource is pre-allocated",
    )
    entity_name: Optional[str] = Field(
        default=None,
        alias="entityName",
        description="Name by which the resource is allocated",
    )
    resource_value: Optional[str] = Field(
        default=None,
        alias="resourceValue",
        description="The allocated resource value",
    )
    resource_id: Optional[int] = Field(
        default=None,
        alias="resourceId",
        description="Unique identifier of the allocated resource",
    )
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="VRF name for the resource",
    )
    create_timestamp: Optional[str] = Field(
        default=None,
        alias="createTimestamp",
        description="Timestamp when the resource was allocated",
    )
    status: Optional[str] = Field(
        default=None,
        description="Status of the resource create request",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional details describing a resource create failure",
    )


__all__ = ["ResourceCreateResponse"]
