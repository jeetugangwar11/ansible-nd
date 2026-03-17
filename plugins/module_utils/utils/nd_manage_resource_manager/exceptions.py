# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco Systems
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Custom exceptions for nd_manage_resource_manager_updated operations."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ResourceManagerError(Exception):
    """Raised when a resource manager operation fails."""

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


__all__ = ["ResourceManagerError"]
