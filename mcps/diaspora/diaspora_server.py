"""FastMCP server exposing Diaspora Event Fabric via diaspora-event-sdk."""

import functools
import logging
import os
import uuid
from typing import Any, Callable, Optional

import globus_sdk
from diaspora_event_sdk import Client as DiasporaClient
from diaspora_event_sdk import KafkaConsumer, KafkaProducer
from diaspora_event_sdk.sdk.login_manager import DiasporaScopes, LoginManager
from fastmcp import FastMCP
from globus_sdk.scopes import AuthScopes

log = logging.getLogger(__name__)
CLIENT_ID = os.getenv("GLOBUS_CLIENT_ID", "ee05bbfa-2a1a-4659-95df-ed8946e3aae6")

mcp = FastMCP("Diaspora Octopus Bridge")

# Globals – initialised lazily after auth
_auth_client: Optional[globus_sdk.NativeAppAuthClient] = None
_login_mgr: Optional[LoginManager] = None
_diaspora: Optional[DiasporaClient] = None
_producer: Optional[KafkaProducer] = None
_is_logged_in: bool = False  # set True by complete_diaspora_auth
_have_rotated_key: bool = False  # set True by create_key

# Helper builders


def _get_login_mgr() -> LoginManager:
    global _login_mgr
    if _login_mgr is None:
        _login_mgr = LoginManager()
    return _login_mgr


def _get_diaspora() -> DiasporaClient:
    global _diaspora
    if _diaspora is None:
        _get_login_mgr().ensure_logged_in()
        _diaspora = DiasporaClient(login_manager=_login_mgr)
    return _diaspora


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer()
    return _producer


def require_login(func: Callable[..., Any]) -> Callable[..., Any]:
    """Ensure the caller has completed the Globus login flow."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not _is_logged_in:  # ← reuse your module-level flag
            raise RuntimeError(
                "Please authenticate first via diaspora_authenticate / complete_diaspora_auth"
            )
        return func(*args, **kwargs)

    return wrapper


def require_rotated_key(func: Callable[..., Any]) -> Callable[..., Any]:
    """Ensure the caller has run create_key() at least once."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not _have_rotated_key:
            raise RuntimeError(
                "Call create_key once before producing/consuming messages"
            )
        return func(*args, **kwargs)

    return wrapper


# Globus Native-App login flow tools


@mcp.tool
def diaspora_authenticate() -> str:
    """Start the Globus Native App flow and return the authorize URL."""
    global _auth_client

    if not CLIENT_ID.lower():
        return "❌ Please set the GLOBUS_CLIENT_ID environment variable."

    _auth_client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    _auth_client.oauth2_start_flow(
        requested_scopes=[DiasporaScopes.all, AuthScopes.openid],
        refresh_tokens=True,
    )
    url = _auth_client.oauth2_get_authorize_url()
    return (
        "🔗 **Authorization URL**\n\n"
        "Visit the link, approve access, then call `complete_diaspora_auth(<code>)` with the returned code.\n\n "
        f"{url}"
    )


@mcp.tool
def complete_diaspora_auth(code: str) -> str:
    """Exchange the authorization *code* for tokens and cache them."""
    global _auth_client, _login_mgr, _diaspora, _is_logged_in

    if _auth_client is None:
        return "❌ You must call diaspora_authenticate first."

    try:
        tokens = _auth_client.oauth2_exchange_code_for_tokens(code.strip())
    except Exception as exc:
        log.error("Token exchange failed", exc_info=True)
        return f"❌ Token exchange failed: {exc}"

    _get_login_mgr()._token_storage.store(tokens)
    _auth_client = None
    _diaspora = None  # force rebuild
    _is_logged_in = True
    return "✅ Login successful! You can now use Diaspora tools."


@mcp.tool
def logout() -> str:
    """Revoke tokens and clear cached clients."""
    global _diaspora, _login_mgr, _is_logged_in, _have_rotated_key
    _is_logged_in = False
    _have_rotated_key = False

    if _login_mgr and _login_mgr.logout():
        _diaspora = None
        return "🚪 Logged out and tokens revoked."
    return "ℹ️ No active tokens found."


# Control‑plane tools


@mcp.tool
@require_login
def create_key() -> str:
    global _have_rotated_key
    result = _get_diaspora().create_key()
    _have_rotated_key = True
    return result


@mcp.tool
@require_login
def list_topics() -> list[str]:
    return _get_diaspora().list_topics()


@mcp.tool
@require_login
def register_topic(topic: str) -> str:
    return _get_diaspora().register_topic(topic)


@mcp.tool
@require_login
def unregister_topic(topic: str) -> str:
    return _get_diaspora().unregister_topic(topic)


# Data‑plane tools


@mcp.tool
@require_login
@require_rotated_key
def produce_event(
    topic: str,
    value: str,
    key: str | None = None,
    headers: dict[str, str] | None = None,
    sync: bool = True,
) -> str:
    producer = _get_producer()
    future = producer.send(topic, value=value, key=key, headers=headers)
    if sync:
        md = future.get(timeout=10)
        return f"partition={md.partition}, offset={md.offset}"
    return "queued"


@mcp.tool
@require_login
@require_rotated_key
def consume_latest_event(
    topic: str,
    timeout_s: int = 5,
) -> dict[str, Any] | None:
    consumer = KafkaConsumer(
        topic,
        group_id=f"peek-{uuid.uuid4()}",
        enable_auto_commit=False,
        auto_offset_reset="latest",
        consumer_timeout_ms=timeout_s * 1000,
    )

    while not consumer.assignment():
        consumer.poll(100)

    for tp in consumer.assignment():
        end = consumer.end_offsets([tp])[tp]
        if end:
            consumer.seek(tp, end - 1)

    recs = consumer.poll(timeout_s * 1000)
    newest = None
    for msgs in recs.values():
        for msg in msgs:
            m = {
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "key": msg.key.decode() if isinstance(msg.key, bytes) else msg.key,
                "value": msg.value.decode()
                if isinstance(msg.value, bytes)
                else msg.value,
                "timestamp": msg.timestamp,
            }
            if newest is None or m["timestamp"] > newest["timestamp"]:
                newest = m
    consumer.close()
    return newest


# Entrypoint

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http", host="0.0.0.0", port=8000, path="/mcps/diaspora"
    )
