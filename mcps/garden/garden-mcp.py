from fastmcp import FastMCP
from garden_ai.client import GardenClient
from fastmcp.exceptions import ToolError
from pathlib import Path
import json

mcp = FastMCP("Garden MCP Server")

# Global singleton for MLIP Garden to maintain job context across tool calls
_mlip_garden = None


def get_mlip_garden():
    """
    Lazy initialization of MLIP Garden singleton to maintain job context.
    """
    global _mlip_garden
    if _mlip_garden is None:
        import garden_ai

        _mlip_garden = garden_ai.get_garden("mlip-garden")
    return _mlip_garden


@mcp.tool
def get_functions(doi: str):
    """
    Return a list of available modal function names for this Garden.
    """
    garden = GardenClient().get_garden(doi)
    data = garden.metadata.model_dump(
        exclude={"owner_identity_id", "id", "language", "publisher"}
    )
    data["entrypoints"] = [ep.metadata.model_dump() for ep in garden.entrypoints]
    data["modal_functions"] = [
        mf.metadata.model_dump() for mf in garden.modal_functions
    ]
    return [f["function_name"] for f in data["modal_functions"]]


@mcp.tool
def run_function(
    doi: str,
    func_name: str,
    func_args: list[str],
):
    """
    Load the Garden by DOI, locate the named function, and invoke it with the provided args.
    """
    garden = GardenClient().get_garden(doi)
    entrypoint = getattr(garden, func_name, None)
    if entrypoint is None:
        raise ToolError(f"No such function '{func_name}' in garden '{doi}'")
    try:
        result = entrypoint(func_args)
    except Exception as e:
        raise ToolError(f"Error running '{func_name}(...)': {e}")
    return result


@mcp.tool
def submit_relaxation_job(xyz_file_path: str, model: str = "mace-mp-0"):
    """
    Submit an XYZ structure file for relaxation on the Edith HPC cluster using the MLIP Garden.

    Args:
        xyz_file_path: Path to the XYZ file containing structures to relax
        model: The ML interatomic potential model to use (default: "mace-mp-0")

    Returns:
        job_id: The job ID for tracking the submitted job
    """
    try:
        xyz_file = Path(xyz_file_path)
        if not xyz_file.exists():
            raise ToolError(f"XYZ file not found: {xyz_file_path}")

        # Edith HPC cluster endpoint ID
        edith_ep_id = "a01b9350-e57d-4c8e-ad95-b4cb3c4cd1bb"

        # Use singleton MLIP garden to maintain job context
        mlip_garden = get_mlip_garden()
        job_id = mlip_garden.batch_relax(xyz_file, model=model, cluster_id=edith_ep_id)

        return {
            "job_id": job_id,
            "message": f"Successfully submitted relaxation job for {xyz_file_path}",
            "model": model,
            "cluster": "Edith",
        }
    except Exception as e:
        raise ToolError(f"Failed to submit relaxation job: {e}")


@mcp.tool
def check_job_status(job_id: str):
    """
    Check the status of a previously submitted relaxation job.

    Args:
        job_id: The job ID returned from submit_relaxation_job

    Returns:
        Status information for the job
    """
    try:
        # Use singleton MLIP garden to access job context
        mlip_garden = get_mlip_garden()
        status = mlip_garden.get_job_status(job_id)

        return {
            "job_id": job_id,
            "status": status,
            "message": f"Job {job_id} status: {status}",
        }
    except Exception as e:
        raise ToolError(f"Failed to check job status for {job_id}: {e}")


@mcp.tool
def get_job_results(job_id: str, output_file_path: str = None):
    """
    Retrieve the results of a completed relaxation job and optionally save to file.

    Args:
        job_id: The job ID returned from submit_relaxation_job
        output_file_path: Optional path to save the results to a file

    Returns:
        The job results, and confirmation if saved to file
    """
    try:
        # Use singleton MLIP garden to access job context
        mlip_garden = get_mlip_garden()
        results = mlip_garden.get_results(job_id)

        response = {"job_id": job_id, "results": results}

        # Optionally save results to file
        if output_file_path:
            output_path = Path(output_file_path)

            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save results as JSON
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2, default=str)

            response["saved_to"] = str(output_path)
            response["message"] = f"Results retrieved and saved to {output_path}"
        else:
            response["message"] = f"Results retrieved for job {job_id}"

        return response

    except Exception as e:
        raise ToolError(f"Failed to get results for job {job_id}: {e}")


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/mcps/garden")

# if __name__ == "__main__":
#     mcp.run(transport="stdio")
