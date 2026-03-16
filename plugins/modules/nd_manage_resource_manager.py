#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: nd_manage_resource_manager
short_description: Nexus Dashboard ansible module for managing resources.
version_added: "0.7.0"
description:
    - Nexus Dashboard ansible module for creating, deleting and querying resources
      via the ND Manage API (C(/api/v1/manage)).
author: Cisco Systems
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
    required: false
    choices:
      - merged
      - deleted
      - query
    default: merged
  config:
    description:
      - A list of dictionaries containing resources and switch information.
    type: list
    elements: dict
    suboptions:
      entity_name:
        description:
          - A unique name which identifies the entity to which the resource is allocated to.
          - The format of this parameter depends on the scope_type. The details are provided in
            the EXAMPLES section.
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
          - The value will be an integer if pool_type is ID.
          - The value will be an IPv4/IPv6 address if pool_type is IP.
          - The value will be an IPv4 address/net_mask or IPv6 address/net_mask if pool_type is SUBNET.
        type: str
        required: false
      switch:
        description:
          - IP address or DNS name of the management interface of the switch to which
            the allocated resource is assigned to.
        type: list
        elements: str
        required: false
extends_documentation_fragment:
- cisco.nd.modules
"""

EXAMPLES = """
# Entity name format
# ==================
#
# The format of the entity name depends on the scope_type of the resource being allocated.

# Scope Type                Entity Name
# =====================================
# Fabric                    Eg: My_Network_30000
# Device                    Eg: loopback0
# Device Pair               Eg: FDO21331S8T~FDO21332E6X~vPC1
# Device Interface          Eg: FDO21332E6X~Ethernet1/13
# Link                      Eg: FDO21332E6X~Ethernet1/3~FDO21331S8T~Ethernet1/3

# where FDO21331S8T and FDO21332E6X are switch serial numbers

# This module supports the following states:

# Merged:
#   Resources defined in the playbook will be merged into the target fabric.
#     - If the Resource does not exist it will be added.
#     - If the Resource exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Resources that are not specified in the playbook will be untouched.
#
# Deleted:
#   Resources defined in the playbook will be deleted.
#
# Query:
#   Returns the current ND state for the Resources listed in the playbook.

# CREATING RESOURCES
# ==================
- name: Create Resources
  cisco.nd.nd_manage_resource_manager:
    state: merged                               # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "L3_VNI"                     # Based on the 'pool_type', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        resource: "101"                         # The value of the resource being created

      - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "VPC_ID"                     # Based on the 'pool_type', select appropriate name
        scope_type: "device_pair"               # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is to be attached
          - 192.175.1.1
          - 192.175.1.2
        resource: "500"                         # The value of the resource being created

      - entity_name: "mmudigon-2"               # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "LOOPBACK0_IP_POOL"          # Based on the 'pool_type', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        resource: "110.1.1.1"                   # The value of the resource being created

      - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "LOOPBACK1_IP_POOL"          # Based on the 'pool_type', select appropriate name
        scope_type: "device_interface"          # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is to be attached
          - 192.175.1.1
        resource: "fe80::04"                    # The value of the resource being created

      - entity_name: "9M99N34RDED~Ethernet1/3~9NXHSNTEO6C~Ethernet1/3"  # A unique name to identify the resource
        pool_type: "SUBNET"                     # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "SUBNET"                     # Based on the 'pool_type', select appropriate name
        scope_type: "link"                      # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is to be attached
          - 192.175.1.1
        resource: "fe80:05::05/64"

# DELETING RESOURCES
# ==================

- name: Delete Resources
  cisco.nd.nd_manage_resource_manager:
    state: deleted                              # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "L3_VNI"                     # Based on the 'pool_type', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']

      - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "VPC_ID"                     # Based on the 'pool_type', select appropriate name
        scope_type: "device_pair"               # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
          - 192.175.1.2

      - entity_name: "mmudigon-2"               # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "LOOPBACK0_IP_POOL"          # Based on the 'pool_type', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']

      - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "LOOPBACK1_IP_POOL"          # Based on the 'pool_type', select appropriate name
        scope_type: "device_interface"          # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

      - entity_name: "9M99N34RDED~Ethernet1/3~9NXHSNTEO6C~Ethernet1/3"  # A unique name to identify the resource
        pool_type: "SUBNET"                     # choose from ['ID', 'IP', 'SUBNET']
        pool_name: "SUBNET"                     # Based on the 'pool_type', select appropriate name
        scope_type: "link"                      # choose from ['fabric', 'device', 'device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

# QUERYING RESOURCES
# ==================

- name: Query all Resources - no filters
  cisco.nd.nd_manage_resource_manager:
    state: query                               # choose from [merged, deleted, query]
    fabric: test_fabric

- name: Query Resources - filter by entity name
  cisco.nd.nd_manage_resource_manager:
    state: query                                # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
      - entity_name: "loopback_dev"             # A unique name to identify the resource
      - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
      - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
      - entity_name: "9M99N34RDED~Ethernet1/2~9NXHSNTEO6C~Ethernet1/2"

