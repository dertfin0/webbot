import hashlib
import logging
import time
from typing import Callable

import requests
from requests import Timeout, RequestException

from errors import VersionError, TokenValidationError, InitRequestError


class Message:
    id: int
    text: str
    sent_at: int

    def __init__(self, id: int, text: str, sent_at: int):
        self.id = id
        self.text = text
        self.sent_at = sent_at


class WebBot:

    VERSION = "0.1.1"

    def __init__(self, server_url, token, logger: logging.Logger = None, **kwargs):
        """
        Initialize a WebBot instance
        :param server_url: API-server URL. Example: http://1.2.3.4:8000
        :param token: API-server token
        :raise VersionError: Critical difference in version
        :raise TokenValidationError: Token validation failed
        :raise InitRequestError: Request error in required requests
        """
        self.server_url = server_url
        self.token = token
        self.token_hash = hashlib.sha256(self.token.encode()).hexdigest()
        self.handlers = []
        if logger is None:
            self.logger = logging.getLogger("WebBot")
        else:
            self.logger = logger

        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            logger.debug("Setting timeout to {}s".format(self.timeout))
        else:
            self.timeout = 5

        if "cooldown" in kwargs:
            self.cooldown = kwargs["cooldown"]
            logger.debug("Setting cooldown to {}s".format(self.cooldown))
        else:
            self.cooldown = 1

        self.next_step_handler = None

        self.logger.debug("Validating library/api version")
        try:
            res = requests.get(self.server_url + "/version", timeout=self.timeout)
            res.raise_for_status()

            library = self.VERSION.split(".")
            api = res.json().split(".")

            if api[0] > library[0]:
                message = f"Library is too outdated to run the bot. Try to run: pip install webbot={res.json()}"
                self.logger.warning(message)
                raise VersionError(message)
            elif api[0] < library[0]:
                message = f"API version is too outdated to run the bot. Update API and run again"
                self.logger.warning(message)
                raise VersionError(message)
            elif api[1] > library[1]:
                self.logger.warning(f"Library version is outdated. Some features may not be available. Update lib and run again: pip install webbot={res.json()}")
            elif api[2] > library[2]:
                self.logger.warning(f"Library version is outdated. Some bugfix may not be available. Update lib and run again: pip install webbot={res.json()}")
        except Timeout as e:
            message = "Can't connect to the server: Timeout"
            self.logger.warning(message, exc_info=e)
            raise InitRequestError(message) from e
        except RequestException as e:
            message = f"API returned non-200 status code: {e}"
            self.logger.warning(message, exc_info=e)
            raise InitRequestError(message) from e

        self.logger.debug("Validating bot token")
        try:
            res = requests.get(self.server_url + "/auth/validate-token", params={
                "token_hash": self.token_hash,
            }, timeout=self.timeout)
            res.raise_for_status()

            if not res.json()["valid"]:
                self.logger.error("Token validation failed")
                raise TokenValidationError("Token validation failed")
        except Timeout:
            self.logger.error("Can't connect to the server: Timeout")
            return
        except RequestException as e:
            self.logger.warning(f"API returned non-200 status code: {e}")
            return

    def message_handler(self):
        def wrapper(func):
            self.handlers.append(func)
            return func
        return wrapper

    def _mark_as_handled(self, message_id):
        try:
            res = requests.patch(self.server_url + "/bot/handled", headers={
                "Authorization": self.token_hash
            }, json={
                "id": message_id
            }, timeout=self.timeout)
            res.raise_for_status()
        except Timeout:
            self.logger.warning("Can't connect to the server: Timeout")
            return
        except RequestException as e:
            self.logger.warning(f"API returned non-200 status code: {e}")
            return

    def _update(self):
        try:
            res = requests.get(self.server_url + "/bot/update", headers={
                "Authorization": self.token_hash,
            }, timeout=self.timeout)
            res.raise_for_status()
        except Timeout:
            self.logger.warning("Can't connect to the server: Timeout")
            return
        except RequestException as e:
            self.logger.warning(f"API returned non-200 status code: {e}")
            return

        for message in res.json():
            message = Message(message["id"], message["content"], message["sent_at"])

            if self.next_step_handler is not None:
                self.next_step_handler(message)
                self._mark_as_handled(message.id)
                self.next_step_handler = None
                continue

            for handler in self.handlers:
                handler(message)
            self._mark_as_handled(message.id)

    def send_message(self, text):
        if len(text) > 2048:
            self.logger.warning("Message length must be <=2048")
            return

        try:
            res = requests.post(self.server_url + "/bot/message",  headers={
                "Authorization": self.token_hash,
            }, json={
                "content": text
            }, timeout=self.timeout)
            res.raise_for_status()
        except Timeout:
            self.logger.warning("Can't connect to the server: Timeout")
            return
        except RequestException as e:
            self.logger.warning(f"API returned non-200 status code: {e}")
            return

    def register_next_step_handler(self, handler: Callable):
        """
        Register the only handler that will be called for next message
        :param handler: Function(message)
        """
        self.next_step_handler = handler

    def infinity_polling(self):
        while True:
            self._update()
            time.sleep(self.cooldown)
