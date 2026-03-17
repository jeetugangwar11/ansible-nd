# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
ResourceManagerConfigModel - Ansible playbook input validation model.

Validates a single config entry for the nd_manage_resource_manager_updated
module. Replaces the missing AnsibleResourceConfigModel.

Fields map directly to the module's config suboptions:
  entity_name  → entityName  (unique name identifying the resource allocation)
  pool_type    → poolType    (ID | IP | SUBNET)
  pool_name    → poolName    (name of the resource pool)
  scope_type   → scopeType   (fabric | device | device_interface | device_pair | link)
  resource     → resource    (value to allocate; optional)
  switch       → switch      (list of switch IPs/serials; required for non-fabric scopes)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import ClassVar, List, Optional

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.constants import (
    POOL_SCOPE_MAP,
    PoolType,
    ScopeType,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import (
    Field,
    model_validator,
)


class ResourceManagerConfigModel(NDBaseModel):
    """
    Input validation model for a single nd_manage_resource_manager_updated config entry.

    Derived from dcnm_resource_manager.py config suboptions with full per-field
    and cross-field validation.
    """

    identifiers: ClassVar[List[str]] = []

    entity_name: str = Field(
        description=(
            "Unique name identifying the entity to which the resource is allocated. "
            "Format depends on scope_type: "
            "fabric/device -> free-form string; "
            "device_pair -> two tildes required e.g. 'SER1~SER2~label'; "
            "device_interface -> one tilde e.g. 'SER~Ethernet1/13'; "
            "link -> three tildes e.g. 'SER1~Eth1/3~SER2~Eth1/3'."
        ),
    )
    pool_type: PoolType = Field(
        description="Type of resource pool. One of: ID (integer), IP (address), SUBNET (CIDR block).",
    )
    pool_name: str = Field(
        description=(
            "Name of the resource pool to use (e.g. 'L3_VNI', 'LOOPBACK_ID', 'SUBNET'). "
            "For known pool names the scope_type must match the allowed scopes in POOL_SCOPE_MAP."
        ),
    )
    scope_type: ScopeType = Field(
        description="Scope for the resource allocation. One of: fabric, device, device_interface, device_pair, link.",
    )
    resource: Optional[str] = Field(
        default=None,
        description=(
            "Value of the resource being allocated. "
            "Integer string for ID pools (e.g. '101'), "
            "IPv4/IPv6 address for IP pools, "
            "CIDR notation for SUBNET pools (e.g. '10.1.1.0/24'). "
            "Required for state=merged."
        ),
    )
    switch: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of switch IP addresses or serial numbers to which the resource is assigned. "
            "Required when scope_type is not 'fabric'."
        ),
    )

    @model_validator(mode="after")
    def validate_scope_and_switch(self) -> "ResourceManagerConfigModel":
        """
        Cross-field validation:
        1. pool_name vs scope_type compatibility via POOL_SCOPE_MAP.
        2. switch required for non-fabric scope_types.
        """
        scope = self.scope_type
        pool = self.pool_name
        pool_type = self.pool_type

        # Determine the lookup key for POOL_SCOPE_MAP
        if pool_type == PoolType.ID:
            check_key = pool
        elif pool_type == PoolType.IP:
            check_key = "IP_POOL"
        else:  # SUBNET
            check_key = "SUBNET"

        allowed_scopes = POOL_SCOPE_MAP.get(check_key)
        if allowed_scopes is not None and scope not in allowed_scopes:
            raise ValueError(
                "scope_type '{0}' is not valid for pool_name '{1}'. "
                "Allowed scope_types: {2}".format(scope, pool, allowed_scopes)
            )

        # Non-fabric scopes require at least one switch entry
        if scope != ScopeType.FABRIC and not self.switch:
            raise ValueError(
                "'switch' is required when scope_type is '{0}' (entity_name: '{1}')".format(
                    scope, self.entity_name
                )
            )

        return self


__all__ = ["ResourceManagerConfigModel"]
