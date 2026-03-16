# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
RemoveByIdResponse - Individual item in remove-by-IDs response.

Standalone model (no composite model fields). All fields are primitives.

Endpoint: POST /fabrics/{fabricName}/resources/actions/remove (response item)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import ClassVar, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class RemoveByIdResponse(NDBaseModel):
    """
    Individual resource removal response item for POST .../actions/remove.
    """

    identifiers: ClassVar[List[str]] = []

    resource_value: Optional[str] = Field(
        default=None,
        alias="resourceValue",
        description="Unique value of the removed resource",
    )
    status: Optional[str] = Field(
        default=None,
        description="Status of the resource delete request",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional details describing a resource delete failure",
    )


__all__ = ["RemoveByIdResponse"]
