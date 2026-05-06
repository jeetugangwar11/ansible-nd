# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Akshayanat C S (@achengam) <achengam@cisco.com>

# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Models for manage switches operations."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from .switch_data_models import SwitchDataModel
from .enums import (
    SwitchRole,
    SystemMode,
    PlatformType,
    SnmpV3AuthProtocol,
    DiscoveryStatus,
    ConfigSyncStatus,
    VpcRole,
    RemoteCredentialStore,
    AnomalyLevel,
    AdvisoryLevel,
)

__all__ = [
    "SwitchDataModel",
    "SwitchRole",
    "SystemMode",
    "PlatformType",
    "SnmpV3AuthProtocol",
    "DiscoveryStatus",
    "ConfigSyncStatus",
    "VpcRole",
    "RemoteCredentialStore",
    "AnomalyLevel",
    "AdvisoryLevel",
]
