#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "community"}

DOCUMENTATION = r"""
---
module: nd_resource_manager
version_added: "1.5.0"
short_description: Manage ND fabric resources.
description:
- Manage resource allocations for a fabric in Nexus Dashboard Manage.
- Keeps DCNM-style state semantics while using ND Manage APIs.
author:
- Jeet Ram (@jeeram)
options:
  fabric:
    description:
    - Name of the target fabric for resource manager operations.
    type: str
    required: true
  state:
    description:
    - Desired end state for the operation.
    - Use C(merged) to allocate resources.
    - Use C(deleted) to release resources.
    - Use C(query) to query resources, pools, or propose VLAN.
    type: str
    choices: [ merged, deleted, query ]
    default: merged
  query_target:
    description:
    - Query target used when O(state=query).
    - C(resources) queries resource allocations.
    - C(pools) queries resource pools.
    - C(propose_vlan) queries next VLAN proposal.
    type: str
    choices: [ resources, pools, propose_vlan ]
    default: resources
  tenant_name:
    description:
    - Optional tenant name used for resource allocation and propose VLAN query.
    type: str
  config:
    description:
    - A list of dictionaries containing resource information.
    - For C(merged) and C(deleted), each dictionary describes a resource to allocate or delete with fields for
    intent specification and ND Manage API payload construction.
    - For C(query), fields depend on O(query_target).
    type: list
    elements: dict
    suboptions:
      entity_name:
        description:
        - Entity identifier for the resource allocation.
        type: str
      pool_type:
        description:
        - Resource pool type for DCNM-style intent validation.
        type: str
        choices: [ ID, IP, SUBNET ]
      pool_name:
        description:
        - Resource pool name.
        type: str
      scope_type:
        description:
        - Scope type for allocation.
        - Supports DCNM names and ND names.
        type: str
        choices: [ fabric, device, device_interface, device_pair, link, deviceInterface, devicePair ]
      resource:
        description:
        - Desired resource value for allocation.
        type: str
      switch:
        description:
        - List of switch selectors (serial, hostname, or IP) for scope translation.
        type: list
        elements: str
      resource_id:
        description:
        - Optional explicit resource ID.
        - In C(state=deleted), deletes this resource by ID.
        - In C(state=query), queries this resource by ID.
        type: int
      resource_ids:
        description:
        - Optional explicit resource ID list for bulk delete in C(state=deleted).
        type: list
        elements: int
      delete_by_details:
        description:
        - When C(true) in C(state=deleted), calls delete-by-details endpoint.
        type: bool
      vlan_type:
        description:
        - VLAN type for C(query_target=propose_vlan).
        type: str
        choices: [ networkVlan, vrfVlan, serviceNetworkVlan, vpcPeerLinkVlan ]
      pool_id:
        description:
        - Optional pool ID filter for C(query_target=pools).
        type: int
      filter:
        description:
        - Optional Lucene filter for C(query_target=resources) or C(query_target=pools).
        type: str
      max:
        description:
        - Optional pagination max.
        type: int
      offset:
        description:
        - Optional pagination offset.
        type: int
      sort:
        description:
        - Optional sort expression.
        type: str
extends_documentation_fragment:
- cisco.nd.modules
- cisco.nd.check_mode
"""

EXAMPLES = r"""
- name: Allocate resources (merged)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: merged
    config:
      - entity_name: "l3_vni_fabric"
        pool_type: "ID"
        pool_name: "L3_VNI"
        scope_type: "fabric"
        resource: "101"
      - entity_name: "SERIAL1~Ethernet1/10"
        pool_type: "IP"
        pool_name: "LOOPBACK1_IP_POOL"
        scope_type: "device_interface"
        switch:
          - "leaf-1"
        resource: "10.10.10.10"

- name: Delete resources by DCNM-style matching (deleted)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: deleted
    config:
      - entity_name: "l3_vni_fabric"
        pool_type: "ID"
        pool_name: "L3_VNI"
        scope_type: "fabric"

- name: Delete explicit resource IDs (deleted)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: deleted
    config:
      - resource_ids: [100, 101, 102]

- name: Delete explicit single resource ID (deleted)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: deleted
    config:
      - resource_id: 200

- name: Delete resource by details endpoint (deleted)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: deleted
    config:
      - delete_by_details: true
        entity_name: "l3_vni_fabric"
        pool_type: "ID"
        pool_name: "L3_VNI"
        scope_type: "fabric"

- name: Query resources (query_target resources)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: query
    query_target: resources

- name: Query pools (query_target pools)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: query
    query_target: pools
    config:
      - pool_id: 10

- name: Query propose VLAN (query_target propose_vlan)
  cisco.nd.nd_resource_manager:
    fabric: fab1
    state: query
    query_target: propose_vlan
    config:
      - vlan_type: networkVlan
        tenant_name: common
"""

RETURN = r"""
changed:
  description: Whether any change occurred.
  returned: always
  type: bool
failed:
  description: Whether the operation failed.
  returned: always
  type: bool
diff:
  description: Collected diffs by operation.
  returned: always
  type: list
  elements: dict
response:
  description: Controller responses per operation.
  returned: always
  type: list
  elements: dict
result:
  description: Result metadata per operation.
  returned: always
  type: list
  elements: dict
metadata:
  description: Operation metadata per operation.
  returned: always
  type: list
  elements: dict
current:
  description: Final normalized current data for the module operation.
  returned: always
  type: raw
"""

import copy
import ipaddress
import logging
import os

from typing import Any, Dict, List, Optional, Set, Tuple

# Create module logger
logger = logging.getLogger(__name__)


