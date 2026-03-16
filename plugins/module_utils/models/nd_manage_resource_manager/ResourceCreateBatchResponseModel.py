# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ResourceCreateBatchResponse - Batch response model for resource creation.

COMPOSITE model: contains List[ResourceCreateResponse].

Endpoint: POST /fabrics/{fabricName}/resources (207 multi-status response)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List
from typing_extensions import Self

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.CreateResourceResponseModel import (
    ResourceCreateResponse,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class ResourceCreateBatchResponse(NDBaseModel):
    """
    Response body for POST /fabrics/{fabricName}/resources (multi-status 207 response).

    Composite: contains List[ResourceCreateResponse].
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[ResourceCreateResponse] = Field(
        default_factory=list,
        description="Response items for the bulk create resources request",
    )

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


__all__ = ["ResourceCreateBatchResponse"]
