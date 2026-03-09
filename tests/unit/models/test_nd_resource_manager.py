# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Unit tests for resource_manager_models.py
"""

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

import pytest

from ansible_collections.cisco.nd.plugins.module_utils.models.base import NDBaseModel, NDNestedModel
from ansible_collections.cisco.nd.plugins.module_utils.pydantic_compat import HAS_PYDANTIC
from ansible_collections.cisco.nd.plugins.module_utils.models.manage_resource_manager_models import (
    AllocateResourcesRequestModel,
    PoolDataModel,
    ProposeVlanResponseModel,
    RemoveResourcesByIdRequestModel,
    ResourceDetailsPostModel,
)
from ansible_collections.cisco.nd.tests.unit.module_utils.common_utils import does_not_raise


class _DummyNested(NDNestedModel):
    name: str


class _DummyBase(NDBaseModel):
    identifiers = ["name"]
    name: str


def test_resource_models_00010():
    with does_not_raise():
        nested = _DummyNested(name="test")
        base = _DummyBase(name="id-1")
    assert nested.to_payload() == {"name": "test"}
    assert base.get_identifier_value() == "id-1"


def test_resource_models_00020():
    payload = {
        "poolName": "L3_VNI",
        "scopeDetails": {
            "scopeType": "fabric",
            "fabricName": "fab1",
        },
        "entityName": "l3_vni_fabric",
        "resourceValue": "101",
        "vrfName": "default",
    }
    with does_not_raise():
        model = ResourceDetailsPostModel.model_validate(payload)
    assert model.to_payload()["scopeDetails"]["scopeType"] == "fabric"


def test_resource_models_00030():
    if not HAS_PYDANTIC:
        pytest.skip("pydantic is not installed in this test environment")
    payload = {
        "poolName": "L3_VNI",
        "entityName": "l3_vni_fabric",
        "resourceValue": "101",
    }
    with pytest.raises(Exception):
        ResourceDetailsPostModel.model_validate(payload)


def test_resource_models_00040():
    request = RemoveResourcesByIdRequestModel.model_validate({"resourceIds": [1, 2, 3]})
    assert request.to_payload() == {"resourceIds": [1, 2, 3]}


def test_resource_models_00050():
    request = AllocateResourcesRequestModel.model_validate(
        {
            "resources": [
                {
                    "poolName": "L3_VNI",
                    "scopeDetails": {
                        "scopeType": "fabric",
                        "fabricName": "fab1",
                    },
                    "entityName": "l3_vni_fabric",
                    "resourceValue": "101",
                }
            ]
        }
    )
    assert request.to_payload()["resources"][0]["scopeDetails"]["scopeType"] == "fabric"


def test_resource_models_00060():
    with does_not_raise():
        model = ProposeVlanResponseModel.from_response({"proposeVlan": 4094})
    assert model.to_payload() == {"proposeVlan": 4094}


def test_resource_models_00070():
    if not HAS_PYDANTIC:
        pytest.skip("pydantic is not installed in this test environment")
    with pytest.raises(Exception):
        PoolDataModel.model_validate({"poolName": "bad", "poolRange": "2600-2300"})
