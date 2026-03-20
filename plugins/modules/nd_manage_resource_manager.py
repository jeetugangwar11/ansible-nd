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
    type: str
    default: merged
    choices:
      - merged
      - deleted
      - query
  config:
    description:
      - A list of dictionaries containing resource configurations.
      - Optional for state C(query) (returns all resources when omitted).
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

- name: Query all resources
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: query

- name: Query resources by entity name
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: query
    config:
      - entity_name: "l3_vni_fabric"
      - entity_name: "loopback_dev"

- name: Query resources by pool name
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: query
    config:
      - pool_name: "L3_VNI"
      - pool_name: "LOOPBACK_ID"

- name: Query resources by switch
  cisco.nd.nd_manage_resource_manager:
    fabric: my_fabric
    state: query
    config:
      - switch:
          - 192.168.10.201
"""

RETURN = """
changed:
  description: Whether any changes were made.
  returned: always
  type: bool
diff:
  description: Tracking of merged and deleted resources.
  returned: always
  type: list
  elements: dict
  sample: [{"merged": [], "deleted": [], "query": [], "debugs": []}]
response:
  description: API responses received during module execution.
  returned: always
  type: list
  elements: dict
before:
  description: State before module execution (always empty list for this module).
  returned: always
  type: list
after:
  description: State after module execution (always empty list for this module).
  returned: always
  type: list
