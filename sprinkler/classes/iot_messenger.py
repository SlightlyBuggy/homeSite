from sprinkler.classes.mqtt_messenger import build_mqtt_messenger
from sprinkler.classes.iot_message_handler import build_iot_message_handler


class IotMessenger:

    def __init__(self):
        self.message_handler = build_iot_message_handler()
        self.messenger = self.create_messenger()

        # should I be doing this?
        self.message_handler.set_message_sender(self.send_message)

        # start the loop
        self.messenger.client.loop_start()

    def create_messenger(self):
        return build_mqtt_messenger(self.message_handler.mqtt_device_status_message_handler)

    def send_message(self, message):
        self.messenger.send_message(message)



def build_iot_messenger():
    return IotMessenger()
