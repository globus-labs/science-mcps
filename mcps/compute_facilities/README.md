# Compute Facility MCP Server

This repository contains a unified Model Context Protocol (MCP) server that enables Claude and other AI assistants to interact with [ALCF](https://www.alcf.anl.gov/) and [NERSC](https://www.nersc.gov/) compute facilities. The server provides comprehensive functionality to check facility status, monitor job queues (in ALCF integration), and retrieve system information (in NERSC integration).

## Overview

The repository provides one unified MCP server:

1. **Facility MCP Server** (`facility_server.py`) - A comprehensive server that combines:
   - **ALCF Integration**: Check the status of ALCF Polaris supercomputer, monitor job queues (running, starting, queued, reservations), and retrieve maintenance information from [Gronkulator](https://status.alcf.anl.gov/#/polaris).
   - **NERSC Integration**: Check the status of all NERSC systems (compute, filesystem, service, storage) with case-insensitive system name matching from the [status API](https://api.nersc.gov/api/v1.2/status).

This server implements the [Model Context Protocol (MCP)](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp), which allows AI assistants like Claude to interact with external tools and services through a standardized interface.

## Prerequisites

- Python 3.11
- Claude Desktop application


## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/globus-labs/science-mcps
   cd science-mcps/mcps/compute_facilities
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

To add the unified facility MCP server to Claude Desktop:

1. Open Claude Desktop
2. Go to Settings (gear icon)
3. Navigate to the "MCP Servers" section
4. Click "Add Server"
5. Configure the server as follows (module invocation recommended).

Edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "facility-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["-m", "mcps.compute_facilities.facility_server"]
    }
  }
}
```

Ensure the python path is correctly set and then restart Claude Desktop.

## Usage

Once configured, you can use the facility server with Claude by asking it to perform status checks on either facility. Claude will automatically use the appropriate MCP server tools.

### Example Queries

You can ask Claude to:

```
Check if Polaris is online and show me the running jobs.
```

```
What's the status of NERSC Perlmutter?
```

```
Show me the first 5 queued jobs on ALCF Polaris.
```

```
Give me a summary of all NERSC systems.
```

## Available Tools

### ALCF Tools

- `get_alcf_status(resource: str = "polaris")` — Summarized ALCF status for a resource (`polaris` or `aurora`), including maintenance and job counts.
- `get_alcf_tasks(kind, n=10, skip=0, resource: str = "polaris")` — Paginated ALCF jobs for a queue.
  - `kind` must be one of: `running`, `starting`, `queued`, `reservation`.
  - `resource` examples: `polaris`, `aurora`.

### NERSC Tools

- `get_nersc_status()` — Returns the full API model with `systems` (list of NERSC systems).
- `get_nersc_system_status(system_name: str)` — Returns one NERSC system by name (case-insensitive).

## Examples

### ALCF

- Polaris: first 10 running jobs
  - Tool: `get_alcf_tasks`
  - Args: `{ "kind": "running", "resource": "polaris", "n": 10, "skip": 0 }`

- Polaris: first 10 starting, queued, reservation jobs
  - Starting: `{ "kind": "starting", "resource": "polaris", "n": 10, "skip": 0 }`
  - Queued: `{ "kind": "queued", "resource": "polaris", "n": 10, "skip": 0 }`
  - Reservation: `{ "kind": "reservation", "resource": "polaris", "n": 10, "skip": 0 }`

- Aurora: first 10 running, starting, queued, reservation jobs
  - Running: `{ "kind": "running", "resource": "aurora", "n": 10, "skip": 0 }`
  - Starting: `{ "kind": "starting", "resource": "aurora", "n": 10, "skip": 0 }`
  - Queued: `{ "kind": "queued", "resource": "aurora", "n": 10, "skip": 0 }`
  - Reservation: `{ "kind": "reservation", "resource": "aurora", "n": 10, "skip": 0 }`

- ALCF status summary (Polaris)
  - Tool: `get_alcf_status`
  - Args: `{ "resource": "polaris" }`

- ALCF status summary (Aurora)
  - Tool: `get_alcf_status`
  - Args: `{ "resource": "aurora" }`

### NERSC

- List all systems
  - Tool: `get_nersc_status`

- Specific system by name
  - Tool: `get_nersc_system_status`
  - Args: `{ "system_name": "perlmutter" }`


## Testing

Run the test suite to verify functionality:

```bash
cd tests
python3 -m pytest facility_server_test.py -v
```

## Troubleshooting

- **Connection Problems**: Check that you have network access to facility status API
- **Server Not Found**: Ensure the path to the Python script in Claude Desktop configuration is correct
- **Type Errors**: Ensure you're using Python 3.9+ for built-in generic type support
- **Import Errors**: Verify all dependencies are installed via `pip install -r requirements.txt`

## License

See the [LICENSE](../../LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
