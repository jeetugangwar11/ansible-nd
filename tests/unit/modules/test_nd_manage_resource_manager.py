# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Unit tests for nd_resource_manager.py
"""

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

from types import SimpleNamespace

import pytest

from ansible_collections.cisco.nd.plugins.module_utils.enums import HttpVerbEnum
import ansible_collections.cisco.nd.plugins.modules.nd_manage_resource_manager as nd_resource_manager


class FakeAnsibleModule:
    def __init__(self, params, check_mode=False):
        self.params = params
        self.check_mode = check_mode
        self._debug = False


class FakeNDModule:
    calls = []

    def __init__(self, module):
        self.module = module
        self.rest_send = SimpleNamespace(response_current={}, result_current={})

    def request(self, path, verb=HttpVerbEnum.GET, data=None):
        self.__class__.calls.append({"path": path, "verb": verb, "data": data})
        response = {
            "RETURN_CODE": 200,
            "MESSAGE": "OK",
            "REQUEST_PATH": path,
            "METHOD": verb.value,
            "DATA": {},
        }
        result = {"success": True, "found": True, "changed": verb != HttpVerbEnum.GET}

        if "proposeVlan" in path:
            response["DATA"] = {"proposeVlan": 3333}
            result = {"success": True, "found": True}
        elif "/resources" in path and verb == HttpVerbEnum.GET:
            response["DATA"] = {"resources": []}
            result = {"success": True, "found": True}
        elif "/pools" in path and verb == HttpVerbEnum.GET:
            response["DATA"] = {"pools": [], "meta": {}}
            result = {"success": True, "found": True}
        elif "/inventory/switches" in path and verb == HttpVerbEnum.GET:
            response["DATA"] = {
                "switches": [
                    {
                        "switchId": "SAL1234",
                        "hostname": "leaf1",
                        "fabricManagementIp": "10.1.1.1",
                    }
                ]
            }
            result = {"success": True, "found": True}

        self.rest_send.response_current = response
        self.rest_send.result_current = result
        return response["DATA"]


class FakeNDModuleNotFound(FakeNDModule):
    def request(self, path, verb=HttpVerbEnum.GET, data=None):
        if path.endswith("/resources/999") and verb == HttpVerbEnum.GET:
            self.__class__.calls.append({"path": path, "verb": verb, "data": data})
            self.rest_send.response_current = {
                "RETURN_CODE": 404,
                "MESSAGE": "Not Found",
                "REQUEST_PATH": path,
                "METHOD": verb.value,
                "DATA": {},
            }
            self.rest_send.result_current = {"success": False, "found": False, "changed": False}
            raise nd_resource_manager.NDModuleError(msg="Not Found", status=404, response_payload={})
        return super().request(path, verb=verb, data=data)


def _build_task(monkeypatch, params, check_mode=False):
    monkeypatch.setattr(nd_resource_manager, "NDModule", FakeNDModule)
    FakeNDModule.calls = []
    module = FakeAnsibleModule(params=params, check_mode=check_mode)
    return nd_resource_manager.NdResourceManagerTask(module)


def test_nd_resource_manager_00010(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "query",
            "query_target": "resources",
            "tenant_name": None,
            "config": None,
        },
    )
    assert task._compare_entity_names("A~B~C", "C~B~A") is True


def test_nd_resource_manager_00020(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "query",
            "query_target": "resources",
            "tenant_name": None,
            "config": None,
        },
    )
    assert task._compare_resource_values("10.1.1.1", "10.1.1.1") is True
    assert task._compare_resource_values("10.1.1.1/24", "10.1.1.0/24") is True


def test_nd_resource_manager_00030(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "query",
            "query_target": "resources",
            "tenant_name": None,
            "config": None,
        },
    )
    assert task._to_scope_snake("deviceInterface") == "device_interface"
    assert task._to_scope_snake("device_pair") == "device_pair"


def test_nd_resource_manager_00040(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "query",
            "query_target": "resources",
            "tenant_name": None,
            "config": None,
        },
    )
    with pytest.raises(ValueError):
        task._to_scope_snake("bad_scope")


def test_nd_resource_manager_00050(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "merged",
            "query_target": "resources",
            "tenant_name": None,
            "config": [
                {
                    "entity_name": "SERIAL~Ethernet1/1",
                    "pool_type": "IP",
                    "pool_name": "LOOPBACK1_IP_POOL",
                    "scope_type": "device_interface",
                    "switch": ["leaf1"],
                    "resource": "10.1.1.1",
                }
            ],
        },
    )

    task._translate_switch_info(task.config)
    rm_info = task._build_rm_info_from_config(task.config)
    payloads = task._build_payloads_from_config(rm_info[0])
    assert payloads[0]["scopeDetails"]["switchId"] == "SAL1234"
    assert payloads[0]["scopeDetails"]["interfaceName"] == "Ethernet1/1"


def test_nd_resource_manager_00060(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "query",
            "query_target": "propose_vlan",
            "tenant_name": None,
            "config": [{"vlan_type": "networkVlan"}],
        },
    )

    task.commit()
    final = task.build_final_result()

    assert final["failed"] is False
    assert final["changed"] is False
    assert final["current"]["proposeVlan"] == 3333


def test_nd_resource_manager_00070(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "deleted",
            "query_target": "resources",
            "tenant_name": None,
            "config": [{"resource_ids": [10, 11]}],
        },
    )

    # Should pass validation for explicit selectors without requiring dcnm fields.
    task._validate_inputs()


def test_nd_resource_manager_00080(monkeypatch):
    task = _build_task(
        monkeypatch,
        {
            "fabric": "fab1",
            "state": "merged",
            "query_target": "resources",
            "tenant_name": None,
            "config": [
                {
                    "entity_name": "l3_vni_fabric",
                    "pool_type": "ID",
                    "pool_name": "L3_VNI",
                    "scope_type": "fabric",
                    "resource": "101",
                }
            ],
        },
        check_mode=True,
    )

    task.commit()
    final = task.build_final_result()

    assert final["changed"] is False
    merged_diffs = [entry for entry in final["diff"] if "merged" in entry]
    assert merged_diffs[0]["merged"][0]["poolName"] == "L3_VNI"
    assert all(call["verb"] == HttpVerbEnum.GET for call in FakeNDModule.calls)


def test_nd_resource_manager_00090(monkeypatch):
    monkeypatch.setattr(nd_resource_manager, "NDModule", FakeNDModuleNotFound)
    FakeNDModuleNotFound.calls = []

    module = FakeAnsibleModule(
        params={
            "fabric": "fab1",
            "state": "deleted",
            "query_target": "resources",
            "tenant_name": None,
            "config": [{"resource_id": 999}],
        },
        check_mode=False,
    )

    task = nd_resource_manager.NdResourceManagerTask(module)
    task.commit()
    final = task.build_final_result()

    assert final["failed"] is False
    assert task.current["deleted_by_id"] == []
