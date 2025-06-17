## Testing Locally without Docker
```bash
# NERSC Status
cd mcps/compute-facilities && python alcf_server.py
# ALCF Status
python nersc_server.py 

# Diaspora
cd mcps/diaspora && python diaspora_server.py

# Globus Transfer
cd mcps/globus && python transfer_server.py
# Globus Compute
python compute_server.py
```

## Testing Locally with Docker

1. **Build**

```bash
cd /path/to/science-mcps/

# Compute facilities
docker build --platform=linux/amd64 -t science-mcps-facility-image -f mcps/compute-facilities/Dockerfile .

# Diaspora
docker build --platform=linux/amd64 -t science-mcps-diaspora-image -f mcps/diaspora/Dockerfile .

# Globus
docker build --platform=linux/amd64 -t science-mcps-globus-image -f mcps/globus/Dockerfile .
```

2. **Run**

```bash
# ALCF Status
docker run --rm -p 8000:8000 -e SERVER_NAME=alcf  science-mcps-facility-image
# NERSC Status
docker run --rm -p 8000:8000 -e SERVER_NAME=nersc science-mcps-facility-image

# Diaspora
docker run --rm -p 8000:8000 -e SERVER_NAME=diaspora science-mcps-diaspora-image 

# Transfer
docker run --rm -p 8000:8000 -e SERVER_NAME=transfer science-mcps-globus-image
# Compute
docker run --rm -p 8000:8000 -e SERVER_NAME=compute  science-mcps-globus-image

```

3. **Inspect via MCP Inspector** 

In a separate terminal, run `npx @modelcontextprotocol/inspector`, then visit:

```
http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...
```

* **Transport Type:** Streamable HTTP
* **URL:** `http://0.0.0.0:8000/mcps/globus-transfer` (or `…/globus-compute`,   `…/alcf-status`,  `…/nersc-status`)

## Locally use Claude or other AI agents to test

```json
    "remote-alcf-status-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://0.0.0.0:8000/mcps/alcf-status",
        "--allow-http"
      ]
    }
```

## Testing the Hosted MCPs

```json
{
  "mcpServers": {
    "remote-globus-transfer-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://science-mcps-transfer.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/globus-transfer/"
      ],
      "env": {
        "GLOBUS_CLIENT_ID": "ee05bbfa-2a1a-4659-95df-ed8946e3aae6"
      }
    },
    "remote-globus-compute-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://science-mcps-compute.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/globus-compute/"
      ],
      "env": {
        "GLOBUS_CLIENT_ID": "ee05bbfa-2a1a-4659-95df-ed8946e3aae6"
      }
    },
    "remote-diaspora-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://science-mcps-diaspora.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/diaspora/"
      ],
      "env": {
        "GLOBUS_CLIENT_ID": "ee05bbfa-2a1a-4659-95df-ed8946e3aae6"
      }
    },
    "remote-alcf-status-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://science-mcps-alcf.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/alcf-status/"
      ]
    },
    "remote-nersc-status-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://science-mcps-nersc.qpp943wkvr7b2.us-east-1.cs.amazonlightsail.com/mcps/nersc-status/"
      ]
    }
  }
}
```