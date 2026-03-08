import hashlib
import logging
import time
from typing import Callable

import requests
from requests import Timeout, RequestException

class Message:
    id: int
    text: str
    sent_at: int

    def __init__(self, id: int, text: str, sent_at: int):
        self.id = id
        self.text = text
        self.sent_at = sent_at


class WebBot:
    def __init__(self, server_url, token, logger: logging.Logger = None, **kwargs):
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
        else:
            self.timeout = 5

        if "cooldown" in kwargs:
            self.cooldown = kwargs["cooldown"]
        else:
            self.cooldown = 1

        self.next_step_handler = None

        try:
            res = requests.get(self.server_url + "/auth/validate-token", params={
                "token_hash": self.token_hash,
            }, timeout=self.timeout)
            res.raise_for_status()

            if not res.json()["valid"]:
                self.logger.error("Token validation failed")
                exit(0)
        except Timeout:
            self.logger.error("Can't connect to the server: Timeout")
            return
        except RequestException as e:
            self.logger.warning(f"API returned non-200 status code: {e}")
            return

        # TODO: Version warnings

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
            self.logger.error("Can't connect to the server: Timeout")
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
            self.logger.error("Can't connect to the server: Timeout")
            return
        except RequestException as e:
            self.logger.warning(f"API returned non-200 status code: {e}")
            return

        for message in res.json():
            message = Message(message["id"], message["content"], message["sent_at"])

            if self.next_step_handler is not None:
                self.next_step_handler(message)
                self.next_step_handler = None
                continue

            for handler in self.handlers:
                handler(message)
            self._mark_as_handled(message.id)

    def send_message(self, text):
        if len(text) > 2048:
            self.logger.error("Message length must be <=2048")
            return

        try:
            res = requests.post(self.server_url + "/bot/message",  headers={
                "Authorization": self.token_hash,
            }, json={
                "content": text
            }, timeout=self.timeout)
            res.raise_for_status()
        except Timeout:
            self.logger.error("Can't connect to the server: Timeout")
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
