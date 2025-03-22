from azure.identity import EnvironmentCredential
from azure.mgmt.resource import ResourceManagementClient
import os
from typing import Any

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