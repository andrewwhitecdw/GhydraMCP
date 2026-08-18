"""Regression tests for instance discovery exception handling."""

from unittest.mock import MagicMock, patch

from ghydra.cli.instances import _discover_instances_on_host
from ghydra.client.exceptions import GhidraAPIError, GhidraConnectionError


def test_discover_skips_connection_errors():
    """Connection failures during port scanning should be skipped, not crash."""
    mock_client = MagicMock()
    mock_client.get.side_effect = GhidraConnectionError("connection refused")

    with patch("ghydra.cli.instances.GhidraHTTPClient") as mock_client_cls:
        mock_client_cls.return_value = mock_client
        result = _discover_instances_on_host("localhost", [8192], None)

    assert result == {"success": True, "instances": []}


def test_discover_handles_program_info_errors():
    """If plugin responds but program info fails, discovery should still report the instance."""
    mock_client = MagicMock()

    def get(endpoint):
        if endpoint == "plugin-version":
            return {"success": True, "result": {"plugin_version": "1.0", "api_version": "1.0"}}
        if endpoint == "program":
            raise GhidraAPIError("program info unavailable")
        raise RuntimeError("unexpected endpoint")

    mock_client.get.side_effect = get

    with patch("ghydra.cli.instances.GhidraHTTPClient") as mock_client_cls:
        mock_client_cls.return_value = mock_client
        result = _discover_instances_on_host("localhost", [8192], None)

    assert len(result["instances"]) == 1
    instance = result["instances"][0]
    assert instance["project"] == "-"
    assert instance["file"] == "-"
    assert instance["plugin_version"] == "1.0"
