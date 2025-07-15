# Garden MCP Server

A lightweight [FastMCP](https://gofastmcp.com) server that lets Claude (or any MCP-aware agent) interact with **Garden AI**—a platform for discovering, publishing, and running scientific computing workflows. The server provides tools for running Garden functions and submitting computational jobs to HPC clusters.

## Available Tools

| Category       | Tools                                                                                   |
| -------------- | --------------------------------------------------------------------------------------- |
| **Discovery**  | `get_functions`                                                                         |
| **Execution**  | `run_function`                                                                          |
| **HPC Jobs**   | `submit_relaxation_job`, `check_job_status`, `get_job_results`                        |

## Prerequisites

- Python 3.11+
- Garden AI CLI installed and configured
- A Globus account
- Claude Desktop application

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/globus-labs/science-mcps
   cd science-mcps/mcps/garden
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

4. **Important**: Authenticate with Garden AI before starting the server:
   ```bash
   garden-ai login
   ```

5. Start the MCP server:
   ```bash
   python garden-mcp.py
   ```

## Setting up the MCP Server in Claude Desktop

To add this MCP server to Claude Desktop, edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "local-garden-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://0.0.0.0:8000/mcps/garden",
        "--allow-http"
      ]
    }
  }
}
```

Make sure the Garden MCP server is running locally before restarting Claude Desktop.

## Usage

Once the Garden MCP server is configured in Claude Desktop, you can ask Claude to perform Garden AI tasks. The server supports both general Garden function execution and specialized HPC cluster workflows.

### General Garden Workflow

Ask Claude:
```
What functions are available in the garden with DOI "10.23677/example-garden"?
```

Claude's workflow:
1. Use `get_functions` to discover available functions in the Garden
2. Optionally use `run_function` to execute specific functions

### HPC Structure Relaxation Workflow

Ask Claude:
```
Submit my structures in /path/to/structures.xyz for relaxation using MACE-MP-0, then check the status and save results when complete
```

Claude's workflow:
1. Use `submit_relaxation_job` to submit the XYZ file to Edith HPC cluster
2. Use `check_job_status` to monitor the job progress  
3. Use `get_job_results` to retrieve and save results when complete

## Available Tools

### Discovery Tools
* `get_functions(doi)` - List all available function names for a Garden by DOI

### Execution Tools  
* `run_function(doi, func_name, func_args)` - Execute a specific Garden function with provided arguments

### HPC Cluster Tools
* `submit_relaxation_job(xyz_file_path, model="mace-mp-0")` - Submit structure relaxation job to Edith HPC cluster using MLIP Garden
* `check_job_status(job_id)` - Check the status of a submitted relaxation job
* `get_job_results(job_id, output_file_path=None)` - Retrieve results from completed jobs, optionally saving to file

The HPC tools maintain job context across calls using a persistent MLIP Garden instance, enabling full workflow management from submission through result retrieval.

## Authentication

Before using the server, ensure you're authenticated with Garden AI:

```bash
garden-ai login
```

This authentication persists across server restarts and is required for accessing Garden functions and submitting HPC jobs.
