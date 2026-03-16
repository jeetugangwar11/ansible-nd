# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ResourcesResponseModel - Response model for list-all-resources endpoint.

COMPOSITE model: contains List[ResourceGetUpdatedModel].

Endpoint: GET /fabrics/{fabricName}/resources
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.ResourceModel import (
    ResourceModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class ResourcesResponseModel(NDBaseModel):
    """
    Response body for GET /fabrics/{fabricName}/resources (updated).

    Composite: contains List[ResourceModel].
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[ResourceModel] = Field(
        default_factory=list, description="List of resource data"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Response metadata"
    )


__all__ = ["ResourcesResponseModel"]
