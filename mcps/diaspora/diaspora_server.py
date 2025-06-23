"""FastMCP server exposing Diaspora Event Fabric via diaspora-event-sdk."""

import functools
import logging
import os
import sys
from time import time
from typing import Any, Callable, Optional

import globus_sdk
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
from diaspora_event_sdk import Client as DiasporaClient
from diaspora_event_sdk.sdk.login_manager import DiasporaScopes, LoginManager
from fastmcp import FastMCP
from globus_sdk import ConfidentialAppAuthClient
from globus_sdk.scopes import AuthScopes
from kafka import KafkaConsumer, KafkaProducer
from kafka.sasl.oauth import AbstractTokenProvider

# Required environment variables for AWS Lightsail and local testing
# Note: AWS Lightsail does not support IAM role assumption; using access keys allows local testing and deployment on Lightsail.
# Note: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY may be set/overridden by the AWS Lightsail deployment library; so I prefix them with Diaspora
REQUIRED_ENV_VARS = [
    "DIASPORA_AWS_ACCESS_KEY_ID",
    "DIASPORA_AWS_SECRET_ACCESS_KEY",
    "DIASPORA_AWS_DEFAULT_REGION",
]
missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    log = logging.getLogger(__name__)
    log.error(f"Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

os.environ["AWS_ACCESS_KEY_ID"] = os.environ["DIASPORA_AWS_ACCESS_KEY_ID"]
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["DIASPORA_AWS_SECRET_ACCESS_KEY"]
os.environ["AWS_DEFAULT_REGION"] = os.environ["DIASPORA_AWS_DEFAULT_REGION"]


log = logging.getLogger(__name__)
CLIENT_ID = os.getenv("GLOBUS_CLIENT_ID", "ee05bbfa-2a1a-4659-95df-ed8946e3aae6")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "423623835312")
OCTOPUS_BOOTSTRAP_SERVERS = os.getenv(
    "OCTOPUS_BOOTSTRAP_SERVERS",
    (
        "b-1-public.diaspora.jdqn8o.c18.kafka.us-east-1.amazonaws.com:9198,"
        "b-2-public.diaspora.jdqn8o.c18.kafka.us-east-1.amazonaws.com:9198"
    ),
)

# Warn if optional environment variables are not set and defaults are used
if "GLOBUS_CLIENT_ID" not in os.environ:
    log.warning(f"GLOBUS_CLIENT_ID not set; using default CLIENT_ID {CLIENT_ID}.")
if "AWS_ACCOUNT_ID" not in os.environ:
    log.warning(
        f"AWS_ACCOUNT_ID not set; using default AWS_ACCOUNT_ID {AWS_ACCOUNT_ID}."
    )
if "OCTOPUS_BOOTSTRAP_SERVERS" not in os.environ:
    log.warning(
        f"OCTOPUS_BOOTSTRAP_SERVERS not set; using default bootstrap servers {OCTOPUS_BOOTSTRAP_SERVERS}."
    )

mcp = FastMCP("Diaspora Octopus Bridge")

# Globals – initialised lazily after auth
_auth_client: Optional[globus_sdk.NativeAppAuthClient] = None
_login_mgr: Optional[LoginManager] = None
_diaspora: Optional[DiasporaClient] = None
_is_logged_in: bool = False  # set True by complete_diaspora_auth
_user_id: Optional[str] = None


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


class MSKTokenProviderFromRole(AbstractTokenProvider):
    """MSKTokenProviderFromRole."""

    def __init__(self, open_id: str) -> None:  # pragma: no cover
        """MSKTokenProviderFromRole init."""
        self.open_id = open_id

    def token(self) -> str:
        """MSKTokenProviderFromRole token."""
        token, _ = MSKAuthTokenProvider.generate_auth_token_from_role_arn(
            "us-east-1",
            f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/ap/{self.open_id}-role",
        )
        return token


def create_producer(
    open_id: str,
) -> KafkaProducer:
    """Create a Kafka producer with the user identity.

    Note: the call should succeed even the user does not exist.
    """
    conf = {
        "bootstrap_servers": OCTOPUS_BOOTSTRAP_SERVERS,
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "OAUTHBEARER",
        "sasl_oauth_token_provider": MSKTokenProviderFromRole(open_id),
        "request_timeout_ms": 10000,
    }
    producer = KafkaProducer(**conf)
    return producer


def create_consumer(
    open_id: str,
    topic: str,
) -> KafkaConsumer:
    """Create a Kafka consumer with the user identity and requested topic.

    Note: the call should succeed even if the user does not exist or does not
      have access to the topic.

    """
    conf = {
        "bootstrap_servers": OCTOPUS_BOOTSTRAP_SERVERS,
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "OAUTHBEARER",
        "sasl_oauth_token_provider": MSKTokenProviderFromRole(open_id),
        "request_timeout_ms": 10000,
    }

    consumer = KafkaConsumer(**conf)
    consumer.subscribe([topic])
    return consumer


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


