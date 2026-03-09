# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.cisco.nd.plugins.module_utils.common.pydantic_compat import BaseModel


class NDBaseModel(BaseModel):
    """Base model for top-level ND API data models."""

    @classmethod
    def from_response(cls, data):
        """Instantiate the model from an API response dict."""
        if hasattr(cls, "model_validate"):
            return cls.model_validate(data)
        return cls(**data)


class NDNestedModel(BaseModel):
    """Base model for nested ND API data models."""

    @classmethod
    def from_response(cls, data):
        """Instantiate the model from an API response dict."""
        if hasattr(cls, "model_validate"):
            return cls.model_validate(data)
        return cls(**data)

    @classmethod
    def from_response(cls, data):
        """Instantiate the model from an API response dict."""
        if hasattr(cls, "model_validate"):
            return cls.model_validate(data)
        return cls(**data)
