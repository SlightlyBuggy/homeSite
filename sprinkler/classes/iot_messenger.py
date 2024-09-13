from mqtt_messenger import build_mqtt_messenger
from iot_message_handler import build_iot_message_handler


class IotMessenger:

    def __init__(self):
        self.message_handler = build_iot_message_handler()
        self.messenger = build_mqtt_messenger(self.message_handler)


def build_iot_messenger():
    return IotMessenger()