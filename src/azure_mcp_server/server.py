from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

import azure.tools.resourcegroup as azrg
import azure.tools.resources as azr
import azure.tools.subscription as azs

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
        response = await azs.list_subscriptions()
        respText = "Subscriptions:\n"
        
        for subscription in response:
            respText += f"ID: {subscription['id']}, Name: {subscription['name']}\n"
    
    elif name == "list-resource-groups":
        subscription_id = arguments.get("subscription_id", None)
        response = await azrg.list_resource_groups(subscription_id)
        respText = f"Resource Groups in {subscription_id}:\n"
        
        for group in response:
            respText += f"Name: {group['name']}, Location: {group['location']}\n"
    
    elif name == "create-resource-group":
        subscription_id = arguments.get("subscription_id", None)
        name = arguments.get("name")
        location = arguments.get("location")
        response = await azrg.create_resource_group(name, location, subscription_id)
        if response != None:
            respText = f"Resource Group {name} created in {subscription_id}:\n"

    elif name == "list-resources":
        subscription_id = arguments.get("subscription_id", None)
        resource_group = arguments.get("resource_group")
        result = await azr.list_resources(resource_group, subscription_id)
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
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )