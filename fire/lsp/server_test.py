#!/usr/bin/env python3
"""End-to-end test: run the server over pipes and exchange JSON-RPC."""

import json
import os
import threading
from typing import Any, BinaryIO

import pytest

from fire.lsp.server import create_server

_BAD_SIL = "## REQ-1\n\nSIL: ASIL-Z | Sec: false | Version: 1\n"


class _Client:
    def __init__(self) -> None:
        server_in, self._to_server = os.pipe()
        self._from_server, server_out = os.pipe()
        self._writer: BinaryIO = os.fdopen(self._to_server, "wb")
        self._reader: BinaryIO = os.fdopen(self._from_server, "rb")
        server = create_server()
        self._thread = threading.Thread(
            target=server.start_io,
            args=(os.fdopen(server_in, "rb"), os.fdopen(server_out, "wb")),
            daemon=True,
        )
        self._thread.start()

    def send(self, message: dict[str, Any]) -> None:
        body = json.dumps({"jsonrpc": "2.0", **message}).encode()
        self._writer.write(b"Content-Length: %d\r\n\r\n%s" % (len(body), body))
        self._writer.flush()

    def receive(self) -> dict[str, Any]:
        length = 0
        while line := self._reader.readline().strip():
            if line.lower().startswith(b"content-length"):
                length = int(line.split(b":")[1])
        return json.loads(self._reader.read(length))

    def receive_until(self, predicate) -> dict[str, Any]:
        while not predicate(message := self.receive()):
            pass
        return message


def _initialize(client: _Client) -> dict[str, Any]:
    client.send({"id": 1, "method": "initialize", "params": {"capabilities": {}}})
    response = client.receive_until(lambda m: m.get("id") == 1)
    client.send({"method": "initialized", "params": {}})
    return response


def _open(client: _Client, uri: str, text: str) -> None:
    item = {"uri": uri, "languageId": "markdown", "version": 1, "text": text}
    client.send({"method": "textDocument/didOpen", "params": {"textDocument": item}})


def _is_publish(message: dict[str, Any]) -> bool:
    return message.get("method") == "textDocument/publishDiagnostics"


def _diagnostics(client: _Client) -> dict[str, Any]:
    return client.receive_until(_is_publish)["params"]


@pytest.fixture
def client() -> _Client:
    return _Client()


class TestServer:
    def test_initialize_reports_server_info(self, client):
        response = _initialize(client)
        assert response["result"]["serverInfo"]["name"] == "fire-ls"

    def test_did_open_publishes_diagnostics(self, client):
        _initialize(client)
        uri = "file:///repo/a.sysreq.md"
        _open(client, uri, _BAD_SIL)
        params = _diagnostics(client)
        assert params["uri"] == uri
        assert [d["code"] for d in params["diagnostics"]] == ["FIRE005"]

    def test_did_change_republishes_diagnostics(self, client):
        _initialize(client)
        uri = "file:///repo/a.sysreq.md"
        _open(client, uri, _BAD_SIL)
        _diagnostics(client)
        change = {"text": "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n"}
        client.send(
            {
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": uri, "version": 2},
                    "contentChanges": [change],
                },
            }
        )
        assert _diagnostics(client)["diagnostics"] == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
