
To add these MCP servers to Claude Desktop, edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`.

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
