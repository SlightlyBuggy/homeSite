import json


class DeviceToServerStatusMessage:
    def __init__(self, raw_message):
        self.raw_message = raw_message

        self.topic = None
        self.device_id = None
        self.status = None
        self.status = {}

        self.parse_message()

    def parse_message(self):
        try:
            self.topic = self.raw_message.topic
        except AttributeError as e:
            raise AttributeError(f"Raw message missing 'topic' attribute: {self.raw_message}")

        # this is mainly for testing
        if self.topic is None:
            raise AttributeError(f"Message topic is None: {self.raw_message}")

        try:
            raw_payload = self.raw_message.payload
        except AttributeError:
            raise AttributeError(f"Message missing 'payload' attribute: {self.raw_message}")

        # this is mainly for testing
        if raw_payload is None:
            raise AttributeError(f"Message payload is None: {self.raw_message}")

        try:
            payload = json.loads(self.raw_message.payload)
        except TypeError as e:
            raise TypeError(f"Unable to parse raw message: {self.raw_message}")
        except AttributeError as e:
            raise AttributeError(f"Raw message missing 'payload' attribute: {self.raw_message}")

        try:
            self.device_id = payload['device_id']
        except KeyError as e:
            raise KeyError(f"Message payload missing 'device_id' key: {self.raw_message}")

        if not type(self.device_id) == int:
            raise TypeError(f"Device id should be an int in message {self.raw_message}")

        try:
            self.status = payload['status']
        except KeyError as e:
            raise KeyError(f"Message payload missing 'status' key: {self.raw_message}")