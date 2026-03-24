#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__copyright__ = "Copyright (c) 2026 Cisco and/or its affiliates."
__author__ = "Jeet Ram"

DOCUMENTATION = """
---
module: nd_manage_resource_manager
short_description: Manage resources in Cisco Nexus Dashboard (ND).
version_added: "1.0.0"
author: Jeet Ram (@jeetram)
description:
  - Create, delete, and query resources in Cisco Nexus Dashboard using smart endpoints and pydantic models.
  - Supports all resource pool types (ID, IP, SUBNET) and scope types (fabric, device, device_interface, device_pair, link).
  - Provides idempotent merged and deleted states.
options:
  fabric:
    description:
      - Name of the target fabric for resource manager operations.
    type: str
    required: true
  state:
    description:
      - The required state of the configuration after module completion.
      - C(gathered) reads the current fabric resource and returns it in the
    type: str
    default: merged
    choices:
      - merged
      - deleted
      - gathered
  config:
    description:
      - A list of dictionaries containing resource configurations.
      - Optional for state C(gathered) (returns all resources when omitted).
    type: list
    elements: dict
    suboptions:
      entity_name:
        description:
          - A unique name which identifies the entity to which the resource is allocated.
          - The format depends on scope_type.
          - "fabric / device: free-form string, e.g. 'l3_vni_fabric'."
          - "device_pair: two tildes required, e.g. 'SER1~SER2~label'."
          - "device_interface: one tilde required, e.g. 'SER~Ethernet1/13'."
          - "link: three tildes required, e.g. 'SER1~Eth1/3~SER2~Eth1/3'."
        type: str
        required: true
      pool_type:
        description:
          - Type of resource pool.
        type: str
        required: true
        choices:
          - ID
          - IP
          - SUBNET
      pool_name:
        description:
          - Name of the resource pool from which the resource is allocated.
        type: str
        required: true
      scope_type:
        description:
          - Scope of resource allocation.
        type: str
        required: true
        choices:
          - fabric
          - device
          - device_interface
          - device_pair
          - link
      resource:
        description:
          - Value of the resource being allocated.
          - An integer string if C(pool_type=ID), e.g. '101'.
          - An IPv4 or IPv6 address if C(pool_type=IP), e.g. '110.1.1.1'.
          - A CIDR block if C(pool_type=SUBNET), e.g. '10.1.1.0/24'.
        type: str
      switch:
        description:
          - List of switch IP addresses to which the resource is assigned.
          - Required when C(scope_type) is not C(fabric).
        type: list
        elements: str
extends_documentation_fragment:
  - cisco.nd.modules
notes:
  - Requires Nexus Dashboard 3.x or higher with the ND Manage API (v1).
  - Idempotence checking compares the existing resource value to the desired value.
  - Entity name matching is order-insensitive for tilde-separated serial numbers.
"""

EXAMPLES = """
- name: Create resources
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: merged
    config:
      - entity_name: "l3_vni_fabric"
        pool_type: "ID"
        pool_name: "L3_VNI"
        scope_type: "fabric"
        resource: "101"

      - entity_name: "loopback_dev"
        pool_type: "ID"
        pool_name: "LOOPBACK_ID"
        scope_type: "device"
        switch:
          - 192.168.10.201
          - 192.168.10.202
        resource: "200"

      - entity_name: "mmudigon-2"
        pool_type: "IP"
        pool_name: "LOOPBACK0_IP_POOL"
        scope_type: "fabric"
        resource: "110.1.1.1"

- name: Delete resources
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: deleted
    config:
      - entity_name: "l3_vni_fabric"
        pool_type: "ID"
        pool_name: "L3_VNI"
        scope_type: "fabric"

- name: Gather all resources from fabric
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: gathered
  register: result

- name: Gather resources by entity name
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: gathered
    config:
      - entity_name: "l3_vni_fabric"
      - entity_name: "loopback_dev"

- name: Gather resources by pool name
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: gathered
    config:
      - pool_name: "L3_VNI"
      - pool_name: "LOOPBACK_ID"

- name: Gather resources by switch
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: gathered
    config:
      - switch:
          - 192.168.10.201
"""

RETURN = """
changed:
  description: Whether any changes were made.
  returned: when state is not gathered
  type: bool
diff:
  description: Tracking of merged and deleted resources.
  returned: when state is not gathered
  type: list
  elements: dict
  sample: [{"merged": [], "deleted": [], "gathered": [], "debugs": []}]
response:
  description: API responses received during module execution.
  returned: always
  type: list
  elements: dict
before:
  description: State before module execution (always empty list for this module).
  returned: when state is not gathered
  type: list
after:
  description: State after module execution (always empty list for this module).
  returned: when state is not gathered
  type: list
gathered:
  description:
  - The current fabric resource returned.
  - Each entry mirrors the resource data from the ND API.
  returned: when state is gathered
  type: list
  elements: dict
"""

