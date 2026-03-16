# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
PoolsListResponse - Response model for list-all-pools endpoint.

COMPOSITE model: contains List[PoolDataUpdatedModel].

Endpoint: GET /fabrics/{fabricName}/pools
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.PoolDataUpdatedModel import (
    PoolDataUpdatedModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class PoolsListResponse(NDBaseModel):
    """
    Response body for GET /fabrics/{fabricName}/pools (updated).

    Composite: contains List[PoolDataUpdatedModel].
    """

    identifiers: ClassVar[List[str]] = []

    pools: List[PoolDataUpdatedModel] = Field(
        default_factory=list, description="List of pool data"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Response metadata"
    )


__all__ = ["PoolsListResponse"]
