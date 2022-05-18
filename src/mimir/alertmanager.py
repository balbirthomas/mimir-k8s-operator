import yaml
import logging

from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen, Request

from .config import MIMIR_PORT

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, host="localhost", tenant="anonymous", timeout=10):
        self._tenant = tenant
        self._host = host
        self._timeout = timeout
        self._base_url = f"http://{self._host}:{MIMIR_PORT}"

    def set_config(self, config):
        url = urljoin(self._base_url, "/api/v1/alerts")
        headers = {"Content-Type": "application/yaml"}
        post_data = yaml.dump(config).encode('utf-8')
        response = self._post(url, post_data, headers=headers)

        return response

    def set_alert_rule_group(self, group):
        url = urljoin(self._base_url, f"/prometheus/config/v1/rules/{self._tenant}")
        headers = {"Content-Type": "application/yaml"}
        post_data = yaml.dump(group).encode('utf-8')
        response = self._post(url, post_data, headers=headers)

        return response

    def delete_alert_rule_group(self, groupname):
        url = urljoin(self._base_url, f"/prometheus/config/v1/rules/{self._tenant}/{groupname}")
        response = self._delete(url)

        return response

    def _get(self, url, headers=None, timeout=None, encoding='utf-8') -> str:
        body = ""
        request = Request(url, headers=headers or {}, method="GET")
        timeout = timeout if timeout else self._timeout

        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
                charset = response.headers.get_content_charset()
                enc = charset if charset else encoding
                body = body.decode(encoding=enc)
        except HTTPError as error:
            logger.error(
                "Failed to fetch %s, status: %s, reason: %s", url, error.status, error.reason
            )
        except URLError as error:
            logger.error("Invalid URL %s", url)
        except TimeoutError:
            logger.error("Request timeout fetching URL %s", url)

        return body

    def _post(self, url, post_data, headers=None, timeout=None) -> str:
        status = ""
        timeout = timeout if timeout else self._timeout
        request = Request(url, headers=headers or {}, data=post_data, method="POST")

        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.status
        except HTTPError as error:
            logger.error(
                "Failed posting to %s, status: %s, reason: %s", url, error.status, error.reason
            )
        except URLError as error:
            logger.error("Invalid URL %s", url)
        except TimeoutError:
            logger.error("Request timeout during posting to URL %s", url)

        return status

    def _delete(self, url, headers=None, timeout=None) -> str:
        status = ""
        timeout = timeout if timeout else self._timeout
        request = Request(url, headers=headers or {}, method="DELETE")

        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.status
        except HTTPError as error:
            logger.error(
                "Delete failed %s, status: %s, reason: %s", url, error.status, error.reason
            )
        except URLError as error:
            logger.error("Invalid URL %s", url)
        except TimeoutError:
            logger.error("Request timeout deleting %s", url)

        return status