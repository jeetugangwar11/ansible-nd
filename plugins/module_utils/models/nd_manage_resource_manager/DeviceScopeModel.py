# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import ClassVar, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class DeviceScope(NDBaseModel):
    """Scope details for resources under Device scope."""

    identifiers: ClassVar[List[str]] = []

    scope_type: str = Field(
        default="device",
        alias="scopeType",
        description="Scope level: device",
    )
    switch_name: Optional[str] = Field(
        default=None,
        alias="switchName",
        description="Name of the switch",
    )
    switch_id: Optional[str] = Field(
        default=None,
        alias="switchId",
        description="Serial number of the switch",
    )
    switch_ip: Optional[str] = Field(
        default=None,
        alias="switchIp",
        description="IP address of the switch",
    )


__all__ = [
    "DeviceScope",
]
