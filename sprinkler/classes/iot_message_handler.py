import json
import sprinkler.service.device_service as device_service


class IotMessageHandler:

    _messenge_sender = None

    def __init__(self):
        pass

    def set_message_sender(self, message_sender):
        self._messenge_sender = message_sender

    def mqtt_device_status_message_handler(self, mqtt_client, userdata, msg):
        return self.device_status_message_handler(msg)

    def device_status_message_handler(self, msg):
        """
        This is the landing point for messages from a device.  From here they are routed to the appropriate specific
        handler
        msg: message from device
        """
        print(f'Received message from device with payload: {msg.payload}')

        try:
            message_contents = json.loads(msg.payload)
        except json.decoder.JSONDecodeError:
            print("JSON message could not be decoded")
            return

        if 'device_id' not in message_contents:
            print("Unable to handle status message.  'device_id' not present")
            return

        if 'status' not in message_contents:
            print("Unable to handle status message.  'status' not present.")

        device_id = message_contents['device_id']
        status = message_contents['status']

        # TODO: depending on message contents, route to other handlers from here
        message_to_send = device_service.handle_device_status(device_id=device_id, status=status)

        if message_to_send:
            self._messenge_sender(message_to_send)


def build_iot_message_handler():

    return IotMessageHandler()
