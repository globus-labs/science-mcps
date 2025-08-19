# Globus MCP Servers

This repository contains Model Context Protocol (MCP) servers that enable Claude and other AI assistants to interact with [Globus](https://www.globus.org/) services for scientific computing and data management.

## Overview

The repository provides three Globus MCP servers:

1. **Globus Compute MCP Server** - Enables AI assistants to register and execute Python functions on remote Globus Compute endpoints (formerly FuncX).

2. **Globus Transfer MCP Server** - Allows AI assistants to transfer files between Globus endpoints, browse endpoint directories, and manage transfer tasks.

3. **Globus Search MCP Server** - Provides AI assistants with the ability to create search indices, ingest documents, and perform powerful searches across Globus Search indexes.

These servers implement the [Model Context Protocol (MCP)](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp), which allows AI assistants like Claude to interact with external tools and services.

## Prerequisites

- Python 3.11
- A Globus account (sign up at [globus.org](https://www.globus.org/))
- Globus Client ID (register an app at [developers.globus.org](https://developers.globus.org/))
- Claude Desktop application


## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/globus-labs/science-mcps
   cd science-mcps/mcps/globus
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

### For Globus Compute Server:

Edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`. Make sure you correct the path information:

```json
{
  "mcpServers": {
    "globus-compute-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["/path/to/science-mcps/mcps/globus/compute_server.py"]
    }
  }
}
```


Ensure the python path is correctly set and then restart Claude desktop.

### For Globus Transfer Server:

Edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`. Make sure you correct the path information:

```json
{
  "mcpServers": {
    ...,
    "globus-transfer-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["/path/to/science-mcps/mcps/globus/transfer_server.py"]
    }
  }
}
```

### For Globus Search Server:

Edit the claude_desktop_config.json file at `~/Library/Application\ Support/Claude/claude_desktop_config.json`. Make sure you correct the path information:

```json
{
  "mcpServers": {
    ...,
    "globus-search-mcp": {
      "command": "/path/to/your/env/python",
      "args": ["/path/to/science-mcps/mcps/globus/search_server.py"]
    }
  }
}
```

## Usage

Once configured, you can use these servers with Claude by asking it to perform Globus-related tasks. Claude will automatically use the appropriate MCP server tools.

### Globus Transfer Example

You can ask Claude to:

```
Transfer files from my Globus endpoint to another endpoint
```

Claude will guide you through:
1. Authentication with Globus
2. Selecting source and destination endpoints
3. Specifying file paths
4. Submitting and monitoring the transfer

### Globus Compute Example

You can ask Claude to:

```
Run a Python function on a Globus Compute endpoint
```

Claude will help you:
1. Authenticate with Globus
2. Write or select a Python function
3. Register the function with Globus Compute
4. Execute it on a specified endpoint
5. Retrieve and display the results

### Globus Search Example

You can ask Claude to:

```
Create a search index and publish research data for discovery
```

Claude will help you:
1. Authenticate with Globus
2. Create a new search index
3. Ingest documents with metadata
4. Perform searches across your data
5. Manage visibility and access permissions

## Available Tools

### Globus Transfer Server Tools

- `search_endpoints_and_collections` - Search Transfer endpoints and collections
- `list_my_endpoints_and_collections` - List endpoints and collections I administer
- `list_endpoints_and_collections_shared_with_me` - List endpoints and collections shared with me
- `submit_transfer` - Submit a file transfer between collections
- `get_task_events` - Get a list of task events to monitor the status and progress of a task
- `list_directory` - Browse files on a collection

### Globus Compute Server Tools

- `list_my_endpoints` - List Globus Compute endpoints that the user owns
- `register_python_function` - Register a Python function with Globus Compute
- `register_shell_command` - Register a shell command function with Globus Compute
- `submit_task` - Submit a function execution task to an endpoint
- `get_task_status` - Retrieve the status and result of a task

### Globus Search Server Tools

- `create_index` - Create a new Globus Search index
- `list_my_indices` - List search indices that the user has access to
- `get_index_info` - Get detailed information about a specific search index
- `delete_index` - Delete a search index (owner only)
- `ingest_document` - Ingest a single document into a search index
- `ingest_documents` - Ingest multiple documents into a search index
- `get_ingestion_status` - Get the status of a document ingestion task
- `delete_subject` - Delete a subject and all its entries from a search index
- `search_index` - Search for documents using a simple query string
- `advanced_search` - Perform advanced search with filters, facets, and sorting
- `get_subject` - Get detailed information about a specific subject

## Troubleshooting

- **Connection Problems**: Check that you have network access to Globus services
- **Permission Errors**: Verify you have the necessary permissions for the endpoints you're trying to access
- **Server Not Found**: Ensure the path to the Python scripts in Claude Desktop configuration is correct

## License

See the [LICENSE](../../LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
