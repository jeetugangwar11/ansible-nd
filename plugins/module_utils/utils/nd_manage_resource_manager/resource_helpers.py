# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Comparison helpers for nd_manage_resource_manager_updated.

Ported from dcnm_resource_manager.py:
  - compare_entity_names  ← dcnm_rm_compare_entity_names
  - compare_resource_values ← dcnm_rm_compare_resource_values
  - match_resources         ← dcnm_rm_match_resources
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ipaddress


def compare_entity_names(e1, e2):
    """
    Compare two entity names in a tilde-order-insensitive manner.

    DCNM/ND may reverse the order of serial numbers in an entity name
    (e.g. 'A~B~label' vs 'B~A~label').  Sorting the tilde-split parts
    before comparing handles both orderings.

    Parameters:
        e1 (str): First entity name.
        e2 (str): Second entity name.

    Returns:
        bool: True if the entity names are equivalent.
    """
    return sorted(e1.split("~")) == sorted(e2.split("~"))


def compare_resource_values(r1, r2):
    """
    Compare two resource values handling IPv4, IPv6, CIDR, and integer forms.

    Ported from dcnm_resource_manager.py dcnm_rm_compare_resource_values().

    Parameters:
        r1 (str): First resource value.
        r2 (str): Second resource value.

    Returns:
        bool: True if the resource values are equivalent.
    """
    r1, r2 = str(r1), str(r2)

    # IPv4 comparison
    if "." in r1 and "." in r2:
        try:
            if "/" in r1 and "/" in r2:
                return str(ipaddress.ip_network(r1, strict=False)) == str(
                    ipaddress.ip_network(r2, strict=False)
                )
            if "/" not in r1 and "/" not in r2:
                return (
                    ipaddress.IPv4Address(r1).exploded
                    == ipaddress.IPv4Address(r2).exploded
                )
        except ValueError:
            pass

    # IPv6 comparison
    if ":" in r1 and ":" in r2:
        try:
            if "/" in r1 and "/" in r2:
                return str(ipaddress.ip_network(r1, strict=False)) == str(
                    ipaddress.ip_network(r2, strict=False)
                )
            if "/" not in r1 and "/" not in r2:
                return (
                    ipaddress.IPv6Address(r1).exploded
                    == ipaddress.IPv6Address(r2).exploded
                )
        except ValueError:
            pass

    # Fall back to string equality (covers integer ID pools)
    return r1 == r2


def match_resources(have_res, want_res):
    """
    Determine whether an existing ND resource record (have_res) matches
    the desired payload (want_res).

    Normalises ND response field names (camelCase vs snake_case variants)
    before comparing on: entityName, scopeType, poolName, and scopeValue.

    Ported from dcnm_resource_manager.py dcnm_rm_match_resources().

    Parameters:
        have_res (dict): Resource dict returned by the ND API.
        want_res (dict): Payload dict from the want list.

    Returns:
        bool: True if the two records refer to the same allocation.
    """
    # Normalise ND response field names
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

    if not compare_entity_names(have_entity, want_res["entityName"]):
        return False
    if have_scope_type != want_res["scopeType"]:
        return False
    if have_pool != want_res["poolName"]:
        return False

    if want_res["scopeType"] == "Fabric":
        # For fabric scope validate fabric name when available
        if have_fabric and have_fabric != want_res.get("_fabric", have_fabric):
            return False
    else:
        # ND may store allocatedScopeValue as first tilde-segment of entityName
        first_part = have_entity.split("~")[0] if "~" in have_entity else ""
        if have_scope_val != want_res["scopeValue"] and have_scope_val != first_part:
            return False

    return True


__all__ = ["compare_entity_names", "compare_resource_values", "match_resources"]
