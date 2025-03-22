from azure.identity import EnvironmentCredential
from azure.mgmt.subscription import SubscriptionClient
from typing import Any

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