- name: Query Resources - filter by switch
  cisco.nd.nd_manage_resource_manager:
    state: query                                # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

- name: Query Resources - filter by fabric and pool name
  cisco.nd.nd_manage_resource_manager:
    state: query                                # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - pool_name: "L3_VNI"                     # Based on the 'pool_type', select appropriate name
      - pool_name: "VPC_ID"                     # Based on the 'pool_type', select appropriate name
      - pool_name: "SUBNET"                     # Based on the 'pool_type', select appropriate name

- name: Query Resources - filter by switch and pool name
  cisco.nd.nd_manage_resource_manager:
    state: query                                # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - pool_name: "L3_VNI"                     # Based on the 'pool_type', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
      - pool_name: "LOOPBACK_ID"                # Based on the 'pool_type', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
      - pool_name: "VPC_ID"                     # Based on the 'pool_type', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.2

- name: Query Resources - mixed query
  cisco.nd.nd_manage_resource_manager:
    state: query                                # choose from [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l2_vni_fabric"            # A unique name to identify the resource
      - switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
      - pool_name: "LOOPBACK_ID"                # Based on the 'pool_type', select appropriate name
      - pool_name: "VPC_ID"                     # Based on the 'pool_type', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
"""

RETURN = r"""
"""

import copy
import ipaddress
import logging
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.nd.plugins.module_utils.nd import (
    NDModule,
    nd_argument_spec,
)
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.nd_resource_manager.nd_manage_resource_manager import (
    EpManageFabricResourcesGet,
    EpManageFabricResourcesPost,
    EpManageFabricResourcesActionsRemovePost,
    EpManageFabricResourcesActionsRemovePostResource,
)
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.base_path import (
    BasePath,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.AnsibleResourceConfigModel import (
    AnsibleResourceConfigModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.RemoveResourcesByIdsRequestModel import (
    RemoveResourcesByIdsRequestModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.common.log import Log

# Bundled logging config: plugins/module_utils/logging_config.json
# Used as fallback when ND_LOGGING_CONFIG environment variable is not set.
_ND_LOG_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "module_utils",
    "logging_config.json",
)

log = logging.getLogger("nd.nd_manage_resource_manager")

# Scope type translation: Ansible/DCNM style → ND API style
SCOPE_TYPE_MAP = {
    "fabric": "Fabric",
    "device": "Device",
    "device_interface": "DeviceInterface",
    "device_pair": "DevicePair",
    "link": "Link",
}


class NDManageResourceManager:
    """
    Ansible module class for managing ND fabric resources via the Manage API.

    Supports states: merged, deleted, query.
    Uses the ND /api/v1/manage/fabrics/{fabric}/resources endpoint family.
    Switch IPs are resolved to serial numbers via /api/v1/manage/inventory/switches.
    """

    def __init__(self, module, nd):
        """
        Initialize the NDManageResourceManager.

        Parameters:
            module (AnsibleModule): The Ansible module instance.
            nd (NDModule): The ND module helper providing request/fail_json/exit_json.
        """
        self.module = module
        self.nd = nd
        self.params = module.params

        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.state = module.params["state"]

        # Validated config entries from validate_input()
        self.rm_info = []

        # Desired and current state
        self.want = []
        self.have = []

        # Delta lists
        self.diff_create = []
        self.diff_delete = []

        # Pool-level resource cache: key=(scope_value, pool_name) → list of resource dicts
        self.res_pools = {}

        # IP → serial number map (populated by build_ip_sn_map)
        self.ip_sn = {}

        # Result dict for exit_json
        self.result = dict(changed=False, diff=[], response=[])

        log.debug(
            "__init__: fabric=%s state=%s config_count=%d",
            self.fabric,
            self.state,
            len(self.config) if self.config else 0,
        )

        # Build the IP→SN map at startup when config with switch IPs may be present
        self.build_ip_sn_map()
        log.debug("__init__: completed initialisation for fabric=%s", self.fabric)

    # -------------------------------------------------------------------------
    # Switch IP → Serial Number Resolution (Option B)
    # -------------------------------------------------------------------------

    def build_ip_sn_map(self):
        """
        Build a mapping of management IP address → switch serial number by
        querying GET /api/v1/manage/inventory/switches.

        Populates self.ip_sn = {mgmtIp: serialNumber, ...}.
        Logs a warning if the inventory endpoint is unavailable but does not
        fail immediately; the caller will fail_json when a specific IP cannot
        be resolved.
        """
        inventory_path = BasePath.path("inventory", "switches")
        log.debug("build_ip_sn_map: querying inventory at %s", inventory_path)
        try:
            response = self.nd.request(inventory_path, method="GET")
        except Exception as exc:
            log.warning("build_ip_sn_map: failed to query inventory: %s", exc)
            return

        if not response:
            log.warning("build_ip_sn_map: empty response from inventory endpoint")
            return

        # The inventory response may be a list directly, a dict with an 'items'
        # key, or a dict with a 'data' key depending on ND version.
        switches = []
        if isinstance(response, list):
            switches = response
        elif isinstance(response, dict):
            for key in ("items", "data", "switches"):
                if key in response:
                    switches = response[key]
                    break
            if not switches:
                # Fallback: treat the whole response as a single switch record
                switches = [response] if response else []

        for sw in switches:
            mgmt_ip = sw.get("mgmtIp") or sw.get("managementIp") or sw.get("ipAddress")
            serial = sw.get("serialNumber") or sw.get("serialNum") or sw.get("serialNo")
            if mgmt_ip and serial:
                self.ip_sn[str(mgmt_ip).strip()] = str(serial).strip()

        log.debug("build_ip_sn_map: resolved %d switch(es)", len(self.ip_sn))

    def resolve_switch_to_serial(self, ip_or_host):
        """
        Resolve a switch IP address or hostname to its serial number.

        Uses self.ip_sn populated by build_ip_sn_map().  If the entry is not
        found in the map (e.g. serial number provided directly) it is returned
        as-is, allowing the playbook to pass serial numbers directly when
        preferred.

        Parameters:
            ip_or_host (str): Management IP address, hostname, or serial number.

        Returns:
            str: Serial number for the switch.
        """
        resolved = self.ip_sn.get(str(ip_or_host).strip())
        if resolved:
            log.debug("resolve_switch_to_serial: %s → %s", ip_or_host, resolved)
            return resolved
        # Not found in map – assume caller passed a serial number directly
        log.debug(
            "resolve_switch_to_serial: %s not in ip_sn map, using as-is", ip_or_host
        )
        return str(ip_or_host).strip()

    def translate_switch_info(self, config):
        """
        Translate switch IP addresses / hostnames in the config list to serial
        numbers in-place, using self.ip_sn.

        Parameters:
            config (list[dict]): The playbook config list. Modified in place.
        """
        log.debug(
            "translate_switch_info: called with config_count=%d",
            len(config) if config else 0,
        )
        if config is None:
            log.debug("translate_switch_info: config is None, returning early")
            return
        for cfg in config:
            if not cfg.get("switch"):
                continue
            original_switches = list(cfg["switch"])
            cfg["switch"] = [self.resolve_switch_to_serial(sw) for sw in cfg["switch"]]
            log.debug(
                "translate_switch_info: entity_name=%s switches %s → %s",
                cfg.get("entity_name", "<unknown>"),
                original_switches,
                cfg["switch"],
            )
        log.debug("translate_switch_info: translation complete")

    # -------------------------------------------------------------------------
    # Input Validation
    # -------------------------------------------------------------------------

    def validate_input(self):
        """
        Validate the playbook config based on the current state.

        For merged/deleted states each config entry must contain the required
        fields (entity_name, pool_type, pool_name, scope_type) and pass
        AnsibleResourceConfigModel validation.

        For the query state all fields are optional; only entity_name,
        pool_name and switch are recognized.

        Populates self.rm_info with validated config entries.
        """
        log.debug(
            "validate_input: state=%s config_count=%d",
            self.state,
            len(self.config) if self.config else 0,
        )
        if self.config is None:
            log.debug("validate_input: config is None, skipping validation")
            return

        for item in self.config:
            if self.state == "query":
                self._validate_query_item(item)
            else:
                self._validate_merge_delete_item(item)
        log.debug(
            "validate_input: rm_info populated with %d entry/entries", len(self.rm_info)
        )

    def _validate_merge_delete_item(self, item):
        """
        Validate a single config item for merged/deleted states using
        AnsibleResourceConfigModel (Pydantic).

        Parameters:
            item (dict): A single config element from self.config.
        """
        log.debug(
            "_validate_merge_delete_item: validating item entity_name=%s pool_type=%s pool_name=%s scope_type=%s",
            item.get("entity_name"),
            item.get("pool_type"),
            item.get("pool_name"),
            item.get("scope_type"),
        )
        # Check mandatory fields before handing off to Pydantic
        for field in ("entity_name", "pool_type", "pool_name", "scope_type"):
            if item.get(field) is None:
                self.module.fail_json(
                    msg="Mandatory parameter '{0}' missing in config entry: {1}".format(
                        field, item
                    )
                )

        try:
            validated = AnsibleResourceConfigModel(**item)
            validated_data = validated.model_dump()
            self.rm_info.append(validated_data)
            log.debug(
                "_validate_merge_delete_item: validated OK entity_name=%s pool_name=%s scope_type=%s resource=%s",
                validated_data.get("entity_name"),
                validated_data.get("pool_name"),
                validated_data.get("scope_type"),
                validated_data.get("resource"),
            )
        except Exception as exc:
            # Pydantic ValidationError or other
            log.debug(
                "_validate_merge_delete_item: validation failed for item=%s error=%s",
                item,
                exc,
            )
            self.module.fail_json(
                msg="Invalid parameters in playbook config: {0}".format(str(exc))
            )

    def _validate_query_item(self, item):
        """
        Validate a single config item for the query state.

        Only entity_name, pool_name and switch are accepted.  All are optional.

        Parameters:
            item (dict): A single config element from self.config.
        """
        log.debug(
            "_validate_query_item: item keys=%s entity_name=%s pool_name=%s switch=%s",
            sorted(item.keys()),
            item.get("entity_name"),
            item.get("pool_name"),
            item.get("switch"),
        )
        allowed = {"entity_name", "pool_name", "switch"}
        unknown = set(item.keys()) - allowed
        if unknown:
            self.module.fail_json(
                msg="Invalid parameters for query state: {0}. Allowed: {1}".format(
                    sorted(unknown), sorted(allowed)
                )
            )
        # Normalize switch IPs to serials even for query
        entry = copy.deepcopy(item)
        if entry.get("switch"):
            entry["switch"] = [
                self.resolve_switch_to_serial(sw) for sw in entry["switch"]
            ]
        self.rm_info.append(entry)
        log.debug(
            "_validate_query_item: accepted entry=%s",
            entry,
        )

    # -------------------------------------------------------------------------
    # Payload Construction
    # -------------------------------------------------------------------------

    def build_resource_payload(self, rm_elem, switch_serial):
        """
        Build the ND API payload for a single resource allocation.

        Parameters:
            rm_elem (dict): Validated resource config entry from self.rm_info.
            switch_serial (str|None): Serial number of the target switch, or
                None when scope_type is 'fabric'.

        Returns:
            dict: Payload dict compatible with POST /fabrics/{fabric}/resources.
        """
        log.debug(
            "build_resource_payload: entity_name=%s pool_name=%s scope_type=%s switch_serial=%s resource=%s",
            rm_elem.get("entity_name"),
            rm_elem.get("pool_name"),
            rm_elem.get("scope_type"),
            switch_serial,
            rm_elem.get("resource"),
        )
        scope_type = rm_elem["scope_type"]
        payload = {
            "poolName": rm_elem["pool_name"],
            "scopeType": SCOPE_TYPE_MAP[scope_type],
            "entityName": rm_elem["entity_name"],
            "resource": rm_elem.get("resource"),
            "scopeValue": self.fabric if scope_type == "fabric" else switch_serial,
        }
        log.debug(
            "build_resource_payload: built payload poolName=%s scopeType=%s entityName=%s scopeValue=%s resource=%s",
            payload["poolName"],
            payload["scopeType"],
            payload["entityName"],
            payload["scopeValue"],
            payload["resource"],
        )
        return payload

    # -------------------------------------------------------------------------
    # Want / Have
    # -------------------------------------------------------------------------

    def get_want(self):
        """
        Populate self.want with API payloads derived from self.rm_info.

        Each config entry is expanded per switch (for non-fabric scopes).
        """
        log.debug(
            "get_want: rm_info_count=%d config_is_none=%s",
            len(self.rm_info),
            self.config is None,
        )
        if self.config is None or not self.rm_info:
            log.debug("get_want: nothing to process, returning early")
            return

        for rm_elem in self.rm_info:
            switches = rm_elem.get("switch") or []
            log.debug(
                "get_want: processing entity_name=%s switch_count=%d",
                rm_elem.get("entity_name"),
                len(switches),
            )
            if switches:
                for sw_serial in switches:
                    payload = self.build_resource_payload(rm_elem, sw_serial)
                    if payload not in self.want:
                        self.want.append(payload)
            else:
                payload = self.build_resource_payload(rm_elem, None)
                if payload not in self.want:
                    self.want.append(payload)
        log.debug("get_want: want populated with %d entry/entries", len(self.want))

    def get_have(self):
        """
        Populate self.have by querying the ND API for existing resources that
        match the entries in self.want.

        Uses EpManageFabricResourcesGet, caching responses keyed by
        (scope_value, pool_name) to avoid redundant API calls.
        """
        log.debug("get_have: querying ND for %d want entry/entries", len(self.want))
        if not self.want:
            log.debug("get_have: want is empty, returning early")
            return

        for res in self.want:
            log.debug(
                "get_have: looking up entityName=%s poolName=%s scopeType=%s scopeValue=%s",
                res.get("entityName"),
                res.get("poolName"),
                res.get("scopeType"),
                res.get("scopeValue"),
            )
            have = self._get_resource_from_nd(res)
            if have and have not in self.have:
                self.have.append(have)
        log.debug("get_have: have populated with %d entry/entries", len(self.have))

    def _get_resource_from_nd(self, res):
        """
        Fetch the existing resource from ND that matches the given payload.

        Parameters:
            res (dict): A payload dict from self.want.

        Returns:
            dict: The matching resource dict from ND, or an empty dict/None.
        """
        cache_key = (res["scopeValue"], res["poolName"])

        if cache_key not in self.res_pools:
            endpoint = EpManageFabricResourcesGet(fabric_name=self.fabric)
            # For non-fabric scopes, narrow the query by switch serial and pool name
            if res["scopeType"] != "Fabric":
                endpoint.endpoint_params.switch_id = res["scopeValue"]
            endpoint.endpoint_params.pool_name = res["poolName"]

            log.debug("_get_resource_from_nd: GET %s", endpoint.path)
            response = self.nd.request(endpoint.path, method=endpoint.verb.value)

            if response:
                # Normalise: response may be a list or a dict with 'items'/'data'
                self.res_pools[cache_key] = self._extract_resource_list(response)
            else:
                self.res_pools[cache_key] = []

        pool_resources = self.res_pools[cache_key]
        for relem in pool_resources:
            if self._match_resources(relem, res):
                return relem
        return None

    def _extract_resource_list(self, response):
        """
        Normalise the GET resources response into a plain list of resource dicts.

        Parameters:
            response: Raw response from nd.request().

        Returns:
            list[dict]: List of resource records.
        """
        log.debug(
            "_extract_resource_list: response type=%s",
            type(response).__name__,
        )
        if isinstance(response, list):
            log.debug(
                "_extract_resource_list: response is list, count=%d", len(response)
            )
            return response
        if isinstance(response, dict):
            for key in ("items", "data", "resources"):
                if key in response:
                    val = response[key]
                    result = val if isinstance(val, list) else [val]
                    log.debug(
                        "_extract_resource_list: extracted key=%s count=%d",
                        key,
                        len(result),
                    )
                    return result
        log.debug(
            "_extract_resource_list: no recognised structure, returning empty list"
        )
        return []

    # -------------------------------------------------------------------------
    # Comparison Helpers
    # -------------------------------------------------------------------------

    def _compare_entity_names(self, e1, e2):
        """
        Compare two entity names in a tilde-order-insensitive manner.

        DCNM/ND may reverse the order of serial numbers in some entity names
        (e.g. 'A~B~label' vs 'B~A~label').  Sorting the split parts before
        comparing handles this.

        Parameters:
            e1 (str): First entity name.
            e2 (str): Second entity name.

        Returns:
            bool: True if the entity names are equivalent.
        """
        result = sorted(e1.split("~")) == sorted(e2.split("~"))
        log.debug(
            "_compare_entity_names: e1=%s e2=%s match=%s",
            e1,
            e2,
            result,
        )
        return result

    def _compare_resource_values(self, r1, r2):
        """
        Compare two resource values, handling IPv4, IPv6, CIDR and integer forms.

        Parameters:
            r1 (str): First resource value.
            r2 (str): Second resource value.

        Returns:
            bool: True if the resource values are equivalent.
        """
        log.debug("_compare_resource_values: comparing r1=%s r2=%s", r1, r2)
        r1 = str(r1)
        r2 = str(r2)

        def _has_ipv4(v):
            return "." in v

        def _has_ipv6(v):
            return ":" in v

        def _has_prefix(v):
            return "/" in v

        if _has_ipv4(r1) and _has_ipv4(r2):
            try:
                if _has_prefix(r1) and _has_prefix(r2):
                    n1 = ipaddress.ip_network(r1, strict=False)
                    n2 = ipaddress.ip_network(r2, strict=False)
                    ipv4_net_result = str(n1) == str(n2)
                    log.debug(
                        "_compare_resource_values: IPv4-network r1=%s r2=%s equal=%s",
                        n1,
                        n2,
                        ipv4_net_result,
                    )
                    return ipv4_net_result
                elif not _has_prefix(r1) and not _has_prefix(r2):
                    ipv4_result = (
                        ipaddress.IPv4Address(r1).exploded
                        == ipaddress.IPv4Address(r2).exploded
                    )
                    log.debug(
                        "_compare_resource_values: IPv4-address r1=%s r2=%s equal=%s",
                        r1,
                        r2,
                        ipv4_result,
                    )
                    return ipv4_result
            except ValueError:
                pass

        if _has_ipv6(r1) and _has_ipv6(r2):
            try:
                if _has_prefix(r1) and _has_prefix(r2):
                    n1 = ipaddress.ip_network(r1, strict=False)
                    n2 = ipaddress.ip_network(r2, strict=False)
                    ipv6_net_result = str(n1) == str(n2)
                    log.debug(
                        "_compare_resource_values: IPv6-network r1=%s r2=%s equal=%s",
                        n1,
                        n2,
                        ipv6_net_result,
                    )
                    return ipv6_net_result
                elif not _has_prefix(r1) and not _has_prefix(r2):
                    ipv6_result = (
                        ipaddress.IPv6Address(r1).exploded
                        == ipaddress.IPv6Address(r2).exploded
                    )
                    log.debug(
                        "_compare_resource_values: IPv6-address r1=%s r2=%s equal=%s",
                        r1,
                        r2,
                        ipv6_result,
                    )
                    return ipv6_result
            except ValueError:
                pass

        result = r1 == r2
        log.debug("_compare_resource_values: r1=%s r2=%s equal=%s", r1, r2, result)
        return result

    def _match_resources(self, have_res, want_res):
        """
        Determine whether an existing ND resource record (have_res) matches
        the desired payload (want_res).

        Matches on: entityName, scopeType (ND format), poolName, and scopeValue.

        For non-fabric scopes ND may store the scopeValue as the first tilde-
        segment of entityName, so both are checked.

        Parameters:
            have_res (dict): Resource dict returned by the ND API.
            want_res (dict): Payload dict from self.want.

        Returns:
            bool: True if the two resources refer to the same allocation.
        """
        log.debug(
            "_match_resources: have_entityName=%s want_entityName=%s want_poolName=%s want_scopeType=%s",
            have_res.get("entityName") or have_res.get("entity_name"),
            want_res.get("entityName"),
            want_res.get("poolName"),
            want_res.get("scopeType"),
        )
        # Normalise ND response field names (camelCase preferred, fallback to snake_case)
        have_entity = have_res.get("entityName") or have_res.get("entity_name", "")
        have_scope_type = (
            have_res.get("entityType")
            or have_res.get("scopeType")
            or have_res.get("scope_type", "")
        )
        have_pool = (
            (have_res.get("resourcePool") or {}).get("poolName")
            or have_res.get("poolName")
            or have_res.get("pool_name", "")
        )
        have_scope_val = (
            have_res.get("allocatedScopeValue")
            or have_res.get("scopeValue")
            or have_res.get("scope_value", "")
        )
        have_fabric = (have_res.get("resourcePool") or {}).get(
            "fabricName"
        ) or have_res.get("fabricName", "")

        if not self._compare_entity_names(have_entity, want_res["entityName"]):
            return False
        if have_scope_type != want_res["scopeType"]:
            return False
        if have_pool != want_res["poolName"]:
            return False

        if want_res["scopeType"] == "Fabric":
            if have_fabric and have_fabric != self.fabric:
                log.debug(
                    "_match_resources: fabric mismatch have_fabric=%s self.fabric=%s",
                    have_fabric,
                    self.fabric,
                )
                return False
        else:
            # ND may set allocatedScopeValue to the first part of entity name
            first_part = have_entity.split("~")[0] if "~" in have_entity else ""
            if (
                have_scope_val != want_res["scopeValue"]
                and have_scope_val != first_part
            ):
                log.debug(
                    "_match_resources: scopeValue mismatch have_scope_val=%s want_scopeValue=%s first_part=%s",
                    have_scope_val,
                    want_res["scopeValue"],
                    first_part,
                )
                return False
        log.debug(
            "_match_resources: match found for entityName=%s poolName=%s",
            want_res.get("entityName"),
            want_res.get("poolName"),
        )
        return True

    def _compare_resources(self, res):
        """
        Check whether a desired resource already exists in self.have with the
        same value (idempotency check).

        Parameters:
            res (dict): Payload dict from self.want.

        Returns:
            str: 'ND_RES_DONT_ADD' if the resource already exists with the
                 correct value; 'ND_RES_ADD' otherwise.
        """
        log.debug(
            "_compare_resources: checking entityName=%s poolName=%s resource=%s",
            res.get("entityName"),
            res.get("poolName"),
            res.get("resource"),
        )
        for have_res in self.have:
            if self._match_resources(have_res, res):
                # Resource exists — compare the allocated value
                have_value = (
                    have_res.get("resourceValue")
                    or have_res.get("allocatedIp")
                    or have_res.get("resource", "")
                )
                if res.get("resource") is not None and have_value is not None:
                    if self._compare_resource_values(
                        str(have_value), str(res["resource"])
                    ):
                        log.debug(
                            "_compare_resources: entityName=%s have_value=%s want_resource=%s values match, status=ND_RES_DONT_ADD",
                            res.get("entityName"),
                            have_value,
                            res["resource"],
                        )
                        return "ND_RES_DONT_ADD"
                else:
                    log.debug(
                        "_compare_resources: entityName=%s exists in have (no resource value to compare), status=ND_RES_DONT_ADD",
                        res.get("entityName"),
                    )
                    return "ND_RES_DONT_ADD"
        log.debug(
            "_compare_resources: entityName=%s not found in have or value differs, status=ND_RES_ADD",
            res.get("entityName"),
        )
        return "ND_RES_ADD"

    # -------------------------------------------------------------------------
    # Diff Computation
    # -------------------------------------------------------------------------

    def get_diff_merge(self):
        """
        Populate self.diff_create with resources from self.want that do not
        already exist in self.have (or exist with a different value).
        """
        log.debug(
            "get_diff_merge: want_count=%d have_count=%d",
            len(self.want),
            len(self.have),
        )
        if not self.want:
            log.debug("get_diff_merge: want is empty, nothing to diff")
            return

        for res in self.want:
            rc = self._compare_resources(res)
            log.debug(
                "get_diff_merge: entityName=%s poolName=%s compare_result=%s",
                res.get("entityName"),
                res.get("poolName"),
                rc,
            )
            if rc == "ND_RES_ADD" and res not in self.diff_create:
                self.diff_create.append(res)
        log.debug("get_diff_merge: diff_create_count=%d", len(self.diff_create))

    def get_diff_deleted(self):
        """
        Populate self.diff_delete with the resource IDs from self.have that
        should be removed.
        """
        log.debug(
            "get_diff_deleted: scanning have_count=%d for resource IDs", len(self.have)
        )
        for have_res in self.have:
            rid = have_res.get("resourceId") or have_res.get("id")
            log.debug(
                "get_diff_deleted: entityName=%s resourceId=%s",
                have_res.get("entityName") or have_res.get("entity_name"),
                rid,
            )
            if rid is not None:
                self.diff_delete.append(int(rid))
        log.debug(
            "get_diff_deleted: %d resource(s) to delete ids=%s",
            len(self.diff_delete),
            self.diff_delete,
        )

    def get_diff_query(self):
        """
        Query ND for resources and populate self.result['response'].

        Dispatch logic mirrors dcnm_resource_manager.py:
          - No config  → GET all resources for the fabric (no filters)
          - entity_name only  → GET all, filter client-side by entity name
          - switch only  → GET with switchId query param
          - pool_name only  → GET with poolName query param
          - switch + pool_name  → GET with both query params
          - Mixed list  → each config entry dispatched independently

        Duplicate responses are suppressed by resource ID.
        """
        log.debug(
            "get_diff_query: fabric=%s rm_info_count=%d",
            self.fabric,
            len(self.rm_info),
        )
        if not self.rm_info:
            # No config provided — fetch everything in the fabric
            log.debug("get_diff_query: no filters provided, fetching all resources")
            self._query_all_resources()
            return

        seen_ids = set()
        for res in self.rm_info:
            filter_entity = res.get("entity_name")
            filter_pool = res.get("pool_name")
            filter_switches = res.get("switch") or []
            log.debug(
                "get_diff_query: dispatching filter_entity=%s filter_pool=%s filter_switches=%s",
                filter_entity,
                filter_pool,
                filter_switches,
            )

            if filter_switches:
                for sw_serial in filter_switches:
                    self._query_resources(
                        switch_id=sw_serial,
                        pool_name=filter_pool,
                        filter_entity=filter_entity,
                        seen_ids=seen_ids,
                    )
            else:
                self._query_resources(
                    switch_id=None,
                    pool_name=filter_pool,
                    filter_entity=filter_entity,
                    seen_ids=seen_ids,
                )
        log.debug(
            "get_diff_query: query complete, response_count=%d",
            len(self.result["response"]),
        )

    def _query_all_resources(self):
        """Fetch all resources for the fabric without any filters."""
        endpoint = EpManageFabricResourcesGet(fabric_name=self.fabric)
        log.debug("_query_all_resources: GET %s", endpoint.path)
        response = self.nd.request(endpoint.path, method=endpoint.verb.value)
        resources = self._extract_resource_list(response)
        self.result["response"].extend(resources)

    def _query_resources(self, switch_id, pool_name, filter_entity, seen_ids):
        """
        Fetch resources using the provided filters and append matching results
        to self.result['response'], avoiding duplicates via seen_ids.

        Parameters:
            switch_id (str|None): Switch serial number for the switchId query param.
            pool_name (str|None): Pool name for the poolName query param.
            filter_entity (str|None): Entity name to apply as a client-side filter.
            seen_ids (set): Set of already-seen resource IDs (mutated in place).
        """
        endpoint = EpManageFabricResourcesGet(fabric_name=self.fabric)
        if switch_id:
            endpoint.endpoint_params.switch_id = switch_id
        if pool_name:
            endpoint.endpoint_params.pool_name = pool_name

        log.debug("_query_resources: GET %s", endpoint.path)
        response = self.nd.request(endpoint.path, method=endpoint.verb.value)
        resources = self._extract_resource_list(response)

        for relem in resources:
            rid = relem.get("resourceId") or relem.get("id")
            if rid is not None and rid in seen_ids:
                continue

            if filter_entity is not None:
                have_entity = relem.get("entityName") or relem.get("entity_name", "")
                if not self._compare_entity_names(have_entity, filter_entity):
                    continue

            self.result["response"].append(relem)
            if rid is not None:
                seen_ids.add(rid)

    # -------------------------------------------------------------------------
    # API Communication
    # -------------------------------------------------------------------------

    def send_message_to_nd(self):
        """
        Push payloads to the ND API.

        Creates resources in self.diff_create one-by-one via
        EpManageFabricResourcesPost.

        Deletes resources in self.diff_delete in bulk via
        EpManageFabricResourcesActionsRemovePost using RemoveResourcesByIdsRequestModel.

        Sets self.result['changed'] = True if any create or delete was performed.
        """
        log.debug(
            "send_message_to_nd: diff_create_count=%d diff_delete_count=%d",
            len(self.diff_create),
            len(self.diff_delete),
        )
        create_flag = False
        delete_flag = False

        # --- CREATE ---
        for res in self.diff_create:
            endpoint = EpManageFabricResourcesPost(fabric_name=self.fabric)
            log.debug(
                "send_message_to_nd: POST %s entityName=%s poolName=%s resource=%s",
                endpoint.path,
                res.get("entityName"),
                res.get("poolName"),
                res.get("resource"),
            )
            resp = self.nd.request(endpoint.path, method=endpoint.verb.value, data=res)
            log.debug("send_message_to_nd: create response=%s", resp)
            create_flag = True
            self.result["response"].append(resp)

        # --- DELETE (bulk by IDs) ---
        if self.diff_delete:
            log.debug(
                "send_message_to_nd: preparing bulk delete for resource_ids=%s",
                self.diff_delete,
            )
            endpoint = EpManageFabricResourcesActionsRemovePost(fabric_name=self.fabric)
            try:
                request_model = RemoveResourcesByIdsRequestModel(
                    resourceIds=self.diff_delete
                )
                payload = request_model.to_payload()
            except Exception as exc:
                log.debug(
                    "send_message_to_nd: failed to build delete payload error=%s",
                    exc,
                )
                self.module.fail_json(
                    msg="Failed to build delete payload: {0}".format(str(exc))
                )
            log.debug(
                "send_message_to_nd: POST %s resource_ids=%s",
                endpoint.path,
                self.diff_delete,
            )
            resp = self.nd.request(
                endpoint.path, method=endpoint.verb.value, data=payload
            )
            log.debug("send_message_to_nd: delete response=%s", resp)
            delete_flag = True
            self.result["response"].append(resp)

        log.debug(
            "send_message_to_nd: complete changed=%s create_flag=%s delete_flag=%s",
            create_flag or delete_flag,
            create_flag,
            delete_flag,
        )
        self.result["changed"] = create_flag or delete_flag


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Main entry point for module execution."""
    argument_spec = nd_argument_spec()
    argument_spec.update(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
        save=dict(type="bool", default=True),
        deploy=dict(type="bool", default=True),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "query"],
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ["state", "merged", ["config"]],
            ["state", "deleted", ["config"]],
        ],
    )

    # Initialise logging using the Log() class from log.py.
     # Initialize logging
    try:
        log_config = Log()
        log_config.config = "/Users/jeeram/ansible/collections/ansible_collections/cisco/nd/plugins/module_utils/logging_config.json"
        log_config.commit()
        # Create logger instance for this module
        log = logging.getLogger("nd.nd_manage_resource_manager")
    except ValueError as error:
        module.fail_json(msg=str(error))

    # Get parameters
    state = module.params.get("state")
    fabric = module.params.get("fabric")
    output_level = module.params.get("output_level")

    # Initialize Results - this collects all operation results
    results = Results()
    results.state = state
    results.check_mode = module.check_mode
    results.action = f"manage_resource_manager_{state}"

    log.debug(
        "main: starting nd_manage_resource_manager fabric=%s state=%s check_mode=%s",
        module.params.get("fabric"),
        state,
        module.check_mode,
    )

    # Translate switch IPs to serial numbers before validation
    if rm.config:
        log.debug("main: translating switch IPs to serial numbers")
        rm.translate_switch_info(rm.config)

    # Validate and populate rm_info
    rm.validate_input()
    log.debug("main: rm_info_count=%d after validation", len(rm.rm_info))


