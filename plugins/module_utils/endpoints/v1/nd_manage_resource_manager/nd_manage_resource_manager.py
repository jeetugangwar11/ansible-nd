# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Allen Robel (@arobel) <arobel@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
ND Manage Resources endpoint models.

This module contains endpoint definitions for resource management operations
in the ND Manage API.
"""

from __future__ import absolute_import, annotations, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type
# pylint: enable=invalid-name

import logging
from typing import Optional

log = logging.getLogger(__name__)

from ansible_collections.cisco.nd.plugins.module_utils.enums import HttpVerbEnum
from ansible_collections.cisco.nd.plugins.module_utils.endpoint.base_paths_manage import (
    BasePath,
)
from ansible_collections.cisco.nd.plugins.module_utils.endpoint.query_params import (
    CompositeQueryParams,
    EndpointQueryParams,
    LuceneQueryParams,
)
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import (
    BaseModel,
    ConfigDict,
    Field,
)

# Common config for basic validation
COMMON_CONFIG = ConfigDict(validate_assignment=True)


# =============================================================================
# QUERY PARAMETER CLASSES
# =============================================================================


class PoolsQueryParams(EndpointQueryParams):
    """
    # Summary

    Endpoint-specific query parameters for pools endpoint.

    ## Parameters

    - pool_id: Optional query parameter to filter based on given pool ID (integer)

    ## Usage

    ```python
    params = PoolsQueryParams(pool_id=21)
    query_string = params.to_query_string()
    # Returns: "poolId=21"
    ```
    """

    pool_id: Optional[int] = Field(
        default=None,
        description="Optional query parameter to filter based on given pool ID",
    )


class ProposeVlanQueryParams(EndpointQueryParams):
    """
    # Summary

    Endpoint-specific query parameters for proposeVlan endpoint.

    ## Parameters

    - vlan_type: The type of VLAN to query (required)
    - tenant_name: Name of the tenant (optional)

    ## Usage

    ```python
    params = ProposeVlanQueryParams(vlan_type="networkVlan")
    query_string = params.to_query_string()
    # Returns: "vlanType=networkVlan"
    ```
    """

    vlan_type: str = Field(
        description="The type of VLAN to query (networkVlan, vrfVlan, serviceNetworkVlan, vpcPeerLinkVlan)"
    )
    tenant_name: Optional[str] = Field(
        default=None, min_length=1, description="Name of the tenant"
    )


class ResourcesQueryParams(EndpointQueryParams):
    """
    # Summary

    Endpoint-specific query parameters for resources endpoint.

    ## Parameters

    - switch_id: Serial Number or Id of the switch/leaf (optional)
    - pool_name: Name of the Pool (optional)
    - tenant_name: Name of the tenant (optional, used for POST)

    ## Usage

    ```python
    params = ResourcesQueryParams(switch_id="leaf-101", pool_name="networkVlan")
    query_string = params.to_query_string()
    # Returns: "switchId=leaf-101&poolName=networkVlan"
    ```
    """

    switch_id: Optional[str] = Field(
        default=None, min_length=1, description="Serial Number or Id of the switch/leaf"
    )
    pool_name: Optional[str] = Field(
        default=None, min_length=1, description="Name of the Pool"
    )
    tenant_name: Optional[str] = Field(
        default=None, min_length=1, description="Name of the tenant"
    )


class UnusedVlansQueryParams(EndpointQueryParams):
    """
    # Summary

    Endpoint-specific query parameters for unusedVlans endpoint.

    ## Parameters

    - vlan_type: The type of VLAN to query (required)
    - switch_id: Serial Number or Id of the switch/leaf (required)
    - tenant_name: Name of the tenant (optional)

    ## Usage

    ```python
    params = UnusedVlansQueryParams(vlan_type="networkVlan", switch_id="leaf-101")
    query_string = params.to_query_string()
    # Returns: "vlanType=networkVlan&switchId=leaf-101"
    ```
    """

    vlan_type: str = Field(
        description="The type of VLAN to query (networkVlan, vrfVlan, serviceNetworkVlan, vpcPeerLinkVlan)"
    )
    switch_id: str = Field(
        min_length=1, description="Serial Number or Id of the switch/leaf"
    )
    tenant_name: Optional[str] = Field(
        default=None, min_length=1, description="Name of the tenant"
    )


# =============================================================================
# POOLS ENDPOINTS
# =============================================================================


class V1ManageGetFabricsPools(BaseModel):
    """
    # Summary

    ND Manage Fabrics Pools GET Endpoint

    ## Description

    Endpoint to retrieve all resource pools configured in the specified fabric.
    Supports both endpoint-specific parameters (pool_id) and Lucene-style
    filtering (filter, max, offset, sort).

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/pools
    - /api/v1/manage/fabrics/{fabricName}/pools?poolId=21
    - /api/v1/manage/fabrics/{fabricName}/pools?filter=poolType:idPool
    - /api/v1/manage/fabrics/{fabricName}/pools?max=10&offset=0&sort=poolName:asc

    ## Verb

    - GET

    ## Usage

    ```python
    # Get all pools in a fabric
    request = V1ManageGetFabricsPools()
    request.fabric_name = "fabric1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/pools

    # Get pools filtered by pool ID
    request = V1ManageGetFabricsPools()
    request.fabric_name = "fabric1"
    request.endpoint_params.pool_id = 21
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/pools?poolId=21

    # Get pools with Lucene filtering
    request = V1ManageGetFabricsPools()
    request.fabric_name = "fabric1"
    request.lucene_params.filter = "poolType:idPool"
    request.lucene_params.max = 10
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/pools?filter=poolType:idPool&max=10
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    endpoint_params: PoolsQueryParams = Field(
        default_factory=PoolsQueryParams,
        description="Endpoint-specific query parameters",
    )
    lucene_params: LuceneQueryParams = Field(
        default_factory=LuceneQueryParams,
        description="Lucene-style filtering query parameters",
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path with optional query string.

        ## Returns

        - Complete endpoint path string, optionally including query parameters
        """
        log.debug(
            "Building path for V1ManageGetFabricsPools: fabric_name=%s, pool_id=%s",
            self.fabric_name,
            self.endpoint_params.pool_id,
        )
        base_path = BasePath.nd_manage("fabrics", self.fabric_name, "pools")

        # Build composite query string
        composite = CompositeQueryParams()
        composite.add(self.endpoint_params)
        composite.add(self.lucene_params)

        query_string = composite.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManageGetFabricsPools: verb=%s",
            HttpVerbEnum.GET,
        )
        return HttpVerbEnum.GET


# =============================================================================
# PROPOSE VLAN ENDPOINTS
# =============================================================================


class V1ManageGetFabricsProposeVlan(BaseModel):
    """
    # Summary

    ND Manage Fabrics Propose VLAN GET Endpoint

    ## Description

    Endpoint to retrieve the next available VLAN ID for the specified VLAN type
    across all switches in the fabric.

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/proposeVlan?vlanType={vlanType}

    ## Verb

    - GET

    ## Usage

    ```python
    # Get next available VLAN ID
    request = V1ManageGetFabricsProposeVlan()
    request.fabric_name = "fabric1"
    request.endpoint_params.vlan_type = "networkVlan"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/proposeVlan?vlanType=networkVlan

    # Get next available VLAN ID with tenant
    request = V1ManageGetFabricsProposeVlan()
    request.fabric_name = "fabric1"
    request.endpoint_params.vlan_type = "networkVlan"
    request.endpoint_params.tenant_name = "tenant1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/proposeVlan?vlanType=networkVlan&tenantName=tenant1
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    endpoint_params: ProposeVlanQueryParams = Field(
        default_factory=ProposeVlanQueryParams,
        description="Endpoint-specific query parameters",
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path with query string.

        ## Returns

        - Complete endpoint path string with query parameters
        """
        log.debug(
            "Building path for V1ManageGetFabricsProposeVlan: fabric_name=%s, vlan_type=%s, tenant_name=%s",
            self.fabric_name,
            self.endpoint_params.vlan_type,
            self.endpoint_params.tenant_name,
        )
        base_path = BasePath.nd_manage("fabrics", self.fabric_name, "proposeVlan")
        query_string = self.endpoint_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManageGetFabricsProposeVlan: verb=%s",
            HttpVerbEnum.GET,
        )
        return HttpVerbEnum.GET


# =============================================================================
# RESOURCES ENDPOINTS
# =============================================================================


class V1ManageGetFabricResources(BaseModel):
    """
    # Summary

    ND Manage Fabrics Resources GET Endpoint

    ## Description

    Endpoint to retrieve all resources for the given fabric.
    Supports both endpoint-specific parameters (switch_id, pool_name) and
    Lucene-style filtering (filter, max, offset, sort).

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/resources
    - /api/v1/manage/fabrics/{fabricName}/resources?switchId=leaf-101
    - /api/v1/manage/fabrics/{fabricName}/resources?poolName=networkVlan
    - /api/v1/manage/fabrics/{fabricName}/resources?filter=isPreAllocated:true
    - /api/v1/manage/fabrics/{fabricName}/resources?max=10&offset=0&sort=poolName:asc

    ## Verb

    - GET

    ## Usage

    ```python
    # Get all resources in a fabric
    request = V1ManageGetFabricResources()
    request.fabric_name = "fabric1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources

    # Get resources filtered by switch
    request = V1ManageGetFabricResources()
    request.fabric_name = "fabric1"
    request.endpoint_params.switch_id = "leaf-101"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources?switchId=leaf-101

    # Get resources with pagination
    request = V1ManageGetFabricResources()
    request.fabric_name = "fabric1"
    request.endpoint_params.pool_name = "networkVlan"
    request.lucene_params.max = 10
    request.lucene_params.offset = 0
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources?poolName=networkVlan&max=10&offset=0
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    endpoint_params: ResourcesQueryParams = Field(
        default_factory=ResourcesQueryParams,
        description="Endpoint-specific query parameters",
    )
    lucene_params: LuceneQueryParams = Field(
        default_factory=LuceneQueryParams,
        description="Lucene-style filtering query parameters",
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path with optional query string.

        ## Returns

        - Complete endpoint path string, optionally including query parameters
        """
        log.debug(
            "Building path for V1ManageGetFabricResources: fabric_name=%s, switch_id=%s, pool_name=%s",
            self.fabric_name,
            self.endpoint_params.switch_id,
            self.endpoint_params.pool_name,
        )
        base_path = BasePath.nd_manage("fabrics", self.fabric_name, "resources")

        # Build composite query string
        composite = CompositeQueryParams()
        composite.add(self.endpoint_params)
        composite.add(self.lucene_params)

        query_string = composite.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManageGetFabricResources: verb=%s",
            HttpVerbEnum.GET,
        )
        return HttpVerbEnum.GET


class V1ManagePostFabricResources(BaseModel):
    """
    # Summary

    ND Manage Fabrics Resources POST Endpoint

    ## Description

    Endpoint to allocate an ID or IP/Subnet resource from the specified pool.
    If a specific resource value is provided in the request, that exact value
    will be allocated. Otherwise, the next available resource will be
    automatically allocated.

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/resources
    - /api/v1/manage/fabrics/{fabricName}/resources?tenantName=tenant1

    ## Verb

    - POST

    ## Usage

    ```python
    # Allocate resource
    request = V1ManagePostFabricResources()
    request.fabric_name = "fabric1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources

    # Allocate resource with tenant
    request = V1ManagePostFabricResources()
    request.fabric_name = "fabric1"
    request.endpoint_params.tenant_name = "tenant1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources?tenantName=tenant1
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    endpoint_params: ResourcesQueryParams = Field(
        default_factory=ResourcesQueryParams,
        description="Endpoint-specific query parameters",
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path with optional query string.

        ## Returns

        - Complete endpoint path string, optionally including query parameters
        """
        log.debug(
            "Building path for V1ManagePostFabricResources: fabric_name=%s, tenant_name=%s",
            self.fabric_name,
            self.endpoint_params.tenant_name,
        )
        base_path = BasePath.nd_manage("fabrics", self.fabric_name, "resources")
        query_string = self.endpoint_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManagePostFabricResources: verb=%s",
            HttpVerbEnum.POST,
        )
        return HttpVerbEnum.POST


# =============================================================================
# RESOURCES ACTIONS ENDPOINTS
# =============================================================================


class V1ManagePostFabricResourcesActionsRemove(BaseModel):
    """
    # Summary

    ND Manage Fabrics Resources Actions Remove POST Endpoint

    ## Description

    Endpoint to release allocated resource IDs from the fabric, returning them
    to the available resource pool.

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/resources/actions/remove

    ## Verb

    - POST

    ## Usage

    ```python
    # Release resource IDs
    request = V1ManagePostFabricResourcesActionsRemove()
    request.fabric_name = "fabric1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources/actions/remove
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path.

        ## Returns

        - Complete endpoint path string
        """
        log.debug(
            "Building path for V1ManagePostFabricResourcesActionsRemove: fabric_name=%s",
            self.fabric_name,
        )
        return BasePath.nd_manage(
            "fabrics", self.fabric_name, "resources", "actions", "remove"
        )

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManagePostFabricResourcesActionsRemove: verb=%s",
            HttpVerbEnum.POST,
        )
        return HttpVerbEnum.POST


class V1ManagePostFabricResourcesActionsRemoveResource(BaseModel):
    """
    # Summary

    ND Manage Fabrics Resources Actions RemoveResource POST Endpoint

    ## Description

    Endpoint to identify and release a resource allocation based on provided
    allocation context instead of resource ID.

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/resources/actions/removeResource

    ## Verb

    - POST

    ## Usage

    ```python
    # Release resource by allocation details
    request = V1ManagePostFabricResourcesActionsRemoveResource()
    request.fabric_name = "fabric1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources/actions/removeResource
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path.

        ## Returns

        - Complete endpoint path string
        """
        log.debug(
            "Building path for V1ManagePostFabricResourcesActionsRemoveResource: fabric_name=%s",
            self.fabric_name,
        )
        return BasePath.nd_manage(
            "fabrics", self.fabric_name, "resources", "actions", "removeResource"
        )

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManagePostFabricResourcesActionsRemoveResource: verb=%s",
            HttpVerbEnum.POST,
        )
        return HttpVerbEnum.POST


# =============================================================================
# GET RESOURCE BY ID ENDPOINTS
# =============================================================================


class V1ManageGetFabricResourceById(BaseModel):
    """
    # Summary

    ND Manage Fabrics Resource By ID GET Endpoint

    ## Description

    Endpoint to retrieve allocation details for the specified
    resource ID in the fabric.

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/resources/{resourceId}

    ## Verb

    - GET

    ## Usage

    ```python
    # Get resource by ID
    request = V1ManageGetFabricResourceById()
    request.fabric_name = "fabric1"
    request.resource_id = 100
    request.http_verb = HttpVerbEnum.GET
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/resources/100

    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    resource_id: int = Field(description="Unique identifier of the resource")
    http_verb: HttpVerbEnum = Field(
        default=HttpVerbEnum.GET, description="HTTP verb for this request"
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path.

        ## Returns

        - Complete endpoint path string
        """
        log.debug(
            "Building path for V1ManageGetFabricResourceById: fabric_name=%s, resource_id=%s",
            self.fabric_name,
            self.resource_id,
        )
        return BasePath.nd_manage(
            "fabrics", self.fabric_name, "resources", str(self.resource_id)
        )

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManageGetFabricResourceById: verb=%s",
            self.http_verb,
        )
        return self.http_verb


# =============================================================================
# DELETE RESOURCE BY ID ENDPOINTS
# =============================================================================


class V1ManageDeleteFabricResourceById(BaseModel):
    """
     # Summary

     ND Manage Fabrics Resource By ID DELETE Endpoint

     ## Description

     Endpoint to delete allocation details for the specified
     resource ID in the fabric.

     ## Path

     - /api/v1/manage/fabrics/{fabricName}/resources/{resourceId}

     ## Verb

     - DELETE

     ## Usage

     ```python

    # Delete resource by ID
     request = V1ManageDeleteFabricResourceById()
     request.fabric_name = "fabric1"
     request.resource_id = 100
     request.http_verb = HttpVerbEnum.DELETE
     path = request.path
     verb = request.verb
     # Path will be: /api/v1/manage/fabrics/fabric1/resources/100
     ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    resource_id: int = Field(description="Unique identifier of the resource")
    http_verb: HttpVerbEnum = Field(
        default=HttpVerbEnum.DELETE, description="HTTP verb for this request"
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path.

        ## Returns

        - Complete endpoint path string
        """
        log.debug(
            "Building path for V1ManageDeleteFabricResourceById: fabric_name=%s, resource_id=%s",
            self.fabric_name,
            self.resource_id,
        )
        return BasePath.nd_manage(
            "fabrics", self.fabric_name, "resources", str(self.resource_id)
        )

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManageDeleteFabricResourceById: verb=%s",
            self.http_verb,
        )
        return self.http_verb


# =============================================================================
# UNUSED VLANS ENDPOINTS
# =============================================================================


class V1ManageGetFabricUnusedVlans(BaseModel):
    """
    # Summary

    ND Manage Fabrics Unused VLANs GET Endpoint

    ## Description

    Endpoint to retrieve all available VLAN IDs from the dynamic and global
    VLAN ranges in the specified fabric.

    ## Path

    - /api/v1/manage/fabrics/{fabricName}/unusedVlans?vlanType={vlanType}&switchId={switchId}

    ## Verb

    - GET

    ## Usage

    ```python
    # Get unused VLANs
    request = V1ManageGetFabricUnusedVlans()
    request.fabric_name = "fabric1"
    request.endpoint_params.vlan_type = "networkVlan"
    request.endpoint_params.switch_id = "leaf-101"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/unusedVlans?vlanType=networkVlan&switchId=leaf-101

    # Get unused VLANs with tenant
    request = V1ManageGetFabricUnusedVlans()
    request.fabric_name = "fabric1"
    request.endpoint_params.vlan_type = "networkVlan"
    request.endpoint_params.switch_id = "leaf-101"
    request.endpoint_params.tenant_name = "tenant1"
    path = request.path
    verb = request.verb
    # Path will be: /api/v1/manage/fabrics/fabric1/unusedVlans?vlanType=networkVlan&switchId=leaf-101&tenantName=tenant1
    ```
    """

    model_config = COMMON_CONFIG

    fabric_name: str = Field(
        min_length=1, max_length=64, description="Name of the fabric"
    )
    endpoint_params: UnusedVlansQueryParams = Field(
        default_factory=UnusedVlansQueryParams,
        description="Endpoint-specific query parameters",
    )

    @property
    def path(self) -> str:
        """
        # Summary

        Build the endpoint path with query string.

        ## Returns

        - Complete endpoint path string with query parameters
        """
        log.debug(
            "Building path for V1ManageGetFabricUnusedVlans: fabric_name=%s, vlan_type=%s, switch_id=%s, tenant_name=%s",
            self.fabric_name,
            self.endpoint_params.vlan_type,
            self.endpoint_params.switch_id,
            self.endpoint_params.tenant_name,
        )
        base_path = BasePath.nd_manage("fabrics", self.fabric_name, "unusedVlans")
        query_string = self.endpoint_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> HttpVerbEnum:
        """Return the HTTP verb for this endpoint."""
        log.debug(
            "Returning HTTP verb for V1ManageGetFabricUnusedVlans: verb=%s",
            HttpVerbEnum.GET,
        )
        return HttpVerbEnum.GET
