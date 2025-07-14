
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

   # For Garden server
   pip install -r mcps/garden/requirements.txt
   ```

## Setting up MCP Servers in Claude Desktop

To add these MCP servers to Claude Desktop:

1. Open **Claude Desktop** and go to **Settings → Developers**.
2. Click **Edit Config**.
3. Configure each server as needed, see below.
4. Restart **Claude Desktop**.

For detailed configuration instructions, see the README files for each component:
- [Globus MCP Servers Setup](/mcps/globus/README.md#setting-up-mcp-servers-in-claude-desktop)
- [Compute Facility MCP Servers Setup](/mcps/compute_facilities/README.md#setting-up-mcp-servers-in-claude-desktop)
- [Diaspora MCP Server Setup](/mcps/diaspora/README.md#setting-up-the-mcp-server-in-claude-desktop)
