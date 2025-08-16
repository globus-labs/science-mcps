import os
import platform

import globus_sdk
from fastmcp.exceptions import ClientError

DEFAULT_CLIENT_ID = "ee05bbfa-2a1a-4659-95df-ed8946e3aae6"


def get_client_creds():
    client_id = os.getenv("GLOBUS_CLIENT_ID")
    client_secret = os.getenv("GLOBUS_CLIENT_SECRET")
    return client_id, client_secret


def get_globus_app() -> globus_sdk.GlobusApp:
    app_name = platform.node()
    client_id, client_secret = get_client_creds()

    if client_id and client_secret:
        return globus_sdk.ClientApp(
            app_name=app_name, client_id=client_id, client_secret=client_secret
        )

    elif client_secret:
        raise ClientError(
            "Both GLOBUS_CLIENT_ID and GLOBUS_CLIENT_SECRET must be set to"
            " use a client identity."
        )

    else:
        client_id = client_id or DEFAULT_CLIENT_ID
        config = globus_sdk.GlobusAppConfig(login_flow_manager="local-server")
        return globus_sdk.UserApp(app_name=app_name, client_id=client_id, config=config)
