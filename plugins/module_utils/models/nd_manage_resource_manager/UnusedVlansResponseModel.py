# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
UnusedVlansResponseModel - Response model for unusedVlans endpoint.

Standalone model (no composite model fields). Contains only List[int] fields.

Endpoint: GET /fabrics/{fabricName}/unusedVlans
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Self

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class UnusedVlansResponseModel(NDBaseModel):
    """
    Contains two lists of unused VLAN IDs (updated).

    Path: GET /fabrics/{fabricName}/unusedVlans
    """

    identifiers: ClassVar[List[str]] = []

    unused_vlans: Optional[List[int]] = Field(
        default=None,
        alias="unusedVlans",
        description="Array of unused VLAN IDs from the dynamic VLAN ID range",
    )
    unused_global_vlans: Optional[List[int]] = Field(
        default=None,
        alias="unusedGlobalVlans",
        description="Array of unused VLAN IDs from the global VLAN ID range",
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


__all__ = ["UnusedVlansResponseModel"]
