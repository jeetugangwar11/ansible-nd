# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import ClassVar, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import Field


class LinkScope(NDBaseModel):
    """Scope details for resources under Link scope."""

    identifiers: ClassVar[List[str]] = []

    scope_type: str = Field(
        default="link",
        alias="scopeType",
        description="Scope level: link",
    )
    src_switch_name: Optional[str] = Field(
        default=None,
        alias="srcSwitchName",
        description="Name of the source switch",
    )
    src_switch_id: Optional[str] = Field(
        default=None,
        alias="srcSwitchId",
        description="Serial number of the source switch",
    )
    src_switch_ip: Optional[str] = Field(
        default=None,
        alias="srcSwitchIp",
        description="IP address of the source switch",
    )
    src_interface_name: Optional[str] = Field(
        default=None,
        alias="srcInterfaceName",
        description="Source interface name",
    )
    dst_switch_name: Optional[str] = Field(
        default=None,
        alias="dstSwitchName",
        description="Name of the destination switch",
    )
    dst_switch_id: Optional[str] = Field(
        default=None,
        alias="dstSwitchId",
        description="Serial number of the destination switch",
    )
    dst_switch_ip: Optional[str] = Field(
        default=None,
        alias="dstSwitchIp",
        description="IP address of the destination switch",
    )
    dst_interface_name: Optional[str] = Field(
        default=None,
        alias="dstInterfaceName",
        description="Destination interface name",
    )


__all__ = [
    "LinkScope",
]
