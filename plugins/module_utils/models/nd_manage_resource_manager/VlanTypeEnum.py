# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Shared enums for the nd_manage_resource_manager model package.

Imported by constants.py and ProposeVlanQueryModel.py.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from enum import Enum


class VlanType(str, Enum):
    """
    VLAN type enumeration for the proposeVlan and unusedVlans endpoints.

    Valid values:
      networkVlan         - Network VLAN
      vrfVlan             - VRF VLAN
      serviceNetworkVlan  - Service network VLAN
      vpcPeerLinkVlan     - VPC peer-link VLAN
    """

    NETWORK_VLAN = "networkVlan"
    VRF_VLAN = "vrfVlan"
    SERVICE_NETWORK_VLAN = "serviceNetworkVlan"
    VPC_PEER_LINK_VLAN = "vpcPeerLinkVlan"

    @classmethod
    def choices(cls):
        """Return list of valid string values."""
        return [e.value for e in cls]


__all__ = ["VlanType"]
