# Science MCPs

A collection of Model Context Protocol (MCP) servers that enable Claude and other AI assistants to interact with scientific computing resources and data management services.

## Overview

This repository contains MCP servers that allow AI assistants to interact with scientific computing infrastructure:

1. **Globus MCP Servers** - Enable interaction with Globus services for data transfer and compute functions
2. **Compute Facility MCP Servers** - Enable interaction with ALCF and NERSC supercomputing facilities
3. **Diaspora MCP Server** - Enables interaction with the Diaspora Event Fabric (Octopus) for topic management and event streaming.

These servers implement the [Model Context Protocol (MCP)](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp), which allows AI assistants like Claude to interact with external tools and services.

## Components

### Globus MCP Servers

The Globus MCP servers enable AI assistants to:

- **Globus Transfer** - Transfer files between Globus endpoints, browse directories, and manage transfer tasks
- **Globus Compute** - Register and execute Python functions on remote Globus Compute endpoints (formerly FuncX)

[Learn more about Globus MCP Servers](mcps/globus/README.md)

### Compute Facility MCP Servers

The Compute Facility MCP servers enable AI assistants to:

- **ALCF** - Check status of ALCF machines (e.g., Polaris) and monitor running jobs
- **NERSC** - Check status of NERSC systems and services

[Learn more about Compute Facility MCP Servers](mcps/compute_facilities/README.md)

### Diaspora MCP Server

The Diaspora MCP server enable AI assistants to:

- **Manage topics** - Create, list, and delete topics within the user’s namespace
- **Stream events** - Publish events to a topic and retrieve the most recent event

[Learn more about the Diaspora MCP Server](mcps/diaspora/README.md)

## Use hosted MCPs (recommended)

Connecting to our hosted MCP servers is the fastest way to get started—no local installation or maintenance required.

1. Open **Claude Desktop** and go to **Settings → Developers**.
2. Click **Edit Config** and paste [the hosted MCPs configuration](docs/hosted-mcps.md).
3. Restart **Claude Desktop**.

## To deploy locally

## Prerequisites

- Python 3.11
- Claude Desktop application
- For Globus servers: A Globus account and Client ID

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/globus-labs/science-mcps
   cd science-mcps
   ```

2. Create a conda environment:
   ```bash
   conda create -n science-mcps python=3.11
   conda activate science-mcps
   ```

3. Install the required dependencies for the specific MCP server you want to use:
   ```bash
   # For Globus servers
   pip install -r mcps/globus/requirements.txt

   # For Compute Facility servers
   pip install -r mcps/compute_facilities/requirements.txt

   # For Diaspora server
   pip install -r mcps/diaspora/requirements.txt
   ```

## Setting up MCP Servers in Claude Desktop

To add these MCP servers to Claude Desktop:

1. Open **Claude Desktop** and go to **Settings → Developers**.
2. Click **Edit Config**.
3. Configure each server as needed, see below.
4. Restart **Claude Desktop**.

For detailed configuration instructions, see the README files for each component:
- [Globus MCP Servers Setup](mcps/globus/README.md#setting-up-mcp-servers-in-claude-desktop)
- [Compute Facility MCP Servers Setup](mcps/compute_facilities/README.md#setting-up-mcp-servers-in-claude-desktop)
- [Diaspora MCP Server Setup](mcps/diaspora/README.md#setting-up-the-mcp-server-in-claude-desktop)

## Usage Examples

### Globus Transfer

You can ask Claude to:
```
Transfer files from my Globus endpoint to another endpoint
```

### Globus Compute

You can ask Claude to:
```
Run a Python function on a Globus Compute endpoint
```

### ALCF Status

You can ask Claude to:
```
Check if Polaris is online
```

### NERSC Status

You can ask Claude to:
```
Check the status of NERSC systems
```

### Diaspora Event Fabric

You can ask Claude to:
```
Register a Diaspora topic, produce three messages, and consume the latest message
```

## Available Tools

### Globus Transfer Server Tools
- `globus_authenticate` - Start Globus authentication
- `complete_globus_auth` - Complete authentication with an auth code
- `list_endpoints` - List available Globus endpoints
- `submit_transfer` - Submit a file transfer between endpoints
- And more...

### Globus Compute Server Tools
- `compute_authenticate` - Start Globus Compute authentication
- `register_function` - Register a Python function with Globus Compute
- `execute_function` - Run a registered function on an endpoint
- And more...

### ALCF Server Tools
- `check_alcf_status` - Get the status of the Polaris machine
- `get_running_jobs` - Return the list of running jobs
- `system_health_summary` - Summarize the jobs submitted to Polaris

### NERSC Server Tools
- `get_nersc_status` - Get the status of various NERSC services
- `check_system_availability` - Check the system's current availability
- `get_maintenance_info` - Check the maintenance schedule of the resources

### Diaspora Event Fabric Tools
- `register_topic` – create a new Kafka topic
- `produce_event` – publish a UTF‑8 message to a topic
- `consume_latest_event` – fetch the most recent event from a topic
- And more...

For a complete list of tools, see the README files for each component.

## Troubleshooting

- **Connection Problems**: Check that you have network access to the required services
- **Permission Errors**: Verify you have the necessary permissions for the endpoints you're trying to access
- **Server Not Found**: Ensure the path to the Python scripts in Claude Desktop configuration is correct

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
