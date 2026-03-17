#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: nd_manage_resource_manager_updated
short_description: Nexus Dashboard module for managing fabric resources.
version_added: "0.7.0"
description:
    - Create, delete, and query resources via the ND Manage API
      (C(/api/v1/manage)).
    - Implements idempotent merged/deleted/query states using the 7-layer
      architecture (endpoints → models → utils → ResourceModule → entry point).
    - Switch management IP addresses are automatically resolved to serial
      numbers via the ND inventory API.
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
      - C(merged) adds resources defined in the playbook that do not yet exist.
      - C(deleted) removes resources defined in the playbook that currently exist.
      - C(query) returns the current state of resources; no changes are made.
    type: str
    required: false
    choices:
      - merged
      - deleted
      - query
    default: merged
  config:
    description:
      - A list of dictionaries containing resource and switch information.
      - Required for C(merged) state.
      - Optional for C(deleted) and C(query) states.
    type: list
    elements: dict
    suboptions:
      entity_name:
        description:
          - A unique name that identifies the entity to which the resource is
            allocated.
          - The format depends on C(scope_type). See EXAMPLES for details.
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
          - An integer when C(pool_type) is C(ID).
          - An IPv4 or IPv6 address when C(pool_type) is C(IP).
          - An IPv4 or IPv6 CIDR when C(pool_type) is C(SUBNET).
        type: str
        required: false
      switch:
        description:
          - Management IP address(es) or serial number(s) of the switch(es) to
            which the resource is assigned.
          - Required for C(scope_type) values other than C(fabric).
        type: list
        elements: str
        required: false
extends_documentation_fragment:
- cisco.nd.modules
"""

EXAMPLES = """
# Entity name format by scope_type
# =================================
# scope_type              entity_name example
# ---------               ---------------
# fabric                  My_Network_30000
# device                  loopback0
# device_pair             FDO21331S8T~FDO21332E6X~vPC1
# device_interface        FDO21332E6X~Ethernet1/13
# link                    FDO21332E6X~Ethernet1/3~FDO21331S8T~Ethernet1/3
#
# (FDO21331S8T and FDO21332E6X are switch serial numbers)

- name: Create fabric-scoped resource
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: merged
    config:
      - entity_name: l3_vni_fabric
        pool_type: ID
        pool_name: L3_VNI
        scope_type: fabric
        resource: "101"

- name: Create device-pair resource
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: merged
    config:
      - entity_name: "9M99N34RDED~9NXHSNTEO6C"
        pool_type: ID
        pool_name: VPC_ID
        scope_type: device_pair
        switch:
          - 192.175.1.1
          - 192.175.1.2
        resource: "500"

- name: Create device-interface resource (IPv6)
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: merged
    config:
      - entity_name: "9M99N34RDED~Ethernet1/10"
        pool_type: IP
        pool_name: LOOPBACK1_IP_POOL
        scope_type: device_interface
        switch:
          - 192.175.1.1
        resource: "fe80::04"

- name: Delete resources
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: deleted
    config:
      - entity_name: l3_vni_fabric
        pool_type: ID
        pool_name: L3_VNI
        scope_type: fabric

- name: Query all resources in fabric
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: query

- name: Query resources by entity name
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: query
    config:
      - entity_name: l3_vni_fabric
      - entity_name: "9M99N34RDED~9NXHSNTEO6C"

- name: Query resources by switch and pool name
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: query
    config:
      - pool_name: L3_VNI
        switch:
          - 192.175.1.1

- name: Mixed query
  cisco.nd.nd_manage_resource_manager_updated:
    fabric: test_fabric
    state: query
    config:
      - entity_name: l2_vni_fabric
      - switch:
          - 192.175.1.1
      - pool_name: VPC_ID
        switch:
          - 192.175.1.2
"""

RETURN = r"""
changed:
  description: Whether any resources were created or deleted.
  returned: always
  type: bool
diff:
  description: Resources that were added (merged key) or removed (deleted key).
  returned: always
  type: dict
  contains:
    merged:
      description: List of resource payloads sent to the create API.
      type: list
      elements: dict
    deleted:
      description: List of resource IDs submitted to the delete API.
      type: list
      elements: int
response:
  description: Raw API responses from create/delete/query operations.
  returned: always
  type: list
  elements: dict
"""

import copy
import logging
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.nd.plugins.module_utils.nd import (
    NDModule,
    nd_argument_spec,
)
from ansible_collections.cisco.nd.plugins.module_utils.common.log import Log
from ansible_collections.cisco.nd.plugins.module_utils.nd_manage_resource_manager_resources import (
    NDManageResourceManagerModule,
)

# Logging config path relative to this module file:
# <collection>/plugins/module_utils/logging_config.json
_ND_LOG_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "module_utils",
    "logging_config.json",
)

log = logging.getLogger("nd.nd_manage_resource_manager_updated")


def main():
    """Main entry point for module execution."""
    argument_spec = nd_argument_spec()
    argument_spec.update(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
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
        ],
    )

    # Initialise logging. When Ansible packages the module into an AnsiballZ zip
    # the __file__-derived path is not a real filesystem path, so only set the
    # config file when it actually exists on disk. Passing config=None disables
    # logging gracefully (Log.commit() calls disable_logging() when config is None).
    try:
        log_config = Log()
        if os.path.isfile(_ND_LOG_CONFIG):
            log_config.config = _ND_LOG_CONFIG
        log_config.commit()
    except ValueError as error:
        module.fail_json(msg=str(error))

    logger = logging.getLogger("nd.nd_manage_resource_manager_updated")

    state = module.params["state"]
    fabric = module.params["fabric"]
    config = copy.deepcopy(module.params.get("config"))

    logger.debug(
        "main: fabric=%s state=%s check_mode=%s config_count=%d",
        fabric,
        state,
        module.check_mode,
        len(config) if config else 0,
    )

    try:
        nd = NDModule(module)

        rm_module = NDManageResourceManagerModule(
            nd=nd,
            fabric=fabric,
            log=logger,
            check_mode=module.check_mode,
        )

        result = rm_module.manage_state(config=config, state=state, module=module)
        module.exit_json(**result)

    except Exception as exc:
        logger.exception("main: unhandled exception: %s", exc)
        module.fail_json(msg=str(exc))


if __name__ == "__main__":
    main()