"""

import ipaddress

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.nd.plugins.module_utils.nd_v2 import (
    NDModule,
    NDModuleError,
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
        self.log = logger

        self.fabric = module.params["fabric"]
        self.state = module.params["state"]
        self.config = module.params.get("config") or []

        # DCNM-compatible tracking dicts
        self.changed_dict = [{"merged": [], "deleted": [], "query": [], "debugs": []}]
        self.api_responses = []

        # Cached GET results
        self._all_resources = []
        self._resources_fetched = False

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def _validate_resource_params(self, item):
        """Validate pool_type/pool_name/scope_type compatibility (mirroring dcnm logic)."""
        pool_type = item.get("pool_type")
        pool_name = item.get("pool_name")
        scope_type = item.get("scope_type")

        if pool_type == "ID":
            check_key = pool_name
        elif pool_type == "IP":
            check_key = "IP_POOL"
        elif pool_type == "SUBNET":
            check_key = "SUBNET"
        else:
            return (
                False,
                "Given pool type = '{0}' is invalid,"
                " Allowed pool types = ['ID', 'IP', 'SUBNET']".format(pool_type),
            )

        allowed_scopes = _POOLNAME_TO_SCOPE_TYPE.get(check_key)
        if allowed_scopes is None:
            return False, "Given pool name '{0}' is not valid".format(pool_name)

        if scope_type not in allowed_scopes:
            return (
                False,
                "Given scope type '{0}' is not valid for pool name = '{1}',"
                " Allowed scope_types = {2}".format(
                    scope_type, pool_name, allowed_scopes
                ),
            )

        return True, ""

    def _validate_input(self):
        """Validate playbook config fields based on the current state."""
        if not self.config:
            if self.state in ("merged", "deleted"):
                self.module.fail_json(
                    msg="'config' element is mandatory for state '{0}'".format(
                        self.state
                    )
                )
            return

        for item in self.config:
            if self.state != "query":
                # Mandatory parameter checks
                for field in ("scope_type", "pool_type", "pool_name", "entity_name"):
                    if item.get(field) is None:
                        self.module.fail_json(
                            msg="Mandatory parameter '{0}' missing".format(field)
                        )

                # Switch required for non-fabric scopes
                if item.get("scope_type") != "fabric" and not item.get("switch"):
                    self.module.fail_json(msg="switch : Required parameter not found")

            # Validate pool_name / scope_type combination (only when pool_type is provided)
            if item.get("pool_type") is not None:
                rc, mesg = self._validate_resource_params(item)
                if not rc:
                    self.module.fail_json(msg=mesg)

            # Pydantic cross-field validation for merged/deleted
            if self.state != "query":
                try:
                    ResourceManagerConfigModel.from_config(item)
                except Exception as exc:
                    self.module.fail_json(
                        msg="Invalid parameters in playbook: {0}".format(str(exc))
                    )

    # ------------------------------------------------------------------
    # ND API interaction helpers
    # ------------------------------------------------------------------

    def _get_all_resources(self):
        """Fetch all resources for the fabric once and cache them."""
        if self._resources_fetched:
            return

        ep = EpManageFabricResourcesGet(fabric_name=self.fabric)
        try:
            data = self.nd.request(ep.path, ep.verb)
        except NDModuleError as exc:
            if exc.status == 404:
                # Fabric has no resources yet — that is valid
                self._resources_fetched = True
                return
            raise

        # The ND API may return a list directly or {"resources": [...], "meta": {...}}
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict) and "resources" in data:
            raw_list = data["resources"]
        elif isinstance(data, dict) and data:
            raw_list = [data]
        else:
            raw_list = []

        for raw in raw_list:
            try:
                self._all_resources.append(ResourceModel.from_response(raw))
            except Exception:
                # If parsing fails, keep the raw dict so we can still match on it
                self._all_resources.append(raw)

        self._resources_fetched = True

    # ------------------------------------------------------------------
    # Resource attribute accessors (handle both ResourceModel and raw dict)
    # ------------------------------------------------------------------

    def _attr(self, resource, model_attr, dict_key):
        if hasattr(resource, model_attr):
            return getattr(resource, model_attr)
        if isinstance(resource, dict):
            return resource.get(dict_key)
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
        elif isinstance(resource, dict):
            sd = resource.get("scopeDetails") or {}
            raw = sd.get("scopeType")
        else:
            return None
        return _API_SCOPE_TYPE_TO_PLAYBOOK.get(raw, raw) if raw else None

    def _get_switch_ip(self, resource):
        """Return the switch IP from scopeDetails."""
        if hasattr(resource, "scope_details") and resource.scope_details:
            return getattr(resource.scope_details, "switch_ip", None)
        if isinstance(resource, dict):
            sd = resource.get("scopeDetails") or {}
            return sd.get("switchIp")
        return None

    def _get_fabric_name(self, resource):
        """Return fabric name from scopeDetails."""
        if hasattr(resource, "scope_details") and resource.scope_details:
            return getattr(resource.scope_details, "fabric_name", None)
        if isinstance(resource, dict):
            sd = resource.get("scopeDetails") or {}
            return sd.get("fabricName")
        return None

    def _to_dict(self, resource):
        """Convert a ResourceModel (or raw dict) to a plain dict for response output."""
        if hasattr(resource, "to_payload"):
            return resource.to_payload()
        return resource

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------

    def _entity_names_match(self, e1, e2):
        """Compare entity names in order-insensitive way (mirrors dcnm logic)."""
        if e1 is None or e2 is None:
            return False
        return sorted(e1.split("~")) == sorted(e2.split("~"))

    def _compare_resource_values(self, have, want):
        """Compare resource values — IPv4/IPv6 aware (mirrors dcnm_rm_compare_resource_values)."""
        if have is None and want is None:
            return True
        if have is None or want is None:
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

        if th == tw == "address":
            return vh.exploded == vw.exploded
        if th == tw == "network":
            return vh == vw
        return have == want

    def _find_matching_resources(
        self, entity_name, pool_name, scope_type, switch_ip=None
    ):
        """Find cached resources matching the given criteria."""
        results = []
        for res in self._all_resources:
            res_entity = self._get_entity_name(res)
            res_pool = self._get_pool_name(res)
            res_scope = self._get_scope_type(res)

            if not self._entity_names_match(res_entity, entity_name):
                continue
            if res_pool != pool_name:
                continue
            if res_scope != scope_type:
                continue

            # For non-fabric scopes, only match if switch_ip aligns
            if scope_type != "fabric" and switch_ip is not None:
                res_sw = self._get_switch_ip(res)
                if res_sw != switch_ip:
                    continue

            results.append(res)
        return results

    # ------------------------------------------------------------------
    # API payload builders
    # ------------------------------------------------------------------

    def _build_scope_details(self, scope_type, switch_ip=None):
        """Build the scopeDetails dict for the ND Manage API."""
        api_scope = _SCOPE_TYPE_TO_API[scope_type]

        if scope_type == "fabric":
            return {
                "scopeType": api_scope,
                "fabricName": self.fabric,
            }
        return {
            "scopeType": api_scope,
            "switchIp": switch_ip,
        }

    def _build_create_payload(self, item, switch_ip=None):
        """Build POST body for resource creation in ND Manage API format."""
        resource_value = item.get("resource")
        payload = {
            "poolName": item["pool_name"],
            "entityName": item["entity_name"],
            "scopeDetails": self._build_scope_details(item["scope_type"], switch_ip),
            "isPreAllocated": True,
        }
        if resource_value is not None:
            payload["resourceValue"] = str(resource_value)
        return payload

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def manage_merged(self):
        """Create resources that don't exist or have a different value."""
        self._get_all_resources()

        for item in self.config:
            scope_type = item["scope_type"]
            pool_name = item["pool_name"]
            entity_name = item["entity_name"]
            resource_value = item.get("resource")
            switches = item.get("switch") or [None]

            if scope_type == "fabric":
                switches = [None]

            for sw in switches:
                matches = self._find_matching_resources(
                    entity_name, pool_name, scope_type, switch_ip=sw
                )

                if matches:
                    existing_value = self._get_resource_value(matches[0])
                    if self._compare_resource_values(existing_value, resource_value):
                        # Already exists with the same value — idempotent, skip
                        continue

                payload = self._build_create_payload(item, switch_ip=sw)

                if self.module.check_mode:
                    self.changed_dict[0]["merged"].append(payload)
                    self.api_responses.append({"RETURN_CODE": 200, "DATA": payload})
                    continue

                ep = EpManageFabricResourcesPost(fabric_name=self.fabric)
                # API expects {"resources": [<resource_object>]}
                resp_data = self.nd.request(
                    ep.path, ep.verb, data={"resources": [payload]}
                )
                self.changed_dict[0]["merged"].append(payload)
                # Unwrap the response — API returns {"resources": [{...}]}
                if isinstance(resp_data, dict) and "resources" in resp_data:
                    items = resp_data["resources"]
                    self.api_responses.append(
                        {"RETURN_CODE": 200, "DATA": items[0] if items else resp_data}
                    )
                else:
                    self.api_responses.append({"RETURN_CODE": 200, "DATA": resp_data})

    def manage_deleted(self):
        """Remove resources that exist in the fabric inventory."""
        self._get_all_resources()

        resource_ids = []

        for item in self.config:
            scope_type = item["scope_type"]
            pool_name = item["pool_name"]
            entity_name = item["entity_name"]
            switches = item.get("switch") or [None]

            if scope_type == "fabric":
                switches = [None]

            for sw in switches:
                matches = self._find_matching_resources(
                    entity_name, pool_name, scope_type, switch_ip=sw
                )
                for res in matches:
                    rid = self._get_resource_id(res)
                    if rid is not None and rid not in resource_ids:
                        resource_ids.append(rid)

        if not resource_ids:
            # Nothing to delete — idempotent
            return

        self.changed_dict[0]["deleted"].extend(str(r) for r in resource_ids)

        if self.module.check_mode:
            self.api_responses.append(
                {"RETURN_CODE": 200, "DATA": {"resourceIds": resource_ids}}
            )
            return

        ep = EpManageFabricResourcesActionsRemovePost(fabric_name=self.fabric)
        remove_req = RemoveResourcesByIdsRequest(resource_ids=resource_ids)
        resp_data = self.nd.request(ep.path, ep.verb, data=remove_req.to_payload())
        self.api_responses.append({"RETURN_CODE": 200, "DATA": resp_data})

    def manage_query(self):
        """Return resources filtered by config criteria (or all resources if no config)."""
        self._get_all_resources()

        if not self.config:
            # No filters — return everything
            results = [self._to_dict(r) for r in self._all_resources]
            self.changed_dict[0]["query"].extend(results)
            self.api_responses.extend(results)
            return

        seen_ids = set()
        results = []

        for filter_item in self.config:
            filter_entity = filter_item.get("entity_name")
            filter_pool = filter_item.get("pool_name")
            filter_switches = filter_item.get("switch") or []

            for res in self._all_resources:
                rid = self._get_resource_id(res)

                # Deduplicate across filter criteria
                if rid is not None and rid in seen_ids:
                    continue

                res_entity = self._get_entity_name(res)
                res_pool = self._get_pool_name(res)
                res_sw = self._get_switch_ip(res)

                # Apply entity_name filter
                if filter_entity and not self._entity_names_match(
                    res_entity, filter_entity
                ):
                    continue

                # Apply pool_name filter
                if filter_pool and res_pool != filter_pool:
                    continue

                # Apply switch filter
                if filter_switches and res_sw not in filter_switches:
                    continue

                result_dict = self._to_dict(res)
                results.append(result_dict)
                if rid is not None:
                    seen_ids.add(rid)

        self.changed_dict[0]["query"].extend(results)
        self.api_responses.extend(results)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def manage_state(self):
        """Validate input and dispatch to the appropriate state handler."""
        self._validate_input()

        if self.state == "merged":
            self.manage_merged()
        elif self.state == "deleted":
            self.manage_deleted()
        elif self.state == "query":
            self.manage_query()

    def exit_module(self):
        """Build and emit module output using NDOutput with DCNM-compatible extras."""
        changed = (
            len(self.changed_dict[0]["merged"]) > 0
            or len(self.changed_dict[0]["deleted"]) > 0
        )
        if self.module.check_mode:
            changed = False

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


def main():
    """Main entry point for nd_manage_resource_manager."""

    argument_spec = nd_argument_spec()
    argument_spec.update(
        fabric=dict(type="str", required=True),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "query"],
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

    state = module.params.get("state")
    config = module.params.get("config")

    # Validate that config is provided for states that require it
    if state in ("merged", "deleted") and not config:
        module.fail_json(
            msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                state, config
            )
        )

    try:
        nd = NDModule(module)
        rm_module = NDResourceManagerModule(module=module, nd=nd)
        rm_module.manage_state()
        rm_module.exit_module()

    except NDModuleError as error:
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
        module.fail_json(msg=str(error))


if __name__ == "__main__":
    main()
