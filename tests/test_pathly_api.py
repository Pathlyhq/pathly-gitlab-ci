"""Tests for Pathly GitLab CI API helper — 100% coverage target."""

from __future__ import annotations

import io
import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pathly_api import (
    DEFAULT_API_URL,
    PathlyClient,
    PathlyError,
    client_from_env,
    normalize_api_url,
    validate_token,
)
from pathly_cli import build_parser, main


class FakeResponse:
    def __init__(self, body: Any = None, status: int = 200, raw: str | None = None) -> None:
        if raw is not None:
            self._raw = raw.encode("utf-8")
        elif body is None:
            self._raw = b""
        else:
            self._raw = json.dumps(body).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class FakeOpener:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[Any] = []

    def open(self, req: Any) -> FakeResponse:
        self.requests.append(req)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_validate_token() -> None:
    assert validate_token(" sp_abc ") == "sp_abc"
    with pytest.raises(ValueError, match="required"):
        validate_token("  ")
    with pytest.raises(ValueError, match="sp_"):
        validate_token("ghp_x")


def test_normalize_api_url() -> None:
    assert normalize_api_url("https://api.pathlyhq.com/") == "https://api.pathlyhq.com"
    assert normalize_api_url("") == DEFAULT_API_URL
    assert normalize_api_url("http://localhost:8084").startswith("http://localhost")
    assert normalize_api_url("http://127.0.0.1:9") == "http://127.0.0.1:9"
    with pytest.raises(ValueError, match="https"):
        normalize_api_url("http://evil.example")


def test_pathly_error_flags() -> None:
    assert PathlyError(401, "/", "x").unauthorized
    assert PathlyError(403, "/", "x").forbidden
    assert PathlyError(404, "/", "x").not_found
    assert not PathlyError(500, "/", "x").unauthorized


def test_ping_ok() -> None:
    opener = FakeOpener([FakeResponse({"planId": "pro"})])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    assert client.ping() == {"ok": True, "planId": "pro"}
    assert "/v1/usage" in opener.requests[0].full_url


def test_ping_forbidden_ok() -> None:
    import urllib.error

    err = urllib.error.HTTPError(
        "https://api.test/v1/usage",
        403,
        "Forbidden",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b'{"error":"missing org:read"}'),
    )
    opener = FakeOpener([err])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    assert client.ping() == {"ok": True}


def test_ping_unauthorized() -> None:
    import urllib.error

    err = urllib.error.HTTPError(
        "https://api.test/v1/usage",
        401,
        "Unauthorized",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b'{"error":"bad"}'),
    )
    opener = FakeOpener([err])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.ping()
    assert ei.value.status == 401
    assert ei.value.message == "bad"


def test_list_and_create_scenario() -> None:
    opener = FakeOpener(
        [
            FakeResponse({"items": [], "nextCursor": None}),
            FakeResponse({"id": "sc-1", "name": "Home"}, status=201),
        ]
    )
    client = PathlyClient("sp_tok", "https://api.test", opener=opener, idempotency_key="k1")
    page = client.list_scenarios(limit=10, cursor="abc/def")
    assert page["items"] == []
    assert "cursor=" in opener.requests[0].full_url
    created = client.create_scenario({"name": "Home", "url": "https://e.com"})
    assert created["id"] == "sc-1"
    hdrs = {k.lower(): v for k, v in opener.requests[1].header_items()}
    assert hdrs.get("idempotency-key") == "k1"


def test_ensure_skips_non_dict_items() -> None:
    opener = FakeOpener(
        [
            FakeResponse({"items": ["skip-me", {"id": "1", "name": "Other"}]}),
            FakeResponse({"id": "2", "name": "Home"}, status=201),
        ]
    )
    client = PathlyClient("sp_tok", "https://api.test", opener=opener, idempotency_key="k")
    r = client.ensure_scenario({"name": "Home", "url": "https://e.com"})
    assert r["created"] is True
    assert r["scenario"]["id"] == "2"

    opener = FakeOpener([FakeResponse({"items": [{"id": "1", "name": "Home"}]})])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    r = client.ensure_scenario({"name": "Home", "url": "https://e.com"})
    assert r["created"] is False
    assert r["scenario"]["id"] == "1"

    opener2 = FakeOpener(
        [
            FakeResponse({"items": []}),
            FakeResponse({"id": "2", "name": "Home"}, status=201),
        ]
    )
    client2 = PathlyClient("sp_tok", "https://api.test", opener=opener2, idempotency_key="x")
    r2 = client2.ensure_scenario({"name": "Home", "url": "https://e.com"})
    assert r2["created"] is True

    with pytest.raises(ValueError, match="name"):
        client2.ensure_scenario({"url": "https://e.com"})


def test_http_error_plain_and_empty() -> None:
    import urllib.error

    err = urllib.error.HTTPError(
        "https://api.test/v1/scenarios",
        500,
        "ERR",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b"boom"),
    )
    opener = FakeOpener([err])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.list_scenarios()
    assert ei.value.message == "boom"

    err2 = urllib.error.HTTPError(
        "https://api.test/v1/scenarios",
        502,
        "ERR",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b""),
    )
    opener2 = FakeOpener([err2])
    client2 = PathlyClient("sp_tok", "https://api.test", opener=opener2)
    with pytest.raises(PathlyError) as ei2:
        client2.list_scenarios()
    assert "502" in ei2.value.message


def test_status_ge_400_via_opener() -> None:
    opener = FakeOpener([FakeResponse({"error": "nope"}, status=400)])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.list_scenarios()
    assert ei.value.status == 400
    assert ei.value.message == "nope"


