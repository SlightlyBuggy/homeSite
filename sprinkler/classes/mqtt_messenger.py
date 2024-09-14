import paho.mqtt.client as mqtt
from django.http import JsonResponse


class MqttMessenger:

    # server to device topic
    SERVER_TO_DEVICE_TOPIC = 'command'

    # device to server
    DEVICE_STATUS_TOPIC = 'device_status'

    MQTT_SERVER = '127.0.0.1'
    MQTT_PORT = 1883
    MQTT_KEEPALIVE = 60
    MQTT_USER = ''
    MQTT_PASSWORD = ''

    def __init__(self, device_status_message_handler):

        self.client = None
        self.on_device_status_message_handler = device_status_message_handler

    @staticmethod
    def on_message(mqtt_client, userdata, msg):
        print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')

    def on_connect(self, mqtt_client, userdata, flags, rc):
        if rc == 0:
            print('Connected to mqtt server')

            # TODO: move to a generic topic for device -> server
            mqtt_client.subscribe(self.DEVICE_STATUS_TOPIC)
        else:
            print('Bad connection. Code:', rc)

    @staticmethod
    def on_disconnect(mqtt_client, userdata, rc):
        if rc != 0:
            print(f"Unexpected disconnect from mqtt broker with code {rc}")

    def send_message(self, body) -> JsonResponse:
        """
        Send a message to the devices
        """

        # cast body to string if needed
        if not type(body) == str:
            body = str(body)
        rc, mid = self.client.publish(self.SERVER_TO_DEVICE_TOPIC, body)
        return JsonResponse({'code': rc})

    def init_connection(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # set callbacks
        self.client.message_callback_add('device_status', self.on_device_status_message_handler)

        self.client.username_pw_set(self.MQTT_USER, self.MQTT_PASSWORD)
        self.client.connect(
            host=self.MQTT_SERVER,
            port=self.MQTT_PORT,
            keepalive=self.MQTT_KEEPALIVE
        )


def build_mqtt_messenger(on_device_status_message_handler):
    return MqttMessenger(on_device_status_message_handler)
