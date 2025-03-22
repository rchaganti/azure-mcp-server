from typing import Any
import os

from azure.mgmt.storage import StorageManagementClient
from azure.identity import EnvironmentCredential

async def check_storage_account_name_availability(subscription_id, storage_account_name) -> list[dict[str, Any]]:
    """Check if the specified storage account name is available or a valid storage account name.
    
    Args:
        subscription_id (str): The subscription ID. This is an optional parameter.
        storage_account_name (str): The name of the storage account.
    """
    credential = EnvironmentCredential()
    if subscription_id is None:
        if "AZURE_SUBSCRIPTION_ID" not in os.environ:
            raise ValueError("subscription_id must be provided or set as an environment variable.")
        else:
            subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

    storage_client = StorageManagementClient(credential, subscription_id)

    availability_result = storage_client.storage_accounts.check_name_availability(
        { "name": storage_account_name }
    )

    return {
        "storage_account_name": storage_account_name,
        "is_name_available": availability_result.name_available,
        "reason": availability_result.reason,
    }
