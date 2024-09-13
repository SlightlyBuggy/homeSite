import json

class IotMessageHandler:

    def __init__(self):
        pass

    def device_to_server_message_handler(self, mqtt_client, userdata, msg):
        """
        This is the landing point for messages from a device.  From here they are routed to the appropriate specific
        handler
        msg: message from device
        """
        print(f'Received message from device with payload: {msg.payload}')

        try:
            message_contents = json.loads(msg.payload)

        # TODO: depending on message contents, route to other handlers from here


def build_iot_message_handler():

    return IotMessageHandler()
