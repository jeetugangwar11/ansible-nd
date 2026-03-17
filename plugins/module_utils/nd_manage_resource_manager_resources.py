# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Manage ND fabric resource lifecycle workflows.

This module validates desired resource state, performs CRUD operations via the
ND Manage API, and coordinates query operations for
nd_manage_resource_manager_updated.

Architecture mirrors nd_switch_resources.py from ansible-nd collection.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.base_path import (
    BasePath,
)
from ansible_collections.cisco.nd.plugins.module_utils.endpoints.v1.manage.nd_resource_manager.nd_manage_resource_manager import (
    EpManageFabricResourcesActionsRemovePost,
    EpManageFabricResourcesGet,
    EpManageFabricResourcesPost,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.ResourceManagerConfigModel import (
    ResourceManagerConfigModel,
)
from ansible_collections.cisco.nd.plugins.module_utils.models.nd_manage_resource_manager.RemoveResourcesByIdsRequestModel import (
    RemoveResourcesByIdsRequest,
)
from ansible_collections.cisco.nd.plugins.module_utils.utils.nd_manage_resource_manager.payload_utils import (
    SCOPE_TYPE_MAP,
    build_resource_payload,
)
from ansible_collections.cisco.nd.plugins.module_utils.utils.nd_manage_resource_manager.resource_helpers import (
    compare_entity_names,
    compare_resource_values,
    match_resources,
)

log = logging.getLogger(__name__)


# =============================================================================
# Service Context (Dependency Container)
# =============================================================================


@dataclass
class ResourceManagerServiceContext:
    """
    Dependency container shared across all resource manager service classes.

    Attributes:
        nd: NDModule v1 instance providing .request() and .fail_json().
        fabric: Target fabric name.
        log: Module-level logger.
        check_mode: Whether Ansible is running in check mode.
        ip_sn: Mapping of management IP → switch serial number.
        result: Aggregated result dict (changed, diff, response).
    """

    nd: Any
    fabric: str
    log: Any
    check_mode: bool
    ip_sn: Dict[str, str] = field(default_factory=dict)
    result: Dict[str, Any] = field(
        default_factory=lambda: {"changed": False, "diff": [], "response": []}
    )


# =============================================================================
# Layer: Inventory Service (IP → Serial resolution)
# =============================================================================


class ResourceManagerInventoryService:
    """Resolves switch management IPs to serial numbers via ND inventory API."""

    @staticmethod
    def build_ip_sn_map(ctx: ResourceManagerServiceContext) -> Dict[str, str]:
        """
        Build a mapping of management IP address → switch serial number by
        querying GET /api/v1/manage/inventory/switches.

        Parameters:
            ctx: Service context holding the NDModule instance.

        Returns:
            dict: {mgmt_ip: serial_number} mapping.
        """
        inventory_path = BasePath.path("inventory", "switches")
        ctx.log.debug("build_ip_sn_map: GET %s", inventory_path)

        try:
            response = ctx.nd.request(inventory_path, method="GET")
        except Exception as exc:
            ctx.log.warning("build_ip_sn_map: inventory query failed: %s", exc)
            return {}

        if not response:
            ctx.log.warning("build_ip_sn_map: empty response from inventory endpoint")
            return {}

        switches = []
        if isinstance(response, list):
            switches = response
        elif isinstance(response, dict):
            for key in ("items", "data", "switches"):
                if key in response:
                    switches = response[key]
                    break
            if not switches:
                switches = [response] if response else []

        ip_sn = {}
        for sw in switches:
            mgmt_ip = sw.get("mgmtIp") or sw.get("managementIp") or sw.get("ipAddress")
            serial = sw.get("serialNumber") or sw.get("serialNum") or sw.get("serialNo")
            if mgmt_ip and serial:
                ip_sn[str(mgmt_ip).strip()] = str(serial).strip()

        ctx.log.debug("build_ip_sn_map: resolved %d switch(es)", len(ip_sn))
        return ip_sn

    @staticmethod
    def resolve_switch(ip_or_host: str, ip_sn: Dict[str, str]) -> str:
        """
        Resolve a switch IP/hostname to its serial number.

        Falls back to returning the value as-is if not found in the map
        (allows passing serial numbers directly in playbooks).
        """
        resolved = ip_sn.get(str(ip_or_host).strip())
        if resolved:
            return resolved
        return str(ip_or_host).strip()

    @staticmethod
    def translate_switch_info(config: List[Dict], ip_sn: Dict[str, str]) -> List[Dict]:
        """
        Translate switch IP addresses/hostnames to serial numbers in-place.

        Parameters:
            config: Playbook config list (modified in place).
            ip_sn: IP → serial mapping from build_ip_sn_map().

        Returns:
            The same config list with switch values replaced.
        """
        if config is None:
            return config
        for cfg in config:
            if not cfg.get("switch"):
                continue
            cfg["switch"] = [
                ResourceManagerInventoryService.resolve_switch(sw, ip_sn)
                for sw in cfg["switch"]
            ]
        return config


# =============================================================================
# Layer: Diff Engine (Validation + Change Computation)
# =============================================================================


class ResourceManagerDiffEngine:
    """Validates playbook config and computes the delta against existing state."""

    @staticmethod
    def validate_configs(config: List[Dict], state: str, module: Any) -> List[Dict]:
        """
        Validate each config entry using ResourceManagerConfigModel.

        For merged/deleted: full validation (required fields + cross-field checks).
        For query: permissive — only entity_name, pool_name, switch accepted.

        Parameters:
            config: List of raw config dicts from the playbook.
            state: Module state (merged | deleted | query).
            module: AnsibleModule instance for fail_json on errors.

        Returns:
            List of validated config dicts (rm_info).
        """
        rm_info = []
        if config is None:
            return rm_info

        for item in config:
            if state == "query":
                rm_info.append(
                    ResourceManagerDiffEngine._validate_query_item(item, module)
                )
            else:
                rm_info.append(
                    ResourceManagerDiffEngine._validate_merge_delete_item(item, module)
                )
        log.debug("validate_configs: rm_info count=%d", len(rm_info))
        return rm_info

    @staticmethod
    def _validate_merge_delete_item(item: Dict, module: Any) -> Dict:
        """Validate one merged/deleted config entry via Pydantic model."""
        for required in ("entity_name", "pool_type", "pool_name", "scope_type"):
            if item.get(required) is None:
                module.fail_json(
                    msg="Mandatory parameter '{0}' missing in config entry: {1}".format(
                        required, item
                    )
                )
        try:
            validated = ResourceManagerConfigModel(**item)
            # model_dump serialises enum values to their string values (use_enum_values=True)
            return validated.model_dump()
        except Exception as exc:
            module.fail_json(msg="Invalid config entry: {0}".format(str(exc)))

    @staticmethod
    def _validate_query_item(item: Dict, module: Any) -> Dict:
        """Validate one query-state config entry (permissive)."""
        allowed = {"entity_name", "pool_name", "switch"}
        unknown = set(item.keys()) - allowed
        if unknown:
            module.fail_json(
                msg="Invalid parameters for query state: {0}. Allowed: {1}".format(
                    sorted(unknown), sorted(allowed)
                )
            )
        return copy.deepcopy(item)

    @staticmethod
    def compute_changes(want: List[Dict], have: List[Dict]) -> Dict[str, List]:
        """
        Compare want vs have and bucket resources into to_create, to_delete,
        and idempotent.

        Parameters:
            want: List of desired resource payloads.
            have: List of existing resource records from ND API.

        Returns:
            dict with keys: to_create (list), to_delete (list of IDs), idempotent (list).
        """
        to_create = []
        idempotent = []

        for res in want:
            status = ResourceManagerDiffEngine._check_idempotent(res, have)
            if status == "ADD":
                to_create.append(res)
            else:
                idempotent.append(res)

        # to_delete: IDs from have that are in want scope
        to_delete = []
        for have_res in have:
            rid = have_res.get("resourceId") or have_res.get("id")
            if rid is not None:
                to_delete.append(int(rid))

        log.debug(
            "compute_changes: to_create=%d to_delete=%d idempotent=%d",
            len(to_create),
            len(to_delete),
            len(idempotent),
        )
        return {
            "to_create": to_create,
            "to_delete": to_delete,
            "idempotent": idempotent,
        }

    @staticmethod
    def _check_idempotent(res: Dict, have: List[Dict]) -> str:
        """Return 'SKIP' if resource already exists with matching value, else 'ADD'."""
        for have_res in have:
            if match_resources(have_res, res):
                have_value = (
                    have_res.get("resourceValue")
                    or have_res.get("allocatedIp")
                    or have_res.get("resource", "")
                )
                if res.get("resource") is not None and have_value is not None:
                    if compare_resource_values(str(have_value), str(res["resource"])):
                        return "SKIP"
                else:
                    return "SKIP"
        return "ADD"


# =============================================================================
# Layer: Resource Operations (API CRUD + Query)
# =============================================================================


class ResourceManagerOps:
    """Performs CRUD and query operations against the ND Manage API."""

    @staticmethod
    def build_want(
        rm_info: List[Dict], ctx: ResourceManagerServiceContext
    ) -> List[Dict]:
        """
        Expand validated rm_info into a flat list of API payload dicts.

        Each entry is expanded per-switch for non-fabric scopes.
        """
        want = []
        for rm_elem in rm_info:
            switches = rm_elem.get("switch") or []
            if switches:
                for sw_serial in switches:
                    payload = build_resource_payload(rm_elem, ctx.fabric, sw_serial)
                    if payload not in want:
                        want.append(payload)
            else:
                payload = build_resource_payload(rm_elem, ctx.fabric, None)
                if payload not in want:
                    want.append(payload)
        ctx.log.debug("build_want: %d payload(s)", len(want))
        return want

    @staticmethod
    def get_existing_resources(
        want: List[Dict], ctx: ResourceManagerServiceContext
    ) -> List[Dict]:
        """
        Query ND for existing resources that correspond to entries in want.

        Caches results keyed by (scopeValue, poolName) to avoid redundant API calls.

        Returns:
            List of matching resource dicts from the ND API.
        """
        cache: Dict[tuple, List[Dict]] = {}
        have = []

        for res in want:
            cache_key = (res["scopeValue"], res["poolName"])

            if cache_key not in cache:
                endpoint = EpManageFabricResourcesGet(fabric_name=ctx.fabric)
                if res["scopeType"] != "Fabric":
                    endpoint.endpoint_params.switch_id = res["scopeValue"]
                endpoint.endpoint_params.pool_name = res["poolName"]

                ctx.log.debug("get_existing_resources: GET %s", endpoint.path)
                response = ctx.nd.request(endpoint.path, method=endpoint.verb.value)
                cache[cache_key] = (
                    ResourceManagerOps._extract_list(response) if response else []
                )

            for relem in cache[cache_key]:
                if match_resources(relem, res) and relem not in have:
                    have.append(relem)

        ctx.log.debug("get_existing_resources: %d existing resource(s)", len(have))
        return have

    @staticmethod
    def create_resources(
        to_create: List[Dict], ctx: ResourceManagerServiceContext
    ) -> None:
        """Create each resource in to_create via POST."""
        for res in to_create:
            endpoint = EpManageFabricResourcesPost(fabric_name=ctx.fabric)
            ctx.log.debug(
                "create_resources: POST %s entityName=%s",
                endpoint.path,
                res.get("entityName"),
            )
            resp = ctx.nd.request(endpoint.path, method=endpoint.verb.value, data=res)
            ctx.result["response"].append(resp)
        if to_create:
            ctx.result["changed"] = True

    @staticmethod
    def delete_resources(
        to_delete: List[int], ctx: ResourceManagerServiceContext
    ) -> None:
        """Bulk-delete resources by ID via POST /actions/remove."""
        if not to_delete:
            return
        endpoint = EpManageFabricResourcesActionsRemovePost(fabric_name=ctx.fabric)
        try:
            request_model = RemoveResourcesByIdsRequest(resourceIds=to_delete)
            payload = request_model.to_payload()
        except Exception as exc:
            ctx.log.error("delete_resources: failed to build payload: %s", exc)
            raise

        ctx.log.debug("delete_resources: POST %s ids=%s", endpoint.path, to_delete)
        resp = ctx.nd.request(endpoint.path, method=endpoint.verb.value, data=payload)
        ctx.result["response"].append(resp)
        ctx.result["changed"] = True

    @staticmethod
    def query_resources(
        rm_info: List[Dict], ctx: ResourceManagerServiceContext
    ) -> List[Dict]:
        """
        Query ND for resources using provided filters.

        Dispatch logic (ported from dcnm_rm_get_diff_query):
          - No rm_info   → GET all resources (no filters)
          - entity_name  → GET all, filter client-side
          - switch       → GET with ?switchId
          - pool_name    → GET with ?poolName
          - switch + pool_name → GET with both params
          - Mixed list   → dispatch each entry independently

        Returns:
            Deduplicated list of matching resource dicts.
        """
        results: List[Dict] = []
        seen_ids: Set = set()

        if not rm_info:
            ctx.log.debug("query_resources: no filters — fetching all resources")
            endpoint = EpManageFabricResourcesGet(fabric_name=ctx.fabric)
            response = ctx.nd.request(endpoint.path, method=endpoint.verb.value)
            return ResourceManagerOps._extract_list(response)

        for res in rm_info:
            filter_entity = res.get("entity_name")
            filter_pool = res.get("pool_name")
            filter_switches = res.get("switch") or []

            if filter_switches:
                for sw_serial in filter_switches:
                    ResourceManagerOps._append_query_results(
                        ctx=ctx,
                        switch_id=sw_serial,
                        pool_name=filter_pool,
                        filter_entity=filter_entity,
                        out=results,
                        seen_ids=seen_ids,
                    )
            else:
                ResourceManagerOps._append_query_results(
                    ctx=ctx,
                    switch_id=None,
                    pool_name=filter_pool,
                    filter_entity=filter_entity,
                    out=results,
                    seen_ids=seen_ids,
                )

        ctx.log.debug("query_resources: %d result(s)", len(results))
        return results

    @staticmethod
    def _append_query_results(
        ctx: ResourceManagerServiceContext,
        switch_id: Optional[str],
        pool_name: Optional[str],
        filter_entity: Optional[str],
        out: List[Dict],
        seen_ids: Set,
    ) -> None:
        """Fetch resources with optional filters and append non-duplicate matches.

        When a switch_id is provided and still looks like an IP address (meaning
        translate_switch_info could not resolve it to a serial number), the API
        call is skipped silently rather than hitting ND with an unknown switchId
        that would return 404 and raise a fatal error.
        """
        if switch_id and ResourceManagerOps._is_ip_address(switch_id):
            ctx.log.warning(
                "_append_query_results: switch '%s' could not be resolved to a "
                "serial number (not found in inventory map); skipping query for "
                "this switch",
                switch_id,
            )
            return

        endpoint = EpManageFabricResourcesGet(fabric_name=ctx.fabric)
        if switch_id:
            endpoint.endpoint_params.switch_id = switch_id
        if pool_name:
            endpoint.endpoint_params.pool_name = pool_name

        ctx.log.debug("_append_query_results: GET %s", endpoint.path)
        response = ctx.nd.request(endpoint.path, method=endpoint.verb.value)
        resources = ResourceManagerOps._extract_list(response)

        for relem in resources:
            rid = relem.get("resourceId") or relem.get("id")
            if rid is not None and rid in seen_ids:
                continue

            if filter_entity is not None:
                have_entity = relem.get("entityName") or relem.get("entity_name", "")
                if not compare_entity_names(have_entity, filter_entity):
                    continue

            out.append(relem)
            if rid is not None:
                seen_ids.add(rid)

    @staticmethod
    def _is_ip_address(value: str) -> bool:
        """Return True if value looks like an IPv4 or IPv6 address (not a serial number)."""
        import ipaddress as _ipaddress

        try:
            _ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _extract_list(response: Any) -> List[Dict]:
        """Normalise any GET response shape into a plain list of dicts."""
        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            for key in ("items", "data", "resources"):
                if key in response:
                    val = response[key]
                    return val if isinstance(val, list) else [val]
        return []


# =============================================================================
# Layer 6: Main Resource Module
# =============================================================================


class NDManageResourceManagerModule:
    """
    Main resource module for nd_manage_resource_manager_updated.

    Orchestrates the full state management lifecycle:
      merged  → translate → validate → want → have → diff → create
      deleted → translate → validate → want → have → diff → delete
      query   → translate → validate (permissive) → query

    Mirrors NDSwitchResourceModule pattern from ansible-nd.
    """

    def __init__(self, nd: Any, fabric: str, log: Any, check_mode: bool):
        """
        Initialise the module, build service context and resolve IP→serial map.

        Parameters:
            nd: NDModule v1 instance.
            fabric: Target fabric name.
            log: Logger instance.
            check_mode: Whether Ansible check_mode is active.
        """
        self.ctx = ResourceManagerServiceContext(
            nd=nd,
            fabric=fabric,
            log=log,
            check_mode=check_mode,
        )
        self.ctx.ip_sn = ResourceManagerInventoryService.build_ip_sn_map(self.ctx)
        log.debug(
            "NDManageResourceManagerModule: initialised fabric=%s check_mode=%s ip_sn_count=%d",
            fabric,
            check_mode,
            len(self.ctx.ip_sn),
        )

    def manage_state(
        self, config: Optional[List[Dict]], state: str, module: Any
    ) -> Dict:
        """
        Orchestrate the full state management lifecycle.

        Parameters:
            config: Playbook config list (may be None for query with no filters).
            state: One of merged | deleted | query.
            module: AnsibleModule instance (for fail_json).

        Returns:
            Result dict: {changed, diff, response}.
        """
        self.ctx.log.debug(
            "manage_state: fabric=%s state=%s config_count=%d",
            self.ctx.fabric,
            state,
            len(config) if config else 0,
        )

        # Translate switch IPs → serials in-place before validation
        if config:
            ResourceManagerInventoryService.translate_switch_info(
                config, self.ctx.ip_sn
            )

        # Validate
        rm_info = ResourceManagerDiffEngine.validate_configs(config, state, module)

        if state == "merged":
            self._handle_merged_state(rm_info, module)
        elif state == "deleted":
            self._handle_deleted_state(rm_info, module)
        elif state == "query":
            self._handle_query_state(rm_info)

        self.ctx.result["diff"] = {
            "merged": self.ctx.result.pop("_diff_create", []),
            "deleted": self.ctx.result.pop("_diff_delete", []),
        }
        return self.ctx.result

    def _handle_merged_state(self, rm_info: List[Dict], module: Any) -> None:
        """Build want/have, compute diff, then create missing resources."""
        want = ResourceManagerOps.build_want(rm_info, self.ctx)
        have = ResourceManagerOps.get_existing_resources(want, self.ctx)
        changes = ResourceManagerDiffEngine.compute_changes(want, have)

        self.ctx.result["_diff_create"] = changes["to_create"]
        self.ctx.result["_diff_delete"] = []

        self.ctx.log.debug(
            "_handle_merged_state: to_create=%d idempotent=%d",
            len(changes["to_create"]),
            len(changes["idempotent"]),
        )

        if self.ctx.check_mode:
            if changes["to_create"]:
                self.ctx.result["changed"] = True
            return

        ResourceManagerOps.create_resources(changes["to_create"], self.ctx)

    def _handle_deleted_state(self, rm_info: List[Dict], module: Any) -> None:
        """Build want/have, then delete matching existing resources."""
        want = ResourceManagerOps.build_want(rm_info, self.ctx)
        have = ResourceManagerOps.get_existing_resources(want, self.ctx)
        changes = ResourceManagerDiffEngine.compute_changes(want, have)

        self.ctx.result["_diff_create"] = []
        self.ctx.result["_diff_delete"] = changes["to_delete"]

        self.ctx.log.debug(
            "_handle_deleted_state: to_delete=%d ids=%s",
            len(changes["to_delete"]),
            changes["to_delete"],
        )

        if self.ctx.check_mode:
            if changes["to_delete"]:
                self.ctx.result["changed"] = True
            return

        ResourceManagerOps.delete_resources(changes["to_delete"], self.ctx)

    def _handle_query_state(self, rm_info: List[Dict]) -> None:
        """Query resources and store results in response."""
        self.ctx.result["_diff_create"] = []
        self.ctx.result["_diff_delete"] = []
        resources = ResourceManagerOps.query_resources(rm_info, self.ctx)
        self.ctx.result["response"] = resources
        self.ctx.log.debug("_handle_query_state: %d resource(s) found", len(resources))

    def exit_json(self, module: Any) -> None:
        """Call module.exit_json with the accumulated result."""
        module.exit_json(**self.ctx.result)
