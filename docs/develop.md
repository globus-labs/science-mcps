## Dev Dependencies
```bash
pip install pytest pytest-asyncio aresponses mypy ruff pre-commit
```

## Testing Locally without Docker
```bash
# NERSC Status
cd mcps/compute_facilities && python alcf_server.py
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
docker build --platform=linux/amd64 -t science-mcps-facility-image -f mcps/compute_facilities/Dockerfile .

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

# Diaspora (needs AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY that are able to assume IAM user roles)
docker run --rm -p 8000:8000 -e SERVER_NAME=diaspora -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... -e AWS_DEFAULT_REGION=us-east-1 science-mcps-diaspora-image

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
## Deploying Hosted MCPs on AWS Lightsail

### Manual Deployment (e.g., for ALCF Status MCP)

You can manually deploy an MCP server (e.g., ALCF status) to AWS Lightsail using the following steps (assume that the container service `science-mcps-alcf` has been created in your AWS account):

```bash
AWS_REGION="us-east-1"
CONTAINER_LABEL="fastmcp"
LOCAL_IMAGE_TAG="science-mcps-facility-image"
LIGHTSAIL_SERVICE_NAME="science-mcps-alcf"
SERVICE_PORT="8000"
SERVER_NAME="alcf"
DEPLOY_IMAGE_TAG=":science-mcps-alcf.fastmcp.latest"

# Push your local image to the Lightsail container registry
aws lightsail push-container-image \
  --region "${AWS_REGION}" \
  --service-name "${LIGHTSAIL_SERVICE_NAME}" \
  --label "${CONTAINER_LABEL}" \
  --image "${LOCAL_IMAGE_TAG}"

# Build the JSON payload for deployment
CONTAINERS_JSON=$(jq -n \
  --arg container "${CONTAINER_LABEL}" \
  --arg imageTag "${DEPLOY_IMAGE_TAG}" \
  --arg port "${SERVICE_PORT}" \
  --arg server "${SERVER_NAME}" \
  '{
     ($container): {
       image:      $imageTag,
       ports:      { ($port): "HTTP" },
       environment: { SERVER_NAME: $server }
     }
   }')

# Create a new deployment in your Lightsail service
aws lightsail create-container-service-deployment \
  --region "${AWS_REGION}" \
  --service-name "${LIGHTSAIL_SERVICE_NAME}" \
  --containers "${CONTAINERS_JSON}" \
  --public-endpoint "{\"containerName\":\"${CONTAINER_LABEL}\",\"containerPort\":${SERVICE_PORT}}"
```

### Manual Deployment - Diaspora MCP
```bash
AWS_REGION="us-east-1"
CONTAINER_LABEL="fastmcp"
LOCAL_IMAGE_TAG="science-mcps-diaspora-image"
LIGHTSAIL_SERVICE_NAME="science-mcps-diaspora"
SERVICE_PORT="8000"
SERVER_NAME="diaspora"
DEPLOY_IMAGE_TAG=":science-mcps-diaspora.fastmcp.latest"
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Push your local image to the Lightsail container registry
aws lightsail push-container-image \
  --region "${AWS_REGION}" \
  --service-name "${LIGHTSAIL_SERVICE_NAME}" \
  --label "${CONTAINER_LABEL}" \
  --image "${LOCAL_IMAGE_TAG}"


# Build the JSON payload for deployment
CONTAINERS_JSON=$(jq -n \
  --arg container "${CONTAINER_LABEL}" \
  --arg imageTag "${DEPLOY_IMAGE_TAG}" \
  --arg port "${SERVICE_PORT}" \
  --arg server "${SERVER_NAME}" \
  --arg access_key "${AWS_ACCESS_KEY_ID}"\
  --arg secret_key "${AWS_SECRET_ACCESS_KEY}"\
  --arg region "${AWS_REGION}" \
  '{
     ($container): {
       image:      $imageTag,
       ports:      { ($port): "HTTP" },
       environment: { SERVER_NAME: $server, AWS_ACCESS_KEY_ID: $access_key, AWS_SECRET_ACCESS_KEY: $secret_key, AWS_DEFAULT_REGION: $region }
     }
   }')

echo "$CONTAINERS_JSON" | jq

# Create a new deployment in your Lightsail service
aws lightsail create-container-service-deployment \
  --region "${AWS_REGION}" \
  --service-name "${LIGHTSAIL_SERVICE_NAME}" \
  --containers "${CONTAINERS_JSON}" \
  --public-endpoint "{\"containerName\":\"${CONTAINER_LABEL}\",\"containerPort\":${SERVICE_PORT}}"
```


### Automated Deployment via GitHub Actions
Use the [deploy.yaml](https://github.com/globus-labs/science-mcps/actions/workflows/deploy.yaml) workflow for automated MCP docker container deployment to AWS Lightsail. It runs on every push to the main branch or when manually triggered. Steps include:
 - Ensure Lightsail service exists
 - Delete old Docker images
 - Push image to Lightsail
 - Deploy to Lightsail


## Globus Labs Hosted MCP Endpoints
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