def test_empty_and_invalid_json_success() -> None:
    opener = FakeOpener([FakeResponse(raw=""), FakeResponse(raw="not-json")])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener, idempotency_key="i")
    assert client.create_scenario({"name": "A", "url": "https://e.com"}) == {}
    # second call returns invalid json → {}
    assert client.create_scenario({"name": "B", "url": "https://e.com"}) == {}


def test_list_non_dict_response() -> None:
    opener = FakeOpener([FakeResponse(raw="[]")])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    assert client.list_scenarios() == {"items": [], "nextCursor": None}


def test_create_non_dict_response() -> None:
    opener = FakeOpener([FakeResponse(raw="[]")])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener, idempotency_key="z")
    assert client.create_scenario({"name": "A", "url": "https://e.com"}) == {}


def test_default_idempotency_and_urlopen_path() -> None:
    fake = FakeResponse({"planId": "solo"})
    with patch("pathly_api.urllib.request.urlopen", return_value=fake) as mocked:
        with patch("pathly_api.ssl.create_default_context", return_value=MagicMock()):
            client = PathlyClient("sp_tok", "https://api.test")
            assert client.ping()["ok"] is True
            mocked.assert_called_once()


def test_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATHLY_API_TOKEN", "sp_env")
    monkeypatch.setenv("PATHLY_API_URL", "https://api.env.test")
    c = client_from_env()
    assert c.token == "sp_env"
    assert c.api_url == "https://api.env.test"


def test_status_400_empty_body() -> None:
    opener = FakeOpener([FakeResponse(raw="", status=418)])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.list_scenarios()
    assert "418" in ei.value.message


def test_status_400_non_dict_json() -> None:
    opener = FakeOpener([FakeResponse(raw='["x"]', status=400)])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.list_scenarios()
    assert ei.value.status == 400


def test_cli_ping(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PATHLY_API_TOKEN", "sp_cli")
    opener = FakeOpener([FakeResponse({"planId": "pro"})])

    def fake_client(**kwargs: Any) -> PathlyClient:
        return PathlyClient("sp_cli", "https://api.test", opener=opener)

    with patch("pathly_cli.client_from_env", side_effect=fake_client):
        assert main(["ping"]) == 0
    out = capsys.readouterr().out
    assert '"ok": true' in out.replace("True", "true") or '"ok": true' in out.lower() or "ok" in out


def test_cli_ensure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PATHLY_API_TOKEN", "sp_cli")
    opener = FakeOpener(
        [
            FakeResponse({"items": []}),
            FakeResponse({"id": "sc", "name": "Home"}, status=201),
        ]
    )

    def fake_client(**kwargs: Any) -> PathlyClient:
        return PathlyClient("sp_cli", "https://api.test", opener=opener, idempotency_key="k")

    with patch("pathly_cli.client_from_env", side_effect=fake_client):
        code = main(
            [
                "ensure-scenario",
                "--scenario-json",
                json.dumps({"name": "Home", "url": "https://e.com"}),
            ]
        )
    assert code == 0
    assert "sc" in capsys.readouterr().out


def test_cli_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATHLY_API_TOKEN", "sp_cli")

    def boom(**kwargs: Any) -> PathlyClient:
        raise PathlyError(401, "/", "nope")

    with patch("pathly_cli.client_from_env", side_effect=boom):
        assert main(["ping"]) == 1

    with patch("pathly_cli.client_from_env", side_effect=lambda **k: PathlyClient("sp_x", "https://a.test")):
        assert main(["ensure-scenario", "--scenario-json", "{bad"]) == 1


def test_cli_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PATHLY_API_TOKEN", raising=False)
    opener = FakeOpener([FakeResponse({"planId": "x"})])

    captured: dict[str, str] = {}

    def fake_from_env(**kwargs: Any) -> PathlyClient:
        captured["token"] = os.environ.get("PATHLY_API_TOKEN", "")
        captured["url"] = os.environ.get("PATHLY_API_URL", "")
        return PathlyClient(captured["token"], captured["url"], opener=opener)

    with patch("pathly_cli.client_from_env", side_effect=fake_from_env):
        assert main(["ping", "--api-token", "sp_ovr", "--api-url", "https://api.ovr"]) == 0
    assert captured["token"] == "sp_ovr"
    assert captured["url"] == "https://api.ovr"


def test_cli_ensure_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATHLY_API_TOKEN", "sp_cli")
    opener = FakeOpener([])

    with patch(
        "pathly_cli.client_from_env",
        return_value=PathlyClient("sp_cli", "https://api.test", opener=opener),
    ):
        with pytest.raises(SystemExit):
            main(["ensure-scenario", "--scenario-json", json.dumps({"name": "only"})])


def test_build_parser() -> None:
    p = build_parser()
    ns = p.parse_args(["ping"])
    assert ns.command == "ping"


def test_ping_non_dict_usage() -> None:
    opener = FakeOpener([FakeResponse(raw="[]")])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    assert client.ping() == {"ok": True, "planId": None}


def test_http_error_with_details() -> None:
    import urllib.error

    err = urllib.error.HTTPError(
        "https://api.test/v1/scenarios",
        400,
        "Bad",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b'{"error":"invalid","details":{"url":"bad"}}'),
    )
    opener = FakeOpener([err])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.list_scenarios()
    assert ei.value.details == {"url": "bad"}


def test_status_ge_400_with_details_via_opener() -> None:
    opener = FakeOpener([FakeResponse({"error": "x", "details": [1]}, status=422)])
    client = PathlyClient("sp_tok", "https://api.test", opener=opener)
    with pytest.raises(PathlyError) as ei:
        client.list_scenarios()
    assert ei.value.details == [1]
