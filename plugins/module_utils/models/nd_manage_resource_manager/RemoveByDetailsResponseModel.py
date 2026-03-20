# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
RemoveByDetailsResponse - Response model for remove-by-details action.

Standalone model (no composite model fields). All fields are primitives.

Endpoint: POST /fabrics/{fabricName}/resources/actions/removeResource
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Self

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class RemoveByDetailsResponse(NDBaseModel):
    """
    Response body for POST /fabrics/{fabricName}/resources/actions/removeResource.
    """

    identifiers: ClassVar[List[str]] = []

    status: Optional[str] = Field(
        default=None,
        description="Status of the resource release request",
    )

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Self:
        """Create model instance from API response."""
        return cls.model_validate(response)


__all__ = ["RemoveByDetailsResponse"]
