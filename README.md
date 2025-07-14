# Science MCPs

A collection of Model Context Protocol (MCP) servers that enable Claude and other AI assistants to interact with scientific computing resources and data management services.

## Overview

This repository contains MCP servers that allow AI assistants to interact with scientific computing infrastructure:

1. **Globus MCP Servers** - Enable interaction with Globus services for data transfer and compute functions
2. **Compute Facility MCP Servers** - Enable interaction with ALCF and NERSC supercomputing facilities
3. **Diaspora MCP Server** - Enables interaction with the Diaspora Event Fabric (Octopus) for topic management and event streaming.

These servers implement the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), which allows AI assistants like Claude to interact with external tools and services.

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

### Garden MCP Server

The Garden MCP server enable AI assistants to:

- **Discover AI Model Gardens** - Search Garden's registry of domain-specific AI-for-science models.
- **Run Models** - Run inference on Garden models.

[Learn more about the Garden MCP Server](mcps/garden/README.md)

## Use hosted MCPs (recommended)

Connecting to our hosted MCP servers is the fastest way to get started—no local installation or maintenance required.

1. Open **Claude Desktop** and go to **Settings → Developers**.
2. Click **Edit Config** and paste [the hosted MCPs configuration](/docs/hosted-mcps.md).
3. Restart **Claude Desktop**.

## Deploy Locally

See [local deployment configuration](/docs/local-mcps.md).

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
- `submit_transfer` - Submit a file transfer between collections
- `get_task_events` - Get a list of task events to monitor the status and progress of a task
- `list_directory` - Browse files on a collection
- And more...

### Globus Compute Server Tools
- `register_python_function` - Register a Python function with Globus Compute
- `submit_task` - Submit a function execution task to an endpoint
- `check_task_status` - Retrieve the status and result of a task
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
