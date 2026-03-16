# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ResourceCreateBatchRequestModel - Batch request model for resource creation.

COMPOSITE model: contains List[CreateResourceRequest].

Endpoint: POST /fabrics/{fabricName}/resources
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.CreateResourceRequestModel import (
    CreateResourceRequest,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class ResourceCreateBatchRequest(NDBaseModel):
    """
    Request body for POST /fabrics/{fabricName}/resources using Ansible-style config.

    Composite: contains List[CreateResourceRequest].
    Each item is validated with CreateResourceRequest before submission.
    """

    identifiers: ClassVar[List[str]] = []

    resources: List[CreateResourceRequest] = Field(
        ..., description="Array of resource configs to allocate"
    )

    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        return self.model_dump(by_alias=True, exclude_none=True)


__all__ = ["ResourceCreateBatchRequest"]
