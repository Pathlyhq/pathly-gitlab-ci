"""Pathly API helpers for GitLab CI/CD components.

Talks to https://api.pathlyhq.com (Bearer sp_…).
Never log the token.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Mapping, MutableMapping, Optional

DEFAULT_API_URL = "https://api.pathlyhq.com"
USER_AGENT = "pathly-gitlab-ci/0.1.0"


class PathlyError(Exception):
    def __init__(self, status: int, path: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.path = path
        self.message = message
        self.details = details

    @property
    def unauthorized(self) -> bool:
        return self.status == 401

    @property
    def forbidden(self) -> bool:
        return self.status == 403

    @property
    def not_found(self) -> bool:
        return self.status == 404


def validate_token(token: str) -> str:
    t = (token or "").strip()
    if not t:
        raise ValueError("Pathly API token is required (Settings → API keys).")
    if not t.startswith("sp_"):
        raise ValueError("A Pathly API token starts with sp_. Check it was not truncated.")
    return t


def normalize_api_url(api_url: str) -> str:
    base = (api_url or DEFAULT_API_URL).rstrip("/")
    if not (
        base.startswith("https://")
        or base.startswith("http://localhost")
        or base.startswith("http://127.0.0.1")
    ):
        raise ValueError("Pathly API URL must use https (localhost http allowed).")
    return base


def _safe_json(text: str) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class PathlyClient:
    def __init__(
        self,
        token: str,
        api_url: str = DEFAULT_API_URL,
        *,
        opener: Any = None,
        idempotency_key: Optional[str] = None,
    ) -> None:
        self.token = validate_token(token)
        self.api_url = normalize_api_url(api_url)
        self._opener = opener
        self._idempotency_key = idempotency_key

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Mapping[str, Any]] = None,
        *,
        idempotent: bool = True,
    ) -> Any:
        url = f"{self.api_url}{path}"
        headers: MutableMapping[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        if method.upper() != "GET" and idempotent:
            headers["Idempotency-Key"] = self._idempotency_key or f"glci-{uuid.uuid4()}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            if self._opener is not None:
                with self._opener.open(req) as resp:
                    raw = resp.read().decode("utf-8")
                    status = getattr(resp, "status", 200)
            else:
                context = ssl.create_default_context()
                with urllib.request.urlopen(req, context=context) as resp:
                    raw = resp.read().decode("utf-8")
                    status = getattr(resp, "status", 200)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            parsed = _safe_json(raw)
            msg = ""
            details = None
            if isinstance(parsed, dict):
                msg = str(parsed.get("error") or "")
                details = parsed.get("details")
            raise PathlyError(
                e.code,
                path,
                msg or raw.strip() or f"HTTP {e.code}",
                details,
            ) from None

        if status >= 400:
            parsed = _safe_json(raw)
            msg = ""
            details = None
            if isinstance(parsed, dict):
                msg = str(parsed.get("error") or "")
                details = parsed.get("details")
            raise PathlyError(status, path, msg or raw.strip() or f"HTTP {status}", details)

        if not raw:
            return {}
        parsed = _safe_json(raw)
        return {} if parsed is None else parsed

    def ping(self) -> dict[str, Any]:
        try:
            data = self._request("GET", "/v1/usage")
            plan = data.get("planId") if isinstance(data, dict) else None
            return {"ok": True, "planId": plan}
        except PathlyError as e:
            if e.forbidden:
                return {"ok": True}
            raise

    def list_scenarios(self, *, limit: int = 100, cursor: Optional[str] = None) -> dict[str, Any]:
        qs = [f"limit={limit}"]
        if cursor:
            qs.append(f"cursor={urllib.parse.quote(cursor)}")
        data = self._request("GET", f"/v1/scenarios?{'&'.join(qs)}")
        items = data.get("items", []) if isinstance(data, dict) else []
        next_cursor = data.get("nextCursor") if isinstance(data, dict) else None
        return {"items": items, "nextCursor": next_cursor}

    def create_scenario(self, body: Mapping[str, Any]) -> dict[str, Any]:
        payload = {"type": "http", "intervalSec": 300, **dict(body)}
        data = self._request("POST", "/v1/scenarios", payload)
        return data if isinstance(data, dict) else {}

    def ensure_scenario(self, body: Mapping[str, Any]) -> dict[str, Any]:
        name = body.get("name")
        if not name:
            raise ValueError('scenario body must include "name"')
        page = self.list_scenarios(limit=200)
        for item in page["items"]:
            if isinstance(item, dict) and item.get("name") == name:
                return {"scenario": item, "created": False}
        created = self.create_scenario(body)
        return {"scenario": created, "created": True}


def client_from_env(
    *,
    token_var: str = "PATHLY_API_TOKEN",
    url_var: str = "PATHLY_API_URL",
) -> PathlyClient:
    token = os.environ.get(token_var, "")
    api_url = os.environ.get(url_var, DEFAULT_API_URL)
    return PathlyClient(token=token, api_url=api_url)
