#!/usr/bin/env python3
"""End-to-end test: run the server over pipes and exchange JSON-RPC."""

import json
import os
import queue
import threading
from collections.abc import Iterator
from typing import Any, BinaryIO

import pytest

from fire.lsp.server import create_server

_TIMEOUT_SECONDS = 5
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
        self._messages: queue.Queue[dict[str, Any]] = queue.Queue()
        threading.Thread(target=self._read_loop, daemon=True).start()

    def close(self) -> None:
        self._writer.close()

    def send(self, message: dict[str, Any]) -> None:
        body = json.dumps({"jsonrpc": "2.0", **message}).encode()
        self._writer.write(b"Content-Length: %d\r\n\r\n%s" % (len(body), body))
        self._writer.flush()

    def _read_loop(self) -> None:
        while True:
            length = 0
            while line := self._reader.readline().strip():
                if line.lower().startswith(b"content-length"):
                    length = int(line.split(b":")[1])
            if not length:
                return
            self._messages.put(json.loads(self._reader.read(length)))

    def receive(self, timeout: float = _TIMEOUT_SECONDS) -> dict[str, Any]:
        try:
            return self._messages.get(timeout=timeout)
        except queue.Empty:
            raise AssertionError(f"no message from server within {timeout}s") from None

    def receive_until(self, predicate) -> dict[str, Any]:
        while not predicate(message := self.receive()):
            pass
        return message


def _initialize(client: _Client) -> dict[str, Any]:
    client.send({"id": 1, "method": "initialize", "params": {"capabilities": {}}})
    response = client.receive_until(lambda m: m.get("id") == 1)
    client.send({"method": "initialized", "params": {}})
    return response


def _open(client: _Client, uri: str, text: str, language: str = "markdown") -> None:
    item = {"uri": uri, "languageId": language, "version": 1, "text": text}
    client.send({"method": "textDocument/didOpen", "params": {"textDocument": item}})


def _is_publish(message: dict[str, Any]) -> bool:
    return message.get("method") == "textDocument/publishDiagnostics"


def _diagnostics(client: _Client) -> dict[str, Any]:
    return client.receive_until(_is_publish)["params"]


def _diagnostics_for(client: _Client, uri: str) -> list[str]:
    def is_for(message: dict[str, Any]) -> bool:
        return _is_publish(message) and message["params"]["uri"] == uri

    params = client.receive_until(is_for)["params"]
    return [d["code"] for d in params["diagnostics"]]


@pytest.fixture
def client() -> Iterator[_Client]:
    client = _Client()
    yield client
    client.close()


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


_LINKING = (
    "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n\n[@x](/p.yaml?version=1#x)\n"
)
_PARAMS = "x_v1:\n  value: 1\n  unit: m\n  description: d\n"


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "MODULE.bazel").write_text("")
    return tmp_path


def _open_linking_document(client: _Client, workspace) -> str:
    _initialize(client)
    uri = (workspace / "a.sysreq.md").as_uri()
    _open(client, uri, _LINKING)
    assert _diagnostics_for(client, uri) == ["FIRE012"]
    return uri


class TestRefresh:
    def test_unsaved_target_buffer_satisfies_a_link(self, client, workspace):
        uri = _open_linking_document(client, workspace)
        _open(client, (workspace / "p.yaml").as_uri(), _PARAMS)
        assert _diagnostics_for(client, uri) == []

    def test_closing_the_target_buffer_falls_back_to_disk(self, client, workspace):
        uri = _open_linking_document(client, workspace)
        target = {"uri": (workspace / "p.yaml").as_uri()}
        _open(client, target["uri"], _PARAMS)
        assert _diagnostics_for(client, uri) == []
        client.send(
            {"method": "textDocument/didClose", "params": {"textDocument": target}}
        )
        assert _diagnostics_for(client, uri) == ["FIRE012"]

    def test_watched_file_change_refreshes_open_documents(self, client, workspace):
        uri = _open_linking_document(client, workspace)
        target = workspace / "p.yaml"
        target.write_text(_PARAMS)
        change = {"uri": target.as_uri(), "type": 1}
        client.send(
            {
                "method": "workspace/didChangeWatchedFiles",
                "params": {"changes": [change]},
            }
        )
        assert _diagnostics_for(client, uri) == []

    def test_watching_is_registered_when_the_client_supports_it(self, client):
        capabilities = {
            "workspace": {"didChangeWatchedFiles": {"dynamicRegistration": True}}
        }
        client.send(
            {"id": 1, "method": "initialize", "params": {"capabilities": capabilities}}
        )
        client.receive_until(lambda m: m.get("id") == 1)
        client.send({"method": "initialized", "params": {}})
        request = client.receive_until(
            lambda m: m.get("method") == "client/registerCapability"
        )
        registration = request["params"]["registrations"][0]
        assert registration["method"] == "workspace/didChangeWatchedFiles"
        assert registration["registerOptions"]["watchers"]
        client.send({"id": request["id"], "result": None})

    def test_no_registration_without_client_support(self, client):
        _initialize(client)
        client.send({"id": 7, "method": "shutdown"})
        message = client.receive_until(
            lambda m: m.get("id") == 7 or m.get("method") == "client/registerCapability"
        )
        assert message.get("method") is None


