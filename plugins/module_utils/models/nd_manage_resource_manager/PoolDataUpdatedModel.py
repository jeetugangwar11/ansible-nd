# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
PoolData - Standalone model for a single pool resource.

Standalone model (no composite model fields). All fields use primitive types only.

Endpoint: GET /fabrics/{fabricName}/pools (individual pool item)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, Optional
from typing_extensions import Self

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.ResourceValidators import (
    ResourceValidators,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import (
    Field,
    field_validator,
)


class PoolData(NDBaseModel):
    """
    Pool Schema for IP, SUBNET, and ID Pools (updated).

    Path: GET /fabrics/{fabricName}/pools
    """

    identifiers: ClassVar[list] = ["pool_id", "pool_name"]
    exclude_from_diff: ClassVar[list] = []

    pool_id: Optional[int] = Field(
        default=None, alias="poolId", description="Unique identifier of the pool"
    )
    pool_name: Optional[str] = Field(
        default=None, alias="poolName", description="Name of the pool"
    )
    fabric_name: Optional[str] = Field(
        default=None,
        alias="fabricName",
        description="Fabric name under which the pool's scope is valid",
    )
    vrf_name: Optional[str] = Field(
        default=None,
        alias="vrfName",
        description=(
            "'default' for pools managed across all VRFs; "
            "otherwise the name of VRF under which the pool's scope is managed"
        ),
    )
    pool_type: Optional[str] = Field(
        default=None,
        alias="poolType",
        description="Indicates the type of resource being allocated and managed under the pool",
    )
    pool_range: Optional[str] = Field(
        default=None,
        alias="poolRange",
        description="Range of values which are generated from the pool",
    )
    overlap_allowed: Optional[bool] = Field(
        default=False,
        alias="overlapAllowed",
        description=(
            "true: duplicate resource values on the pool are permitted; "
            "false: duplicate resource allocation raises an error"
        ),
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


__all__ = ["PoolData"]
