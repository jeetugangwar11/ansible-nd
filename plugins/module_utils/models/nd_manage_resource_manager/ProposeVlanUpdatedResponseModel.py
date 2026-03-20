# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ProposeVlanResponse - Response model for proposeVlan endpoint.

Standalone model (no composite model fields).

Endpoint: GET /fabrics/{fabricName}/proposeVlan
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Self

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class ProposeVlanResponse(NDBaseModel):
    """
    Response for GET /fabrics/{fabricName}/proposeVlan (updated).
    """

    identifiers: ClassVar[List[str]] = []

    propose_vlan: Optional[int] = Field(
        default=None,
        alias="proposeVlan",
        description="Next available VLAN ID across all switches in the fabric",
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


__all__ = ["ProposeVlanResponse"]
