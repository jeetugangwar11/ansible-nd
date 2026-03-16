# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
CreateResourceRequest - Ansible-facing config model for resource allocation/deallocation.

Standalone model (no composite model fields). All fields use primitive types
or List[str] only.

Endpoint: POST /fabrics/{fabricName}/resources (input validation layer)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
from ipaddress import ip_address, ip_network
from typing import ClassVar, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.constants import (
    POOL_SCOPE_MAP,
    PoolType,
    ScopeType,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import (
    Field,
    field_validator,
    model_validator,
)


class CreateResourceRequest(NDBaseModel):
    """
    Ansible-facing config model for resource allocation/deallocation.

    Matches the 6 config suboptions from dcnm_resource_manager.py DOCUMENTATION,
    with full per-field and cross-field validation derived from
    dcnm_rm_check_resource_params().

    Field mapping to dcnm_resource_manager.py config suboptions:
      entity_name      -> entityName      (name of the entity owning the resource)
      pool_type        -> poolType        (ID | IP | SUBNET)
      pool_name        -> poolName        (name of the resource pool)
      scope_type       -> scopeDetails.scopeType  (fabric | device | device_interface | device_pair | link)
      is_pre_allocated -> isPreAllocated  (whether a specific resource value is pre-allocated)
      resource         -> resourceValue   (value to pre-allocate; required when is_pre_allocated=True)
      vrf_name         -> vrfName         (VRF name; use 'default' for the default VRF)
      switch           -> switch          (list of switch IPs, required for non-fabric scopes)
    """

    identifiers: ClassVar[List[str]] = []

    entity_name: str = Field(
        ...,
        description=(
            "Name by which the resource is allocated. "
            "Format depends on scope_type: "
            "device_pair requires exactly 2 tildes (~), e.g. 'SER1~SER2~label'; "
            "device_interface requires exactly 1 tilde, e.g. 'SER~Ethernet1/13'; "
            "link requires exactly 3 tildes, e.g. 'SER1~Eth1/3~SER2~Eth1/3'; "
            "fabric and device have no tilde constraint."
        ),
    )
    pool_type: PoolType = Field(
        ...,
        description="Type of resource pool. One of: ID (integer), IP (IP address), SUBNET (CIDR block).",
    )
    pool_name: str = Field(
        ...,
        description=(
            "Name of the resource pool to use (e.g. 'LOOPBACK_ID', 'IP_POOL', 'SUBNET'). "
            "For known pool names the scope_type must match the allowed scopes."
        ),
    )
    scope_type: ScopeType = Field(
        ...,
        description="Scope level for the resource. One of: fabric, device, device_interface, device_pair, link.",
    )
    is_pre_allocated: bool = Field(
        ...,
        description=(
            "Whether the resource value is pre-allocated. "
            "Set to True to reserve a specific resource value; "
            "False to let the system auto-assign. "
            "When True, the 'resource' field must also be provided."
        ),
    )
    resource: Optional[str] = Field(
        default=None,
        description=(
            "Resource value to pre-allocate (API field: resourceValue). Required when is_pre_allocated=True. "
            "Format: integer string for ID (e.g. '101'), "
            "IPv4/IPv6 address for IP (e.g. '110.1.1.1'), "
            "CIDR notation for SUBNET (e.g. '10.1.1.0/24')."
        ),
    )
    vrf_name: Optional[str] = Field(
        default=None,
        description=(
            "VRF name associated with the resource allocation (API field: vrfName). "
            "Use 'default' for the global default VRF."
        ),
    )
    switch: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of switch management IP addresses (IPv4/IPv6) or hostnames. "
            "Required when scope_type is not 'fabric'."
        ),
    )

    @field_validator("entity_name", mode="before")
    @classmethod
    def validate_entity_name(cls, v: str) -> str:
        if not isinstance(v, str) or not str(v).strip():
            raise ValueError("entity_name must be a non-empty string")
        return str(v).strip()

    @field_validator("pool_name", mode="before")
    @classmethod
    def validate_pool_name(cls, v: str) -> str:
        if not isinstance(v, str) or not str(v).strip():
            raise ValueError("pool_name must be a non-empty string")
        return str(v).strip()

    @field_validator("is_pre_allocated", mode="before")
    @classmethod
    def validate_is_pre_allocated(cls, v) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            lower = v.strip().lower()
            if lower in ("true", "yes", "1"):
                return True
            if lower in ("false", "no", "0"):
                return False
        if isinstance(v, int) and v in (0, 1):
            return bool(v)
        raise ValueError(f"is_pre_allocated must be a boolean (true/false), got: {v!r}")

    @field_validator("vrf_name", mode="before")
    @classmethod
    def validate_vrf_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str) or not str(v).strip():
            raise ValueError("vrf_name must be a non-empty string when provided")
        return str(v).strip()

    @field_validator("switch", mode="before")
    @classmethod
    def validate_switch_entries(cls, v: Optional[List]) -> Optional[List[str]]:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("switch must be a list of IP addresses or hostnames")
        validated = []
        for entry in v:
            entry_str = str(entry).strip()
            if not entry_str:
                raise ValueError("switch list entries must be non-empty strings")
            try:
                ip_address(entry_str)
            except ValueError:
                pass
            validated.append(entry_str)
        return validated

    @model_validator(mode="after")
    def validate_resource_value(self) -> "CreateResourceRequest":
        """Validate the resource value format matches the pool_type."""
        if self.resource is None:
            return self
        resource = str(self.resource).strip()
        pool_type = self.pool_type
        if pool_type == "ID":
            if not re.match(r"^\d+$", resource):
                raise ValueError(
                    f"resource must be an integer string when pool_type is 'ID', got: '{resource}'"
                )
        elif pool_type == "IP":
            try:
                ip_address(resource)
            except ValueError:
                raise ValueError(
                    f"resource must be a valid IPv4/IPv6 address when pool_type is 'IP', got: '{resource}'"
                )
        elif pool_type == "SUBNET":
            if "/" not in resource:
                raise ValueError(
                    f"resource must be CIDR notation (IP/mask) when pool_type is 'SUBNET', got: '{resource}'"
                )
            try:
                ip_network(resource, strict=False)
            except ValueError:
                raise ValueError(f"resource '{resource}' is not a valid CIDR network")
        return self

    @model_validator(mode="after")
    def validate_pre_allocated_requires_resource(self) -> "CreateResourceRequest":
        """Require resource value when is_pre_allocated is True."""
        if self.is_pre_allocated and self.resource is None:
            raise ValueError(
                "'resource' must be provided when 'is_pre_allocated' is True"
            )
        return self

    @model_validator(mode="after")
    def validate_switch_required(self) -> "CreateResourceRequest":
        """Require switch when scope_type is not 'fabric'."""
        if self.scope_type != "fabric" and not self.switch:
            raise ValueError(
                f"switch is required when scope_type is '{self.scope_type}'"
            )
        return self

    @model_validator(mode="after")
    def validate_pool_name_scope_combination(self) -> "CreateResourceRequest":
        """Validate pool_name and scope_type are a known-valid combination."""
        pool_name = self.pool_name
        scope_type = self.scope_type
        if pool_name in POOL_SCOPE_MAP:
            allowed = POOL_SCOPE_MAP[pool_name]
            if scope_type not in allowed:
                raise ValueError(
                    f"scope_type '{scope_type}' is invalid for pool_name '{pool_name}', "
                    f"allowed: {allowed}"
                )
        return self

    @model_validator(mode="after")
    def validate_entity_name_format(self) -> "CreateResourceRequest":
        """Validate entity_name tilde (~) count matches the required scope_type format."""
        entity_name = self.entity_name
        scope_type = self.scope_type
        tilde_count = entity_name.count("~")
        if scope_type == "device_pair":
            if tilde_count != 2:
                raise ValueError(
                    f"entity_name for scope_type 'device_pair' must contain exactly 2 tildes (~), "
                    f"e.g. 'SER1~SER2~label', got: '{entity_name}' ({tilde_count} tilde(s))"
                )
        elif scope_type == "device_interface":
            if tilde_count != 1:
                raise ValueError(
                    f"entity_name for scope_type 'device_interface' must contain exactly 1 tilde (~), "
                    f"e.g. 'SER~Ethernet1/13', got: '{entity_name}' ({tilde_count} tilde(s))"
                )
        elif scope_type == "link":
            if tilde_count != 3:
                raise ValueError(
                    f"entity_name for scope_type 'link' must contain exactly 3 tildes (~), "
                    f"e.g. 'SER1~Eth1/3~SER2~Eth1/3', got: '{entity_name}' ({tilde_count} tilde(s))"
                )
        return self


__all__ = ["CreateResourceRequest"]
