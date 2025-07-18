import os
os.environ["REQUESTS_CA_BUNDLE"] = "./certs/cacert.pem"
from dotenv import load_dotenv
import requests
import json
import asyncio
import httpx
from fastmcp import FastMCP
import uvicorn
import logging
from fastmcp.server.openapi import RouteMap, RouteType

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_openapi_spec_from_url(url: str):
    """
    Loads the OpenAPI specification from the given URL and logs available schema names.

    Args:
        url (str): The base URL of the API, e.g., 'https://fakerestapi.azurewebsites.net'
    """
    openapi_url = f"{url.rstrip('/')}/swagger/v1/swagger.json"
    logger.info(f"Fetching OpenAPI spec from {openapi_url}")

    try:
        response = requests.get(openapi_url)
        response.raise_for_status()  # Raises HTTPError if response status is 4xx or 5xx

        openapi_spec = response.json()
        schemas = openapi_spec.get("components", {}).get("schemas", {})

        if schemas:
            logger.info(f"Loaded schemas: {list(schemas.keys())}")
        else:
            logger.warning("No schemas found in OpenAPI spec.")

        return openapi_spec

    except requests.RequestException as e:
        logger.error(f"Error fetching OpenAPI spec: {e}")
        return None

async def main():
    """
    Main entry point for the FastMCP server.
    Loads OpenAPI spec, sets up the server, and starts Uvicorn.
    """
    # spec_path = "open-api-spec.json"
    spec_path = "bookstore_spec.json"

    logger.info(f"Loading OpenAPI spec from {spec_path}")
    try:

        # Can also fetch open api spec from API server.
        # openapi_spec = load_openapi_spec_from_url(url)

        # Loading openapi spec from local file
        with open(spec_path, "r") as f:
            openapi_spec = json.load(f)

        # Debug print to verify loaded schemas from the OpenAPI spec.
        schemas = openapi_spec.get("components", {}).get("schemas", {})
        logger.info(f"Loaded schemas: {list(schemas.keys())}")

    except FileNotFoundError:
        logger.error(f"OpenAPI spec file not found: {spec_path}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAPI spec JSON: {e}")
        return

    logger.info("Creating FastMCP server from OpenAPI spec")
    # Define your own custom maps to expose only certain methods as needed.
    custom_maps = [
        RouteMap(methods=["GET"], pattern=r".*", route_type=RouteType.TOOL)
    ]
    # Exposing all GET methods as tools for this example.

    mcp = FastMCP(
        title="Bookstore MCP Server",
        description="MCP server generated from Swagger Bookstore OpenAPI specification",
        version="1.0.0",
    )

    # Use HTTP client to call remote API
    async with httpx.AsyncClient(base_url="https://fakerestapi.azurewebsites.net") as http_client:
        logger.info("Creating FastMCP API from OpenAPI spec")
        fastmcp_api = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=http_client,
            route_maps=custom_maps
        )

        # Get the SSE app from the FastMCP API
        app = fastmcp_api.sse_app

        logger.info("Starting FastMCP server")
        # use host="0.0.0.0" to allow external access
        config = uvicorn.Config(app, host="localhost", port=int(os.getenv("MCP_SERVER_PORT", 8000)))

        # Create the Uvicorn server for the SSE app.
        server = uvicorn.Server(config)
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Error running Uvicorn server: {e}")
        finally:
            logger.info("FastMCP server shutdown.")


if __name__ == "__main__":
    asyncio.run(main())
