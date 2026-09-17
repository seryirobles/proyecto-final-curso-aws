"""Dev-only entry point: runs the `api` Lambda as a local HTTP server (stdlib
only, `uv run python -m planner_api.local_server`). Mirrors what API Gateway
does in production - invoke the authorizer, then the handler - by hand, so
`handler.py` and `routing.py` stay untouched (docs/rest_api_contract.md
section 8.1)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from planner_api import authorizer, handler
from planner_api.adapters.dynamo._table import create_data_table
from planner_api.routing import ROUTES
from planner_api.wiring import Dependencies

logger = logging.getLogger("planner_api.local_server")

_DEFAULT_PORT = 8080


@dataclass(frozen=True)
class MatchedRoute:
    resource: str
    path_params: dict[str, str]


def match_resource(path: str) -> MatchedRoute | None:
    """Real API Gateway resolves `resource`/`pathParameters` from its own
    configuration; locally there is none, so this matches the incoming path
    against every `resource` template `routing.ROUTES` declares. Matching is
    exact, like API Gateway's: a trailing or doubled slash produces an empty
    segment and must not match the canonical path."""
    if not path.startswith("/"):
        return None
    segments = path[1:].split("/")
    if "" in segments:
        return None
    for _method, template in ROUTES:
        template_segments = [s for s in template.split("/") if s]
        if len(template_segments) != len(segments):
            continue
        params: dict[str, str] = {}
        for t_seg, p_seg in zip(template_segments, segments, strict=True):
            if t_seg.startswith("{") and t_seg.endswith("}"):
                params[t_seg[1:-1]] = p_seg
            elif t_seg != p_seg:
                break
        else:
            return MatchedRoute(template, params)
    return None


def _header(headers: dict[str, str], name: str) -> str | None:
    """Case-insensitive lookup - `http.server` preserves whatever case the
    client sent, unlike a real API Gateway proxy event's normalized dict."""
    folded = name.casefold()
    return next((v for k, v in headers.items() if k.casefold() == folded), None)


def _normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Re-key to standard HTTP Title-Case so handler.py's exact-case lookups
    (e.g. `If-None-Match`) find a header regardless of the case the client
    sent it in - unlike a real API Gateway proxy event, `http.server` hands
    us the client's raw casing verbatim."""
    return {"-".join(p.capitalize() for p in k.split("-")): v for k, v in headers.items()}


def handle_request(
    method: str,
    raw_target: str,
    headers: dict[str, str],
    body: bytes | None,
    deps: Dependencies | None = None,
) -> dict[str, Any]:
    """The full per-request translation, orchestration and back-translation -
    plain in, plain out, so it needs no socket to test (T2, T13)."""
    headers = _normalize_headers(headers)
    split = urlsplit(raw_target)
    matched = match_resource(split.path)
    resource = matched.resource if matched is not None else split.path
    path_params = matched.path_params if matched is not None else {}
    query = dict(parse_qsl(split.query))
    spec = ROUTES.get((method, resource))

    authorizer_context: dict[str, Any] = {}
    if spec is None or not spec.public:
        authorizer_event = {
            "methodArn": f"arn:local:execute-api:local::local/dev/{method}{resource}",
            "headers": {"Cookie": _header(headers, "Cookie") or ""},
        }
        policy = authorizer.handle(authorizer_event, deps)
        if policy["policyDocument"]["Statement"][0]["Effect"] != "Allow":
            return {"statusCode": 403, "headers": {}, "body": ""}
        authorizer_context = policy["context"]

    event = {
        "httpMethod": method,
        "resource": resource,
        "pathParameters": path_params or None,
        "queryStringParameters": query or None,
        "headers": headers,
        "body": None if body is None else body.decode("utf-8"),
        "requestContext": {"authorizer": authorizer_context},
    }
    return handler.handle(event, deps)


class _RequestHandler(BaseHTTPRequestHandler):
    def _dispatch(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw_body = self.rfile.read(length) if length else None
            response = handle_request(self.command, self.path, dict(self.headers.items()), raw_body)
        except ValueError:
            # Malformed Content-Length or a body that isn't valid UTF-8 - the
            # client's fault; reply instead of letting the thread crash silently.
            response = {"statusCode": 400, "headers": {}, "body": ""}
        except Exception:
            logger.exception("Unhandled error dispatching %s %s", self.command, self.path)
            response = {"statusCode": 500, "headers": {}, "body": ""}
        self._reply(response)

    def _reply(self, response: dict[str, Any]) -> None:
        self.send_response(int(response["statusCode"]))
        body = response.get("body") or ""
        encoded = body.encode("utf-8")
        for key, value in (response.get("headers") or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        self._dispatch()

    do_POST = do_PUT = do_PATCH = do_DELETE = do_GET

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - stdlib signature
        logger.info(format, *args)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("LOCAL_SERVER_PORT", _DEFAULT_PORT))
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL")
    if endpoint:
        try:
            create_data_table()  # convenience for a fresh DynamoDB Local container
        except Exception:
            # create_data_table() already swallows the one expected case
            # (table exists) internally, so anything reaching here is a real
            # connectivity problem - fail loudly instead of serving a broken backend.
            logger.exception("Could not reach DynamoDB at %s - is it running?", endpoint)
            raise SystemExit(1) from None
    server = ThreadingHTTPServer(("", port), _RequestHandler)
    logger.info("planner_api local server listening on port %s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