def _definition(client: _Client, uri: str, line: int, character: int):
    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": character},
    }
    client.send({"id": 99, "method": "textDocument/definition", "params": params})
    return client.receive_until(lambda m: m.get("id") == 99)["result"]


class TestDefinition:
    def test_link_jumps_to_the_parameter_on_disk(self, client, workspace):
        (workspace / "p.yaml").write_text("y_v1:\n  value: 0\n" + _PARAMS)
        uri = _open_linking_document_without_target(client, workspace)
        result = _definition(client, uri, 4, 3)
        assert result["uri"] == (workspace / "p.yaml").as_uri()
        assert result["range"]["start"] == {"line": 2, "character": 0}

    def test_link_jumps_into_an_unsaved_buffer(self, client, workspace):
        uri = _open_linking_document(client, workspace)
        target = (workspace / "p.yaml").as_uri()
        _open(client, target, "\n\n\n" + _PARAMS)
        assert _diagnostics_for(client, uri) == []
        result = _definition(client, uri, 4, 3)
        assert result["uri"] == target
        assert result["range"]["start"]["line"] == 3

    def test_no_definition_off_a_link(self, client, workspace):
        uri = _open_linking_document(client, workspace)
        assert _definition(client, uri, 0, 1) is None


def _open_linking_document_without_target(client: _Client, workspace) -> str:
    _initialize(client)
    uri = (workspace / "a.sysreq.md").as_uri()
    _open(client, uri, _LINKING)
    return uri


class TestDocumentSymbols:
    def test_outline_of_a_requirement_document(self, client):
        _initialize(client)
        uri = "file:///repo/a.sysreq.md"
        _open(client, uri, "## REQ-A\n\nVersion: 1\n\n## REQ-B\n\nVersion: 2\n")
        client.send(
            {
                "id": 50,
                "method": "textDocument/documentSymbol",
                "params": {"textDocument": {"uri": uri}},
            }
        )
        result = client.receive_until(lambda m: m.get("id") == 50)["result"]
        assert [s["name"] for s in result] == ["REQ-A", "REQ-B"]


def _workspace_symbols(client: _Client, query: str) -> list[dict[str, Any]]:
    client.send({"id": 60, "method": "workspace/symbol", "params": {"query": query}})
    return client.receive_until(lambda m: m.get("id") == 60)["result"]


def _initialize_with_folder(client: _Client, folder) -> None:
    params = {
        "capabilities": {},
        "workspaceFolders": [{"uri": folder.as_uri(), "name": "ws"}],
    }
    client.send({"id": 1, "method": "initialize", "params": params})
    client.receive_until(lambda m: m.get("id") == 1)
    client.send({"method": "initialized", "params": {}})


class TestWorkspaceSymbols:
    def test_search_across_the_workspace_folder(self, client, workspace):
        (workspace / "a.sysreq.md").write_text("## REQ-FIND-ME\n\n## REQ-OTHER\n")
        _initialize_with_folder(client, workspace)
        result = _workspace_symbols(client, "find")
        assert [s["name"] for s in result] == ["REQ-FIND-ME"]
        assert result[0]["location"]["uri"] == (workspace / "a.sysreq.md").as_uri()
        assert result[0]["containerName"] == "a.sysreq.md"

    def test_unsaved_documents_are_included(self, client, workspace):
        _initialize_with_folder(client, workspace)
        _open(client, (workspace / "new.sysreq.md").as_uri(), "## REQ-UNSAVED\n")
        assert [s["name"] for s in _workspace_symbols(client, "unsaved")] == [
            "REQ-UNSAVED"
        ]

    def test_files_changed_on_disk_are_picked_up(self, client, workspace):
        _initialize_with_folder(client, workspace)
        assert _workspace_symbols(client, "late") == []
        (workspace / "late.sysreq.md").write_text("## REQ-LATE\n")
        assert [s["name"] for s in _workspace_symbols(client, "late")] == ["REQ-LATE"]

    def test_without_a_workspace_the_result_is_empty(self, client):
        _initialize(client)
        assert _workspace_symbols(client, "x") == []


