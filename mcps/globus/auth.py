import os

import globus_sdk
from fastmcp.exceptions import ClientError
from fastmcp.server.dependencies import get_http_headers


def get_client_creds():
    client_id = os.getenv("GLOBUS_CLIENT_ID")
    client_secret = os.getenv("GLOBUS_CLIENT_SECRET")
    return client_id, client_secret


def get_access_token():
    headers = get_http_headers()
    auth_header = headers.get("authorization")
    if not auth_header:
        raise ClientError("Request is missing the required 'Authorization' header")
    if not auth_header.startswith("Bearer "):
        raise ClientError("Authorization header must start with 'Bearer '")
    return auth_header[7:]


def get_authorizer(scopes: str | list[str]):
    client_id, client_secret = get_client_creds()

    if client_id and client_secret:
        auth_client = globus_sdk.ConfidentialAppAuthClient(client_id, client_secret)
        return globus_sdk.ClientCredentialsAuthorizer(auth_client, scopes)

    elif client_id:
        raise ClientError(
            "Both GLOBUS_CLIENT_ID and GLOBUS_CLIENT_SECRET must be set to use"
            " a client identity."
        )

    else:
        access_token = get_access_token()
        return globus_sdk.AccessTokenAuthorizer(access_token)
