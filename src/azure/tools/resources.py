from azure.identity import EnvironmentCredential
from azure.mgmt.resource import ResourceManagementClient
import os
from typing import Any

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