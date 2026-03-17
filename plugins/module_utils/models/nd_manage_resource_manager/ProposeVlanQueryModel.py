# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ProposeVlanQuery - Query parameter model for proposeVlan endpoint.

Standalone model (no composite model fields).

Endpoint: GET /fabrics/{fabricName}/proposeVlan
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.nd_manage_resource_manager import (
    VlanType,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class ProposeVlanQuery(NDBaseModel):
    """
    Query parameters model for GET /fabrics/{fabricName}/proposeVlan.

    The vlanType query parameter is required.
    """

    identifiers: ClassVar[List[str]] = []

    vlan_type: VlanType = Field(
        alias="vlanType",
        description=(
            "The type of VLAN to propose. "
            "One of: networkVlan, vrfVlan, serviceNetworkVlan, vpcPeerLinkVlan."
        ),
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format (used as query params)."""
        return self.model_dump(by_alias=True, exclude_none=True)


__all__ = ["ProposeVlanQuery"]
