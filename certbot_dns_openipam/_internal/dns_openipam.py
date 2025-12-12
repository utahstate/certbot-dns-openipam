"""DNS Authenticator for OpenIPAM."""
import logging
import requests
import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from certbot import errors
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

logger = logging.getLogger(__name__)

ACCOUNT_URL = 'https://openipam.usu.edu/api/'


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for OpenIPAM

    This Authenticator uses the OpenIPAM API to fulfill a dns-01 challenge.
    """

    description = ('Obtain certificates using a DNS TXT record (if you are using OpenIPAM for '
                   'DNS).')
    ttl = 300

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.credentials: Optional[CredentialsConfiguration] = None

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None],
                             default_propagation_seconds: int = 180) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add('credentials', help='OpenIPAM credentials INI file.')

    def more_info(self) -> str:
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'the OpenIPAM API.'

    def _validate_credentials(self, credentials: CredentialsConfiguration) -> None:
        token = credentials.conf('api-token')
        if not token:
            raise errors.PluginError('{}: The dns_openipam_api_token is required. ')

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            'credentials',
            'OpenIPAM credentials INI file',
            None,
            self._validate_credentials
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_openipam_client().add_txt_record(domain, validation_name, validation, self.ttl)

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_openipam_client().del_txt_record(domain, validation_name, validation)

    def _get_openipam_client(self) -> "_OpenIPAMClient":
        if not self.credentials:  # pragma: no cover
            raise errors.Error("Plugin has not been prepared.")
        if self.credentials.conf('api-token'):
            return _OpenIPAMClient(None, self.credentials.conf('api-token'))


class _OpenIPAMClient:
    """
    Encapsulates all communication with the OpenIPAM API.
    """

    def __init__(self, email: Optional[str],api_key: str) -> None:
        self.api_key = api_key

    def add_txt_record(self, domain: str, record_name: str, record_content: str,
                       record_ttl: int) -> None:
        """
        Add a TXT record using the supplied information.

        :param str domain: The domain to use to look up the OpenIPAM zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the Cloudflare API
        """
        try:
            data = {'dns_type': 'TXT',
                    'name': record_name,
                    'content': record_content,
                    'ttl': record_ttl}
            logger.debug('Attempting to add record: %s', data)
            res = requests.post(
                f"{ACCOUNT_URL}dns/add/",
                data,
                headers={
                    "Authorization": f"Token {self.api_key}",
                },
            )
            if res.status_code != 201:
                raise Exception(f"Failed to add DNS record: {res.text}")
        except Exception as e:
            print(f"Error: {e}")
            print("Unable to create DNS record automatically.")

        logger.debug('Successfully added TXT record: %s', record_name)

    def del_txt_record(self, domain: str, record_name: str, record_content: str) -> None:
        """
        Delete a TXT record using the supplied information.

        Note that both the record's name and content are used to ensure that similar records
        created concurrently (e.g., due to concurrent invocations of this plugin) are not deleted.

        Failures are logged, but not raised.

        :param str domain: The domain to use to look up the Cloudflare zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        """
        record_id = self._find_txt_record_id(record_name)
        if record_id:
            try:
                logger.debug('Attempting to delete record: %s', record_name)
                res = requests.delete(
                    f"{ACCOUNT_URL}dns/{record_id}/delete/",
                    headers={
                        "Authorization": f"Token {self.api_key}",
                    },
                )
                if res.status_code != 204:
                    raise Exception(f"Failed to delete DNS record: {res.text}")
                logger.debug('Successfully deleted TXT record with record_id: %s', record_id)
            except Exception as e:
                print(f"Error: {e}")
                print("Unable to delete DNS record automatically.")
        else:
            logger.debug('TXT record not found; no cleanup needed.')

    def _find_txt_record_id(self, record_name: str) -> Optional[str]:
        """
        Find the record_id for a TXT record with the given name and content.

        :param str zone_id: The zone_id which contains the record.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :returns: The record_id, if found.
        :rtype: str
        """
        try:
            logger.debug('Attempting to find record: %s', record_name)
            res = requests.get(
                f"{ACCOUNT_URL}dns/?name={record_name}",
                headers={
                    "Authorization": f"Token {self.api_key}",
                },
            )
            if res.status_code != 200:
                raise Exception(f"Failed to find DNS record: {res.text}")
            records = json.loads(res.content)
        except Exception as e:
            print(f"Error: {e}")
            records = []

        if records:
            # Cleanup is returning the system to the state we found it. If, for some reason,
            # there are multiple matching records, we only delete one because we only added one.
            return records['results'][0]['id']
        logger.debug('Unable to find TXT record.')
        return None
