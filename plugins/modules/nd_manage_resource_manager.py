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
          - Required when C(state=merged).
        type: str
        required: false
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
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.nd.plugins.module_utils.common.log import Log
from ansible_collections.cisco.nd.plugins.module_utils.nd_v2 import (
    NDModule,
    nd_argument_spec,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.manage_resource_manager.resource_manager_config_model import (
    ResourceManagerConfigModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.common.exceptions import NDModuleError
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.base_path import BasePath
from ansible_collections.cisco.nd.plugins.module_utils.rest.results import Results
from ansible_collections.cisco.nd.plugins.module_utils.manage_resource_manager.nd_manage_resource_manager_resources import NDResourceManagerModule


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
    """Main entry point for the nd_manage_resource_manager module."""

    # Build argument spec
    argument_spec = nd_argument_spec()
    argument_spec.update(ResourceManagerConfigModel.get_argument_spec())

    # Create Ansible module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "merged", ["config"]),
            ("state", "overridden", ["config"]),
        ],
    )

    # Initialize logging — always get a logger; configure file output if config is available
    try:
        log_config = Log()
        log_config.config = "/Users/jeeram/ansible/collections/ansible_collections/cisco/nd/plugins/module_utils/logging_config.json"
        log_config.commit()
    except (ValueError, Exception):
        pass
    log = logging.getLogger("nd.nd_manage_resource_manager")

    # Get parameters
    fabric = module.params.get("fabric")
    output_level = module.params.get("output_level")

    # Initialize Results - this collects all operation results
    results = Results()
    results.check_mode = module.check_mode
    results.action = "manage_resource_manager"

    try:
        # Initialize NDModule (uses RestSend infrastructure internally)
        nd = NDModule(module)

        log.debug("Switch ID resolution started")
        config_copy = _resolve_switch_ids(nd, fabric, module.params["config"])
        log.debug("Switch ID resolution complete")

        # Create NDResourceManagerModule
        rm_module = NDResourceManagerModule(
            nd=nd,
            results=results,
            logger=log
        )
        rm_module.config = config_copy

        # Manage state for merged, overridden, deleted
        rm_module.manage_state()

        # Exit with results
        log.info(f"State management completed successfully. Changed: {results.changed}")
        rm_module.exit_module()

    except NDModuleError as error:
        # NDModule-specific errors (API failures, authentication issues, etc.)
        log.error(f"NDModule error: {error.msg}")

        # Try to get response from RestSend if available
        try:
            results.response_current = nd.rest_send.response_current
            results.result_current = nd.rest_send.result_current
        except (AttributeError, ValueError):
            # Fallback if RestSend wasn't initialized or no response available
            results.response_current = {
                "RETURN_CODE": error.status if error.status else -1,
                "MESSAGE": error.msg,
                "DATA": error.response_payload if error.response_payload else {},
            }
            results.result_current = {
                "success": False,
                "found": False,
            }

        results.diff_current = {}
        results.register_api_call()
        results.build_final_result()

        # Add error details if debug output is requested
        if output_level == "debug":
            results.final_result["error_details"] = error.to_dict()

        log.error(f"Module failed: {results.final_result}")
        module.fail_json(msg=error.msg, **results.final_result)

    except Exception as error:
        # Unexpected errors
        log.error(f"Unexpected error during module execution: {str(error)}")
        log.error(f"Error type: {type(error).__name__}")

        # Build failed result
        results.response_current = {
            "RETURN_CODE": -1,
            "MESSAGE": f"Unexpected error: {str(error)}",
            "DATA": {},
        }
        results.result_current = {
            "success": False,
            "found": False,
        }
        results.diff_current = {}
        results.register_api_call()
        results.build_final_result()

        if output_level == "debug":
            import traceback
            results.final_result["traceback"] = traceback.format_exc()

        module.fail_json(msg=str(error), **results.final_result)


if __name__ == "__main__":
    main()