@mcp.tool
def diaspora_authenticate() -> str:
    """Begin the Globus Native App OAuth2 flow.

    Initiates a Native App login flow for the Diaspora scopes and
    returns the URL the user must visit to grant access.

    Returns:
        An authorization URL string. The user should visit this URL,
        approve access, and then call `complete_diaspora_auth(code)`.
    """
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
    """Exchange an OAuth2 authorization code for tokens.

    Args:
        code: The one-time authorization code returned by the
              Native App flow.

    Returns:
        A success message including the user's OpenID on success,
        or an error string if the exchange fails or wasn't initiated.
    """

    global _auth_client, _login_mgr, _diaspora, _is_logged_in
    global _user_id

    if _auth_client is None:
        return "❌ You must call diaspora_authenticate first."

    try:
        tokens = _auth_client.oauth2_exchange_code_for_tokens(code.strip())
    except Exception as exc:
        log.error("Token exchange failed", exc_info=True)
        return f"❌ Token exchange failed: {exc}"

    _get_login_mgr()._token_storage.store(tokens)
    userinfo = _get_login_mgr().get_auth_client().userinfo()
    _user_id = userinfo.get("sub")

    _auth_client = None
    _diaspora = None
    _is_logged_in = True
    return f"✅ Login successful as user {_user_id}! You can now use Diaspora tools."


@mcp.tool
def diaspora_confidential_auth(
    client_id: str,
    client_secret: str,
) -> str:
    """Authenticate via the OAuth2 Client Credentials grant.

    Args:
        client_id: OAuth2 Confidential Client ID.
        client_secret: OAuth2 Confidential Client Secret.

    Returns:
        A success message including the service account's OpenID on
        success, or an error string if credentials are missing.
    """
    global _auth_client, _login_mgr, _diaspora, _is_logged_in
    global _user_id

    if not client_id:
        return "❌ Please provide a confidential client id."
    if not client_secret:
        return "❌ Please provide a confidential client secret."
    ca = ConfidentialAppAuthClient(client_id, client_secret)
    tokens = ca.oauth2_client_credentials_tokens(
        requested_scopes=[DiasporaScopes.all, AuthScopes.openid],
    )

    _get_login_mgr()._token_storage.store(tokens)
    userinfo = _get_login_mgr().get_auth_client().userinfo()
    _user_id = userinfo.get("sub")

    _auth_client = None
    _diaspora = None
    _is_logged_in = True
    return f"✅ Confidential client authentication successful with user {_user_id}!"


@mcp.tool
def logout() -> str:
    """Revoke tokens and clear cached clients."""
    global _auth_client, _login_mgr, _diaspora, _is_logged_in
    global _user_id

    # Attempt to revoke tokens via the login manager, if present
    if _login_mgr:
        try:
            logged_out = _login_mgr.logout()
        except Exception:
            logged_out = False
        _login_mgr = None
    else:
        logged_out = False

    # Clear all authentication state
    _auth_client = None
    _diaspora = None
    _is_logged_in = False
    _user_id = None

    # Return appropriate message
    return (
        "🚪 Logged out and tokens revoked."
        if logged_out
        else "ℹ️ No active tokens found."
    )


@mcp.tool
@require_login
def list_topics() -> list[str]:
    """List all Diaspora event topics the authenticated user can produce and consume."""
    return _get_diaspora().list_topics()


@mcp.tool
@require_login
def register_topic(topic: str) -> str:
    """Register a new Diaspora event topic so the user can produce and consume."""
    return _get_diaspora().register_topic(topic)


@mcp.tool
@require_login
def unregister_topic(topic: str) -> str:
    """Unregister (delete) an existing Diaspora event topic that the user has registered."""
    return _get_diaspora().unregister_topic(topic)


@mcp.tool
@require_login
def produce_one(
    topic: str,
    value: str,
    key: str | None = None,
    sync: bool = True,
) -> dict[str, Any]:
    """Produce a single message to a topic that the user has registered."""
    assert _user_id
    producer = create_producer(_user_id)

    try:
        future = producer.send(
            topic,
            key=key.encode("utf-8") if key else None,
            value=value.encode("utf-8"),
        )
        if sync:
            md = future.get(timeout=20)
            result = {
                "status": "produced",
                "topic": md.topic,
                "partition": md.partition,
                "offset": md.offset,
                "timestamp": md.timestamp,
            }

        else:
            result = {
                "status": "queued",
                "timestamp": int(time() * 1000),
            }
        return result

    finally:
        producer.close()


@mcp.tool
@require_login
def consume_latest(topic: str, timeout_s: int = 5) -> dict[str, Any]:
    """Fetch the single most-recent message from a topic that the user has registered."""
    assert _user_id

    consumer = create_consumer(_user_id, topic)
    try:
        max_attempts, attempts = 10, 0
        while not consumer.assignment() and attempts < max_attempts:
            consumer.poll(100)
            attempts += 1

        if not consumer.assignment():
            raise Exception(
                "consumer cannot acquire partition assignment; maybe the user has not registered the topic."
            )

        for tp in consumer.assignment():
            end = consumer.end_offsets([tp])[tp]
            if end:
                consumer.seek(tp, end - 1)

        newest = None
        for msgs in consumer.poll(timeout_s * 1000).values():
            for msg in msgs:
                m = {
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "key": msg.key.decode() if msg.key else None,
                    "value": msg.value.decode(),
                    "timestamp": msg.timestamp,
                }
                if newest is None or m["timestamp"] > newest["timestamp"]:
                    newest = m
        return newest if newest is not None else {}

    finally:
        consumer.close()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http", host="0.0.0.0", port=8000, path="/mcps/diaspora"
    )
