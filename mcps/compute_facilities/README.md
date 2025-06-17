# Compute Facility MCP Servers

This repository contains Model Context Protocol (MCP) servers that enable Claude and other AI assistants to interact with [ALCF](https://www.alcf.anl.gov/) and [NERSC](https://www.nersc.gov/) compute facilities. These are simple MCPs that provide functionality to check the facility status and, in ALCF's case, check the status of Polaris jobs.

## Overview

The repository provides two Globus MCP servers:

1. **ALCF MCP Server** - Enables AI assistants to check the status of ALCF machines and jobs. Status information is pulled from [Gronkulator](https://status.alcf.anl.gov/#/polaris).

2. **NERSC MCP Server** - Allows AI assistants to check the status of NERSC systems. System information is pulled from the [status API](https://api.nersc.gov/api/v1.2/status).

These servers implement the [Model Context Protocol (MCP)](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp), which allows AI assistants like Claude to interact with external tools and services.

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

## Setting up MCP Servers in Claude Desktop

To add these MCP servers to Claude Desktop:

1. Open Claude Desktop
2. Go to Settings (gear icon)
3. Navigate to the "MCP Servers" section
4. Click "Add Server"
5. Configure each server as follows:

### For the ALCF Server:

Edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`. Make sure you correct the path information:

```json
{
  "mcpServers": {
    "alcf-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["/path/to/science-mcps/mcps/compute_facilities/alcf_server.py"],
    }
  }
}
```


Ensure the python path is correctly set and then restart Claude desktop.

### For the NERSC Server:

Edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`. Make sure you correct the path information:

```json
{
  "mcpServers": {
    ...,
    "nersc-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["/path/to/science-mcps/mcps/compute_facilities/nersc_server.py"],
    }
  }
}
```

## Usage

Once configured, you can use these servers with Claude by asking it to perform status checks on each facility. Claude will automatically use the appropriate MCP server tools.

### Facility Example

You can ask Claude to:

```
Check if Polaris is online.
```

Claude will report whether the Polaris supercomputer is online and the number of jobs currently running.


## Available Tools

### ALCF Server Tools

- `check_alcf_status` - Get the status of the Polaris machine
- `get_running_jobs` - Return the list of running jobs
- `system_health_summary` - Summarize the jobs submitted to Polaris

### NERSC Server Tools

- `get_nersc_status` - Get the status of various NERSC services
- `check_system_availability` - Check the system's current availability
- `get_maintenance_info` - Check the maintenance schedule of the resources


## Troubleshooting

- **Connection Problems**: Check that you have network access to facility status pages
- **Server Not Found**: Ensure the path to the Python scripts in Claude Desktop configuration is correct

## License

See the [LICENSE](../../LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
