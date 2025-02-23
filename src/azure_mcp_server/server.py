import asyncio

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from typing import Any
import os
import json

from azure.identity import EnvironmentCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from dotenv import load_dotenv

server = Server("azure-mcp-server")
load_dotenv()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="list-subscriptions",
            description="List all Azure subscriptions for the authenticated user.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="list-resource-groups",
            description="List all resource groups in an Azure subscription.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="list-resources",
            description="List all resources in a resource group.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                    "resource_group": {"type": "string"}
                },
                "required": ["resource_group"],
            },
        )                
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "list-subscriptions":
        response = await list_subscriptions()
        return types.TextContent(type="text", text=json.dumps(response))
    
    elif name == "list-resource-groups":
        subscription_id = arguments.get("subscription_id", None)
        response = await list_resource_groups(subscription_id)
        return types.TextContent(type="text", text=json.dumps(response))
    
    elif name == "list-resources":
        subscription_id = arguments.get("subscription_id", None)
        resource_group = arguments.get("resource_group")
        result = await list_resources(resource_group, subscription_id)
        return types.TextContent(type="text", text=json.dumps(response))
    
    else:
        return types.TextContent(type="text", text="Invalid tool name.")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="azure-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

async def list_subscriptions() -> list[dict[str, Any]]:
    """List all subscriptions in the account.
    
    Args:
        None
    """
    credential = EnvironmentCredential()
    subscription_client = SubscriptionClient(credential)
    subscriptions = subscription_client.subscriptions.list()

    subscription_list = []
    for subscription in list(subscriptions):
        subscription_info = {
            "id": subscription.subscription_id,
            "name": subscription.display_name,
        }
        subscription_list.append(subscription_info)

    return subscription_list

async def list_resource_groups(subscription_id=None) -> list[dict[str, Any]]:
    """List all resource groups in the subscription.
    
    Args:
        subscription_id (str): The subscription ID. This is an optional parameter.
    """
    credential = EnvironmentCredential()
    if subscription_id is None:
        if "AZURE_SUBSCRIPTION_ID" not in os.environ:
            raise ValueError("subscription_id must be provided or set as an environment variable.")
        else:
            subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

    resource_client = ResourceManagementClient(credential, subscription_id)
    group_list = resource_client.resource_groups.list()

    resource_groups = []
    for group in list(group_list):
        resource = {
            "name": group.name,
            "location": group.location,
        }
        resource_groups.append(resource)

    return resource_groups

async def list_resources(resource_group, subscription_id) -> list[dict[str, Any]]:
    """List all resources in the resource group.
    
    Args:
        resource_group (str): The resource group name.
        subscription_id (str): The subscription ID. This is an optional parameter.
    """
    credential = EnvironmentCredential()
    if subscription_id is None:
        if "AZURE_SUBSCRIPTION_ID" not in os.environ:
            raise ValueError("subscription_id must be provided or set as an environment variable.")
        else:
            subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

    resource_client = ResourceManagementClient(credential, subscription_id)
    resources = resource_client.resources.list_by_resource_group(resource_group)

    resource_list = []
    for resource in list(resources):
        resource_info = {
            "name": resource.name,
            "type": resource.type,
            "location": resource.location,
        }
        resource_list.append(resource_info)

    return resource_list