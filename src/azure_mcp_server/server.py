import asyncio

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from typing import Any
import os

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
            name="create-resource-group",
            description="Create a resource group in an Azure subscription.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                    "name": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": [
                    "name",
                    "location",
                ],
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
                "required": [
                    "resource_group"
                ],
            },
        )                
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "list-subscriptions":
        response = await list_subscriptions()
        respText = "Subscriptions:\n"
        
        for subscription in response:
            respText += f"ID: {subscription['id']}, Name: {subscription['name']}\n"
    
    elif name == "list-resource-groups":
        subscription_id = arguments.get("subscription_id", None)
        response = await list_resource_groups(subscription_id)
        respText = f"Resource Groups in {subscription_id}:\n"
        
        for group in response:
            respText += f"Name: {group['name']}, Location: {group['location']}\n"
    
    elif name == "create-resource-group":
        subscription_id = arguments.get("subscription_id", None)
        name = arguments.get("name")
        location = arguments.get("location")
        response = await create_resource_group(name, location, subscription_id)
        if response != None:
            respText = f"Resource Group {name} created in {subscription_id}:\n"

    elif name == "list-resources":
        subscription_id = arguments.get("subscription_id", None)
        resource_group = arguments.get("resource_group")
        result = await list_resources(resource_group, subscription_id)
        respText = f"Resources in {resource_group} in the {subscription_id}:\n"

        for resource in result:
            respText += f"Name: {resource['name']}, Type: {resource['type']}, Location: {resource['location']}\n"
    
    else:
        respText = "Invalid tool name."
    
    return [
            types.TextContent(
                type="text",
                text=respText
            )
        ]

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

async def create_resource_group(name: str, location: str, subscription_id=None) -> list[dict[str, Any]]:
    """Create a resource group in the subscription.
    
    Args:
        subscription_id (str): The subscription ID. This is an optional parameter.
        name (str): The name of the resource group.
        location (str): The location of the resource group
    """
    credential = EnvironmentCredential()
    if subscription_id is None:
        if "AZURE_SUBSCRIPTION_ID" not in os.environ:
            raise ValueError("subscription_id must be provided or set as an environment variable.")
        else:
            subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

    resource_client = ResourceManagementClient(credential, subscription_id)
    rg_result = resource_client.resource_groups.create_or_update(
        name, {"location": location}
    )

    return rg_result

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