def setup_logging():
    """
    Configure file logging for nd_resource_manager module.

    Creates a file handler that writes to nd.log in the current directory
    with detailed formatting including timestamp, level, and message.
    """
    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set logger level
    logger.setLevel(logging.DEBUG)

    # Create file handler
    log_file = os.path.join(os.getcwd(), "nd.log")
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    logger.info("=" * 80)
    logger.info("Logging initialized for nd_resource_manager module")
    logger.info("=" * 80)


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.nd.plugins.module_utils.enums import HttpVerbEnum, OperationType
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.nd_resource_manager.nd_resource_manager import (
    V1ManageSwitchesGet as EpApiV1ManageSwitchesGet,
    V1ManageDeleteFabricResourceById as EpApiV1ManageDeleteFabricResourceById,
    V1ManageGetFabricResourceById as EpApiV1ManageGetFabricResourceById,
    V1ManageGetFabricResources as EpApiV1ManageGetFabricResources,
    V1ManageGetFabricsPools as EpApiV1ManageGetFabricsPools,
    V1ManageGetFabricsProposeVlan as EpApiV1ManageGetFabricsProposeVlan,
    V1ManagePostFabricResources as EpApiV1ManagePostFabricResources,
    V1ManagePostFabricResourcesActionsRemove as EpApiV1ManagePostFabricResourcesActionsRemove,
    V1ManagePostFabricResourcesActionsRemoveResource as EpApiV1ManagePostFabricResourcesActionsRemoveResource,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_resource_manager.nd_resource_manager import (
    AllocateResourcesResponseModel,
    AllocateResourcesRequestModel,
    PoolsResponseModel,
    ProposeVlanResponseModel,
    RemoveResourceByDetailsResponseModel,
    RemoveResourcesByIdRequestModel,
    RemoveResourcesResponseModel,
    ResourceDetailsGetModel,
    ResourceDetailsPostModel,
    ResourcesResponseModel,
    ScopeType,
    VlanType,
)
from ansible_collections.cisco.nd.plugins.module_utils.nd_v2 import NDModule, NDModuleError, nd_argument_spec
from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import ValidationError
from ansible_collections.cisco.nd.plugins.module_utils.rest.results import Results


POOLNAME_TO_SCOPE_TYPE = {
    "L3_VNI": ["fabric"],
    "L2_VNI": ["fabric"],
    "VPC_ID": ["device_pair"],
    "FEX_ID": ["device"],
    "BGP_ASN_ID": ["fabric"],
    "LOOPBACK_ID": ["device"],
    "PORT_CHANNEL_ID": ["device"],
    "VPC_DOMAIN_ID": ["fabric"],
    "VPC_PEER_LINK_VLAN": ["device_pair"],
    "TOP_DOWN_L3_DOT1Q": ["device_interface"],
    "TUNNEL_ID_IOS_XE": ["device"],
    "OBJECT_TRACKING_NUMBER_POOL": ["device"],
    "INSTANCE_ID": ["device"],
    "PORT_CHANNEL_ID_IOS_XE": ["device"],
    "ROUTE_MAP_SEQUENCE_NUMBER_POOL": ["device"],
    "SERVICE_NETWORK_VLAN": ["device"],
    "TOP_DOWN_VRF_VLAN": ["device"],
    "TOP_DOWN_NETWORK_VLAN": ["device"],
    "IP_POOL": ["fabric", "device_interface"],
    "SUBNET": ["link"],
}

SCOPE_ALIAS_TO_SNAKE = {
    "fabric": "fabric",
    "device": "device",
    "device_interface": "device_interface",
    "device_pair": "device_pair",
    "link": "link",
    "deviceInterface": "device_interface",
    "devicePair": "device_pair",
}

SCOPE_SNAKE_TO_API = {
    "fabric": ScopeType.FABRIC.value,
    "device": ScopeType.DEVICE.value,
    "device_interface": ScopeType.DEVICE_INTERFACE.value,
    "device_pair": ScopeType.DEVICE_PAIR.value,
    "link": ScopeType.LINK.value,
}

SCOPE_API_TO_SNAKE = {value: key for key, value in SCOPE_SNAKE_TO_API.items()}


class NdResourceManagerTask:
    """
    Task implementation for nd_resource_manager.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the NdResourceManagerTask.

        Args:
            module: AnsibleModule instance with module parameters

        Initializes all instance variables including state, fabric name,
        query_target, config, and sets up the ND module connection.
        """
        logger.info("Initializing NdResourceManagerTask")
        self.module = module
        self.params = module.params
        self.state = self.params.get("state")
        self.fabric = self.params.get("fabric")
        self.query_target = self.params.get("query_target")
        self.tenant_name = self.params.get("tenant_name")
        self.config = copy.deepcopy(self.params.get("config"))
        logger.debug(f"State: {self.state}, Fabric: {self.fabric}, Query target: {self.query_target}")

        self.nd = NDModule(module)
        self.results = Results()
        self.current: Any = {}

        self._switch_lookup: Optional[Dict[str, str]] = None
        self._all_resources: Optional[List[Dict[str, Any]]] = None

        self.rm_info: List[Dict[str, Any]] = []
        self.want: List[Dict[str, Any]] = []
        self.have: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------------
    # Core workflow
    # ---------------------------------------------------------------------

    def commit(self) -> None:
        """
        Execute the main workflow for resource manager operations.

        This is the entry point for all resource manager operations. It:
        1. Validates input parameters
        2. Translates switch information if needed
        3. Builds desired state (want) and fetches current state (have)
        4. Dispatches to appropriate state handler (merged, deleted, or query)

        Raises:
            ValueError: If validation fails
            NDModuleError: If API requests fail
        """
        logger.info(f"Starting commit workflow - state: {self.state}, fabric: {self.fabric}")
        self._validate_inputs()

        if self.query_target == "resources" and self._config_uses_switch_translation(self.config):
            logger.debug("Config requires switch translation")
            self._translate_switch_info(self.config)

        if self.state != "query":
            logger.debug("Building resource management information from config")
            self.rm_info = self._build_rm_info_from_config(self.config)
            self.want = self._build_want(self.rm_info)
            self.have = self._fetch_all_resources()
            logger.info(f"Loaded {len(self.want)} desired resources and {len(self.have)} existing resources")

        if self.state == "merged":
            logger.info("Handling merged state")
            self._handle_merged()
        elif self.state == "deleted":
            logger.info("Handling deleted state")
            self._handle_deleted()
        else:
            logger.info(f"Handling query state - target: {self.query_target}")
            self._handle_query()
        logger.info("Commit workflow completed successfully")

    # ---------------------------------------------------------------------
    # Request and results helpers
    # ---------------------------------------------------------------------

    def _prepare_results(self, action: str, operation_type: OperationType) -> None:
        """
        Prepare result context for the current operation.

        Args:
            action: Description of the action being performed
            operation_type: Type of operation (CREATE, DELETE, QUERY)

        Sets up the results object with action, operation type, state, and check mode.
        """
        logger.debug(f"Preparing results - action: {action}, operation: {operation_type.value}")
        self.results.action = action
        self.results.operation_type = operation_type
        self.results.state = self.state
        self.results.check_mode = self.module.check_mode

    def _register_from_nd(self, action: str, operation_type: OperationType, diff: Optional[Dict[str, Any]] = None) -> None:
        """
        Register results from an ND API request.

        Args:
            action: Description of the action performed
            operation_type: Type of operation (CREATE, DELETE, QUERY)
            diff: Optional dictionary containing the diff for this operation

        Captures the response and result from the ND module's REST sender
        and registers it with the results tracker.
        """
        logger.debug(f"Registering results from ND - action: {action}")
        self._prepare_results(action, operation_type)
        self.results.response_current = self.nd.rest_send.response_current
        self.results.result_current = self.nd.rest_send.result_current
        self.results.diff_current = diff or {}
        self.results.register_task_result()

    def _register_synthetic(
        self,
        action: str,
        operation_type: OperationType,
        response: Dict[str, Any],
        result: Dict[str, Any],
        diff: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register synthetic results (not from actual API request).

        Args:
            action: Description of the action performed
            operation_type: Type of operation (CREATE, DELETE, QUERY)
            response: Synthetic response dictionary
            result: Synthetic result dictionary
            diff: Optional dictionary containing the diff for this operation

        Used for check mode operations or special case handling where
        an actual API request was not made but results need to be recorded.
        """
        logger.debug(f"Registering synthetic results - action: {action}")
        self._prepare_results(action, operation_type)
        self.results.response_current = response
        self.results.result_current = result
        self.results.diff_current = diff or {}
        self.results.register_task_result()

    def _request(
        self,
        action: str,
        operation_type: OperationType,
        path: str,
        verb: HttpVerbEnum,
        payload: Optional[Dict[str, Any]] = None,
        allow_207: bool = False,
        allow_404: bool = False,
        diff: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an API request to the ND controller.

        Args:
            action: Description of the action being performed
            operation_type: Type of operation (CREATE, DELETE, QUERY)
            path: API endpoint path
            verb: HTTP verb (GET, POST, DELETE, etc.)
            payload: Optional request payload for POST/PUT requests
            allow_207: If True, treat HTTP 207 as success (multi-status)
            allow_404: If True, treat HTTP 404 as success (not found)
            diff: Optional diff to record for this operation

        Returns:
            Response data from the controller

        Raises:
            NDModuleError: If the request fails (unless handled by allow_* flags)

        Handles check mode by returning synthetic responses for mutations.
        Handles special status codes (207, 404) based on allow_* flags.
        """
        logger.info(f"Executing request - action: {action}, verb: {verb.value}, path: {path}")
        if self.module.check_mode and operation_type in (OperationType.CREATE, OperationType.DELETE):
            logger.info("Check mode enabled - skipping controller mutation")
            response = {
                "RETURN_CODE": 200,
                "MESSAGE": "Skipped controller mutation in check mode",
                "REQUEST_PATH": path,
                "METHOD": verb.value,
                "DATA": payload if payload is not None else {},
            }
            result = {
                "success": True,
                "changed": True,
                "found": True,
            }
            self._register_synthetic(action, operation_type, response, result, diff=diff)
            return payload if payload is not None else {}

        try:
            logger.debug(f"Sending request to controller: {verb.value} {path}")
            data = self.nd.request(path, verb, payload)
            logger.debug(f"Request succeeded")
            self._register_from_nd(action, operation_type, diff=diff)
            return data
        except NDModuleError as error:
            logger.warning(f"Request failed with status {error.status}: {error.msg}")
            # POST /resources and POST /resources/actions/remove return 207 on partial/full success.
            if allow_207 and error.status == 207:
                logger.info("Status 207 - treating as success (allow_207=True)")
                response = self.nd.rest_send.response_current
                result = {
                    "success": True,
                    "changed": operation_type != OperationType.QUERY,
                }
                self._register_synthetic(action, operation_type, response, result, diff=diff)
                return error.response_payload or {}

            # GET /resources/{resourceId} can return 404 when not found and should not fail delete idempotency flows.
            if allow_404 and error.status == 404:
                logger.info("Status 404 - treating as success (allow_404=True)")
                response = self.nd.rest_send.response_current
                result = {
                    "success": True,
                    "changed": False,
                    "found": False,
                }
                self._register_synthetic(action, operation_type, response, result, diff=diff)
                return {}

            logger.error(f"Request failed - status: {error.status}, message: {error.msg}")
            response = {
                "RETURN_CODE": error.status if error.status is not None else -1,
                "MESSAGE": error.msg,
                "DATA": error.response_payload if error.response_payload is not None else {},
            }
            result = {"success": False, "changed": False}
            self._register_synthetic(action, operation_type, response, result, diff=diff)
            raise

    # ---------------------------------------------------------------------
    # Validation and normalization
    # ---------------------------------------------------------------------

    def _validate_inputs(self) -> None:
        """
        Validate module input parameters.

        Validates:
        - Config is provided for merged/deleted states
        - Query target is valid for query state
        - Propose VLAN queries have required parameters
        - Individual config items are valid dicts
        - Config items match requirements for their state/query_target

        Raises:
            ValueError: If any validation fails
        """
        logger.debug(f"Validating inputs - state: {self.state}, query_target: {self.query_target}")
        if self.state in ("merged", "deleted") and not self.config:
            logger.error(f"Config is mandatory for state '{self.state}'")
            raise ValueError("'config' element is mandatory for state '{0}'".format(self.state))

        if self.state != "query":
            self.query_target = "resources"

        if self.state == "query" and self.query_target not in ("resources", "pools", "propose_vlan"):
            logger.error(f"Invalid query_target: {self.query_target}")
            raise ValueError("'query_target' must be one of ['resources', 'pools', 'propose_vlan'] for state=query")

        if self.state == "query" and self.query_target == "propose_vlan" and not self.config:
            logger.error("query_target=propose_vlan requires config")
            raise ValueError("query_target=propose_vlan requires exactly one config item")

        if not self.config:
            logger.debug("No config provided - skipping config validation")
            return

        logger.debug(f"Validating {len(self.config)} config items")
        for idx, item in enumerate(self.config):
            logger.debug(f"Validating config item {idx+1}/{len(self.config)}")
            if not isinstance(item, dict):
                logger.error(f"Config item {idx+1} is not a dictionary: {type(item)}")
                raise ValueError("All config entries must be dictionaries")

            if self.state == "query":
                logger.debug(f"Validating query config item {idx+1}")
                self._validate_query_config_item(item)
            else:
                logger.debug(f"Validating resource manager config item {idx+1}")
                self._validate_rm_config_item(item)

        if self.state == "query" and self.query_target == "propose_vlan":
            if len(self.config) != 1:
                logger.error(f"propose_vlan requires exactly one config item, got {len(self.config)}")
                raise ValueError("query_target=propose_vlan requires exactly one config item")
            if self.config[0].get("vlan_type") is None:
                logger.error("vlan_type is required for propose_vlan")
                raise ValueError("query_target=propose_vlan requires 'vlan_type'")
        logger.debug("Input validation completed successfully")

    def _validate_query_config_item(self, item: Dict[str, Any]) -> None:
        """
        Validate a config item for query operations.

        Args:
            item: Config dictionary to validate

        Validates:
        - resource_id is an integer if provided
        - switch is a list of strings if provided
        - max and offset are integers if provided
        - pool_id is an integer if provided (for pools query)
        - vlan_type is valid if provided (for propose_vlan query)

        Raises:
            ValueError: If validation fails
        """
        if self.query_target == "resources":
            if item.get("resource_id") is not None and not isinstance(item.get("resource_id"), int):
                raise ValueError("'resource_id' must be an integer")

            if item.get("switch") is not None:
                if not isinstance(item.get("switch"), list) or not all(isinstance(s, str) for s in item.get("switch")):
                    raise ValueError("'switch' must be a list of strings")

            for int_key in ("max", "offset"):
                if item.get(int_key) is not None and not isinstance(item.get(int_key), int):
                    raise ValueError("'{0}' must be an integer".format(int_key))

            return

        if self.query_target == "pools":
            if item.get("pool_id") is not None and not isinstance(item.get("pool_id"), int):
                raise ValueError("'pool_id' must be an integer")
            for int_key in ("max", "offset"):
                if item.get(int_key) is not None and not isinstance(item.get(int_key), int):
                    raise ValueError("'{0}' must be an integer".format(int_key))
            return

        # propose_vlan
        vlan_type = item.get("vlan_type")
        if vlan_type is not None and vlan_type not in VlanType.choices():
            raise ValueError("'vlan_type' must be one of {0}".format(VlanType.choices()))

    def _validate_rm_config_item(self, item: Dict[str, Any]) -> None:
        """
        Validate a config item for resource management (merged/deleted) operations.

        Args:
            item: Config dictionary to validate

        Validates:
        - Required fields are present (entity_name, pool_type, pool_name, scope_type)
        - pool_type is one of 'ID', 'IP', or 'SUBNET'
        - scope_type is valid for the given pool_name
        - switch list is provided for non-fabric scopes
        - resource value is valid for the pool_type (in merged state)

        Raises:
            ValueError: If validation fails
        """
        logger.debug(f"Validating resource manager config item: entity_name={item.get('entity_name')}, pool_name={item.get('pool_name')}")
        # Explicit ID-based delete inputs remain valid shortcuts.
        if self.state == "deleted" and self._has_explicit_delete_selector(item):
            logger.debug("Config item has explicit delete selector - skipping full validation")
            return

        required = ["entity_name", "pool_type", "pool_name", "scope_type"]
        for field in required:
            if item.get(field) is None:
                raise ValueError("Mandatory parameter '{0}' missing".format(field))

        scope_type = self._to_scope_snake(item.get("scope_type"))

        pool_type = str(item.get("pool_type", "")).upper()
        if pool_type not in ["ID", "IP", "SUBNET"]:
            raise ValueError("Given pool type = '{0}' is invalid, Allowed pool types = ['ID', 'IP', 'SUBNET']".format(pool_type))

        if pool_type == "ID":
            validation_pool_name = item.get("pool_name")
        elif pool_type == "IP":
            validation_pool_name = "IP_POOL"
        else:
            validation_pool_name = "SUBNET"

        allowed_scope_types = POOLNAME_TO_SCOPE_TYPE.get(validation_pool_name)
        if allowed_scope_types is None:
            raise ValueError("Given pool name '{0}' is not valid".format(item.get("pool_name")))

        logger.debug(f"Validating scope_type '{scope_type}' against allowed types: {allowed_scope_types}")
        if scope_type not in allowed_scope_types:
            raise ValueError(
                "Given scope type '{0}' is not valid for pool name = '{1}', Allowed scope_types = {2}".format(
                    item.get("scope_type"), item.get("pool_name"), allowed_scope_types
                )
            )

        if scope_type != "fabric":
            switches = item.get("switch")
            logger.debug(f"Non-fabric scope - validating switch list: {switches}")
            if not isinstance(switches, list) or not switches:
                raise ValueError("Mandatory parameter 'switch' missing for non-fabric scope")
            if not all(isinstance(sw, str) for sw in switches):
                raise ValueError("'switch' must contain only string values")

        if self.state == "merged":
            resource = item.get("resource")
            if resource is None:
                raise ValueError("Mandatory parameter 'resource' missing for merged state")

            logger.debug(f"Validating resource value for merged state")
            self._validate_resource_value(pool_type, str(resource))
        logger.debug("Config item validation passed")

    def _validate_resource_value(self, pool_type: str, resource: str) -> None:
        """
        Validate a resource value matches the expected format for its pool type.

        Args:
            pool_type: Type of pool - 'ID', 'IP', or 'SUBNET'
            resource: Resource value to validate

        Validates:
        - ID pool type: resource is a valid integer
        - IP pool type: resource is a valid IP address
        - SUBNET pool type: resource is a valid subnet

        Raises:
            ValueError: If resource value is invalid for the pool type
        """
        logger.debug(f"Validating resource value '{resource}' for pool_type '{pool_type}'")
        if pool_type == "ID":
            try:
                int(str(resource))
            except (TypeError, ValueError) as exc:
                raise ValueError("Resource value must be an integer for pool_type=ID") from exc
            return

        if pool_type == "IP":
            try:
                ipaddress.ip_address(resource)
            except ValueError as exc:
                raise ValueError("Resource value must be a valid IP address for pool_type=IP") from exc
            return

        try:
            ipaddress.ip_network(resource, strict=False)
        except ValueError as exc:
            raise ValueError("Resource value must be a valid subnet for pool_type=SUBNET") from exc

    def _to_scope_snake(self, scope_type: str) -> str:
        """
        Convert scope type to snake_case format.

        Args:
            scope_type: Scope type (can be in camelCase or snake_case)

        Returns:
            Normalized scope type in snake_case

        Raises:
            ValueError: If scope type is not recognized

        Supports both DCNM-style (device_interface) and ND-style (deviceInterface) naming.
        """
        logger.debug(f"Converting scope type '{scope_type}' to snake_case")
        if scope_type not in SCOPE_ALIAS_TO_SNAKE:
            raise ValueError(
                "Given scope type '{0}' is invalid, Allowed scope types = {1}".format(
                    scope_type,
                    sorted(SCOPE_ALIAS_TO_SNAKE.keys()),
                )
            )
        return SCOPE_ALIAS_TO_SNAKE[scope_type]

    def _has_explicit_delete_selector(self, item: Dict[str, Any]) -> bool:
        """
        Check if config item has explicit delete selector (resource_id or resource_ids).

        Args:
            item: Config dictionary to check

        Returns:
            True if item has resource_id or resource_ids for explicit deletion

        Validates:
        - resource_ids is a non-empty list of integers if provided
        - resource_id is an integer if provided
        - delete_by_details is a boolean if provided

        Raises:
            ValueError: If selector values are invalid
        """
        has_ids = item.get("resource_ids") is not None
        has_id = item.get("resource_id") is not None
        if has_ids:
            resource_ids = item.get("resource_ids")
            if not isinstance(resource_ids, list) or not resource_ids or not all(isinstance(value, int) for value in resource_ids):
                raise ValueError("'resource_ids' must be a non-empty list of integers")
        if has_id and not isinstance(item.get("resource_id"), int):
            raise ValueError("'resource_id' must be an integer")
        if item.get("delete_by_details") is not None and not isinstance(item.get("delete_by_details"), bool):
            raise ValueError("'delete_by_details' must be boolean")
        return has_ids or has_id

    def _config_uses_switch_translation(self, config: Optional[List[Dict[str, Any]]]) -> bool:
        """
        Check if any config items require switch translation.

        Args:
            config: List of config dictionaries

        Returns:
            True if any config item has a 'switch' field requiring translation
        """
        if not config:
            return False
        return any(isinstance(item, dict) and item.get("switch") for item in config)

    # ---------------------------------------------------------------------
    # Switch translation
    # ---------------------------------------------------------------------

    def _translate_switch_info(self, config: Optional[List[Dict[str, Any]]]) -> None:
        """
        Translate switch selectors to switch IDs in-place.

        Args:
            config: List of config dictionaries (modified in-place)

        For each config item with a 'switch' list, resolves each switch
        identifier (hostname, IP, or serial) to its switchId and updates
        the config in-place.
        """
        logger.debug("Starting switch translation")
        if config is None:
            return
        for item in config:
            switches = item.get("switch")
            if not switches:
                continue
            logger.debug(f"Translating {len(switches)} switch identifiers")
            translated = []
            for switch in switches:
                translated.append(self._resolve_switch(str(switch)))
            item["switch"] = translated
        logger.debug("Switch translation completed")

    def _resolve_switch(self, switch_value: str) -> str:
        """
        Resolve a switch identifier to its switchId.

        Args:
            switch_value: Switch identifier (hostname, IP, or serial number)

        Returns:
            The switchId for the given identifier

        Raises:
            ValueError: If switch cannot be resolved in the fabric

        Lazily loads switch lookup table on first call.
        """
        logger.debug(f"Resolving switch identifier: {switch_value}")
        if self._switch_lookup is None:
            self._switch_lookup = self._load_switch_lookup()

        key = str(switch_value).strip().lower()
        switch_id = self._switch_lookup.get(key)
        if switch_id is None:
            logger.error(f"Unable to resolve switch '{switch_value}' in fabric '{self.fabric}'")
            raise ValueError("Unable to resolve switch '{0}' to a switchId in fabric '{1}'".format(switch_value, self.fabric))
        logger.debug(f"Resolved '{switch_value}' to switchId: {switch_id}")
        return switch_id

    def _load_switch_lookup(self) -> Dict[str, str]:
        """
        Load switch lookup table mapping identifiers to switchIds.

        Returns:
            Dictionary mapping switch identifiers (lowercase) to switchIds

        Queries the fabric for all switches and builds a lookup table
        using switchId, hostname, fabric management IP, and telemetry IPs.
        """
        logger.info(f"Loading switch lookup table for fabric '{self.fabric}'")
        ep = EpApiV1ManageSwitchesGet()
        ep.endpoint_params.fabric_name = self.fabric

        data = self._request(
            action="resolve_switches",
            operation_type=OperationType.QUERY,
            path=ep.path,
            verb=ep.verb,
            diff={},
        )

        lookup: Dict[str, str] = {}
        switch_count = len(data.get("switches", []))
        logger.debug(f"Processing {switch_count} switches from API response")

        for idx, switch in enumerate(data.get("switches", [])):
            switch_id = switch.get("switchId")
            if not switch_id:
                logger.debug(f"Switch {idx+1} has no switchId - skipping")
                continue

            keys = self._switch_keys_for_lookup(switch)
            logger.debug(f"Switch {idx+1} ({switch_id}): generated {len(keys)} lookup keys")
            for key in keys:
                lookup[key] = switch_id

        logger.info(f"Loaded {switch_count} switches with {len(lookup)} lookup keys")
        return lookup

    def _switch_keys_for_lookup(self, switch: Dict[str, Any]) -> Set[str]:
        """
        Extract all possible lookup keys for a switch.

        Args:
            switch: Switch dictionary from API response

        Returns:
            Set of lowercase lookup keys (switchId, hostname, IPs)

        Extracts switchId, hostname, fabricManagementIp, and any IPs
        from telemetryIpCollection as potential lookup keys.
        """
        keys: Set[str] = set()

        for field in ["switchId", "hostname", "fabricManagementIp"]:
            value = switch.get(field)
            if isinstance(value, str) and value.strip():
                keys.add(value.strip().lower())

        telemetry = switch.get("telemetryIpCollection")
        if isinstance(telemetry, dict):
            logger.debug(f"Processing {len(telemetry)} telemetry IPs for switch lookup")
            for value in telemetry.values():
                if isinstance(value, str) and value.strip():
                    keys.add(value.strip().lower())

        logger.debug(f"Generated {len(keys)} keys for switch: {switch.get('switchId')}")
        return keys

    # ---------------------------------------------------------------------
    # Desired state model building
    # ---------------------------------------------------------------------

    def _build_rm_info_from_config(self, config: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Build resource manager info list from config.

        Args:
            config: List of config dictionaries

        Returns:
            List of normalized resource manager info dictionaries

        Filters out config items with explicit delete selectors and
        normalizes scope_type to snake_case format.
        """
        logger.debug(f"Building resource manager info from {len(config) if config else 0} config items")
        if not config:
            logger.debug("No config provided - returning empty rm_info")
            return []

        rm_info: List[Dict[str, Any]] = []
        for idx, item in enumerate(config):
            logger.debug(f"Processing config item {idx+1}/{len(config)}: {item.get('entity_name')}")
            if self.state == "deleted" and (self._has_explicit_delete_selector(item) or item.get("delete_by_details") is True):
                logger.debug(f"Skipping item {idx+1} - has explicit delete selector")
                continue

            entry = copy.deepcopy(item)
            entry["scope_type"] = self._to_scope_snake(item.get("scope_type"))
            rm_info.append(entry)
            logger.debug(f"Added item {idx+1} to rm_info with scope_type: {entry['scope_type']}")

        logger.debug(f"Built {len(rm_info)} resource manager info entries")
        return rm_info

    def _build_want(self, rm_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build desired state (want) from resource manager info.

        Args:
            rm_info: List of resource manager info dictionaries

        Returns:
            List of want entries with payload and signature

        Generates API payloads from config and deduplicates based on
        signature (pool_name, entity_name, scope details).
        """
        logger.debug(f"Building desired state from {len(rm_info)} config items")
        want: List[Dict[str, Any]] = []
        for idx, cfg in enumerate(rm_info):
            logger.debug(f"Processing config {idx+1}/{len(rm_info)}: entity={cfg.get('entity_name')}, pool={cfg.get('pool_name')}")
            payloads = self._build_payloads_from_config(cfg)
            logger.debug(f"Generated {len(payloads)} payload(s) from config {idx+1}")
            for payload in payloads:
                signature = self._want_signature(payload)
                if not any(entry["signature"] == signature for entry in want):
                    want.append(
                        {
                            "payload": payload,
                            "signature": signature,
                        }
                    )
                    logger.debug(f"Added unique payload - total want entries: {len(want)}")
                else:
                    logger.debug(f"Skipped duplicate payload with signature: {signature}")
        logger.debug(f"Built {len(want)} unique desired state entries")
        return want

    def _want_signature(self, payload: Dict[str, Any]) -> Tuple[Any, ...]:
        """
        Generate a unique signature for a resource payload.

        Args:
            payload: Resource payload dictionary

        Returns:
            Tuple signature for deduplication and matching

        Signature includes pool_name, entity_name, scope_type, and
        all scope details fields (sorted for consistency).
        """
        scope = payload.get("scopeDetails", {})
        return (
            payload.get("poolName"),
            payload.get("entityName"),
            scope.get("scopeType"),
            tuple(sorted(scope.items())),
        )

    def _build_payloads_from_config(self, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build one or more API payloads from a config item.

        Args:
            cfg: Config dictionary

        Returns:
            List of API payload dictionaries

        For device and device_interface scopes, generates one payload per switch.
        For other scopes, generates a single payload.
        """
        logger.debug(f"Building payloads from config - scope_type: {cfg.get('scope_type')}, entity: {cfg.get('entity_name')}")
        scope_type = cfg.get("scope_type")
        payloads: List[Dict[str, Any]] = []

        if scope_type in ("device", "device_interface"):
            switches = cfg.get("switch", [])
            logger.debug(f"Scope requires per-switch payloads - generating for {len(switches)} switches")
            for idx, switch_id in enumerate(switches):
                logger.debug(f"Building payload {idx+1}/{len(switches)} for switch: {switch_id}")
                payloads.append(self._build_single_payload(cfg, switch_id=switch_id))
            logger.debug(f"Generated {len(payloads)} payloads for device/device_interface scope")
            return payloads

        logger.debug(f"Scope '{scope_type}' uses single payload")
        payloads.append(self._build_single_payload(cfg, switch_id=None))
        return payloads

    def _build_single_payload(self, cfg: Dict[str, Any], switch_id: Optional[str]) -> Dict[str, Any]:
        """
        Build a single API payload from config.

        Args:
            cfg: Config dictionary
            switch_id: Switch ID for device/device_interface scopes (optional for others)

        Returns:
            Validated API payload dictionary

        Raises:
            ValueError: If payload validation fails

        Constructs payload with pool_name, scope_details, entity_name, vrf_name,
        is_pre_allocated, and resource_value (if provided).
        """
        logger.debug(f"Building single payload - switch_id: {switch_id}, entity: {cfg.get('entity_name')}")
        scope_type = cfg.get("scope_type")
        resource_value = cfg.get("resource")

        payload: Dict[str, Any] = {
            "poolName": cfg.get("pool_name"),
            "scopeDetails": self._build_scope_details(cfg, switch_id=switch_id),
            "entityName": cfg.get("entity_name"),
            "vrfName": cfg.get("vrf_name", "default"),
            "isPreAllocated": cfg.get("is_pre_allocated", False),
        }

        if resource_value is not None:
            logger.debug(f"Including resource value in payload: {resource_value}")
            payload["resourceValue"] = str(resource_value)

        try:
            model = ResourceDetailsPostModel.model_validate(payload)
            logger.debug(f"Payload validation successful")
        except ValidationError as exc:
            logger.error(f"Payload validation failed: {exc}")
            raise ValueError("Invalid resource payload generated from config: {0}".format(exc)) from exc

        final_payload = model.to_payload()
        logger.debug(f"Generated final payload with poolName: {final_payload.get('poolName')}")
        return final_payload

    def _build_scope_details(self, cfg: Dict[str, Any], switch_id: Optional[str]) -> Dict[str, Any]:
        """
        Build scope details for a resource payload.

        Args:
            cfg: Config dictionary
            switch_id: Switch ID for device/device_interface scopes

        Returns:
            Scope details dictionary with scopeType and scope-specific fields

        Raises:
            ValueError: If required fields are missing or scope type is unsupported

        Handles all scope types:
        - fabric: fabricName
        - device: switchId
        - device_interface: switchId, interfaceName
        - device_pair: srcSwitchId, dstSwitchId
        - link: srcSwitchId, srcInterfaceName, dstSwitchId, dstInterfaceName
        """
        logger.debug(f"Building scope details - scope_type: {cfg.get('scope_type')}")
        scope_type = cfg.get("scope_type")
        entity_name = str(cfg.get("entity_name", ""))
        parts = entity_name.split("~") if entity_name else []

        if scope_type == "fabric":
            return {
                "scopeType": ScopeType.FABRIC.value,
                "fabricName": cfg.get("fabric_name", self.fabric),
            }

        if scope_type == "device":
            if not switch_id:
                raise ValueError("switch_id is required for device scope")
            return {
                "scopeType": ScopeType.DEVICE.value,
                "switchId": switch_id,
            }

        if scope_type == "device_interface":
            if not switch_id:
                raise ValueError("switch_id is required for device_interface scope")

            interface_name = cfg.get("interface_name")
            if interface_name is None and len(parts) > 1:
                interface_name = parts[1]
            if interface_name is None:
                raise ValueError("interface_name is required or must be derivable from entity_name for device_interface scope")

            return {
                "scopeType": ScopeType.DEVICE_INTERFACE.value,
                "switchId": switch_id,
                "interfaceName": interface_name,
            }

        if scope_type == "device_pair":
            src_switch_id, dst_switch_id = self._pair_switch_ids(cfg, parts)
            return {
                "scopeType": ScopeType.DEVICE_PAIR.value,
                "srcSwitchId": src_switch_id,
                "dstSwitchId": dst_switch_id,
            }

        if scope_type == "link":
            src_switch_id, dst_switch_id = self._pair_switch_ids(cfg, parts)
            src_interface = cfg.get("src_interface_name")
            dst_interface = cfg.get("dst_interface_name")

            if src_interface is None and len(parts) > 1:
                src_interface = parts[1]
            if dst_interface is None and len(parts) > 3:
                dst_interface = parts[3]

            if src_interface is None or dst_interface is None:
                raise ValueError("src_interface_name and dst_interface_name are required or must be derivable from entity_name for link scope")

            return {
                "scopeType": ScopeType.LINK.value,
                "srcSwitchId": src_switch_id,
                "srcInterfaceName": src_interface,
                "dstSwitchId": dst_switch_id,
                "dstInterfaceName": dst_interface,
            }

        raise ValueError("Unsupported scope type '{0}'".format(scope_type))

    def _pair_switch_ids(self, cfg: Dict[str, Any], entity_parts: List[str]) -> Tuple[str, str]:
        """
        Resolve source and destination switch IDs for pair/link scopes.

        Args:
            cfg: Config dictionary
            entity_parts: Parts of entity_name split by '~'

        Returns:
            Tuple of (src_switch_id, dst_switch_id)

        Raises:
            ValueError: If switch IDs cannot be resolved

        Tries multiple sources in order:
        1. Explicit src_switch_id/dst_switch_id in config
        2. First two elements of 'switch' list
        3. First two parts of entity_name
        """
        logger.debug("Resolving switch pair for device_pair or link scope")
        src_switch_id = cfg.get("src_switch_id")
        dst_switch_id = cfg.get("dst_switch_id")

        switches = cfg.get("switch") or []
        if src_switch_id is None and len(switches) > 0:
            src_switch_id = switches[0]
        if dst_switch_id is None and len(switches) > 1:
            dst_switch_id = switches[1]

        if src_switch_id is None and len(entity_parts) > 0:
            src_switch_id = self._resolve_switch(entity_parts[0])
        elif src_switch_id is not None:
            src_switch_id = self._resolve_switch(src_switch_id)

        if dst_switch_id is None and len(entity_parts) > 1:
            dst_switch_id = self._resolve_switch(entity_parts[1])
        elif dst_switch_id is not None:
            dst_switch_id = self._resolve_switch(dst_switch_id)

        if src_switch_id is None or dst_switch_id is None:
            raise ValueError("Unable to resolve src/dst switch IDs for pair/link scope")

        return src_switch_id, dst_switch_id

    # ---------------------------------------------------------------------
    # Existing state loading and matching
    # ---------------------------------------------------------------------

    def _fetch_all_resources(self) -> List[Dict[str, Any]]:
        """
        Fetch all existing resources from the fabric.

        Returns:
            List of resource payload dictionaries

        Raises:
            ValueError: If response validation fails

        Caches the result in _all_resources for subsequent calls.
        """
        logger.info(f"Fetching all resources from fabric '{self.fabric}'")
        if self._all_resources is not None:
            logger.debug(f"Using cached resources ({len(self._all_resources)} resources)")
            return self._all_resources

        logger.debug(f"Making API request to fetch resources")
        ep = EpApiV1ManageGetFabricResources(fabric_name=self.fabric)
        data = self._request(
            action="query_resources_existing",
            operation_type=OperationType.QUERY,
            path=ep.path,
            verb=ep.verb,
            diff={},
        )

        try:
            model = ResourcesResponseModel.from_response(data)
        except ValidationError as exc:
            logger.error(f"Failed to validate resources response: {exc}")
            raise ValueError("Invalid resources response payload: {0}".format(exc)) from exc

        resources = [resource.to_payload() for resource in model.resources]
        self._all_resources = resources
        logger.info(f"Fetched and cached {len(resources)} resources from fabric")
        return resources

    def _match_resource_core(self, have: Dict[str, Any], want: Dict[str, Any], compare_value: bool) -> bool:
        """
        Check if an existing resource matches a desired resource.

        Args:
            have: Existing resource payload
            want: Desired resource payload
            compare_value: If True, also compare resource values

        Returns:
            True if resources match

        Compares entity_name, pool_name, scope_type, and scope details.
        If compare_value is True, also compares resourceValue.
        """
        have_entity = have.get("entityName", "")
        want_entity = want.get("entityName", "")
        logger.debug(f"Matching resources - have_entity: {have_entity}, want_entity: {want_entity}, compare_value: {compare_value}")

        if not self._compare_entity_names(str(have_entity), str(want_entity)):
            logger.debug(f"Entity names don't match")
            return False

        have_pool = have.get("poolName")
        want_pool = want.get("poolName")
        if have_pool != want_pool:
            logger.debug(f"Pool names don't match - have: {have_pool}, want: {want_pool}")
            return False

        have_scope = have.get("scopeDetails") or {}
        want_scope = want.get("scopeDetails") or {}

        have_scope_type = SCOPE_API_TO_SNAKE.get(have_scope.get("scopeType"))
        want_scope_type = SCOPE_API_TO_SNAKE.get(want_scope.get("scopeType"))

        if have_scope_type != want_scope_type:
            logger.debug(f"Scope types don't match - have: {have_scope_type}, want: {want_scope_type}")
            return False

        if not self._match_scope_details(have_scope_type, have_scope, want_scope):
            logger.debug(f"Scope details don't match for scope_type: {have_scope_type}")
            return False

        if compare_value:
            have_value = have.get("resourceValue", "")
            want_value = want.get("resourceValue", "")
            match = self._compare_resource_values(str(have_value), str(want_value))
            logger.debug(f"Resource value comparison - have: {have_value}, want: {want_value}, match: {match}")
            return match

        logger.debug(f"Resources match (value not compared)")
        return True

    def _match_scope_details(self, scope_type: Optional[str], have_scope: Dict[str, Any], want_scope: Dict[str, Any]) -> bool:
        """
        Check if scope details match between existing and desired resources.

        Args:
            scope_type: Normalized scope type (snake_case)
            have_scope: Existing scope details
            want_scope: Desired scope details

        Returns:
            True if scope details match for the given scope type

        Handles scope-specific matching logic:
        - fabric: fabricName
        - device: switchId
        - device_interface: switchId and interfaceName
        - device_pair: src/dst switchIds (order-independent)
        - link: src/dst switchIds and interfaceNames (bidirectional)
        """
        logger.debug(f"Matching scope details for scope_type: {scope_type}")

        if scope_type == "fabric":
            have_fab = have_scope.get("fabricName", "")
            want_fab = want_scope.get("fabricName", "")
            match = str(have_fab) == str(want_fab)
            logger.debug(f"Fabric scope - have: {have_fab}, want: {want_fab}, match: {match}")
            return match

        if scope_type == "device":
            have_sw = have_scope.get("switchId", "")
            want_sw = want_scope.get("switchId", "")
            match = str(have_sw) == str(want_sw)
            logger.debug(f"Device scope - have: {have_sw}, want: {want_sw}, match: {match}")
            return match

        if scope_type == "device_interface":
            have_sw = have_scope.get("switchId", "")
            want_sw = want_scope.get("switchId", "")
            have_if = have_scope.get("interfaceName", "")
            want_if = want_scope.get("interfaceName", "")
            match = str(have_sw) == str(want_sw) and str(have_if) == str(want_if)
            logger.debug(
                f"Device interface scope - switch match: {str(have_sw)==str(want_sw)}, interface match: {str(have_if)==str(want_if)}, overall: {match}"
            )
            return match

        if scope_type == "device_pair":
            have_pair = sorted([str(have_scope.get("srcSwitchId", "")), str(have_scope.get("dstSwitchId", ""))])
            want_pair = sorted([str(want_scope.get("srcSwitchId", "")), str(want_scope.get("dstSwitchId", ""))])
            match = have_pair == want_pair
            logger.debug(f"Device pair scope - have: {have_pair}, want: {want_pair}, match: {match}")
            return match

        if scope_type == "link":
            forward = (
                str(have_scope.get("srcSwitchId", "")) == str(want_scope.get("srcSwitchId", ""))
                and str(have_scope.get("srcInterfaceName", "")) == str(want_scope.get("srcInterfaceName", ""))
                and str(have_scope.get("dstSwitchId", "")) == str(want_scope.get("dstSwitchId", ""))
                and str(have_scope.get("dstInterfaceName", "")) == str(want_scope.get("dstInterfaceName", ""))
            )
            reverse = (
                str(have_scope.get("srcSwitchId", "")) == str(want_scope.get("dstSwitchId", ""))
                and str(have_scope.get("srcInterfaceName", "")) == str(want_scope.get("dstInterfaceName", ""))
                and str(have_scope.get("dstSwitchId", "")) == str(want_scope.get("srcSwitchId", ""))
                and str(have_scope.get("dstInterfaceName", "")) == str(want_scope.get("srcInterfaceName", ""))
            )
            match = forward or reverse
            logger.debug(f"Link scope - forward: {forward}, reverse: {reverse}, match: {match}")
            return match

        logger.warning(f"Unknown scope_type: {scope_type} - returning False")
        return False

    def _compare_entity_names(self, first: str, second: str) -> bool:
        """
        Compare entity names (order-independent for ~ delimited parts).

        Args:
            first: First entity name
            second: Second entity name

        Returns:
            True if entity names match (parts can be in any order)
        """
        return sorted(first.split("~")) == sorted(second.split("~"))

    def _compare_resource_values(self, first: str, second: str) -> bool:
        """
        Compare resource values with intelligent type handling.

        Args:
            first: First resource value
            second: Second resource value

        Returns:
            True if resource values match

        Handles:
        - String comparison
        - IP subnet comparison (normalizes prefix)
        - IP address comparison
        Falls back to string comparison if parsing fails.
        """
        if first == second:
            return True

        try:
            if "/" in first and "/" in second:
                network_first = ipaddress.ip_network(first, strict=False)
                network_second = ipaddress.ip_network(second, strict=False)
                return network_first == network_second

            if "/" not in first and "/" not in second:
                ip_first = ipaddress.ip_address(first)
                ip_second = ipaddress.ip_address(second)
                return ip_first == ip_second
        except ValueError:
            return first == second

        return first == second

    # ---------------------------------------------------------------------
    # State handlers
    # ---------------------------------------------------------------------

    def _handle_merged(self) -> None:
        """
        Handle merged state - allocate resources.

        Compares desired resources (want) with existing resources (have)
        and allocates any that don't exist or have different values.

        Updates self.current with:
        - merged: List of resources that were allocated
        - response: API response
        - existing: List of existing resources (if no changes)
        """
        logger.info(f"Handling merged state - checking {len(self.want)} desired resources against {len(self.have)} existing resources")
        diff_create: List[Dict[str, Any]] = []

        for idx, want_entry in enumerate(self.want):
            payload = want_entry["payload"]
            entity = payload.get("entityName")
            pool = payload.get("poolName")
            logger.debug(f"Checking resource {idx+1}/{len(self.want)}: entity={entity}, pool={pool}")
            matched = [resource for resource in self.have if self._match_resource_core(resource, payload, compare_value=False)]
            if not matched:
                logger.debug(f"Resource {idx+1} not found - will create")
                diff_create.append(payload)
                continue

            logger.debug(f"Resource {idx+1} found - checking if value matches")
            if not any(self._match_resource_core(resource, payload, compare_value=True) for resource in matched):
                logger.debug(f"Resource {idx+1} has different value - will update")
                diff_create.append(payload)
            else:
                logger.debug(f"Resource {idx+1} matches - no action needed")

        if not diff_create:
            logger.info("No resources need to be created - all desired resources already exist")
            self.current = {"merged": [], "existing": self.have}
            return

        logger.info(f"Allocating {len(diff_create)} resources")
        request_model = AllocateResourcesRequestModel.model_validate({"resources": diff_create})

        ep = EpApiV1ManagePostFabricResources(fabric_name=self.fabric)
        if self.tenant_name:
            ep.endpoint_params.tenant_name = self.tenant_name

        data = self._request(
            action="allocate_resources",
            operation_type=OperationType.CREATE,
            path=ep.path,
            verb=ep.verb,
            payload=request_model.to_payload(),
            allow_207=True,
            diff={"merged": diff_create},
        )

        try:
            AllocateResourcesResponseModel.from_response(data)
        except ValidationError:
            # Keep raw response in current if the controller payload differs.
            pass

        self.current = {"merged": diff_create, "response": data}

    def _handle_deleted(self) -> None:
        """
        Handle deleted state - release resources.

        Supports three deletion methods:
        1. Explicit resource IDs (resource_id, resource_ids)
        2. DCNM-style matching (entity_name, pool_name, scope)
        3. Delete-by-details endpoint (delete_by_details flag)

        Updates self.current with:
        - deleted_resource_ids: IDs deleted via bulk endpoint
        - deleted_by_id: IDs deleted via individual endpoint
        - deleted_by_details: Payloads deleted via details endpoint
        """
        logger.info(f"Handling deleted state - processing {len(self.config) if self.config else 0} config items")
        explicit_ids: Set[int] = set()
        explicit_delete_by_id: List[int] = []
        delete_by_details_payloads: List[Dict[str, Any]] = []

        # Parse explicit selectors.
        if self.config:
            logger.debug(f"Parsing explicit delete selectors from config")
            for idx, item in enumerate(self.config):
                logger.debug(f"Processing delete config item {idx+1}/{len(self.config)}")
                resource_ids = item.get("resource_ids")
                if isinstance(resource_ids, list):
                    logger.debug(f"Item {idx+1} has resource_ids list: {resource_ids}")
                    explicit_ids.update(int(value) for value in resource_ids)

                resource_id = item.get("resource_id")
                if isinstance(resource_id, int):
                    logger.debug(f"Item {idx+1} has resource_id: {resource_id}")
                    explicit_delete_by_id.append(resource_id)

                if item.get("delete_by_details") is True:
                    logger.debug(f"Item {idx+1} uses delete_by_details method")
                    scoped_cfg = copy.deepcopy(item)
                    scoped_cfg["scope_type"] = self._to_scope_snake(scoped_cfg.get("scope_type"))
                    for payload in self._build_payloads_from_config(scoped_cfg):
                        delete_by_details_payloads.append(payload)
                    logger.debug(f"Generated {len(delete_by_details_payloads)} delete_by_details payloads")

        # DCNM-style matching to existing resources.
        matched_ids: Set[int] = set(explicit_ids)
        fallback_delete_by_details: List[Dict[str, Any]] = []

        for want_entry in self.want:
            payload = want_entry["payload"]
            matched = [resource for resource in self.have if self._match_resource_core(resource, payload, compare_value=False)]
            if not matched:
                continue

            for have_entry in matched:
                resource_id = have_entry.get("resourceId")
                if isinstance(resource_id, int):
                    matched_ids.add(resource_id)
                else:
                    fallback_delete_by_details.append(payload)

        # Remove duplicates for delete-by-details payloads.
        seen_signatures: Set[Tuple[Any, ...]] = set()
        dedup_delete_by_details: List[Dict[str, Any]] = []
        for payload in delete_by_details_payloads + fallback_delete_by_details:
            signature = self._want_signature(payload)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            dedup_delete_by_details.append(payload)

        # Bulk delete by ID endpoint.
        if matched_ids:
            logger.info(f"Deleting {len(matched_ids)} resources by IDs via bulk endpoint")
            request_model = RemoveResourcesByIdRequestModel.model_validate({"resourceIds": sorted(matched_ids)})
            ep = EpApiV1ManagePostFabricResourcesActionsRemove(fabric_name=self.fabric)
            data = self._request(
                action="delete_resources_by_ids",
                operation_type=OperationType.DELETE,
                path=ep.path,
                verb=ep.verb,
                payload=request_model.to_payload(),
                allow_207=True,
                diff={"deleted_resource_ids": sorted(matched_ids)},
            )

            try:
                RemoveResourcesResponseModel.from_response(data)
            except ValidationError:
                # Keep raw data in current if response is non-standard.
                pass

        # Explicit delete-by-id endpoint.
        deleted_by_id: List[int] = []
        logger.debug(f"Processing {len(explicit_delete_by_id)} explicit delete-by-id requests")
        for resource_id in explicit_delete_by_id:
            if not self._resource_exists_by_id(resource_id):
                logger.debug(f"Resource {resource_id} does not exist - skipping")
                continue

            ep_delete = EpApiV1ManageDeleteFabricResourceById(fabric_name=self.fabric, resource_id=resource_id)
            self._request(
                action="delete_resource_by_id",
                operation_type=OperationType.DELETE,
                path=ep_delete.path,
                verb=ep_delete.verb,
                diff={"deleted_resource_id": resource_id},
            )
            deleted_by_id.append(resource_id)

        # Delete-by-details endpoint.
        deleted_by_details: List[Dict[str, Any]] = []
        logger.debug(f"Processing {len(dedup_delete_by_details)} delete-by-details requests")
        for payload in dedup_delete_by_details:
            ResourceDetailsPostModel.model_validate(payload)
            ep = EpApiV1ManagePostFabricResourcesActionsRemoveResource(fabric_name=self.fabric)
            data = self._request(
                action="delete_resource_by_details",
                operation_type=OperationType.DELETE,
                path=ep.path,
                verb=ep.verb,
                payload=payload,
                diff={"deleted_by_details": payload},
            )
            try:
                RemoveResourceByDetailsResponseModel.from_response(data)
            except ValidationError:
                pass
            deleted_by_details.append(payload)

        self.current = {
            "deleted_resource_ids": sorted(matched_ids),
            "deleted_by_id": deleted_by_id,
            "deleted_by_details": deleted_by_details,
        }

    def _resource_exists_by_id(self, resource_id: int) -> bool:
        """
        Check if a resource exists by its ID.

        Args:
            resource_id: Resource ID to check

        Returns:
            True if resource exists, False otherwise

        Queries the resource by ID and validates the response.
        Returns False on 404 (not found) or validation errors.
        """
        logger.debug(f"Checking if resource {resource_id} exists")
        ep = EpApiV1ManageGetFabricResourceById(fabric_name=self.fabric, resource_id=resource_id)
        data = self._request(
            action="query_resource_by_id_for_delete",
            operation_type=OperationType.QUERY,
            path=ep.path,
            verb=ep.verb,
            allow_404=True,
            diff={},
        )

        response_result = self.nd.rest_send.result_current
        if response_result.get("found") is False:
            return False

        if not data:
            return False

        try:
            ResourceDetailsGetModel.from_response(data)
        except ValidationError:
            return False

        return True

    def _handle_query(self) -> None:
        """
        Handle query state - retrieve resource or pool information.

        Dispatches to appropriate query handler based on query_target:
        - resources: Query resource allocations
        - pools: Query resource pools
        - propose_vlan: Query next available VLAN

        Updates self.current with query results.
        """
        logger.info(f"Handling query state - target: {self.query_target}")
        if self.query_target == "resources":
            self.current = self._query_resources()
            return
        if self.query_target == "pools":
            self.current = self._query_pools()
            return
        self.current = self._query_propose_vlan()

    # ---------------------------------------------------------------------
    # Query handlers
    # ---------------------------------------------------------------------

    def _query_resources(self) -> Dict[str, Any]:
        """
        Query resource allocations.

        Returns:
            Dictionary with 'resources' list and optional 'meta'

        If no config provided, queries all resources.
        If config provided, supports:
        - Query by resource_id
        - Filter by pool_name, entity_name, switches
        - Lucene filters, pagination, sorting

        Deduplicates results by resource ID or signature.
        """
        logger.info(f"Querying resources for fabric '{0}'".format(self.fabric))
        if not self.config:
            logger.info("No config provided - querying all resources")
            ep = EpApiV1ManageGetFabricResources(fabric_name=self.fabric)
            data = self._request(
                action="query_resources",
                operation_type=OperationType.QUERY,
                path=ep.path,
                verb=ep.verb,
                diff={},
            )
            try:
                logger.debug("calling ResourcesResponseModel.from_response()::{0}".format(data))
                model = ResourcesResponseModel.from_response(data)
                logger.info(f"Query returned {len(model.resources)} resources")
                return {"resources": [resource.to_payload() for resource in model.resources], "meta": model.meta}
            except ValidationError:
                logger.warning("Failed to validate response model - returning raw data")
                return data

        dedup: Dict[str, Dict[str, Any]] = {}
        all_resources = self._fetch_all_resources()
        logger.info(f"Processing {len(self.config)} query config items against {len(all_resources)} total resources")

        for idx, cfg in enumerate(self.config):
            logger.debug(f"Processing query config {idx+1}/{len(self.config)}")
            resource_id = cfg.get("resource_id")
            if isinstance(resource_id, int):
                logger.debug(f"Querying resource by ID: {resource_id}")
                ep_by_id = EpApiV1ManageGetFabricResourceById(fabric_name=self.fabric, resource_id=resource_id)
                data = self._request(
                    action="query_resource_by_id",
                    operation_type=OperationType.QUERY,
                    path=ep_by_id.path,
                    verb=ep_by_id.verb,
                    diff={},
                )
                if self.nd.rest_send.result_current.get("found") is False:
                    logger.debug(f"Resource ID {resource_id} not found")
                    continue
                logger.debug(f"Resource ID {resource_id} found")
                try:
                    resource_model = ResourceDetailsGetModel.from_response(data)
                    resource = resource_model.to_payload()
                except ValidationError:
                    resource = data
                key = self._resource_dedup_key(resource)
                dedup[key] = resource
                continue

            filtered = self._filter_resources_by_cfg(all_resources, cfg)
            for resource in filtered:
                key = self._resource_dedup_key(resource)
                dedup[key] = resource

        return {"resources": list(dedup.values())}

    def _filter_resources_by_cfg(self, resources: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter resources based on config criteria.

        Args:
            resources: List of resource payloads to filter
            cfg: Config dictionary with filter criteria

        Returns:
            Filtered list of resource payloads

        Filters by:
        - pool_name: Exact match
        - entity_name: Order-independent part matching
        - switch: Any scope field contains a listed switch
        """
        filtered: List[Dict[str, Any]] = []
        pool_name = cfg.get("pool_name")
        entity_name = cfg.get("entity_name")
        switches = cfg.get("switch") or []

        for resource in resources:
            if pool_name is not None and resource.get("poolName") != pool_name:
                continue

            if entity_name is not None and not self._compare_entity_names(str(resource.get("entityName", "")), str(entity_name)):
                continue

            if switches and not self._resource_matches_switches(resource, switches):
                continue

            filtered.append(resource)

        return filtered

    def _resource_matches_switches(self, resource: Dict[str, Any], switches: List[str]) -> bool:
        """
        Check if a resource matches any of the given switches.

        Args:
            resource: Resource payload with scopeDetails
            switches: List of switch identifiers

        Returns:
            True if any scope field (switchId, srcSwitchId, dstSwitchId)
            matches any of the given switches
        """
        switch_set = set(str(switch) for switch in switches)
        scope = resource.get("scopeDetails") or {}

        for key in ["switchId", "srcSwitchId", "dstSwitchId"]:
            value = scope.get(key)
            if value is not None and str(value) in switch_set:
                return True

        return False

    def _resource_dedup_key(self, resource: Dict[str, Any]) -> str:
        """
        Generate a deduplication key for a resource.

        Args:
            resource: Resource payload

        Returns:
            Unique key string for deduplication

        Uses resourceId if available, otherwise generates a signature
        from pool_name, entity_name, and scope details.
        """
        resource_id = resource.get("resourceId")
        if resource_id is not None:
            return "id:{0}".format(resource_id)
        return "sig:{0}:{1}:{2}".format(
            resource.get("poolName"),
            resource.get("entityName"),
            sorted((resource.get("scopeDetails") or {}).items()),
        )

    def _query_pools(self) -> Dict[str, Any]:
        """
        Query resource pools.

        Returns:
            Dictionary with 'pools' list and optional 'meta'

        If no config provided, queries all pools.
        If config provided, supports:
        - Query by pool_id
        - Lucene filters, pagination, sorting

        Deduplicates results by poolId:poolName.
        """
        logger.debug("Querying pools")
        if not self.config:
            logger.debug("No config provided - querying all pools")
            ep = EpApiV1ManageGetFabricsPools(fabric_name=self.fabric)
            data = self._request(
                action="query_pools",
                operation_type=OperationType.QUERY,
                path=ep.path,
                verb=ep.verb,
                diff={},
            )
            try:
                model = PoolsResponseModel.from_response(data)
                return {"pools": [pool.to_payload() for pool in model.pools], "meta": model.meta}
            except ValidationError:
                return data

        pools_dedup: Dict[str, Dict[str, Any]] = {}
        meta: Optional[Dict[str, Any]] = None
        logger.debug(f"Processing {len(self.config)} pool query config items")

        for cfg in self.config:
            ep = EpApiV1ManageGetFabricsPools(fabric_name=self.fabric)

            if cfg.get("pool_id") is not None:
                ep.endpoint_params.pool_id = cfg.get("pool_id")

            if cfg.get("filter") is not None:
                ep.lucene_params.filter = cfg.get("filter")
            if cfg.get("max") is not None:
                ep.lucene_params.max = cfg.get("max")
            if cfg.get("offset") is not None:
                ep.lucene_params.offset = cfg.get("offset")
            if cfg.get("sort") is not None:
                ep.lucene_params.sort = cfg.get("sort")

            data = self._request(
                action="query_pools",
                operation_type=OperationType.QUERY,
                path=ep.path,
                verb=ep.verb,
                diff={},
            )

            try:
                model = PoolsResponseModel.from_response(data)
                if model.meta is not None:
                    meta = model.meta
                for pool in model.pools:
                    payload = pool.to_payload()
                    key = "{0}:{1}".format(payload.get("poolId"), payload.get("poolName"))
                    pools_dedup[key] = payload
            except ValidationError:
                for pool in data.get("pools", []):
                    key = "{0}:{1}".format(pool.get("poolId"), pool.get("poolName"))
                    pools_dedup[key] = pool
                if data.get("meta") is not None:
                    meta = data.get("meta")

        return {"pools": list(pools_dedup.values()), "meta": meta}

    def _query_propose_vlan(self) -> Dict[str, Any]:
        """
        Query next available VLAN proposal.

        Returns:
            Dictionary with proposed VLAN information

        Requires:
        - vlan_type in first config item
        - Optional tenant_name for tenant-specific proposal
        """
        logger.debug("Querying propose VLAN")
        config = self.config[0] if self.config else {}
        ep = EpApiV1ManageGetFabricsProposeVlan(fabric_name=self.fabric)

        vlan_type = config.get("vlan_type")
        tenant_name = config.get("tenant_name") or self.tenant_name

        logger.debug(f"Propose VLAN parameters - vlan_type: {vlan_type}, tenant_name: {tenant_name}")
        ep.endpoint_params.vlan_type = vlan_type
        if tenant_name:
            ep.endpoint_params.tenant_name = tenant_name

        data = self._request(
            action="query_propose_vlan",
            operation_type=OperationType.QUERY,
            path=ep.path,
            verb=ep.verb,
            diff={},
        )

        logger.debug(f"Propose VLAN response received")
        try:
            model = ProposeVlanResponseModel.from_response(data)
            logger.info(f"Propose VLAN successful - proposed VLAN: {model.propose_vlan}")
            return model.to_payload()
        except ValidationError:
            logger.warning("Failed to validate propose VLAN response - returning raw data")
            return data

    # ---------------------------------------------------------------------
    # Result finalization
    # ---------------------------------------------------------------------

    def build_final_result(self) -> Dict[str, Any]:
        """
        Build final result dictionary for module output.

        Returns:
            Dictionary with all results including:
            - changed, failed, diff, response, result, metadata
            - current: Final state from operation
        """
        logger.info("Building final result for module output")
        self.results.build_final_result()
        final = self.results.final_result
        final["current"] = self.current

        logger.debug(f"Final result - changed: {final.get('changed')}, failed: {final.get('failed')}")

        # Safely log diff and response structures
        diff_value = final.get("diff")
        if isinstance(diff_value, dict):
            logger.debug(f"Final result - diff keys: {list(diff_value.keys())}")
        elif isinstance(diff_value, list):
            logger.debug(f"Final result - diff is list with {len(diff_value)} items")
        else:
            logger.debug(f"Final result - diff type: {type(diff_value)}")

        response_value = final.get("response")
        if isinstance(response_value, dict):
            logger.debug(f"Final result - response keys: {list(response_value.keys())}")
        elif isinstance(response_value, list):
            logger.debug(f"Final result - response is list with {len(response_value)} items")
        else:
            logger.debug(f"Final result - response type: {type(response_value)}")

        logger.info(f"Final result built successfully - returning to Ansible")
        return final


def main() -> None:
    """
    Main entry point for the nd_resource_manager Ansible module.

    Sets up argument specification, creates the module instance,
    executes the task, and returns results to Ansible.

    Handles errors by returning failed results with error messages.
    """
    # Set up file logging
    setup_logging()

    logger.info("Starting nd_resource_manager module")
    argument_spec = nd_argument_spec()
    argument_spec.update(
        fabric=dict(type="str", required=True),
        config=dict(type="list", elements="dict"),
        tenant_name=dict(type="str"),
        query_target=dict(type="str", default="resources", choices=["resources", "pools", "propose_vlan"]),
        state=dict(type="str", default="merged", choices=["merged", "deleted", "query"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    task = NdResourceManagerTask(module)

    try:
        logger.info("Starting task commit workflow")
        task.commit()
        logger.info("Task commit completed successfully")
        final = task.build_final_result()
        if True in task.results.failed:
            logger.error("Module execution failed - one or more operations failed")
            logger.error(f"Failed operations: {task.results.failed}")
            module.fail_json(**final)
        logger.info("Module execution completed successfully - returning success")
        module.exit_json(**final)
    except (NDModuleError, ValidationError, ValueError, TypeError) as error:
        logger.error(f"Module execution failed with exception: {type(error).__name__}")
        logger.error(f"Error message: {error}")
        try:
            final = task.build_final_result()
        except (ValueError, TypeError):
            final = task.results.failed_result
            final["current"] = task.current
        module.fail_json(msg=str(error), **final)


if __name__ == "__main__":
    main()
