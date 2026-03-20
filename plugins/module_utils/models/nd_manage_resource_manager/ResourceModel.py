# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ResourceModel - GET response model for a single resource allocation.

COMPOSITE model: contains Union[FabricScope, DeviceScope, DeviceInterfaceScope,
LinkScope, DevicePairScope] as the scope_details field.

Endpoints:
  GET    /fabrics/{fabricName}/resources
  GET    /fabrics/{fabricName}/resources/{resourceId}
  DELETE /fabrics/{fabricName}/resources/{resourceId}
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List, Optional, Union
from typing_extensions import Self

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


class ResourceModel(NDBaseModel):
    """
    Schema for GET APIs that contain resource allocation details (updated).

    Composite: scope_details field is a Union of scope models discriminated
    by scopeType.

    Path: GET    /fabrics/{fabricName}/resources
    Path: GET    /fabrics/{fabricName}/resources/{resourceId}
    Path: DELETE /fabrics/{fabricName}/resources/{resourceId}
    """

    identifiers: ClassVar[List[str]] = ["resource_id"]
    exclude_from_diff: ClassVar[List[str]] = []

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
        description="true if the resource is pre-allocated (reserved) to an entity",
    )
    entity_name: Optional[str] = Field(
        default=None,
        alias="entityName",
        description="Name by which the resource is allocated",
    )
    resource_value: Optional[str] = Field(
        default=None,
        alias="resourceValue",
        description="Resource value: an ID, IP address, or subnet/CIDR",
    )
    resource_id: Optional[int] = Field(
        default=None,
        alias="resourceId",
        description="Unique identifier of the allocated resource",
    )
    vrf_name: Optional[str] = Field(
        default="default",
        alias="vrfName",
        description="VRF name when the pool is VRF-scoped; 'default' otherwise",
    )
    create_timestamp: Optional[str] = Field(
        default=None,
        alias="createTimestamp",
        description="Timestamp when the resource was allocated or reserved",
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


__all__ = ["ResourceModel"]
