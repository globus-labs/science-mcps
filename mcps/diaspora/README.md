# Diaspora Octopus MCP Server

A lightweight [FastMCP](https://gofastmcp.com) server that lets Claude (or any MCP-aware agent) publish, consume and administer streams on the **Diaspora Event Fabric**—a Kafka-based data-streaming platform.  The server wraps the official [`diaspora-event-sdk`](https://github.com/globus-labs/diaspora-event-sdk).

## Available Tools

| Category       | Tools                                                                                   |
| -------------- | --------------------------------------------------------------------------------------- |
| **Auth**       | `start_diaspora_login`, `finish_diaspora_login`, `diaspora_confidential_auth`, `logout` |
| **Topics**     | `list_topics`, `register_topic`, `unregister_topic`                                     |
| **Data plane** | `produce_one`, `consume_latest`                                                         |


## Prerequisites

- Python 3.11
- A Globus account (sign up at [globus.org](https://www.globus.org/))
- Globus Client ID (register an app at [developers.globus.org](https://developers.globus.org/))
- Claude Desktop application

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/globus-labs/science-mcps
   cd science-mcps/mcps/diaspora
   ```

2. Create a conda environment:
   ```bash
   conda create -n science-mcps python=3.11
   conda activate science-mcps
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setting up the MCP Server in Claude Desktop

To add this MCP server to Claude Desktop, edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`. Make sure you correct the path information:

```json
{
  "mcpServers": {
    "diaspora-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["/path/to/science-mcps/mcps/diaspora/diaspora_server.py"],
      "env": {
        "GLOBUS_CLIENT_ID": "ee05bbfa-2a1a-4659-95df-ed8946e3aae6"
      }
    }
  }
}
```

Ensure the python path is correctly set and then restart Claude desktop.

## Usage

Once the Diaspora MCP server is configured in Claude Desktop, simply ask Claude to perform streaming-related tasks; it will invoke the correct Diaspora tools for you.

Ask Claude:

```bash
Register a Diaspora topic, produce three messages, and consume the latest message
```

Claude’s typical workflow:
1. Authenticate with Globus (diaspora_authenticate → complete_diaspora_auth)
3. Register the topic (register_topic)
4. Produce three string messages (produce_one)
5. Consume the newest message (consume_latest) and display it


## Available Tools

* `diaspora_authenticate`	Start the Globus Native-App login flow
* `complete_diaspora_auth`	Exchange the auth code for refresh tokens
* `diaspora_confidential_auth` Authenticate via the Globus Client Credentials.
* `logout`	Revoke stored tokens and clear cached clients
* `list_topics`	List all topics owned by the caller
* `register_topic`	Create a new Kafka topic under the caller’s namespace
* `unregister_topic`	Delete an existing topic
* `produce_one`	Publish a UTF-8 message (optionally with key)
* `consume_latest`	Retrieve the most recent message from a topic

These tools cover authentication, credential management, topic administration, and core data-plane operations.