def _references(
    client: _Client, uri: str, line: int, character: int, declaration=False
):
    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": character},
        "context": {"includeDeclaration": declaration},
    }
    client.send({"id": 70, "method": "textDocument/references", "params": params})
    return client.receive_until(lambda m: m.get("id") == 70)["result"]


_TARGET = "## REQ-A\n\nSIL: QM | Sec: false | Version: 3\n"
_LINK = "[REQ-A](/reqs.sysreq.md?version=3#REQ-A)\n"


class TestReferences:
    def _setup(self, client, workspace):
        (workspace / "reqs.sysreq.md").write_text(_TARGET)
        (workspace / "other.sysreq.md").write_text("See " + _LINK)
        _initialize_with_folder(client, workspace)
        uri = (workspace / "reqs.sysreq.md").as_uri()
        _open(client, uri, _TARGET)
        return uri

    def test_references_from_a_heading(self, client, workspace):
        uri = self._setup(client, workspace)
        result = _references(client, uri, 0, 5)
        assert [r["uri"] for r in result] == [(workspace / "other.sysreq.md").as_uri()]
        assert result[0]["range"]["start"] == {"line": 0, "character": 4}

    def test_declaration_is_included_on_request(self, client, workspace):
        uri = self._setup(client, workspace)
        result = _references(client, uri, 0, 5, declaration=True)
        assert [r["uri"] for r in result][0] == uri
        assert len(result) == 2

    def test_unsaved_buffer_adds_a_reference(self, client, workspace):
        uri = self._setup(client, workspace)
        _open(client, (workspace / "draft.sysreq.md").as_uri(), _LINK)
        uris = {r["uri"] for r in _references(client, uri, 0, 5)}
        assert (workspace / "draft.sysreq.md").as_uri() in uris

    def test_no_references_off_a_symbol(self, client, workspace):
        uri = self._setup(client, workspace)
        assert _references(client, uri, 2, 1) == []


_PARAMS_OK = "max_speed_v1:\n  value: 30.0\n  unit: m/s\n  description: Maximum speed\n"
_PARAMS_NO_UNIT = "max_speed_v1:\n  value: 30.0\n  description: Maximum speed\n"


def _change(client: _Client, uri: str, version: int, text: str) -> None:
    client.send(
        {
            "method": "textDocument/didChange",
            "params": {
                "textDocument": {"uri": uri, "version": version},
                "contentChanges": [{"text": text}],
            },
        }
    )


class TestParameterFiles:
    def test_removing_the_unit_shows_a_diagnostic_and_adding_it_clears_it(self, client):
        _initialize(client)
        uri = "file:///repo/params.yaml"
        _open(client, uri, _PARAMS_OK, "yaml")
        _change(client, uri, 2, _PARAMS_NO_UNIT)
        assert _diagnostics_for(client, uri) == ["FIRE018"]
        _change(client, uri, 3, _PARAMS_OK)
        assert _diagnostics_for(client, uri) == []

    def test_other_yaml_files_get_no_diagnostics(self, client):
        _initialize(client)
        yaml_uri = "file:///repo/ci.yaml"
        _open(client, yaml_uri, "name: ci\non: push\n", "yaml")
        doc_uri = "file:///repo/a.sysreq.md"
        _open(client, doc_uri, _BAD_SIL)
        assert _diagnostics_for(client, doc_uri) == ["FIRE005"]


def _complete(client: _Client, uri: str, line: int, character: int):
    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": character},
    }
    client.send({"id": 80, "method": "textDocument/completion", "params": params})
    return client.receive_until(lambda m: m.get("id") == 80)["result"]


class TestCompletion:
    def test_server_announces_trigger_characters(self, client):
        response = _initialize(client)
        options = response["result"]["capabilities"]["completionProvider"]
        assert ":" in options["triggerCharacters"]

    def test_metadata_keys_and_values(self, client):
        _initialize(client)
        keys_uri, values_uri = "file:///repo/a.sysreq.md", "file:///repo/b.sysreq.md"
        _open(client, keys_uri, "## R-1\n\nSIL: QM | \n")
        _open(client, values_uri, "## R-1\n\nSIL: \n")
        keys = _complete(client, keys_uri, 2, 10)
        assert [i["label"] for i in keys["items"]] == ["Sec", "Version", "Parent"]
        values = _complete(client, values_uri, 2, 5)
        assert values["items"][0]["label"] == "ASIL-A"

    def test_no_completions_outside_metadata(self, client):
        _initialize(client)
        uri = "file:///repo/a.sysreq.md"
        _open(client, uri, "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\nText\n")
        assert _complete(client, uri, 4, 4)["items"] == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
