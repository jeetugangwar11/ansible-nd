# -*- coding: utf-8 -*-

"""Unit tests for the Nexus Dashboard HTTPAPI plugin."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from unittest.mock import Mock

import pytest
from ansible_collections.cisco.nd.plugins.httpapi.nd import HttpApi


def _http_api():
    connection = Mock()
    connection._auth = None
    connection._url = "https://nd.example.com"
    return HttpApi(connection)


def _response(status_code, message="Multi-Status"):
    response = Mock()
    response.getcode.return_value = status_code
    response.geturl.return_value = "/api/v1/manage/test"
    response.msg = message
    response.headers = {}
    response.info.return_value = {}
    return response


def _response_data(body):
    data = Mock()
    data.getvalue.return_value = json.dumps(body).encode("utf-8")
    return data


@pytest.mark.parametrize(
    "body",
    [
        {"results": [{"status": "success"}, {"status": "failed"}]},
        {"resources": [{"status": "FAILURE"}]},
        {"nested": {"items": [{"details": {"status": "Error"}}]}},
    ],
)
def test_has_partial_failure_detects_nested_failure_statuses(body):
    original = copy.deepcopy(body)

    assert HttpApi._has_partial_failure(body) is True
    assert body == original


@pytest.mark.parametrize(
    "body",
    [
        {"results": [{"status": "success"}, {"status": "warning"}]},
        {"results": [{"status": None}, {}, "invalid", 1]},
        {"statusCode": "failure", "request_status": "failed"},
        {"results": []},
        None,
        "failure",
    ],
)
def test_has_partial_failure_ignores_non_failure_shapes(body):
    assert HttpApi._has_partial_failure(body) is False


def test_verify_response_marks_mixed_207_as_error():
    http_api = _http_api()
    body = {"results": [{"name": "one", "status": "success"}, {"name": "two", "status": "failure"}]}

    result = http_api._verify_response(_response(207), "POST", "/requested", _response_data(body))

    assert result["error"] == {"code": 207, "message": body}
    assert result["body"] == body
    assert result["DATA"] == body
    assert result["RETURN_CODE"] == 207
    assert result["METHOD"] == "POST"
    assert result["REQUEST_PATH"] == "/api/v1/manage/test"


@pytest.mark.parametrize(
    "body",
    [
        {"results": [{"status": "success"}, {"status": "warning"}]},
        {"results": []},
        {"results": "malformed"},
        {},
    ],
)
def test_verify_response_allows_207_without_failure(body):
    result = _http_api()._verify_response(_response(207), "POST", "/requested", _response_data(body))

    assert "error" not in result
    assert result["body"] == body


def test_verify_response_does_not_inspect_non_207_success():
    body = {"results": [{"status": "failure"}]}

    result = _http_api()._verify_response(_response(200, "OK"), "POST", "/requested", _response_data(body))

    assert "error" not in result


def test_verify_response_preserves_non_success_handling():
    http_api = _http_api()
    body = {"message": "request failed"}

    result = http_api._verify_response(_response(400, "Bad Request"), "POST", "/requested", _response_data(body))

    assert result["error"] == {"code": 400, "message": body}
    assert result["MESSAGE"] == "Bad Request"