######


    try:
        log.info(f"Starting nd_manage_resource_manager module: fabric={fabric}, state={state}")

        # Initialize NDModule (uses RestSend infrastructure internally)
        nd = NDModule(module)
        rm = NDManageResourceManager(module, nd, )
        log.info("NDModule initialized successfully")

        # Create NDSwitchResourceModule
        sw_module = NDSwitchResourceModule(
            nd=nd,
            results=results,
            logger=log
        )
        log.info(f"NDSwitchResourceModule initialized for fabric: {fabric}")

        # Manage state for merged, overridden, deleted, query
        log.info(f"Managing state: {state}")
        sw_module.manage_state()

        # Exit with results
        log.info(f"State management completed successfully. Changed: {results.changed}")
        sw_module.exit_json()

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
        results.register_task_result()
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
        results.register_task_result()
        results.build_final_result()

        if output_level == "debug":
            import traceback
            results.final_result["traceback"] = traceback.format_exc()

        module.fail_json(msg=str(error), **results.final_result)




#######
    if state != "query":
        rm.get_want()
        rm.get_have()
        log.debug("main: want_count=%d have_count=%d", len(rm.want), len(rm.have))

    if state == "merged":
        rm.get_diff_merge()
        log.debug("main: diff_create_count=%d", len(rm.diff_create))
    elif state == "deleted":
        rm.get_diff_deleted()
        log.debug("main: diff_delete_count=%d", len(rm.diff_delete))
    elif state == "query":
        rm.get_diff_query()
        log.debug("main: query response_count=%d", len(rm.result["response"]))

    rm.result["diff"] = {"merged": rm.diff_create, "deleted": rm.diff_delete}

    if rm.diff_create or rm.diff_delete:
        rm.result["changed"] = True

    if module.check_mode:
        log.debug("main: check_mode=True, skipping API calls")
        rm.result["changed"] = False
        module.exit_json(**rm.result)
        return

    if state in ("merged", "deleted"):
        rm.send_message_to_nd()

    log.debug("main: finished state=%s changed=%s", state, rm.result["changed"])
    module.exit_json(**rm.result)


if __name__ == "__main__":
    main()