import copy
import ipaddress
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.nd.plugins.module_utils.common.log import Log
from ansible_collections.cisco.nd.plugins.module_utils.nd_v2 import (
    NDModule,
    nd_argument_spec,
)
from ansible_collections.cisco.nd.plugins.module_utils.nd_output import NDOutput
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.ResourceManagerConfigModel import (
    ResourceManagerConfigModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.ResourceModel import (
    ResourceModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.RemoveResourcesByIdsRequestModel import (
    RemoveResourcesByIdsRequest,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.constants import (
    POOL_SCOPE_MAP,
    PoolType,
    ScopeType,
)
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.nd_resource_manager.nd_manage_resource_manager import (
    EpManageFabricResourcesGet,
    EpManageFabricResourcesPost,
    EpManageFabricResourcesActionsRemovePost,
)
from ansible_collections.cisco.nd.plugins.module_utils.common.exceptions import NDModuleError
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.base_path import BasePath


# Map from playbook scope_type values to ND API scopeType values
_SCOPE_TYPE_TO_API = {
    "fabric": "fabric",
    "device": "device",
    "device_interface": "deviceInterface",
    "device_pair": "devicePair",
    "link": "link",
}

# Map from ND API scopeType values back to playbook scope_type values
_API_SCOPE_TYPE_TO_PLAYBOOK = {v: k for k, v in _SCOPE_TYPE_TO_API.items()}

# Valid pool_name -> scope_type combinations (from dcnm_resource_manager)
_POOLNAME_TO_SCOPE_TYPE = {
    "L3_VNI": ["fabric"],
    "L2_VNI": ["fabric"],
    "BGP_ASN_ID": ["fabric"],
    "VPC_DOMAIN_ID": ["fabric"],
    "VPC_ID": ["device_pair"],
    "VPC_PEER_LINK_VLAN": ["device_pair"],
    "FEX_ID": ["device"],
    "LOOPBACK_ID": ["device"],
    "PORT_CHANNEL_ID": ["device"],
    "TUNNEL_ID_IOS_XE": ["device"],
    "OBJECT_TRACKING_NUMBER_POOL": ["device"],
    "INSTANCE_ID": ["device"],
    "PORT_CHANNEL_ID_IOS_XE": ["device"],
    "ROUTE_MAP_SEQUENCE_NUMBER_POOL": ["device"],
    "SERVICE_NETWORK_VLAN": ["device"],
    "TOP_DOWN_VRF_VLAN": ["device"],
    "TOP_DOWN_NETWORK_VLAN": ["device"],
    "TOP_DOWN_L3_DOT1Q": ["device_interface"],
    "IP_POOL": ["fabric", "device_interface"],
    "SUBNET": ["link"],
}


class NDResourceManagerModule:
    """
    Manage resources in Cisco Nexus Dashboard via the ND Manage v1 API.

    Uses pydantic models for input validation and smart endpoints for path/verb generation.
    Preserves the same business logic as dcnm_resource_manager.py.
    """

    def __init__(self, module, nd, logger=None):
        self.module = module
        self.nd = nd
        self.log = logger if logger is not None else logging.getLogger(__name__)

        self.fabric = module.params["fabric"]
        self.state = module.params["state"]
        self.config = module.params.get("config") or []

        # ND-compatible tracking dicts
        self.changed_dict = [{"merged": [], "deleted": [], "gathered": [], "debugs": []}]
        self.api_responses = []

        # Cached GET results
        self._all_resources = []
        self._resources_fetched = False

        self.log.info(
            f"NDResourceManagerModule initialized: fabric={self.fabric}, "
            f"state={self.state}, config_count={len(self.config)}"
        )

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def _validate_resource_params(self, item):
        """Validate pool_type/pool_name/scope_type compatibility (mirroring dcnm logic)."""
        pool_type = item.get("pool_type")
        pool_name = item.get("pool_name")
        scope_type = item.get("scope_type")

        self.log.debug(
            f"Validating resource params: pool_type={pool_type}, "
            f"pool_name={pool_name}, scope_type={scope_type}"
        )

        if pool_type == "ID":
            self.log.debug(f"pool_type is 'ID', using pool_name as check_key: {pool_name}")
            check_key = pool_name
        elif pool_type == "IP":
            self.log.debug("pool_type is 'IP', using check_key='IP_POOL'")
            check_key = "IP_POOL"
        elif pool_type == "SUBNET":
            self.log.debug("pool_type is 'SUBNET', using check_key='SUBNET'")
            check_key = "SUBNET"
        else:
            msg = (
                "Given pool type = '{0}' is invalid,"
                " Allowed pool types = ['ID', 'IP', 'SUBNET']".format(pool_type)
            )
            self.log.warning(f"Validation failed: {msg}")
            return False, msg

        allowed_scopes = _POOLNAME_TO_SCOPE_TYPE.get(check_key)
        if allowed_scopes is None:
            msg = "Given pool name '{0}' is not valid".format(pool_name)
            self.log.warning(f"Validation failed: {msg}")
            return False, msg

        if scope_type not in allowed_scopes:
            msg = (
                "Given scope type '{0}' is not valid for pool name = '{1}',"
                " Allowed scope_types = {2}".format(
                    scope_type, pool_name, allowed_scopes
                )
            )
            self.log.warning(f"Validation failed: {msg}")
            return False, msg

        self.log.debug(
            f"Validation passed: pool_name={pool_name}, scope_type={scope_type}, "
            f"allowed_scopes={allowed_scopes}"
        )
        return True, ""

    def _validate_input(self):
        """Validate playbook config fields based on the current state."""
        self.log.info(
            f"Validating input: state={self.state}, config_count={len(self.config)}"
        )

        if not self.config:
            if self.state in ("merged", "deleted"):
                self.log.error(
                    f"'config' is mandatory for state '{self.state}' but was not provided"
                )
                self.module.fail_json(
                    msg="'config' element is mandatory for state '{0}'".format(
                        self.state
                    )
                )
            return

        for item in self.config:
            self.log.debug(
                f"Validating config item: entity_name={item.get('entity_name')}, "
                f"pool_name={item.get('pool_name')}, scope_type={item.get('scope_type')}, "
                f"pool_type={item.get('pool_type')}"
            )
            if self.state != "gathered":
                # Mandatory parameter checks
                for field in ("scope_type", "pool_type", "pool_name", "entity_name"):
                    if item.get(field) is None:
                        self.log.error(
                            f"Mandatory parameter '{field}' is missing in config item: {item}"
                        )
                        self.module.fail_json(
                            msg="Mandatory parameter '{0}' missing".format(field)
                        )
                    else:
                        self.log.debug(f"Mandatory parameter '{field}' present: {item.get(field)}")

                # Switch required for non-fabric scopes
                if item.get("scope_type") != "fabric" and not item.get("switch"):
                    self.log.error(
                        f"'switch' is required for scope_type='{item.get('scope_type')}' "
                        f"but is missing in config item: {item}"
                    )
                    self.module.fail_json(msg="switch : Required parameter not found")
                elif item.get("scope_type") != "fabric":
                    self.log.debug(
                        f"'switch' provided for scope_type='{item.get('scope_type')}': "
                        f"{item.get('switch')}"
                    )

            # Validate pool_name / scope_type combination (only when pool_type is provided)
            if item.get("pool_type") is not None:
                self.log.debug(
                    f"Running pool_type/pool_name/scope_type compatibility check for: "
                    f"pool_type={item.get('pool_type')}, pool_name={item.get('pool_name')}, "
                    f"scope_type={item.get('scope_type')}"
                )
                rc, mesg = self._validate_resource_params(item)
                if not rc:
                    self.log.error(f"Pool/scope compatibility check failed: {mesg}")
                    self.module.fail_json(msg=mesg)
                else:
                    self.log.debug("Pool/scope compatibility check passed")

            # Pydantic cross-field validation for merged/deleted
            if self.state != "gathered":
                try:
                    ResourceManagerConfigModel.from_config(item)
                    self.log.debug(
                        f"Pydantic validation passed for entity_name={item.get('entity_name')}"
                    )
                except Exception as exc:
                    self.log.error(
                        f"Pydantic validation failed for entity_name={item.get('entity_name')}: {exc}"
                    )
                    self.module.fail_json(
                        msg="Invalid parameters in playbook: {0}".format(str(exc))
                    )

    # ------------------------------------------------------------------
    # ND API interaction helpers
    # ------------------------------------------------------------------

    def _get_all_resources(self):
        """Fetch all resources for the fabric once and cache them."""
        if self._resources_fetched:
            self.log.debug(
                f"Resources already cached for fabric={self.fabric}: "
                f"{len(self._all_resources)} resource(s)"
            )
            return

        self.log.info(f"Fetching all resources for fabric={self.fabric}")

        ep = EpManageFabricResourcesGet(fabric_name=self.fabric)
        try:
            data = self.nd.request(ep.path, ep.verb)
        except NDModuleError as exc:
            if exc.status == 404:
                # Fabric has no resources yet — that is valid
                self.log.info(
                    f"No resources found (404) for fabric={self.fabric}, treating as empty"
                )
                self._resources_fetched = True
                return
            raise

        # The ND API may return a list directly or {"resources": [...], "meta": {...}}
        if isinstance(data, list):
            self.log.debug(f"API returned a list with {len(data)} item(s)")
            raw_list = data
        elif isinstance(data, dict) and "resources" in data:
            self.log.debug(
                f"API returned dict with 'resources' key, "
                f"{len(data['resources'])} resource(s)"
            )
            raw_list = data["resources"]
        elif isinstance(data, dict) and data:
            self.log.debug("API returned a non-empty dict without 'resources' key, wrapping in list")
            raw_list = [data]
        else:
            self.log.debug("API returned empty or unexpected data, treating as empty list")
            raw_list = []

        for raw in raw_list:
            try:
                resource_model = ResourceModel.from_response(raw)
                self.log.debug(
                    f"Parsed resource: entity_name={getattr(resource_model, 'entity_name', None)}, "
                    f"pool_name={getattr(resource_model, 'pool_name', None)}"
                )
                self._all_resources.append(resource_model)
            except Exception as exc:
                # If parsing fails, keep the raw dict so we can still match on it
                self.log.warning(
                    f"Failed to parse resource into ResourceModel (keeping raw): {exc} | raw={raw}"
                )
                self._all_resources.append(raw)

        self._resources_fetched = True
        self.log.info(
            f"Fetched {len(self._all_resources)} resource(s) for fabric={self.fabric}"
        )

    # ------------------------------------------------------------------
    # Resource attribute accessors (handle both ResourceModel and raw dict)
    # ------------------------------------------------------------------

    def _attr(self, resource, model_attr, dict_key):
        if hasattr(resource, model_attr):
            value = getattr(resource, model_attr)
            self.log.debug(f"_attr: resolved '{model_attr}' from model: {value}")
            return value
        if isinstance(resource, dict):
            value = resource.get(dict_key)
            self.log.debug(f"_attr: resolved '{dict_key}' from dict: {value}")
            return value
        self.log.debug(f"_attr: could not resolve '{model_attr}'/'{dict_key}' from resource type {type(resource)}")
        return None

    def _get_entity_name(self, resource):
        return self._attr(resource, "entity_name", "entityName")

    def _get_pool_name(self, resource):
        return self._attr(resource, "pool_name", "poolName")

    def _get_resource_id(self, resource):
        return self._attr(resource, "resource_id", "resourceId")

    def _get_resource_value(self, resource):
        return self._attr(resource, "resource_value", "resourceValue")

    def _get_scope_type(self, resource):
        """Return the playbook-style scope_type string."""
        if hasattr(resource, "scope_details") and resource.scope_details:
            raw = getattr(resource.scope_details, "scope_type", None)
            self.log.debug(f"_get_scope_type: from model scope_details, raw={raw}")
        elif isinstance(resource, dict):
            sd = resource.get("scopeDetails") or {}
            raw = sd.get("scopeType")
            self.log.debug(f"_get_scope_type: from dict scopeDetails, raw={raw}")
        else:
            self.log.debug(f"_get_scope_type: unrecognised resource type {type(resource)}, returning None")
            return None
        mapped = _API_SCOPE_TYPE_TO_PLAYBOOK.get(raw, raw) if raw else None
        self.log.debug(f"_get_scope_type: mapped API scope '{raw}' -> playbook scope '{mapped}'")
        return mapped

    def _get_switch_ip(self, resource):
        """Return the switch IP from scopeDetails."""
        if hasattr(resource, "scope_details") and resource.scope_details:
            value = getattr(resource.scope_details, "switch_ip", None)
            self.log.debug(f"_get_switch_ip: from model scope_details, switch_ip={value}")
            return value
        if isinstance(resource, dict):
            sd = resource.get("scopeDetails") or {}
            value = sd.get("switchIp")
            self.log.debug(f"_get_switch_ip: from dict scopeDetails, switchIp={value}")
            return value
        self.log.debug(f"_get_switch_ip: unrecognised resource type {type(resource)}, returning None")
        return None

    def _get_fabric_name(self, resource):
        """Return fabric name from scopeDetails."""
        if hasattr(resource, "scope_details") and resource.scope_details:
            value = getattr(resource.scope_details, "fabric_name", None)
            self.log.debug(f"_get_fabric_name: from model scope_details, fabric_name={value}")
            return value
        if isinstance(resource, dict):
            sd = resource.get("scopeDetails") or {}
            value = sd.get("fabricName")
            self.log.debug(f"_get_fabric_name: from dict scopeDetails, fabricName={value}")
            return value
        self.log.debug(f"_get_fabric_name: unrecognised resource type {type(resource)}, returning None")
        return None

    def _to_dict(self, resource):
        """Convert a ResourceModel (or raw dict) to a plain dict for response output."""
        if hasattr(resource, "to_payload"):
            result = resource.to_payload()
            self.log.debug(f"_to_dict: converted ResourceModel to dict via to_payload(): {result}")
            return result
        self.log.debug(f"_to_dict: resource is already a raw dict, returning as-is")
        return resource

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------

    def _entity_names_match(self, e1, e2):
        """Compare entity names in order-insensitive way (mirrors dcnm logic)."""
        if e1 is None or e2 is None:
            self.log.debug(
                f"_entity_names_match: one or both entity names are None "
                f"(e1={e1}, e2={e2}), returning False"
            )
            return False
        result = sorted(e1.split("~")) == sorted(e2.split("~"))
        self.log.debug(
            f"_entity_names_match: e1='{e1}', e2='{e2}', "
            f"sorted_e1={sorted(e1.split('~'))}, sorted_e2={sorted(e2.split('~'))}, "
            f"match={result}"
        )
        return result

    def _compare_resource_values(self, have, want):
        """Compare resource values — IPv4/IPv6 aware (mirrors dcnm_rm_compare_resource_values)."""
        if have is None and want is None:
            self.log.debug("_compare_resource_values: both have and want are None, treating as equal")
            return True
        if have is None or want is None:
            self.log.debug(
                f"_compare_resource_values: one value is None (have={have}, want={want}), not equal"
            )
            return False

        have = str(have).strip()
        want = str(want).strip()

        def _classify(val):
            if "/" in val:
                try:
                    return "network", ipaddress.ip_network(val, strict=False)
                except ValueError:
                    pass
            try:
                return "address", ipaddress.ip_address(val)
            except ValueError:
                pass
            return "raw", val

        th, vh = _classify(have)
        tw, vw = _classify(want)

        self.log.debug(
            f"_compare_resource_values: have='{have}' classified as ({th}, {vh}), "
            f"want='{want}' classified as ({tw}, {vw})"
        )

        if th == tw == "address":
            result = vh.exploded == vw.exploded
            self.log.debug(
                f"_compare_resource_values: address comparison: "
                f"{vh.exploded} == {vw.exploded} -> {result}"
            )
            return result
        if th == tw == "network":
            result = vh == vw
            self.log.debug(
                f"_compare_resource_values: network comparison: {vh} == {vw} -> {result}"
            )
            return result
        result = have == want
        self.log.debug(
            f"_compare_resource_values: raw string comparison: '{have}' == '{want}' -> {result}"
        )
        return result

    def _find_matching_resources(
        self, entity_name, pool_name, scope_type, switch_ip=None
    ):
        """Find cached resources matching the given criteria."""
        self.log.debug(
            f"Finding matching resources: entity_name={entity_name}, "
            f"pool_name={pool_name}, scope_type={scope_type}, switch_ip={switch_ip}"
        )
        results = []
        for res in self._all_resources:
            res_entity = self._get_entity_name(res)
            res_pool = self._get_pool_name(res)
            res_scope = self._get_scope_type(res)

            if not self._entity_names_match(res_entity, entity_name):
                self.log.debug(
                    f"_find_matching_resources: skipping resource, entity_name mismatch: "
                    f"resource_entity='{res_entity}' vs wanted='{entity_name}'"
                )
                continue
            if res_pool != pool_name:
                self.log.debug(
                    f"_find_matching_resources: skipping resource, pool_name mismatch: "
                    f"resource_pool='{res_pool}' vs wanted='{pool_name}'"
                )
                continue
            if res_scope != scope_type:
                self.log.debug(
                    f"_find_matching_resources: skipping resource, scope_type mismatch: "
                    f"resource_scope='{res_scope}' vs wanted='{scope_type}'"
                )
                continue

            # For non-fabric scopes, only match if switch_ip aligns
            if scope_type != "fabric" and switch_ip is not None:
                res_sw = self._get_switch_ip(res)
                if res_sw != switch_ip:
                    self.log.debug(
                        f"_find_matching_resources: skipping resource, switch_ip mismatch: "
                        f"resource_switch_ip='{res_sw}' vs wanted='{switch_ip}'"
                    )
                    continue

            self.log.debug(
                f"_find_matching_resources: matched resource: entity_name='{res_entity}', "
                f"pool_name='{res_pool}', scope_type='{res_scope}'"
            )
            results.append(res)

        self.log.debug(
            f"Found {len(results)} matching resource(s) for entity_name={entity_name}, "
            f"pool_name={pool_name}, scope_type={scope_type}, switch_ip={switch_ip}"
        )
        return results

    # ------------------------------------------------------------------
    # API payload builders
    # ------------------------------------------------------------------

    def _build_scope_details(self, scope_type, switch_ip=None, entity_name=None):
        """Build the scopeDetails dict for the ND Manage API.

        ``switch_ip`` is the translated switchId (serial number) of the source switch
        from the playbook ``switch`` list.  The entity_name encodes the full topology
        (src and dst) as tilde-separated fields — the server uses it to resolve
        additional context, so we only need to supply srcSwitchId for multi-switch
        scopes (device_pair, link) and let the server derive dst from entityName.

          - fabric:           fabricName
          - device:           switchId
          - device_interface: switchId (= switch_ip) + interfaceName  (from entity SN~IF)
          - device_pair:      srcSwitchId (= switch_ip)  — dst derived by server from entityName
          - link:             srcSwitchId (= switch_ip)  — dst derived by server from entityName
        """
        self.log.debug(
            f"_build_scope_details: scope_type={scope_type}, switch_ip={switch_ip}, "
            f"entity_name={entity_name}, fabric={self.fabric}"
        )
        api_scope = _SCOPE_TYPE_TO_API[scope_type]

        if scope_type == "fabric":
            self.log.debug(
                f"_build_scope_details: fabric scope -> fabricName={self.fabric}"
            )
            result = {
                "scopeType": api_scope,
                "fabricName": self.fabric,
            }

        elif scope_type == "device":
            self.log.debug(
                f"_build_scope_details: device scope -> switchId={switch_ip}"
            )
            result = {
                "scopeType": api_scope,
                "switchId": switch_ip,
            }

        elif scope_type == "device_interface":
            # entity_name format: <serialNumber>~<interfaceName>
            # switch_ip is already the translated switchId (serial number)
            parts = (entity_name or "").split("~", 1)
            if_name = parts[1] if len(parts) > 1 else None
            self.log.debug(
                f"_build_scope_details: device_interface scope -> "
                f"switchId={switch_ip}, interfaceName={if_name} "
                f"(interfaceName parsed from entity_name='{entity_name}')"
            )
            result = {"scopeType": api_scope, "switchId": switch_ip}
            if if_name:
                result["interfaceName"] = if_name
            else:
                self.log.warning(
                    f"_build_scope_details: device_interface scope: could not parse "
                    f"interfaceName from entity_name='{entity_name}'"
                )

        elif scope_type == "device_pair":
            # switch_ip is the src switchId (serial number).
            # dstSwitchId is intentionally omitted — the server derives the destination
            # switch from entityName (format: <srcSN>~<dstSN>[~<label>]) to avoid a
            # NullPointerException when the dst switch ID is not registered in ND Manage.
            self.log.debug(
                f"_build_scope_details: device_pair scope -> srcSwitchId={switch_ip} "
                f"(dst derived by server from entityName='{entity_name}')"
            )
            result = {
                "scopeType": api_scope,
                "srcSwitchId": switch_ip,
            }

        elif scope_type == "link":
            # switch_ip is the src switchId (serial number).
            # dstSwitchId/dstInterfaceName are intentionally omitted — the server derives
            # destination context from entityName (format: <srcSN>~<srcIF>~<dstSN>~<dstIF>).
            parts = (entity_name or "").split("~")
            src_if = parts[1] if len(parts) > 1 else None
            self.log.debug(
                f"_build_scope_details: link scope -> srcSwitchId={switch_ip}, "
                f"srcInterfaceName={src_if} "
                f"(dst derived by server from entityName='{entity_name}')"
            )
            result = {"scopeType": api_scope, "srcSwitchId": switch_ip}
            if src_if:
                result["srcInterfaceName"] = src_if

        else:
            self.log.warning(
                f"_build_scope_details: unrecognised scope_type='{scope_type}', "
                f"falling back to generic switchId payload"
            )
            result = {
                "scopeType": api_scope,
                "switchId": switch_ip,
            }

        self.log.debug(f"_build_scope_details: result={result}")
        return result

    def _build_create_payload(self, item, switch_ip=None):
        """Build POST body for resource creation in ND Manage API format."""
        scope_type = item["scope_type"]
        entity_name = item["entity_name"]
        pool_name = item["pool_name"]
        pool_type = item.get("pool_type")
        resource_value = item.get("resource")

        self.log.debug(
            f"_build_create_payload: pool_name={pool_name}, pool_type={pool_type}, "
            f"entity_name={entity_name}, scope_type={scope_type}, "
            f"switch_ip={switch_ip}, resource={resource_value}"
        )

        payload = {
            "poolName": pool_name,
            "poolType": pool_type,
            "entityName": entity_name,
            "scopeDetails": self._build_scope_details(scope_type, switch_ip, entity_name=entity_name),
            "isPreAllocated": True,
        }
        if resource_value is not None:
            self.log.debug(
                f"_build_create_payload: adding resourceValue='{resource_value}' to payload"
            )
            payload["resourceValue"] = str(resource_value)
        else:
            self.log.debug(
                "_build_create_payload: no resource value provided, omitting resourceValue field"
            )
        self.log.debug(f"_build_create_payload: final payload={payload}")
        return payload


    def manage_merged(self):
        """Create resources that don't exist or have a different value."""
        self.log.info(
            f"manage_merged: Processing {len(self.config)} config item(s) "
            f"for fabric={self.fabric}"
        )
        self._get_all_resources()

        for item in self.config:
            scope_type = item["scope_type"]
            pool_name = item["pool_name"]
            entity_name = item["entity_name"]
            resource_value = item.get("resource")
            switches = item.get("switch") or [None]

            if scope_type == "fabric":
                self.log.debug(
                    f"manage_merged: scope_type='fabric', overriding switches to [None] "
                    f"for entity_name={entity_name}, pool_name={pool_name}"
                )
                switches = [None]

            self.log.debug(
                f"manage_merged: Processing item: entity_name={entity_name}, "
                f"pool_name={pool_name}, scope_type={scope_type}, "
                f"resource_value={resource_value}, switches={switches}"
            )

            for sw in switches:
                self.log.debug(
                    f"manage_merged: Processing switch={sw} for entity_name={entity_name}, "
                    f"pool_name={pool_name}"
                )
                matches = self._find_matching_resources(
                    entity_name, pool_name, scope_type, switch_ip=sw
                )

                if matches:
                    existing_value = self._get_resource_value(matches[0])
                    self.log.debug(
                        f"manage_merged: Found {len(matches)} existing match(es) for "
                        f"entity_name={entity_name}, pool_name={pool_name}, switch_ip={sw}, "
                        f"existing_value={existing_value}, desired_value={resource_value}"
                    )
                    if self._compare_resource_values(existing_value, resource_value):
                        # Already exists with the same value — idempotent, skip
                        self.log.debug(
                            f"Resource already exists with the same value, skipping "
                            f"(idempotent): entity_name={entity_name}, "
                            f"pool_name={pool_name}, scope_type={scope_type}, "
                            f"switch_ip={sw}, existing_value={existing_value}"
                        )
                        continue
                    else:
                        self.log.debug(
                            f"manage_merged: Existing resource value differs "
                            f"(existing={existing_value}, desired={resource_value}), "
                            f"will recreate for entity_name={entity_name}, pool_name={pool_name}, switch_ip={sw}"
                        )

                payload = self._build_create_payload(item, switch_ip=sw)

                if self.module.check_mode:
                    self.log.info(
                        f"Check mode: would create resource: entity_name={entity_name}, "
                        f"pool_name={pool_name}, scope_type={scope_type}, switch_ip={sw}"
                    )
                    self.changed_dict[0]["merged"].append(payload)
                    self.api_responses.append({"RETURN_CODE": 200, "DATA": payload})
                    continue

                self.log.info(
                    f"Creating resource: entity_name={entity_name}, "
                    f"pool_name={pool_name}, scope_type={scope_type}, switch_ip={sw}"
                )
                ep = EpManageFabricResourcesPost(fabric_name=self.fabric)
                # API expects {"resources": [<resource_object>]}
                resp_data = self.nd.request(
                    ep.path, ep.verb, data={"resources": [payload]}
                )
                self.changed_dict[0]["merged"].append(payload)
                # Unwrap the response — API returns {"resources": [{...}]}
                if isinstance(resp_data, dict) and "resources" in resp_data:
                    items = resp_data["resources"]
                    self.log.debug(
                        f"manage_merged: API response contained 'resources' key with "
                        f"{len(items)} item(s), using first item as response DATA"
                    )
                    self.api_responses.append(
                        {"RETURN_CODE": 200, "DATA": items[0] if items else resp_data}
                    )
                else:
                    self.log.debug(
                        f"manage_merged: API response did not contain 'resources' key, "
                        f"storing raw response: {resp_data}"
                    )
                    self.api_responses.append({"RETURN_CODE": 200, "DATA": resp_data})
                self.log.info(
                    f"Resource created successfully: entity_name={entity_name}, "
                    f"pool_name={pool_name}, scope_type={scope_type}, switch_ip={sw}"
                )

    def manage_deleted(self):
        """Remove resources that exist in the fabric inventory."""
        self.log.info(
            f"manage_deleted: Processing {len(self.config)} config item(s) "
            f"for fabric={self.fabric}"
        )
        self._get_all_resources()

        resource_ids = []

        for item in self.config:
            scope_type = item["scope_type"]
            pool_name = item["pool_name"]
            entity_name = item["entity_name"]
            switches = item.get("switch") or [None]

            if scope_type == "fabric":
                self.log.debug(
                    f"manage_deleted: scope_type='fabric', overriding switches to [None] "
                    f"for entity_name={entity_name}, pool_name={pool_name}"
                )
                switches = [None]

            self.log.debug(
                f"manage_deleted: Processing item: entity_name={entity_name}, "
                f"pool_name={pool_name}, scope_type={scope_type}, switches={switches}"
            )

            for sw in switches:
                self.log.debug(
                    f"manage_deleted: Searching for resources: entity_name={entity_name}, "
                    f"pool_name={pool_name}, scope_type={scope_type}, switch_ip={sw}"
                )
                matches = self._find_matching_resources(
                    entity_name, pool_name, scope_type, switch_ip=sw
                )
                self.log.debug(
                    f"manage_deleted: Found {len(matches)} match(es) for "
                    f"entity_name={entity_name}, pool_name={pool_name}, switch_ip={sw}"
                )
                for res in matches:
                    rid = self._get_resource_id(res)
                    if rid is not None and rid not in resource_ids:
                        self.log.debug(
                            f"manage_deleted: Queuing resource ID '{rid}' for deletion "
                            f"(entity_name={entity_name}, pool_name={pool_name}, switch_ip={sw})"
                        )
                        resource_ids.append(rid)
                    elif rid is not None:
                        self.log.debug(
                            f"manage_deleted: Resource ID '{rid}' already queued for deletion, skipping duplicate"
                        )
                    else:
                        self.log.debug(
                            f"manage_deleted: Matched resource has no resource ID, skipping: {res}"
                        )

        if not resource_ids:
            # Nothing to delete — idempotent
            self.log.info(
                f"manage_deleted: No matching resources found to delete "
                f"for fabric={self.fabric}, nothing to do"
            )
            return

        self.log.info(
            f"manage_deleted: Collected {len(resource_ids)} resource ID(s) "
            f"to delete: {resource_ids}"
        )

        self.changed_dict[0]["deleted"].extend(str(r) for r in resource_ids)

        if self.module.check_mode:
            self.log.info(
                f"Check mode: would delete {len(resource_ids)} resource(s): {resource_ids}"
            )
            self.api_responses.append(
                {"RETURN_CODE": 200, "DATA": {"resourceIds": resource_ids}}
            )
            return

        ep = EpManageFabricResourcesActionsRemovePost(fabric_name=self.fabric)
        remove_req = RemoveResourcesByIdsRequest(resource_ids=resource_ids)
        resp_data = self.nd.request(ep.path, ep.verb, data=remove_req.to_payload())
        self.api_responses.append({"RETURN_CODE": 200, "DATA": resp_data})
        self.log.info(
            f"manage_deleted: Successfully deleted {len(resource_ids)} resource(s): "
            f"{resource_ids}"
        )

    def manage_gathered(self):
        """Return resources filtered by config criteria (or all resources if no config)."""
        config_count = len(self.config) if self.config else 0
        self.log.info(
            f"manage_gathered: Gathering resources for fabric={self.fabric}, "
            f"filter_count={config_count}"
        )
        self._get_all_resources()

        if not self.config:
            # No filters — return everything
            results = [self._to_dict(r) for r in self._all_resources]
            self.log.info(
                f"manage_gathered: No filter criteria provided, "
                f"returning all {len(results)} resource(s)"
            )
            self.api_responses.extend(results)
            self.changed_dict[0]["gathered"].extend(results)
            return

        seen_ids = set()
        results = []

        for filter_item in self.config:
            filter_entity = filter_item.get("entity_name")
            filter_pool = filter_item.get("pool_name")
            filter_switches = filter_item.get("switch") or []

            self.log.debug(
                f"manage_query: Applying filter: entity_name={filter_entity}, "
                f"pool_name={filter_pool}, switches={filter_switches}"
            )

            for res in self._all_resources:
                rid = self._get_resource_id(res)

                # Deduplicate across filter criteria
                if rid is not None and rid in seen_ids:
                    self.log.debug(
                        f"manage_query: Skipping resource id='{rid}' (already included via previous filter)"
                    )
                    continue

                res_entity = self._get_entity_name(res)
                res_pool = self._get_pool_name(res)
                res_sw = self._get_switch_ip(res)

                # Apply entity_name filter
                if filter_entity and not self._entity_names_match(
                    res_entity, filter_entity
                ):
                    self.log.debug(
                        f"manage_query: Skipping resource id='{rid}', entity_name mismatch: "
                        f"resource='{res_entity}' vs filter='{filter_entity}'"
                    )
                    continue

                # Apply pool_name filter
                if filter_pool and res_pool != filter_pool:
                    self.log.debug(
                        f"manage_query: Skipping resource id='{rid}', pool_name mismatch: "
                        f"resource='{res_pool}' vs filter='{filter_pool}'"
                    )
                    continue

                # Apply switch filter
                if filter_switches and res_sw not in filter_switches:
                    self.log.debug(
                        f"manage_query: Skipping resource id='{rid}', switch_ip not in filter: "
                        f"resource_switch='{res_sw}', filter_switches={filter_switches}"
                    )
                    continue

                self.log.debug(
                    f"manage_query: Resource id='{rid}' matched all filters "
                    f"(entity_name='{res_entity}', pool_name='{res_pool}', switch_ip='{res_sw}')"
                )
                result_dict = self._to_dict(res)
                results.append(result_dict)
                if rid is not None:
                    seen_ids.add(rid)

        self.log.info(
            f"manage_gathered: Gather complete, {len(results)} resource(s) matched filters"
        )
        self.api_responses.extend(results)
        self.changed_dict[0]["gathered"].extend(results)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def manage_state(self):
        """Validate input and dispatch to the appropriate state handler."""
        self.log.info(f"manage_state: Dispatching to state handler: state={self.state}")
        self._validate_input()

        if self.state == "merged":
            self.log.info("manage_state: Dispatching to manage_merged()")
            self.manage_merged()
        elif self.state == "deleted":
            self.log.info("manage_state: Dispatching to manage_deleted()")
            self.manage_deleted()
        elif self.state == "gathered":
            self.log.info("manage_state: Dispatching to manage_gathered()")
            self.manage_gathered()

        self.log.info(f"manage_state: State handler completed for state={self.state}")

    def exit_module(self):
        """Build and emit module output following the nd_manage_switches output structure."""
        # gathered state: return only the gathered list, no diff/response/before/after
        if self.state == "gathered":
            self.log.info(
                f"exit_module: gathered state, returning "
                f"{len(self.changed_dict[0]['gathered'])} resource(s)"
            )
            self.module.exit_json(
                changed=False,
                gathered=self.changed_dict[0]["gathered"],
            )
            return

        changed = (
            len(self.changed_dict[0]["merged"]) > 0
            or len(self.changed_dict[0]["deleted"]) > 0
        )
        if self.module.check_mode:
            self.log.info(
                "exit_module: check_mode is enabled, overriding changed=False "
                f"(would have been changed={changed})"
            )
            changed = False

        self.log.info(
            f"exit_module: merged={len(self.changed_dict[0]['merged'])}, "
            f"deleted={len(self.changed_dict[0]['deleted'])}, "
            f"gathered={len(self.changed_dict[0]['gathered'])}, "
            f"changed={changed}, check_mode={self.module.check_mode}"
        )

        output_level = self.module.params.get("output_level", "normal")
        nd_output = NDOutput(output_level=output_level)

        # format() accepts **kwargs that are merged into the output dict.
        # We inject DCNM-compatible 'diff' and 'response' keys here so that
        # integration tests written for dcnm_resource_manager still pass.
        result = nd_output.format(
            changed=changed,
            diff=self.changed_dict,
            response=self.api_responses,
        )
        self.module.exit_json(**result)


def _resolve_switch_ids(nd, fabric_name, config):
    """Build a switchIp -> switchId map from ND and return a translated deep copy of config.

    Each item's ``switch`` list is translated from management IP strings to
    switchId values.  If an IP is not found in the map it is passed through
    unchanged so the caller can decide how to handle unresolved entries.

    Args:
        nd: Initialised NDModule instance.
        fabric_name: Fabric name used to query the switch inventory.
        config: Raw config list (not mutated — a deep copy is returned).

    Returns:
        A deep copy of ``config`` with switch IPs replaced by switchId values.
    """
    log = logging.getLogger(__name__)

    log.debug(f"_resolve_switch_ids: starting for fabric='{fabric_name}', config_items={len(config or [])}")

    # Build switchIp -> switchId map
    ip_to_switch_id = {}
    raw_switches = _query_fabric_switches(nd, fabric_name)
    log.debug(f"_resolve_switch_ids: retrieved {raw_switches} raw switch(es) from ND")
    for sw in raw_switches:
        switch_id = sw.get("switchId") or sw.get("serialNumber")
        switch_ip = sw.get("fabricManagementIp") or sw.get("ip")
        log.debug(f"_resolve_switch_ids: processing switch record: switch_id='{switch_id}', switch_ip='{switch_ip}'")
        if switch_id and switch_ip:
            ip_to_switch_id[str(switch_ip).strip()] = switch_id
            log.debug(f"Mapped switchIp='{switch_ip}' -> switchId='{switch_id}'")
        else:
            log.debug(
                f"_resolve_switch_ids: skipping switch record missing id or ip: "
                f"switch_id='{switch_id}', switch_ip='{switch_ip}'"
            )
    log.debug(f"Switch IP-to-ID map built: {len(ip_to_switch_id)} entry/entries")

    # Translate switch IPs to switch IDs in a copy of the config
    config_copy = copy.deepcopy(config or [])
    log.debug(f"_resolve_switch_ids: translating switch lists for {len(config_copy)} config item(s)")
    for item in config_copy:
        raw_switch_list = item.get("switch") or []
        log.debug(
            f"_resolve_switch_ids: item entity_name='{item.get('entity_name')}', "
            f"raw_switch_list={raw_switch_list}"
        )
        if raw_switch_list:
            item["switch"] = [
                ip_to_switch_id.get(str(sw).strip(), str(sw).strip())
                for sw in raw_switch_list
            ]
            log.debug(
                f"Translated switches for entity '{item.get('entity_name')}': "
                f"{raw_switch_list} -> {item['switch']}"
            )
        else:
            log.debug(
                f"_resolve_switch_ids: no switch list for entity '{item.get('entity_name')}', skipping translation"
            )

    log.debug(f"_resolve_switch_ids: completed, returning {len(config_copy)} translated config item(s)")
    return config_copy


def _query_fabric_switches(nd, fabric_name):
    """Query all switches for a fabric and return raw switch records.

    Uses RestSend save_settings/restore_settings to temporarily force
    check_mode=False so that this read-only GET always hits the controller,
    even when the module is running in Ansible check mode.
    """
    log = logging.getLogger(__name__)
    path = f"{BasePath.path('fabrics', fabric_name, 'switches')}?max=10000"
    log.debug(f"_query_fabric_switches: querying path='{path}' for fabric='{fabric_name}'")

    # Temporarily disable check_mode for this read-only lookup so the
    # controller is queried even when Ansible runs with --check.
    rest_send = nd._get_rest_send()
    rest_send.save_settings()
    rest_send.check_mode = False
    log.debug("_query_fabric_switches: check_mode disabled for read-only GET")
    try:
        response = nd.request(path)
        log.debug(f"_query_fabric_switches: received response type={type(response).__name__}")
    finally:
        rest_send.restore_settings()
        log.debug("_query_fabric_switches: rest_send settings restored")

    if isinstance(response, list):
        log.debug(
            f"_query_fabric_switches: API returned a list of {len(response)} switch(es) "
            f"for fabric='{fabric_name}'"
        )
        return response
    if isinstance(response, dict):
        switches_list = response.get("switches", [])
        log.debug(
            f"_query_fabric_switches: API returned dict, extracted "
            f"{len(switches_list)} switch(es) for fabric='{fabric_name}'"
        )
        return switches_list
    log.warning(
        f"_query_fabric_switches: unexpected response type {type(response).__name__} "
        f"for fabric='{fabric_name}', returning empty list"
    )
    return []


def main():
    """Main entry point for nd_manage_resource_manager."""

    argument_spec = nd_argument_spec()
    argument_spec.update(
        fabric=dict(type="str", required=True),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "gathered"],
        ),
        config=dict(
            type="list",
            elements="dict",
            options=dict(
                entity_name=dict(type="str"),
                pool_type=dict(
                    type="str",
                    choices=["ID", "IP", "SUBNET"],
                ),
                pool_name=dict(type="str"),
                scope_type=dict(
                    type="str",
                    choices=[
                        "fabric",
                        "device",
                        "device_interface",
                        "device_pair",
                        "link",
                    ],
                ),
                resource=dict(type="str"),
                switch=dict(type="list", elements="str"),
            ),
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Initialize logging — always get a logger; configure file output if config is available
    log = logging.getLogger("nd.nd_manage_resource_manager")
    try:
        log_config = Log()
        log_config.config = "/Users/jeeram/ansible/collections/ansible_collections/cisco/nd/plugins/module_utils/logging_config.json"
        log_config.commit()
    except (ValueError, Exception):
        pass

    state = module.params.get("state")
    fabric = module.params.get("fabric")
    config = module.params.get("config")

    # Validate that config is provided for states that require it
    if state in ("merged", "deleted") and not config:
        module.fail_json(
            msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                state, config
            )
        )

    try:
        log.info(
            f"Starting nd_manage_resource_manager module: fabric={fabric}, state={state}"
        )
        nd = NDModule(module)
        log.info("NDModule initialized successfully")

        config_copy = _resolve_switch_ids(nd, fabric, module.params["config"])
        log.debug("Switch ID resolution complete")

        rm_module = NDResourceManagerModule(module=module, nd=nd, logger=log)
        rm_module.config = config_copy
        log.info(f"NDResourceManagerModule initialized for fabric: {fabric}")

        rm_module.manage_state()
        log.info("State management completed successfully")
        rm_module.exit_module()

    except NDModuleError as error:
        log.error(f"NDModule error: {error.msg}")
        module.fail_json(
            msg=error.msg,
            response=[
                {
                    "RETURN_CODE": error.status if error.status else -1,
                    "MESSAGE": error.msg,
                }
            ],
        )
    except Exception as error:
        log.error(f"Unexpected error during module execution: {str(error)}")
        module.fail_json(msg=str(error))


if __name__ == "__main__":
    main()
