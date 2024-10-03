from sprinkler.classes.AbstractMqttClient import AbstractMqttClient
from sprinkler.classes.test_classes.ParsedDeviceToServerStatusMessage import ParsedDeviceToServerStatusMessage
import sprinkler.constants as spinkler_constants
from sprinkler.service.device_service import handle_device_status
import paho.mqtt.client as mqtt
from django.http import JsonResponse
from homeAutomation import settings


class RealMqttClient(AbstractMqttClient):

    client = None

    def __init__(self):
        self.init_mqtt()

    def on_device_status(self, mqtt_client, userdata, msg):

        parsed_message = ParsedDeviceToServerStatusMessage(msg)

        handle_device_status(parsed_message.device_id, parsed_message.status)

    def on_device_status(self, mqtt_client, userdata, msg):
        parsed_message = ParsedDeviceToServerStatusMessage(msg)

        handle_device_status(parsed_message.device_id, parsed_message.status)

    def on_connect(self, mqtt_client, userdata, flags, rc):
        if rc == 0:
            print('Connected to mqtt server')
            mqtt_client.subscribe(spinkler_constants.DEVICE_STATUS_TOPIC)
        else:
            print('Bad connection. Code:', rc)

    def on_disconnect(self, mqtt_client, userdata, rc):
        if rc != 0:
            print(f"Unexpected disconnect from mqtt broker with code {rc}")

    def init_mqtt(self):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.message_callback_add(spinkler_constants.DEVICE_STATUS_TOPIC, self.on_device_status)
        client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
        client.connect(
            host=settings.MQTT_SERVER,
            port=settings.MQTT_PORT,
            keepalive=settings.MQTT_KEEPALIVE
        )
        client.loop_start()

    def send_mqtt_message(self, topic, body) -> JsonResponse:
        # TODO: validate message

        if not self.client:
            raise Exception("mqtt client has not been initialized")

        # cast body to string if needed
        if not type(body) == str:
            body = str(body)
        rc, mid = self.client.publish(topic, body)
        return JsonResponse({'code': rc})