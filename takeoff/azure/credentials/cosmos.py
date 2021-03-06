from dataclasses import dataclass

import voluptuous as vol
from azure.mgmt.cosmosdb import CosmosDB

from takeoff.application_version import ApplicationVersion
from takeoff.azure.credentials.active_directory_user import ActiveDirectoryUserCredentials
from takeoff.azure.credentials.keyvault import KeyVaultClient
from takeoff.azure.credentials.subscription_id import SubscriptionId
from takeoff.azure.util import get_resource_group_name, get_cosmos_name
from takeoff.schemas import TAKEOFF_BASE_SCHEMA


@dataclass(frozen=True)
class CosmosInfo(object):
    client: CosmosDB
    instance: dict
    endpoint: str


@dataclass(frozen=True)
class CosmosCredentials(object):
    uri: str
    key: str


SCHEMA = TAKEOFF_BASE_SCHEMA.extend(
    {
        "azure": {
            vol.Required(
                "cosmos_naming",
                description=(
                    "Naming convention for the resource."
                    "This should include the {env} parameter. For example"
                    "cosmos_{env}"
                ),
            ): str
        }
    }
)


class Cosmos(object):
    def __init__(self, env: ApplicationVersion, config: dict):
        self.env = env
        self.config = SCHEMA.validate(config)

    def _get_cosmos_management_client(self) -> CosmosDB:
        vault, client = KeyVaultClient.vault_and_client(self.config, self.env)
        credentials = ActiveDirectoryUserCredentials(vault_name=vault, vault_client=client).credentials(
            self.config
        )
        return CosmosDB(credentials, SubscriptionId(vault, client).subscription_id(self.config))

    def _get_cosmos_instance(self) -> dict:
        return {
            "resource_group_name": get_resource_group_name(self.config, self.env),
            "account_name": get_cosmos_name(self.config, self.env),
        }

    @staticmethod
    def _get_cosmos_endpoint(cosmos: CosmosDB, cosmos_instance: dict):
        return cosmos.database_accounts.get(**cosmos_instance).document_endpoint

    def _get_instance(self) -> CosmosInfo:
        cosmos = self._get_cosmos_management_client()
        cosmos_instance = self._get_cosmos_instance()
        endpoint = self._get_cosmos_endpoint(cosmos, cosmos_instance)
        return CosmosInfo(cosmos, cosmos_instance, endpoint)

    def get_cosmos_write_credentials(self) -> CosmosCredentials:
        cosmos = self._get_instance()
        key = cosmos.client.database_accounts.list_keys(**cosmos.instance).primary_master_key

        return CosmosCredentials(cosmos.endpoint, key)

    def get_cosmos_read_only_credentials(self) -> CosmosCredentials:
        cosmos = self._get_instance()

        key = cosmos.client.database_accounts.list_read_only_keys(
            **cosmos.instance
        ).primary_readonly_master_key

        return CosmosCredentials(cosmos.endpoint, key)
