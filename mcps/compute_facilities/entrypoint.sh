#!/usr/bin/env bash
set -e

# SERVER_NAME must be passed via --env
if [ -z "$SERVER_NAME" ]; then
    echo "ERROR: you must set \$SERVER_NAME to facility" >&2
    exit 1
fi

SCRIPT_NAME="${SERVER_NAME}_server.py"

exec conda run --no-capture-output -n science-mcps fastmcp run "$SCRIPT_NAME" --transport http --host 0.0.0.0 --port 8000
