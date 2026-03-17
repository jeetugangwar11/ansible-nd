# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Payload construction helpers for nd_manage_resource_manager_updated.

Ported from dcnm_resource_manager.py dcnm_rm_get_rm_payload().
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# Ansible/DCNM-style scope type values → ND API camelCase values
SCOPE_TYPE_MAP = {
    "fabric": "Fabric",
    "device": "Device",
    "device_interface": "DeviceInterface",
    "device_pair": "DevicePair",
    "link": "Link",
}


def build_resource_payload(rm_elem, fabric, scope_value):
    """
    Build the ND API payload dict for a single resource allocation.

    Ported from dcnm_resource_manager.py dcnm_rm_get_rm_payload().

    Parameters:
        rm_elem (dict): Validated resource config entry.  Must contain
            pool_name, scope_type, entity_name, and optionally resource.
        fabric (str): Target fabric name (used as scopeValue for fabric scope).
        scope_value (str|None): Switch serial number for non-fabric scopes,
            or None when scope_type is 'fabric' (fabric name used instead).

    Returns:
        dict: Payload compatible with POST /fabrics/{fabric}/resources.
    """
    scope_type = rm_elem["scope_type"]
    return {
        "poolName": rm_elem["pool_name"],
        "scopeType": SCOPE_TYPE_MAP[scope_type],
        "entityName": rm_elem["entity_name"],
        "resource": rm_elem.get("resource"),
        "scopeValue": fabric if scope_type == "fabric" else scope_value,
    }


__all__ = ["SCOPE_TYPE_MAP", "build_resource_payload"]
